"""
HJG — Hierarchical Joint Graph pour CBIR médical
=================================================
Adaptation du papier : "HJG: An Effective Hierarchical Joint Graph
for ANNS in Multi-Metric Spaces" (ICDE 2024, ZJU-DAILY)

Dataset   : HAM10000 (10 015 images)
Vecteur   : fusion_concat.npy (2816D = CNN 2048D + ViT 768D)
Métriques : Euclidienne sur partie CNN + Cosinus sur partie ViT
Exécution : 100% local, CPU, aucune dépendance cloud

Usage :
    pip install numpy pandas scikit-learn
    python hjg.py

Résultats : Vectors-C/hjg_results.csv
Graphe    : Vectors-C/hjg_graph.pkl  (sauvegardé, rechargé si relancé)
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
VECTORS_DIR = Path(r"C:\Users\hp\Desktop\PFE\Vectors-C")

# ─────────────────────────────────────────────────────────────────────────────
#  PARAMÈTRES
# ─────────────────────────────────────────────────────────────────────────────
CFG = {
    "cnn_dim"    : 2048,   # fusion_concat[:, :2048]  → CNN → euclidienne
    "vit_dim"    : 768,    # fusion_concat[:, 2048:]  → ViT → cosinus
    "k"          : 15,     # voisins k-NN par nœud et par métrique
    "n_coarse"   : 500,   # nœuds au niveau grossier (~10% de 10015)
    "w_cnn"      : 0.1,    # poids de la distance CNN
    "w_vit"      : 0.9,    # poids de la distance ViT
    "ef_search"  : 30,     # candidats explorés à la recherche (plus = meilleur recall)
    "k_query"    : 20,     # résultats retournés par requête
    "n_queries"  : 300,    # requêtes d'évaluation
    "eval_seed"  : 42,
    "k_eval"     : [5, 10, 20],
    "batch"      : 500,    # images traitées par batch (limiter RAM)
}


# ─────────────────────────────────────────────────────────────────────────────
#  CHARGEMENT
# ─────────────────────────────────────────────────────────────────────────────

def load_data():
    print("Chargement des données...")
    fusion = np.load(VECTORS_DIR / "fusion_concat.npy").astype(np.float32)
    labels = np.load(VECTORS_DIR / "labels.npy")

    cnn = fusion[:, :CFG["cnn_dim"]]
    vit = fusion[:, CFG["cnn_dim"]:]

    # L2-normalisation (cosinus = produit scalaire après normalisation)
    cnn /= (np.linalg.norm(cnn, axis=1, keepdims=True) + 1e-8)
    vit /= (np.linalg.norm(vit, axis=1, keepdims=True) + 1e-8)

    N = len(fusion)
    print(f"  {N} images | CNN {cnn.shape[1]}D | ViT {vit.shape[1]}D\n")
    return cnn, vit, labels, N


# ─────────────────────────────────────────────────────────────────────────────
#  DISTANCES
# ─────────────────────────────────────────────────────────────────────────────

def d_euc(q, db):
    """Euclidienne entre q (D,) et db (N, D)."""
    diff = db - q
    return np.einsum('ij,ij->i', diff, diff)  # carré (pas besoin sqrt pour tri)


def d_cos(q, db):
    """Cosinus = 1 - similarité. q et db L2-normalisés."""
    return 1.0 - (db @ q)


def d_joint(q_cnn, q_vit, cnn, vit, idx):
    """Distance jointe sur un sous-ensemble d'indices."""
    dc = np.sqrt(d_euc(q_cnn, cnn[idx]))
    dv = d_cos(q_vit, vit[idx])
    return CFG["w_cnn"] * dc + CFG["w_vit"] * dv


# ─────────────────────────────────────────────────────────────────────────────
#  CONSTRUCTION DU GRAPHE K-NN (par batch)
# ─────────────────────────────────────────────────────────────────────────────

