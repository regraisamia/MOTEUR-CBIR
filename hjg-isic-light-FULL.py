"""
HJG — LIGHT VERSION (Optimisée RAM & Big Data)
=================================================
Vecteurs compressés par PCA : 384D (256D CNN + 128D ViT)
Poids optimisés : Alpha = 0.1 (90% ViT / 10% CNN)
"""

import os
import sys
import time
import heapq
import pickle
import numpy as np
import pandas as pd
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
#  CHEMIN DES FICHIERS
# ─────────────────────────────────────────────────────────────────────────────
VECTORS_DIR = Path(r"C:\Users\hp\Desktop\PFE\Vectors-ISIC-FULL")

# ─────────────────────────────────────────────────────────────────────────────
#  PARAMÈTRES (MODIFIÉS POUR VERSION LIGHT)
# ─────────────────────────────────────────────────────────────────────────────
CFG = {
    "cnn_dim"    : 256,    # CNN compressé -> 256D
    "vit_dim"    : 128,    # ViT compressé -> 128D
    "k"          : 15,     # voisins k-NN
    "n_coarse"   : 500,    # points d'entrée
    "w_cnn"      : 0.1,    # Poids optimal validé par ablation
    "w_vit"      : 0.9,    # Poids optimal validé par ablation
    "ef_search"  : 30,     
    "k_query"    : 20,     
    "n_queries"  : 300,    
    "eval_seed"  : 42,
    "k_eval"     : [5, 10, 20],
    "batch"      : 1000,   # On peut augmenter le batch car les vecteurs sont légers
}

# ─────────────────────────────────────────────────────────────────────────────
#  CHARGEMENT
# ─────────────────────────────────────────────────────────────────────────────

def load_data():
    print("Chargement des données COMPRESSÉES...")
    # On charge le fichier 384D généré par compress_vectors.py
    fusion = np.load(VECTORS_DIR / "fusion_compressed_384D.npy").astype(np.float32)
    labels = np.load(VECTORS_DIR / "labels.npy")

    cnn = fusion[:, :CFG["cnn_dim"]]
    vit = fusion[:, CFG["cnn_dim"]:]

    # L2-normalisation
    cnn /= (np.linalg.norm(cnn, axis=1, keepdims=True) + 1e-8)
    vit /= (np.linalg.norm(vit, axis=1, keepdims=True) + 1e-8)

    N = len(fusion)
    print(f"  {N} images | CNN {cnn.shape[1]}D | ViT {vit.shape[1]}D\n")
    return cnn, vit, labels, N

# ─────────────────────────────────────────────────────────────────────────────
#  DISTANCES
# ─────────────────────────────────────────────────────────────────────────────

def d_euc(q, db):
    diff = db - q
    return np.einsum('ij,ij->i', diff, diff)

def d_cos(q, db):
    return 1.0 - (db @ q)

def d_joint(q_cnn, q_vit, cnn, vit, idx):
    dc = np.sqrt(d_euc(q_cnn, cnn[idx]))
    dv = d_cos(q_vit, vit[idx])
    return CFG["w_cnn"] * dc + CFG["w_vit"] * dv

# ─────────────────────────────────────────────────────────────────────────────
#  CONSTRUCTION K-NN
# ─────────────────────────────────────────────────────────────────────────────

def build_knn(data, dist_fn, k, name):
    N = len(data)
    graph = np.empty((N, k), dtype=np.int32)
    B = CFG["batch"]

    print(f"  Graphe {name} k={k}...")
    for start in range(0, N, B):
        end = min(start + B, N)
        if start % (B * 4) == 0:
            print(f"    {start}/{N}")
        for i in range(start, end):
            d = dist_fn(data[i], data)
            d[i] = np.inf
            graph[i] = np.argpartition(d, k)[:k]
    return graph

# ─────────────────────────────────────────────────────────────────────────────
#  CONSTRUCTION HJG
# ─────────────────────────────────────────────────────────────────────────────

