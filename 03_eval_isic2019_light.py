import time
import pickle
import heapq
import numpy as np
import pandas as pd
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

VECTORS_DIR = Path(r"C:\Users\hp\Desktop\PFE\Vectors-ISIC2019")
RESULTS_DIR = VECTORS_DIR / "analysis_results_light"
RESULTS_DIR.mkdir(exist_ok=True)

FUSION_FILE = VECTORS_DIR / "fusion_compressed_384D.npy"
LABELS_FILE = VECTORS_DIR / "labels.npy"
IMAGE_IDS_FILE = VECTORS_DIR / "image_ids.npy"
METADATA_FILE = VECTORS_DIR / "metadata.csv"
GRAPH_FILE = VECTORS_DIR / "hjg_graph_light.pkl"

CNN_DIM = 256
ALPHA_FINAL = 0.1
SEED = 42

N_QUERIES_GLOBAL = 500
N_QUERIES_PER_CLASS = 150
K_VALUES = [5, 10, 20]

CLASS_NAMES = {
    0: "MEL",
    1: "NV",
    2: "BCC",
    3: "AK",
    4: "BKL",
    5: "DF",
    6: "VASC",
    7: "SCC",
}

FULL_NAMES = {
    0: "Melanoma",
    1: "Melanocytic nevus",
    2: "Basal cell carcinoma",
    3: "Actinic keratosis",
    4: "Benign keratosis",
    5: "Dermatofibroma",
    6: "Vascular lesion",
    7: "Squamous cell carcinoma",
}


# ============================================================
# CHARGEMENT
# ============================================================

def l2_normalize(x):
    return x / (np.linalg.norm(x, axis=1, keepdims=True) + 1e-8)


def load_data():
    print("=" * 70)
    print("ÉVALUATION ISIC 2019 LIGHT 384D")
    print("=" * 70)

    fusion = np.load(FUSION_FILE).astype(np.float32)
    labels = np.load(LABELS_FILE)
    image_ids = np.load(IMAGE_IDS_FILE, allow_pickle=True)

    assert fusion.shape[1] == 384, f"Attendu 384D, obtenu {fusion.shape[1]}D"

    cnn = fusion[:, :CNN_DIM]
    vit = fusion[:, CNN_DIM:]

    assert cnn.shape[1] == 256
    assert vit.shape[1] == 128

    cnn = l2_normalize(cnn)
    vit = l2_normalize(vit)

    with open(GRAPH_FILE, "rb") as f:
        hjg = pickle.load(f)

    print(f"Images : {len(labels)}")
    print(f"CNN : {cnn.shape[1]}D | ViT : {vit.shape[1]}D")

    unique, counts = np.unique(labels, return_counts=True)
    print("\nDistribution :")
    for u, c in zip(unique, counts):
        print(f"  {u} = {CLASS_NAMES.get(int(u), str(u))} : {c}")

    print("=" * 70 + "\n")

    return cnn, vit, labels, image_ids, hjg


# ============================================================
# DISTANCE
# ============================================================

def d_joint(q_cnn, q_vit, cnn, vit, idx, alpha=ALPHA_FINAL):
    dc = np.sqrt(np.einsum("ij,ij->i", cnn[idx] - q_cnn, cnn[idx] - q_cnn))
    dv = 1.0 - (vit[idx] @ q_vit)
    return alpha * dc + (1.0 - alpha) * dv


def get_ranked_bruteforce(q_idx, cnn, vit, alpha=ALPHA_FINAL):
    idx = np.arange(len(cnn))
    d = d_joint(cnn[q_idx], vit[q_idx], cnn, vit, idx, alpha)
    d[q_idx] = np.inf
    return np.argsort(d)


# ============================================================
# HJG SEARCH
# ============================================================

