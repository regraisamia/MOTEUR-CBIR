import time
import heapq
import pickle
import numpy as np
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

VECTORS_DIR = Path(r"C:\Users\hp\Desktop\PFE\Vectors-ISIC2019")

FUSION_FILE = VECTORS_DIR / "fusion_compressed_384D.npy"
LABELS_FILE = VECTORS_DIR / "labels.npy"

OUT_GRAPH = VECTORS_DIR / "hjg_graph_light.pkl"

CFG = {
    "cnn_dim": 256,
    "vit_dim": 128,
    "k": 15,
    "n_coarse": 700,
    "w_cnn": 0.1,
    "w_vit": 0.9,
    "batch": 512,
    "ef_search": 60,
    "k_query": 20,
}


# ============================================================
# CHARGEMENT
# ============================================================

def l2_normalize(x):
    return x / (np.linalg.norm(x, axis=1, keepdims=True) + 1e-8)


def load_data():
    print("=" * 70)
    print("CHARGEMENT ISIC 2019 COMPRESSÉ 384D")
    print("=" * 70)

    fusion = np.load(FUSION_FILE).astype(np.float32)
    labels = np.load(LABELS_FILE)

    assert fusion.shape[1] == 384, (
        f"Erreur : attendu 384D, obtenu {fusion.shape[1]}D"
    )

    cnn = fusion[:, :CFG["cnn_dim"]]
    vit = fusion[:, CFG["cnn_dim"]:]

    assert cnn.shape[1] == 256
    assert vit.shape[1] == 128

    cnn = l2_normalize(cnn)
    vit = l2_normalize(vit)

    print(f"Images : {len(fusion)}")
    print(f"CNN : {cnn.shape[1]}D")
    print(f"ViT : {vit.shape[1]}D")

    unique, counts = np.unique(labels, return_counts=True)
    print("\nDistribution :")
    for u, c in zip(unique, counts):
        print(f"  Classe {u} : {c}")

    print("=" * 70 + "\n")

    return cnn, vit, labels


# ============================================================
# DISTANCES
# ============================================================

def d_euc_one(q, db):
    diff = db - q
    return np.einsum("ij,ij->i", diff, diff)


def d_cos_one(q, db):
    return 1.0 - (db @ q)


def d_joint(q_cnn, q_vit, cnn, vit, idx):
    dc = np.sqrt(d_euc_one(q_cnn, cnn[idx]))
    dv = d_cos_one(q_vit, vit[idx])
    return CFG["w_cnn"] * dc + CFG["w_vit"] * dv


# ============================================================
# CONSTRUCTION KNN RAPIDE PAR BATCH
# ============================================================

def build_knn_normalized(data, k, metric_name):
    """
    data est déjà L2-normalisé.
    Pour euclidien sur vecteurs normalisés :
        ||x-y||² = 2 - 2*cos(x,y)
    Pour cosinus :
        distance = 1 - cos(x,y)
    """
    N = len(data)
    B = CFG["batch"]
    graph = np.empty((N, k), dtype=np.int32)

    print(f"Construction graphe {metric_name} | N={N}, k={k}")

    for start in range(0, N, B):
        end = min(start + B, N)

        block = data[start:end]
        sims = block @ data.T

        if metric_name == "euclidean":
            dists = 2.0 - 2.0 * sims
        else:
            dists = 1.0 - sims

        rows = np.arange(end - start)
        cols = np.arange(start, end)
        dists[rows, cols] = np.inf

        idx = np.argpartition(dists, k, axis=1)[:, :k]
        graph[start:end] = idx.astype(np.int32)

        print(f"  {end}/{N}")

    return graph


# ============================================================
# CONSTRUCTION HJG
# ============================================================

def build_hjg(cnn, vit):
    N = len(cnn)
    k = CFG["k"]

    t0 = time.perf_counter()

    g_cnn = build_knn_normalized(cnn, k, "euclidean")
    g_vit = build_knn_normalized(vit, k, "cosine")

    print("\nJointure des graphes CNN + ViT")
    joint = [None] * N

    for i in range(N):
        cands = list(set(g_cnn[i].tolist()) | set(g_vit[i].tolist()))
        cands = [c for c in cands if c != i]

        if len(cands) == 0:
            joint[i] = []
            continue

        cands_arr = np.array(cands, dtype=np.int32)
        dists = d_joint(cnn[i], vit[i], cnn, vit, cands_arr)

        if len(cands) > k:
            best = np.argpartition(dists, k)[:k]
            selected = [(float(dists[b]), int(cands_arr[b])) for b in best]
        else:
            selected = [(float(dists[b]), int(cands_arr[b])) for b in range(len(cands_arr))]

        joint[i] = sorted(selected, key=lambda x: x[0])

        if i % 5000 == 0:
            print(f"  Jointure : {i}/{N}")

    n_coarse = min(CFG["n_coarse"], N)
    np.random.seed(42)
    coarse_idx = np.random.choice(N, n_coarse, replace=False)

    print(f"\nConstruction niveau coarse : {n_coarse} noeuds")

    cnn_c = cnn[coarse_idx]
    vit_c = vit[coarse_idx]

    coarse = [None] * n_coarse
    k_c = min(k, n_coarse - 1)

    for i in range(n_coarse):
        dc = np.sqrt(d_euc_one(cnn_c[i], cnn_c))
        dv = d_cos_one(vit_c[i], vit_c)
        dj = CFG["w_cnn"] * dc + CFG["w_vit"] * dv
        dj[i] = np.inf

        best = np.argpartition(dj, k_c)[:k_c]
        coarse[i] = sorted(
            [(float(dj[b]), int(coarse_idx[b])) for b in best],
            key=lambda x: x[0]
        )

    hjg = {
        "joint": joint,
        "coarse_idx": coarse_idx.astype(np.int32),
        "coarse": coarse,
        "cfg": CFG,
    }

    elapsed = round(time.perf_counter() - t0, 2)
    print(f"\nConstruction HJG terminée en {elapsed} secondes")

    return hjg


# ============================================================
# TEST RECHERCHE HJG
# ============================================================

def search_hjg(q_cnn, q_vit, hjg, cnn, vit, top_k=10, ef=60):
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

    if len(all_candidates) == 0:
        return [], []

    cand_arr = np.array(all_candidates, dtype=np.int32)
    dists = d_joint(q_cnn, q_vit, cnn, vit, cand_arr)

    order = np.argsort(dists)[:top_k]

    indices = cand_arr[order]
    distances = dists[order]

    return indices.tolist(), distances.tolist()


# ============================================================
# MAIN
# ============================================================

def main():
    cnn, vit, labels = load_data()

    hjg = build_hjg(cnn, vit)

    with open(OUT_GRAPH, "wb") as f:
        pickle.dump(hjg, f)

    print("\nGraphe sauvegardé :")
    print(OUT_GRAPH)

    print("\nTest rapide HJG sur 5 requêtes")
    np.random.seed(42)
    queries = np.random.choice(len(cnn), size=5, replace=False)

    for q in queries:
        indices, distances = search_hjg(
            cnn[q], vit[q], hjg, cnn, vit,
            top_k=10,
            ef=CFG["ef_search"]
        )

        same = sum(labels[i] == labels[q] for i in indices)
        print(f"Query {q} | label={labels[q]} | correct top10={same}/10")

    print("\nOK : HJG ISIC 2019 prêt.")


if __name__ == "__main__":
    main()