def build_hjg(cnn, vit):
    N = len(cnn)
    k = CFG["k"]

    g_cnn = build_knn(cnn, d_euc, k, "CNN-Euclidien")
    g_vit = build_knn(vit, d_cos, k, "ViT-Cosinus")

    print("  Jointure des graphes...")
    joint = [None] * N
    for i in range(N):
        cands = list(set(g_cnn[i].tolist()) | set(g_vit[i].tolist()))
        cands = [c for c in cands if c != i]
        dists = d_joint(cnn[i], vit[i], cnn, vit, np.array(cands))
        if len(cands) > k:
            best = np.argpartition(dists, k)[:k]
            joint[i] = sorted(zip(dists[best].tolist(), [cands[b] for b in best]))
        else:
            joint[i] = sorted(zip(dists.tolist(), cands))

    np.random.seed(42)
    coarse_idx = np.random.choice(N, CFG["n_coarse"], replace=False)
    print(f"  Niveau grossier : {len(coarse_idx)} nœuds")

    cnn_c = cnn[coarse_idx]
    vit_c = vit[coarse_idx]
    k_c = min(k, len(coarse_idx) - 1)
    coarse = [None] * len(coarse_idx)

    for i in range(len(coarse_idx)):
        dc = np.sqrt(d_euc(cnn_c[i], cnn_c))
        dv = d_cos(vit_c[i], vit_c)
        dj = CFG["w_cnn"] * dc + CFG["w_vit"] * dv
        dj[i] = np.inf
        best = np.argpartition(dj, k_c)[:k_c]
        coarse[i] = sorted(zip(dj[best].tolist(), coarse_idx[best].tolist()))

    return {"joint": joint, "coarse_idx": coarse_idx, "coarse": coarse}

# ─────────────────────────────────────────────────────────────────────────────
#  RECHERCHE & EVALUATION
# ─────────────────────────────────────────────────────────────────────────────

def search(q_cnn, q_vit, hjg, cnn, vit, k=10, ef=60):
    joint = hjg["joint"]
    coarse_idx = hjg["coarse_idx"]
    coarse = hjg["coarse"]

    def jd(idx):
        dc = float(np.sqrt(float(d_euc(q_cnn, cnn[idx:idx+1])[0])))
        dv = float(d_cos(q_vit, vit[idx:idx+1])[0])
        return CFG["w_cnn"] * dc + CFG["w_vit"] * dv

    start_local = int(np.random.randint(0, len(coarse_idx)))
    start_global = int(coarse_idx[start_local])
    visited_c = {start_local}
    best_d, best_g = jd(start_global), start_global
    heap_c = [(best_d, start_local, start_global)]

    while heap_c:
        d_cur, l_cur, g_cur = heapq.heappop(heap_c)
        if d_cur > best_d * 2.0: break
        for d_nb, g_nb in coarse[l_cur]:
            locs = np.where(coarse_idx == g_nb)[0]
            if len(locs) == 0: continue
            l_nb = int(locs[0])
            if l_nb in visited_c: continue
            visited_c.add(l_nb)
            d = jd(g_nb)
            if d < best_d: best_d, best_g = d, g_nb
            heapq.heappush(heap_c, (d, l_nb, g_nb))

    visited_f = {best_g}
    d0 = jd(best_g)
    W, C = [(-d0, best_g)], [(d0, best_g)]

    while C:
        d_cur, n_cur = heapq.heappop(C)
        if len(W) >= ef and d_cur > -W[0][0]: break
        for d_nb, n_nb in joint[n_cur]:
            if n_nb in visited_f: continue
            visited_f.add(n_nb)
            d = jd(n_nb)
            if len(W) < ef:
                heapq.heappush(W, (-d, n_nb))
                heapq.heappush(C, (d, n_nb))
            elif d < -W[0][0]:
                heapq.heapreplace(W, (-d, n_nb))
                heapq.heappush(C, (d, n_nb))

    results = sorted([(-nd, n) for nd, n in W])
    return results[:k]