def search_hjg(q_cnn, q_vit, hjg, cnn, vit, top_k=10, ef=60, exclude_idx=None):
    joint = hjg["joint"]
    coarse_idx = hjg["coarse_idx"]
    coarse = hjg["coarse"]

    def jd(idx):
        idx_arr = np.array([idx], dtype=np.int32)
        return float(d_joint(q_cnn, q_vit, cnn, vit, idx_arr)[0])

    start_local = int(np.random.randint(0, len(coarse_idx)))
    start_global = int(coarse_idx[start_local])

    visited_c = {start_local}
    heap_c = [(jd(start_global), start_local, start_global)]

    best_global = start_global
    best_distance = jd(start_global)

    while heap_c:
        d_cur, l_cur, g_cur = heapq.heappop(heap_c)

        if d_cur > best_distance * 2.0:
            break

        for _, g_nb in coarse[l_cur]:
            locs = np.where(coarse_idx == g_nb)[0]
            if len(locs) == 0:
                continue

            l_nb = int(locs[0])

            if l_nb in visited_c:
                continue

            visited_c.add(l_nb)
            d = jd(g_nb)

            if d < best_distance:
                best_distance = d
                best_global = g_nb

            heapq.heappush(heap_c, (d, l_nb, g_nb))

    visited = set([best_global])
    heap = [(jd(best_global), best_global)]
    candidates = []

    while heap and len(visited) < ef:
        d_cur, idx_cur = heapq.heappop(heap)
        candidates.append((d_cur, idx_cur))

        for _, nb in joint[idx_cur]:
            if nb in visited:
                continue

            visited.add(nb)
            d = jd(nb)
            heapq.heappush(heap, (d, nb))

    all_candidates = list(set([idx for _, idx in candidates] + list(visited)))

    if exclude_idx is not None and exclude_idx in all_candidates:
        all_candidates.remove(exclude_idx)

    if len(all_candidates) == 0:
        return []

    cand_arr = np.array(all_candidates, dtype=np.int32)
    dists = d_joint(q_cnn, q_vit, cnn, vit, cand_arr)

    order = np.argsort(dists)[:top_k]

    return cand_arr[order].tolist()


# ============================================================
# MÉTRIQUES
# ============================================================

def precision_at_k(ranked, q_idx, labels, k):
    top = [i for i in ranked if i != q_idx][:k]
    if len(top) == 0:
        return 0.0
    return sum(labels[i] == labels[q_idx] for i in top) / len(top)


def recall_at_k(ranked, q_idx, labels, k):
    top = [i for i in ranked if i != q_idx][:k]
    if len(top) == 0:
        return 0.0
    total_relevant = (labels == labels[q_idx]).sum() - 1
    denom = min(k, max(1, total_relevant))
    correct = sum(labels[i] == labels[q_idx] for i in top)
    return correct / denom


def map_at_k(ranked, q_idx, labels, k):
    top = [i for i in ranked if i != q_idx][:k]
    if len(top) == 0:
        return 0.0

    hits = 0
    score = 0.0

    for rank, idx in enumerate(top, start=1):
        if labels[idx] == labels[q_idx]:
            hits += 1
            score += hits / rank

    total_relevant = (labels == labels[q_idx]).sum() - 1
    denom = min(k, max(1, total_relevant))

    return score / denom


def ndcg_at_k(ranked, q_idx, labels, k):
    top = [i for i in ranked if i != q_idx][:k]
    if len(top) == 0:
        return 0.0

    dcg = 0.0
    for rank, idx in enumerate(top):
        rel = 1.0 if labels[idx] == labels[q_idx] else 0.0
        dcg += rel / np.log2(rank + 2)

    total_relevant = (labels == labels[q_idx]).sum() - 1
    ideal_relevant = min(k, max(0, total_relevant))
    idcg = sum(1.0 / np.log2(rank + 2) for rank in range(ideal_relevant))

    return dcg / max(idcg, 1e-8)


# ============================================================
# ABLATION ALPHA BRUTE-FORCE
# ============================================================

