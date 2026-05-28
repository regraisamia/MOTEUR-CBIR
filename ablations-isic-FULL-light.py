"""
Analyse finale — ISIC 2020 complet — Version compressée 384D
============================================================

Ce script évalue la version finale du système CBIR médical :

- Dataset : ISIC 2020 complet
- Vecteurs : fusion_compressed_384D.npy
- CNN compressé : 256D
- ViT compressé : 128D
- Distance jointe : alpha * d_CNN + (1-alpha) * d_ViT
- Alpha final retenu : 0.1

Fichiers générés :
- ablation_alpha_light.csv
- metrics_global_light.csv
- metrics_per_class_light.csv
- metrics_malignant_light.csv
- scalability_light.csv

Usage :
python 03_ablations_isic_full_light.py
"""

import time
import numpy as np
import pandas as pd
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

VECTORS_DIR = Path(r"C:\Users\hp\Desktop\PFE\Vectors-ISIC-FULL")
RESULTS_DIR = VECTORS_DIR / "analysis_results_light"
RESULTS_DIR.mkdir(exist_ok=True)

FUSION_FILE = VECTORS_DIR / "fusion_compressed_384D.npy"
LABELS_FILE = VECTORS_DIR / "labels.npy"

CNN_DIM = 256
EXPECTED_TOTAL_DIM = 384
EXPECTED_VIT_DIM = 128

ALPHA_FINAL = 0.1
SEED = 42

N_QUERIES_GLOBAL = 500
N_QUERIES_PER_CLASS = 200

K_VALUES = [5, 10, 20]


# ============================================================
# CHARGEMENT
# ============================================================

def load_data():
    print("=" * 70)
    print("CHARGEMENT DES VECTEURS ISIC 2020 COMPLET — VERSION 384D")
    print("=" * 70)

    fusion = np.load(FUSION_FILE).astype(np.float32)
    labels = np.load(LABELS_FILE)

    assert fusion.shape[1] == EXPECTED_TOTAL_DIM, (
        f"Erreur : attendu {EXPECTED_TOTAL_DIM}D, obtenu {fusion.shape[1]}D"
    )

    cnn = fusion[:, :CNN_DIM]
    vit = fusion[:, CNN_DIM:]

    assert cnn.shape[1] == CNN_DIM, f"Erreur CNN : attendu {CNN_DIM}D"
    assert vit.shape[1] == EXPECTED_VIT_DIM, (
        f"Erreur ViT : attendu {EXPECTED_VIT_DIM}D, obtenu {vit.shape[1]}D"
    )

    cnn = cnn / (np.linalg.norm(cnn, axis=1, keepdims=True) + 1e-8)
    vit = vit / (np.linalg.norm(vit, axis=1, keepdims=True) + 1e-8)

    print(f"Nombre d'images : {len(labels)}")
    print(f"Dimension totale : {fusion.shape[1]}D")
    print(f"CNN : {cnn.shape[1]}D")
    print(f"ViT : {vit.shape[1]}D")

    unique, counts = np.unique(labels, return_counts=True)
    print("\nDistribution des classes :")
    for cls, count in zip(unique, counts):
        print(f"Classe {cls} : {count} images")

    print("=" * 70 + "\n")
    return cnn, vit, labels


# ============================================================
# DISTANCE ET RANKING
# ============================================================

def d_joint(q_cnn, q_vit, cnn, vit, alpha):
    d_cnn = np.sqrt(np.einsum("ij,ij->i", cnn - q_cnn, cnn - q_cnn))
    d_vit = 1.0 - (vit @ q_vit)
    return alpha * d_cnn + (1.0 - alpha) * d_vit


def get_ranked(q_idx, cnn, vit, alpha):
    d = d_joint(cnn[q_idx], vit[q_idx], cnn, vit, alpha)
    d[q_idx] = np.inf
    return np.argsort(d)


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
    denominator = min(k, max(1, total_relevant))
    correct = sum(labels[i] == labels[q_idx] for i in top)

    return correct / denominator


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
    denominator = min(k, max(1, total_relevant))

    return score / denominator


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
# 1. ABLATION ALPHA
# ============================================================