def brute_force(q_cnn, q_vit, cnn, vit, k=20):
    dc = np.sqrt(d_euc(q_cnn, cnn))
    dv = d_cos(q_vit, vit)
    dj = CFG["w_cnn"] * dc + CFG["w_vit"] * dv
    idx = np.argpartition(dj, k + 1)[:k + 1]
    idx = sorted(idx, key=lambda i: dj[i])
    return [(float(dj[i]), int(i)) for i in idx]

def recall_k(hjg_res, bf_res, k):
    true = set(i for _, i in bf_res[:k])
    found = set(i for _, i in hjg_res[:k])
    return len(true & found) / max(1, len(true))

def map_k(res, q, labels, k):
    top = [i for _, i in res if i != q][:k]
    hits, s = 0, 0.0
    ql = labels[q]
    for r, i in enumerate(top, 1):
        if labels[i] == ql:
            hits += 1; s += hits / r
    return s / min(k, max(1, (labels == ql).sum() - 1))

def evaluate(hjg, cnn, vit, labels):
    N = len(cnn)
    np.random.seed(CFG["eval_seed"])
    queries = np.random.choice(N, min(CFG["n_queries"], N), replace=False)
    ks = CFG["k_eval"]
    km = max(ks)
    rec, mh, mb, th, tb = {k: [] for k in ks}, {k: [] for k in ks}, {k: [] for k in ks}, [], []

    print(f"\nÉvaluation : {len(queries)} requêtes...")
    for i, q in enumerate(queries):
        if i % 100 == 0: print(f"  [{i}/{len(queries)}]")
        qc, qv = cnn[q], vit[q]
        t0 = time.perf_counter()
        rb = brute_force(qc, qv, cnn, vit, k=km)
        tb.append((time.perf_counter() - t0) * 1000)
        rb = [(d, i) for d, i in rb if i != q][:km]
        t0 = time.perf_counter()
        rh = search(qc, qv, hjg, cnn, vit, k=km, ef=CFG["ef_search"])
        th.append((time.perf_counter() - t0) * 1000)
        rh = [(d, i) for d, i in rh if i != q][:km]
        for k in ks:
            rec[k].append(recall_k(rh, rb, k))
            mh[k].append(map_k(rh, q, labels, k))
            mb[k].append(map_k(rb, q, labels, k))

    return {
        "recall": {k: round(float(np.mean(rec[k])), 4) for k in ks},
        "map_hjg": {k: round(float(np.mean(mh[k])), 4) for k in ks},
        "map_bf": {k: round(float(np.mean(mb[k])), 4) for k in ks},
        "t_hjg": float(np.mean(th)),
        "t_bf": float(np.mean(tb)),
        "speedup": float(np.mean(tb)) / max(float(np.mean(th)), 0.001),
    }

# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("HJG LIGHT — Optimisation RAM (384D)")
    print("=" * 60)

    cnn, vit, labels, N = load_data()
    graph_path = VECTORS_DIR / "hjg_graph_light.pkl"

    if graph_path.exists():
        print(f"Graphe LIGHT trouvé. Chargement...")
        with open(graph_path, "rb") as f: hjg = pickle.load(f)
    else:
        print(f"Construction du graphe LIGHT (k={CFG['k']})...")
        t0 = time.time()
        hjg = build_hjg(cnn, vit)
        print(f"\nGraphe LIGHT construit en {(time.time()-t0)/60:.1f} min")
        with open(graph_path, "wb") as f: pickle.dump(hjg, f)

    res = evaluate(hjg, cnn, vit, labels)
    print(f"\nSPEEDUP : {res['speedup']:.1f}x")
    print(f"RECALL@10 : {res['recall'][10]:.4f}")
    print(f"mAP@10 HJG : {res['map_hjg'][10]:.4f} (Original: 0.9642)")
    print(f"TEMPS : {res['t_hjg']:.2f} ms/req")

if __name__ == "__main__":
    main()