def run_alpha_ablation(cnn, vit, labels):
    print("=" * 70)
    print("1. ABLATION ALPHA — ISIC 2019")
    print("=" * 70)

    np.random.seed(SEED)
    queries = np.random.choice(len(labels), size=min(300, len(labels)), replace=False)

    alphas = [round(i * 0.1, 1) for i in range(11)]
    rows = []

    print(f"{'alpha':>6} {'mAP@10':>10} {'P@10':>10} {'R@10':>10} {'NDCG@10':>10}")
    print("-" * 60)

    for alpha in alphas:
        maps, ps, rs, ns = [], [], [], []

        for q in queries:
            ranked = get_ranked_bruteforce(q, cnn, vit, alpha)
            maps.append(map_at_k(ranked, q, labels, 10))
            ps.append(precision_at_k(ranked, q, labels, 10))
            rs.append(recall_at_k(ranked, q, labels, 10))
            ns.append(ndcg_at_k(ranked, q, labels, 10))

        row = {
            "alpha": alpha,
            "mAP@10": round(np.mean(maps), 4),
            "P@10": round(np.mean(ps), 4),
            "R@10": round(np.mean(rs), 4),
            "NDCG@10": round(np.mean(ns), 4),
        }

        rows.append(row)

        marker = " <- alpha final" if alpha == ALPHA_FINAL else ""

        print(
            f"{alpha:>6.1f} "
            f"{row['mAP@10']:>10.4f} "
            f"{row['P@10']:>10.4f} "
            f"{row['R@10']:>10.4f} "
            f"{row['NDCG@10']:>10.4f}"
            f"{marker}"
        )

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS_DIR / "ablation_alpha_isic2019.csv", index=False)

    best = max(rows, key=lambda x: x["mAP@10"])
    print("\nMeilleur alpha :", best["alpha"])
    print("Alpha final retenu :", ALPHA_FINAL)
    print("Sauvegardé : ablation_alpha_isic2019.csv\n")


# ============================================================
# ÉVALUATION BRUTE-FORCE
# ============================================================

def evaluate_bruteforce(cnn, vit, labels):
    print("=" * 70)
    print("2. ÉVALUATION BRUTE-FORCE — QUALITÉ MAX")
    print("=" * 70)

    np.random.seed(SEED)
    queries = np.random.choice(len(labels), size=min(N_QUERIES_GLOBAL, len(labels)), replace=False)

    results = {k: {"map": [], "p": [], "r": [], "ndcg": []} for k in K_VALUES}
    times = []

    for q in queries:
        t0 = time.perf_counter()
        ranked = get_ranked_bruteforce(q, cnn, vit, ALPHA_FINAL)
        times.append((time.perf_counter() - t0) * 1000)

        for k in K_VALUES:
            results[k]["map"].append(map_at_k(ranked, q, labels, k))
            results[k]["p"].append(precision_at_k(ranked, q, labels, k))
            results[k]["r"].append(recall_at_k(ranked, q, labels, k))
            results[k]["ndcg"].append(ndcg_at_k(ranked, q, labels, k))

    row = {
        "method": "bruteforce",
        "dataset": "ISIC2019_LIGHT",
        "n_images": len(labels),
        "n_queries": len(queries),
        "alpha": ALPHA_FINAL,
        "time_ms": round(np.mean(times), 2),
    }

    for k in K_VALUES:
        row[f"mAP@{k}"] = round(np.mean(results[k]["map"]), 4)
        row[f"P@{k}"] = round(np.mean(results[k]["p"]), 4)
        row[f"R@{k}"] = round(np.mean(results[k]["r"]), 4)
        row[f"NDCG@{k}"] = round(np.mean(results[k]["ndcg"]), 4)

    pd.DataFrame([row]).to_csv(RESULTS_DIR / "metrics_bruteforce_isic2019.csv", index=False)

    for key, value in row.items():
        print(f"{key:<15} : {value}")

    print("Sauvegardé : metrics_bruteforce_isic2019.csv\n")


# ============================================================
# ÉVALUATION HJG
# ============================================================