def build_knn(data, dist_fn, k, name):
    """Construit le graphe k-NN exact pour une métrique."""
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
    """
    HJG à deux niveaux :
      Level 0 (fin)     : graphe joint CNN+ViT sur tous les N nœuds
      Level 1 (grossier): graphe joint sur n_coarse nœuds (points d'entrée)

    Joint graph : pour chaque nœud, ses voisins = union k-NN CNN ∪ k-NN ViT,
    distances recalculées avec la distance jointe.
    """
    N = len(cnn)
    k = CFG["k"]

    # ── Graphe CNN (euclidienne)
    g_cnn = build_knn(cnn, d_euc, k, "CNN-Euclidien")

    # ── Graphe ViT (cosinus)
    g_vit = build_knn(vit, d_cos, k, "ViT-Cosinus")

    # ── Jointure : union des voisins, distances jointes recalculées
    print("  Jointure des graphes...")
    joint = [None] * N
    for i in range(N):
        cands = list(set(g_cnn[i].tolist()) | set(g_vit[i].tolist()))
        cands = [c for c in cands if c != i]
        dists = d_joint(cnn[i], vit[i], cnn, vit, np.array(cands))
        if len(cands) > k:
            best = np.argpartition(dists, k)[:k]
            joint[i] = sorted(zip(dists[best].tolist(),
                                  [cands[b] for b in best]))
        else:
            joint[i] = sorted(zip(dists.tolist(), cands))

    # ── Niveau grossier (n_coarse nœuds)
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
        coarse[i] = sorted(zip(dj[best].tolist(),
                               coarse_idx[best].tolist()))

    return {
        "joint"      : joint,        # graphe fin
        "coarse_idx" : coarse_idx,   # indices globaux des nœuds grossiers
        "coarse"     : coarse,       # graphe grossier
    }


# ─────────────────────────────────────────────────────────────────────────────
#  RECHERCHE BEST-FIRST
# ─────────────────────────────────────────────────────────────────────────────

def search(q_cnn, q_vit, hjg, cnn, vit, k=10, ef=60):
    """
    Recherche Best-First à deux niveaux.

    Level 1 (grossier) : trouve le meilleur point d'entrée
    Level 0 (fin)      : Best-First depuis ce point d'entrée
    """
    joint      = hjg["joint"]
    coarse_idx = hjg["coarse_idx"]
    coarse     = hjg["coarse"]

    def jd(idx):
        dc = float(np.sqrt(float(d_euc(q_cnn, cnn[idx:idx+1])[0])))
        dv = float(d_cos(q_vit, vit[idx:idx+1])[0])
        return CFG["w_cnn"] * dc + CFG["w_vit"] * dv

    # ── Level 1 : navigation grossière ──────────────────────────────────────
    start_local = int(np.random.randint(0, len(coarse_idx)))
    start_global = int(coarse_idx[start_local])

    visited_c = {start_local}
    best_d = jd(start_global)
    best_g = start_global
    best_l = start_local

    heap_c = [(best_d, start_local, start_global)]
    while heap_c:
        d_cur, l_cur, g_cur = heapq.heappop(heap_c)
        if d_cur > best_d * 2.0:
            break
        for d_nb, g_nb in coarse[l_cur]:
            locs = np.where(coarse_idx == g_nb)[0]
            if len(locs) == 0:
                continue
            l_nb = int(locs[0])
            if l_nb in visited_c:
                continue
            visited_c.add(l_nb)
            d = jd(g_nb)
            if d < best_d:
                best_d, best_g, best_l = d, g_nb, l_nb
            heapq.heappush(heap_c, (d, l_nb, g_nb))

    # ── Level 0 : Best-First fin ─────────────────────────────────────────────
    visited_f = {best_g}
    d0 = jd(best_g)

    # Max-heap pour garder les ef meilleurs (negate pour simuler max-heap)
    W = [(-d0, best_g)]   # pire résultat en tête
    C = [(d0, best_g)]    # candidats à explorer (min-heap)

    while C:
        d_cur, n_cur = heapq.heappop(C)
        # Arrêt : le candidat est plus loin que le pire dans W
        if len(W) >= ef and d_cur > -W[0][0]:
            break
        for d_nb, n_nb in joint[n_cur]:
            if n_nb in visited_f:
                continue
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


# ─────────────────────────────────────────────────────────────────────────────
#  BRUTE-FORCE BASELINE
# ─────────────────────────────────────────────────────────────────────────────

def brute_force(q_cnn, q_vit, cnn, vit, k=20):
    dc = np.sqrt(d_euc(q_cnn, cnn))
    dv = d_cos(q_vit, vit)
    dj = CFG["w_cnn"] * dc + CFG["w_vit"] * dv
    idx = np.argpartition(dj, k + 1)[:k + 1]
    idx = sorted(idx, key=lambda i: dj[i])
    return [(float(dj[i]), int(i)) for i in idx]


# ─────────────────────────────────────────────────────────────────────────────
#  MÉTRIQUES
# ─────────────────────────────────────────────────────────────────────────────

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


def prec_k(res, q, labels, k):
    top = [i for _, i in res if i != q][:k]
    return sum(labels[i] == labels[q] for i in top) / max(1, len(top))


# ─────────────────────────────────────────────────────────────────────────────
#  ÉVALUATION
# ─────────────────────────────────────────────────────────────────────────────