def run_alpha_ablation(cnn, vit, labels):
    print("=" * 70)
    print("1. ABLATION ALPHA")
    print("=" * 70)

    np.random.seed(SEED)
    queries = np.random.choice(
        len(labels),
        size=min(N_QUERIES_GLOBAL, len(labels)),
        replace=False
    )

    alphas = [round(i * 0.1, 1) for i in range(11)]
    rows = []

    print(f"{'alpha':>6} {'mAP@10':>10} {'P@10':>10} {'R@10':>10} {'NDCG@10':>10}")
    print("-" * 55)

    for alpha in alphas:
        maps, precisions, recalls, ndcgs = [], [], [], []

        for q in queries:
            ranked = get_ranked(q, cnn, vit, alpha)
            maps.append(map_at_k(ranked, q, labels, 10))
            precisions.append(precision_at_k(ranked, q, labels, 10))
            recalls.append(recall_at_k(ranked, q, labels, 10))
            ndcgs.append(ndcg_at_k(ranked, q, labels, 10))

        row = {
            "alpha": alpha,
            "mAP@10": round(np.mean(maps), 4),
            "P@10": round(np.mean(precisions), 4),
            "R@10": round(np.mean(recalls), 4),
            "NDCG@10": round(np.mean(ndcgs), 4),
        }

        rows.append(row)

        marker = "  <- alpha final" if alpha == ALPHA_FINAL else ""
        print(
            f"{alpha:>6.1f} "
            f"{row['mAP@10']:>10.4f} "
            f"{row['P@10']:>10.4f} "
            f"{row['R@10']:>10.4f} "
            f"{row['NDCG@10']:>10.4f}"
            f"{marker}"
        )

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS_DIR / "ablation_alpha_light.csv", index=False)

    best = max(rows, key=lambda x: x["mAP@10"])
    print("\nMeilleur alpha selon mAP@10 :", best["alpha"])
    print("Alpha final retenu :", ALPHA_FINAL)
    print("Fichier sauvegardé : ablation_alpha_light.csv\n")

    return df


# ============================================================
# 2. MÉTRIQUES GLOBALES
# ============================================================

def run_global_metrics(cnn, vit, labels):
    print("=" * 70)
    print("2. MÉTRIQUES GLOBALES AVEC ALPHA FINAL")
    print("=" * 70)

    np.random.seed(SEED)
    queries = np.random.choice(
        len(labels),
        size=min(N_QUERIES_GLOBAL, len(labels)),
        replace=False
    )

    results = {
        "mAP@5": [],
        "mAP@10": [],
        "mAP@20": [],
        "P@5": [],
        "P@10": [],
        "P@20": [],
        "R@5": [],
        "R@10": [],
        "R@20": [],
        "NDCG@5": [],
        "NDCG@10": [],
        "NDCG@20": [],
    }

    times = []

    for q in queries:
        t0 = time.perf_counter()
        ranked = get_ranked(q, cnn, vit, ALPHA_FINAL)
        times.append((time.perf_counter() - t0) * 1000)

        for k in K_VALUES:
            results[f"mAP@{k}"].append(map_at_k(ranked, q, labels, k))
            results[f"P@{k}"].append(precision_at_k(ranked, q, labels, k))
            results[f"R@{k}"].append(recall_at_k(ranked, q, labels, k))
            results[f"NDCG@{k}"].append(ndcg_at_k(ranked, q, labels, k))

    row = {
        "dataset": "ISIC2020_FULL_LIGHT",
        "n_images": len(labels),
        "n_queries": len(queries),
        "dimension": 384,
        "cnn_dim": 256,
        "vit_dim": 128,
        "alpha": ALPHA_FINAL,
        "time_ms": round(np.mean(times), 2),
    }

    for key, values in results.items():
        row[key] = round(np.mean(values), 4)

    pd.DataFrame([row]).to_csv(RESULTS_DIR / "metrics_global_light.csv", index=False)

    for key, value in row.items():
        print(f"{key:<15} : {value}")

    print("\nFichier sauvegardé : metrics_global_light.csv\n")
    return row


# ============================================================
# 3. MÉTRIQUES PAR CLASSE
# ============================================================