def evaluate_hjg(cnn, vit, labels, hjg):
    print("=" * 70)
    print("3. ÉVALUATION HJG LIGHT")
    print("=" * 70)

    np.random.seed(SEED)
    queries = np.random.choice(len(labels), size=min(N_QUERIES_GLOBAL, len(labels)), replace=False)

    results = {k: {"map": [], "p": [], "r": [], "ndcg": []} for k in K_VALUES}
    times = []

    for q in queries:
        t0 = time.perf_counter()
        ranked = search_hjg(
            cnn[q], vit[q], hjg, cnn, vit,
            top_k=max(K_VALUES),
            ef=80,
            exclude_idx=q
        )
        times.append((time.perf_counter() - t0) * 1000)

        for k in K_VALUES:
            results[k]["map"].append(map_at_k(ranked, q, labels, k))
            results[k]["p"].append(precision_at_k(ranked, q, labels, k))
            results[k]["r"].append(recall_at_k(ranked, q, labels, k))
            results[k]["ndcg"].append(ndcg_at_k(ranked, q, labels, k))

    row = {
        "method": "hjg_light",
        "dataset": "ISIC2019_LIGHT",
        "n_images": len(labels),
        "n_queries": len(queries),
        "alpha": ALPHA_FINAL,
        "time_ms": round(np.mean(times), 2),
    }

    for k in K_VALUES:
        row[f"mAP@{k}"] = round(np.mean(results[k]["map"]), 4)
        row[f"P@{k}"] = round(np.mean(results[k]["p"]), 4)
        row[f"R@{k}"] = round(np.mean(results[k]["r"]), 4)
        row[f"NDCG@{k}"] = round(np.mean(results[k]["ndcg"]), 4)

    pd.DataFrame([row]).to_csv(RESULTS_DIR / "metrics_hjg_isic2019.csv", index=False)

    for key, value in row.items():
        print(f"{key:<15} : {value}")

    print("Sauvegardé : metrics_hjg_isic2019.csv\n")


# ============================================================
# MÉTRIQUES PAR CLASSE
# ============================================================

def evaluate_per_class(cnn, vit, labels):
    print("=" * 70)
    print("4. MÉTRIQUES PAR CLASSE — BRUTE-FORCE")
    print("=" * 70)

    rows = []

    for cls in np.unique(labels):
        cls = int(cls)
        cls_idx = np.where(labels == cls)[0]

        np.random.seed(SEED + cls)
        queries = np.random.choice(
            cls_idx,
            size=min(N_QUERIES_PER_CLASS, len(cls_idx)),
            replace=False
        )

        maps, ps, rs, ns = [], [], [], []

        for q in queries:
            ranked = get_ranked_bruteforce(q, cnn, vit, ALPHA_FINAL)
            maps.append(map_at_k(ranked, q, labels, 10))
            ps.append(precision_at_k(ranked, q, labels, 10))
            rs.append(recall_at_k(ranked, q, labels, 10))
            ns.append(ndcg_at_k(ranked, q, labels, 10))

        row = {
            "classe": cls,
            "code": CLASS_NAMES.get(cls, str(cls)),
            "full_name": FULL_NAMES.get(cls, str(cls)),
            "n_images": len(cls_idx),
            "n_queries": len(queries),
            "mAP@10": round(np.mean(maps), 4),
            "P@10": round(np.mean(ps), 4),
            "R@10": round(np.mean(rs), 4),
            "NDCG@10": round(np.mean(ns), 4),
        }

        rows.append(row)

        print(
            f"{cls} {row['code']:<5} | N={row['n_images']:<6} | "
            f"mAP@10={row['mAP@10']} | P@10={row['P@10']}"
        )

    macro = {
        "classe": "MACRO_AVG",
        "code": "MACRO",
        "full_name": "Macro average",
        "n_images": len(labels),
        "n_queries": sum(r["n_queries"] for r in rows),
        "mAP@10": round(np.mean([r["mAP@10"] for r in rows]), 4),
        "P@10": round(np.mean([r["P@10"] for r in rows]), 4),
        "R@10": round(np.mean([r["R@10"] for r in rows]), 4),
        "NDCG@10": round(np.mean([r["NDCG@10"] for r in rows]), 4),
    }

    rows.append(macro)

    print("\nMACRO AVG")
    print(macro)

    pd.DataFrame(rows).to_csv(RESULTS_DIR / "metrics_per_class_isic2019.csv", index=False)
    print("Sauvegardé : metrics_per_class_isic2019.csv\n")


# ============================================================
# MAIN
# ============================================================

def main():
    cnn, vit, labels, image_ids, hjg = load_data()

    run_alpha_ablation(cnn, vit, labels)
    evaluate_bruteforce(cnn, vit, labels)
    evaluate_hjg(cnn, vit, labels, hjg)
    evaluate_per_class(cnn, vit, labels)

    print("=" * 70)
    print("FIN ANALYSE ISIC 2019")
    print("=" * 70)
    print("Résultats dans :")
    print(RESULTS_DIR)


if __name__ == "__main__":
    main()