def evaluate(hjg, cnn, vit, labels):
    N = len(cnn)
    np.random.seed(CFG["eval_seed"])
    queries = np.random.choice(N, min(CFG["n_queries"], N), replace=False)
    ks = CFG["k_eval"]
    km = max(ks)

    rec = {k: [] for k in ks}
    mh  = {k: [] for k in ks}
    ph  = {k: [] for k in ks}
    mb  = {k: [] for k in ks}
    pb  = {k: [] for k in ks}
    th, tb = [], []

    print(f"\nÉvaluation : {len(queries)} requêtes...")
    for i, q in enumerate(queries):
        if i % 50 == 0:
            print(f"  [{i}/{len(queries)}]")
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
            ph[k].append(prec_k(rh, q, labels, k))
            mb[k].append(map_k(rb, q, labels, k))
            pb[k].append(prec_k(rb, q, labels, k))

    mean = lambda d: {k: round(float(np.mean(d[k])), 4) for k in ks}
    return {
        "recall" : mean(rec),
        "map_hjg": mean(mh),
        "prec_hjg":mean(ph),
        "map_bf" : mean(mb),
        "prec_bf": mean(pb),
        "t_hjg"  : float(np.mean(th)),
        "t_bf"   : float(np.mean(tb)),
        "speedup": float(np.mean(tb)) / max(float(np.mean(th)), 0.001),
    }


# ─────────────────────────────────────────────────────────────────────────────
#  AFFICHAGE + CSV
# ─────────────────────────────────────────────────────────────────────────────

def print_and_save(res):
    ks = CFG["k_eval"]
    sep = "=" * 90
    print(f"\n{sep}")
    print("RÉSULTATS FINAUX — HJG Multi-Métrique vs Brute-Force")
    print(sep)

    header = f"{'Méthode':<28} {'ms':>7}"
    for k in ks:
        header += f"  {'Recall@'+str(k):>10}  {'mAP@'+str(k):>8}  {'P@'+str(k):>7}"
    print(header)
    print("-" * 90)

    bf_row = f"{'Brute-Force (exact)':<28} {res['t_bf']:>7.1f}"
    for k in ks:
        bf_row += f"  {'1.000':>10}  {res['map_bf'][k]:>8.3f}  {res['prec_bf'][k]:>7.3f}"
    print(bf_row)

    hj_row = f"{'HJG (notre)':<28} {res['t_hjg']:>7.1f}"
    for k in ks:
        hj_row += f"  {res['recall'][k]:>10.3f}  {res['map_hjg'][k]:>8.3f}  {res['prec_hjg'][k]:>7.3f}"
    print(hj_row)
    print(sep)

    print(f"\n  Speedup     : {res['speedup']:.1f}x plus rapide que brute-force")
    print(f"  Recall@10   : {res['recall'][10]:.3f}  (1.000 = parfait)")
    print(f"  mAP@10 HJG  : {res['map_hjg'][10]:.3f}")
    print(f"  mAP@10 BF   : {res['map_bf'][10]:.3f}")
    print(f"  Perte mAP   : {res['map_bf'][10]-res['map_hjg'][10]:.4f}")

    rows = []
    for method, prefix, recall_val in [
        ("Brute-Force", "bf", None),
        ("HJG",         "hjg", res["recall"]),
    ]:
        row = {"methode": method,
               "time_ms": round(res[f"t_{prefix}"], 2),
               "speedup": round(res["speedup"], 1) if method == "HJG" else 1.0}
        for k in ks:
            if recall_val:
                row[f"Recall@{k}"] = recall_val[k]
            row[f"mAP@{k}"]    = res[f"map_{prefix}"][k]
            row[f"P@{k}"]      = res[f"prec_{prefix}"][k]
        rows.append(row)

    df = pd.DataFrame(rows)
    out = VECTORS_DIR / "hjg_results.csv"
    df.to_csv(out, index=False)
    print(f"\n  CSV sauvegardé : {out}")
    print(df.to_string(index=False))


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("HJG — Hierarchical Joint Graph (ICDE 2024 adaptation)")
    print("=" * 60)

    cnn, vit, labels, N = load_data()

    graph_path = VECTORS_DIR / "hjg_graph.pkl"
    if graph_path.exists():
        print(f"Graphe existant trouvé. Chargement...")
        with open(graph_path, "rb") as f:
            hjg = pickle.load(f)
        print("OK\n")
    else:
        print(f"Construction du graphe (N={N}, k={CFG['k']})...")
        print(f"Durée estimée : 15-25 min sur CPU\n")
        t0 = time.time()
        hjg = build_hjg(cnn, vit)
        dt = time.time() - t0
        print(f"\nGraphe construit en {dt/60:.1f} min")
        with open(graph_path, "wb") as f:
            pickle.dump(hjg, f)
        print(f"Sauvegardé : {graph_path}\n")

    res = evaluate(hjg, cnn, vit, labels)
    print_and_save(res)


if __name__ == "__main__":
    main()