def run_per_class_metrics(cnn, vit, labels):
    print("=" * 70)
    print("3. MÉTRIQUES PAR CLASSE")
    print("=" * 70)

    rows = []

    for cls in np.unique(labels):
        cls_idx = np.where(labels == cls)[0]

        np.random.seed(SEED + int(cls))
        queries = np.random.choice(
            cls_idx,
            size=min(N_QUERIES_PER_CLASS, len(cls_idx)),
            replace=False
        )

        maps, precisions, recalls, ndcgs = [], [], [], []

        for q in queries:
            ranked = get_ranked(q, cnn, vit, ALPHA_FINAL)
            maps.append(map_at_k(ranked, q, labels, 10))
            precisions.append(precision_at_k(ranked, q, labels, 10))
            recalls.append(recall_at_k(ranked, q, labels, 10))
            ndcgs.append(ndcg_at_k(ranked, q, labels, 10))

        row = {
            "classe": int(cls),
            "n_images": len(cls_idx),
            "n_queries": len(queries),
            "mAP@10": round(np.mean(maps), 4),
            "P@10": round(np.mean(precisions), 4),
            "R@10": round(np.mean(recalls), 4),
            "NDCG@10": round(np.mean(ndcgs), 4),
        }

        rows.append(row)

        print(
            f"Classe {cls} | "
            f"N={row['n_images']} | "
            f"mAP@10={row['mAP@10']} | "
            f"P@10={row['P@10']} | "
            f"R@10={row['R@10']}"
        )

    macro = {
        "classe": "MACRO_AVG",
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

    pd.DataFrame(rows).to_csv(RESULTS_DIR / "metrics_per_class_light.csv", index=False)
    print("\nFichier sauvegardé : metrics_per_class_light.csv\n")

    return rows


# ============================================================
# 4. ANALYSE DES CAS MALINS
# ============================================================

def run_malignant_analysis(cnn, vit, labels):
    print("=" * 70)
    print("4. ANALYSE DES CAS MALINS")
    print("=" * 70)

    malignant_label = 1
    malignant_queries = np.where(labels == malignant_label)[0]

    if len(malignant_queries) == 0:
        print("Aucun cas malin trouvé avec le label 1.")
        return None

    maps, precisions, recalls, ndcgs = [], [], [], []
    malignant_counts_top10 = []
    times = []

    for q in malignant_queries:
        t0 = time.perf_counter()
        ranked = get_ranked(q, cnn, vit, ALPHA_FINAL)
        times.append((time.perf_counter() - t0) * 1000)

        top10 = [i for i in ranked if i != q][:10]
        n_malignant_top10 = sum(labels[i] == malignant_label for i in top10)

        malignant_counts_top10.append(n_malignant_top10)
        maps.append(map_at_k(ranked, q, labels, 10))
        precisions.append(precision_at_k(ranked, q, labels, 10))
        recalls.append(recall_at_k(ranked, q, labels, 10))
        ndcgs.append(ndcg_at_k(ranked, q, labels, 10))

    row = {
        "classe": "malignant",
        "label": malignant_label,
        "n_queries": len(malignant_queries),
        "alpha": ALPHA_FINAL,
        "mAP@10_malin": round(np.mean(maps), 4),
        "P@10_malin": round(np.mean(precisions), 4),
        "R@10_malin": round(np.mean(recalls), 4),
        "NDCG@10_malin": round(np.mean(ndcgs), 4),
        "malins_moyens_top10": round(np.mean(malignant_counts_top10), 2),
        "time_ms": round(np.mean(times), 2),
    }

    pd.DataFrame([row]).to_csv(RESULTS_DIR / "metrics_malignant_light.csv", index=False)

    for key, value in row.items():
        print(f"{key:<22} : {value}")

    print("\nFichier sauvegardé : metrics_malignant_light.csv\n")
    return row


# ============================================================
# 5. SCALABILITÉ BRUTE-FORCE
# ============================================================

def run_scalability(cnn, vit):
    print("=" * 70)
    print("5. SCALABILITÉ BRUTE-FORCE JOINTE")
    print("=" * 70)

    N = len(cnn)
    sizes = [1000, 2000, 5000, 10000, N]
    simulated_sizes = [50000, 100000, 1000000]

    rows = []
    np.random.seed(SEED)

    for size in sizes:
        size = min(size, N)

        idx = np.random.choice(N, size=size, replace=False)
        cnn_s = cnn[idx]
        vit_s = vit[idx]

        q_cnn = cnn_s[0]
        q_vit = vit_s[0]

        times = []

        for _ in range(30):
            t0 = time.perf_counter()
            _ = d_joint(q_cnn, q_vit, cnn_s, vit_s, ALPHA_FINAL)
            times.append((time.perf_counter() - t0) * 1000)

        row = {
            "N": size,
            "BF_ms": round(np.mean(times), 2),
            "simulated": False,
        }

        rows.append(row)
        print(f"N={row['N']:<8} BF={row['BF_ms']} ms")

    x1, y1 = rows[-2]["N"], rows[-2]["BF_ms"]
    x2, y2 = rows[-1]["N"], rows[-1]["BF_ms"]
    slope = (y2 - y1) / max(1, (x2 - x1))

    for size in simulated_sizes:
        if size <= N:
            continue

        estimated_time = round(y2 + slope * (size - x2), 2)

        row = {
            "N": size,
            "BF_ms": estimated_time,
            "simulated": True,
        }

        rows.append(row)
        print(f"N={row['N']:<8} BF estimé={row['BF_ms']} ms")

    pd.DataFrame(rows).to_csv(RESULTS_DIR / "scalability_light.csv", index=False)
    print("\nFichier sauvegardé : scalability_light.csv\n")

    return rows


# ============================================================
# MAIN
# ============================================================

def main():
    print("\n")
    print("=" * 70)
    print("ANALYSE FINALE — ISIC 2020 COMPLET — VERSION LIGHT 384D")
    print("=" * 70)
    print("\n")

    cnn, vit, labels = load_data()

    run_alpha_ablation(cnn, vit, labels)
    global_results = run_global_metrics(cnn, vit, labels)
    run_per_class_metrics(cnn, vit, labels)
    malignant_results = run_malignant_analysis(cnn, vit, labels)
    run_scalability(cnn, vit)

    print("=" * 70)
    print("RÉSUMÉ FINAL")
    print("=" * 70)

    print("Résultats globaux :")
    for key, value in global_results.items():
        print(f"{key:<18} : {value}")

    if malignant_results is not None:
        print("\nRésultats cas malins :")
        for key, value in malignant_results.items():
            print(f"{key:<22} : {value}")

    print("\nDossier des résultats :")
    print(RESULTS_DIR)
    print("=" * 70)


if __name__ == "__main__":
    main()