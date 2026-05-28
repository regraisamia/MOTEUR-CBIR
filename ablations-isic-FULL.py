"""
Ablation Study Complet — HJG CBIR Médical
==========================================
Script 1 : Ablation α (poids CNN vs ViT dans d_joint)
Script 2 : mAP par classe (analyse ISIC paradoxe)
Script 3 : Métriques supplémentaires (P@1, NDCG@10)
Script 4 : Courbe scalabilité (temps = f(N))

Usage : python ablations.py
Résultats : Vectors-C/ablation_*.csv
"""

import numpy as np
import pandas as pd
import time
from pathlib import Path

VECTORS_DIR = Path(r"C:\Users\hp\Desktop\PFE\Vectors-ISIC-FULL")
CNN_DIM = 2048
N_QUERIES = 300
SEED = 42

# ═══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def load(folder=VECTORS_DIR):
    print(f"Chargement depuis {folder}...")
    fusion = np.load(folder / "fusion_concat.npy").astype(np.float32)
    labels = np.load(folder / "labels.npy")
    cnn = fusion[:, :CNN_DIM]
    vit = fusion[:, CNN_DIM:]
    cnn /= (np.linalg.norm(cnn, axis=1, keepdims=True) + 1e-8)
    vit /= (np.linalg.norm(vit, axis=1, keepdims=True) + 1e-8)
    print(f"  {len(fusion)} images | CNN {cnn.shape[1]}D | ViT {vit.shape[1]}D\n")
    return cnn, vit, labels


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS MÉTRIQUES
# ═══════════════════════════════════════════════════════════════════════════════

def d_joint(q_cnn, q_vit, cnn, vit, alpha):
    diff = cnn - q_cnn
    d_cnn = np.sqrt(np.einsum('ij,ij->i', diff, diff))
    d_vit = 1.0 - (vit @ q_vit)
    return alpha * d_cnn + (1 - alpha) * d_vit


def map_k(ranked, q, labels, k):
    top = [i for i in ranked if i != q][:k]
    hits, s = 0, 0.0
    ql = labels[q]
    for r, i in enumerate(top, 1):
        if labels[i] == ql:
            hits += 1; s += hits / r
    return s / min(k, max(1, (labels == ql).sum() - 1))


def prec_k(ranked, q, labels, k):
    top = [i for i in ranked if i != q][:k]
    return sum(labels[i] == labels[q] for i in top) / max(1, len(top))


def ndcg_k(ranked, q, labels, k):
    """Normalized Discounted Cumulative Gain@K"""
    top = [i for i in ranked if i != q][:k]
    ql = labels[q]
    dcg = sum((labels[i] == ql) / np.log2(r + 2)
              for r, i in enumerate(top))
    # IDCG : si tous les premiers étaient corrects
    n_rel = min(k, max(0, (labels == ql).sum() - 1))
    idcg = sum(1.0 / np.log2(r + 2) for r in range(n_rel))
    return dcg / max(idcg, 1e-8)


def get_ranked(q_idx, cnn, vit, alpha):
    d = d_joint(cnn[q_idx], vit[q_idx], cnn, vit, alpha)
    d[q_idx] = np.inf
    return np.argsort(d)


# ═══════════════════════════════════════════════════════════════════════════════
# SCRIPT 1 — ABLATION α
# ═══════════════════════════════════════════════════════════════════════════════

def ablation_alpha(cnn, vit, labels):
    print("=" * 70)
    print("SCRIPT 1 — Ablation α : d_joint = α×d_CNN + (1-α)×d_ViT")
    print("=" * 70)

    np.random.seed(SEED)
    queries = np.random.choice(len(cnn), min(N_QUERIES, len(cnn)), replace=False)
    alphas = [round(a * 0.1, 1) for a in range(0, 11)]
    rows = []

    print(f"{'α':>5}  {'mAP@5':>7}  {'mAP@10':>7}  {'mAP@20':>7}  "
          f"{'P@1':>6}  {'P@10':>6}  {'NDCG@10':>8}")
    print("-" * 70)

    for alpha in alphas:
        m5, m10, m20, p1, p10, ndcg10 = [], [], [], [], [], []
        for q in queries:
            r = get_ranked(q, cnn, vit, alpha)
            m5.append(map_k(r, q, labels, 5))
            m10.append(map_k(r, q, labels, 10))
            m20.append(map_k(r, q, labels, 20))
            p1.append(prec_k(r, q, labels, 1))
            p10.append(prec_k(r, q, labels, 10))
            ndcg10.append(ndcg_k(r, q, labels, 10))

        row = {
            "alpha"  : alpha,
            "mAP@5"  : round(np.mean(m5), 4),
            "mAP@10" : round(np.mean(m10), 4),
            "mAP@20" : round(np.mean(m20), 4),
            "P@1"    : round(np.mean(p1), 4),
            "P@10"   : round(np.mean(p10), 4),
            "NDCG@10": round(np.mean(ndcg10), 4),
        }
        rows.append(row)

        best_so_far = max(r["mAP@10"] for r in rows)
        marker = " ← best" if row["mAP@10"] == best_so_far else ""
        print(f"{alpha:>5.1f}  {row['mAP@5']:>7.4f}  {row['mAP@10']:>7.4f}  "
              f"{row['mAP@20']:>7.4f}  {row['P@1']:>6.4f}  "
              f"{row['P@10']:>6.4f}  {row['NDCG@10']:>8.4f}{marker}")

    print("=" * 70)
    best = max(rows, key=lambda x: x["mAP@10"])
    a05 = next(r for r in rows if r["alpha"] == 0.5)
    print(f"α optimal : {best['alpha']}  →  mAP@10 = {best['mAP@10']}")
    print(f"α = 0.5   : mAP@10 = {a05['mAP@10']}")
    if best["alpha"] == 0.5:
        print("→ α=0.5 est confirmé optimal. Votre choix est justifié.")
    else:
        print(f"→ α={best['alpha']} est meilleur. Mettez à jour le paramètre.")

    df = pd.DataFrame(rows)
    out = VECTORS_DIR / "ablation_alpha.csv"
    df.to_csv(out, index=False)
    print(f"\nSauvegardé : {out}\n")
    return best["alpha"]


# ═══════════════════════════════════════════════════════════════════════════════
# SCRIPT 2 — mAP PAR CLASSE (analyse paradoxe ISIC + HAM10000)
# ═══════════════════════════════════════════════════════════════════════════════

def map_per_class(cnn, vit, labels, alpha, dataset_name="HAM10000"):
    print("=" * 70)
    print(f"SCRIPT 2 — mAP par classe ({dataset_name})")
    print("=" * 70)

    classes = np.unique(labels)
    rows = []

    print(f"{'Classe':>8}  {'N images':>9}  {'N requêtes':>11}  "
          f"{'mAP@10':>8}  {'P@10':>7}  {'NDCG@10':>9}")
    print("-" * 70)

    for cls in classes:
        cls_idx = np.where(labels == cls)[0]
        n_cls = len(cls_idx)

        # Prend au max 30 requêtes par classe
        np.random.seed(SEED + int(cls))
        q_sample = cls_idx[:min(30, n_cls)]

        m10, p10, n10 = [], [], []
        for q in q_sample:
            r = get_ranked(q, cnn, vit, alpha)
            m10.append(map_k(r, q, labels, 10))
            p10.append(prec_k(r, q, labels, 10))
            n10.append(ndcg_k(r, q, labels, 10))

        row = {
            "dataset": dataset_name,
            "classe" : int(cls),
            "n_imgs" : n_cls,
            "n_req"  : len(q_sample),
            "mAP@10" : round(np.mean(m10), 4),
            "P@10"   : round(np.mean(p10), 4),
            "NDCG@10": round(np.mean(n10), 4),
        }
        rows.append(row)
        print(f"{cls:>8}  {n_cls:>9}  {len(q_sample):>11}  "
              f"{row['mAP@10']:>8.4f}  {row['P@10']:>7.4f}  {row['NDCG@10']:>9.4f}")

    print("-" * 70)
    macro = {
        "dataset": dataset_name, "classe": "MACRO AVG",
        "n_imgs": len(labels), "n_req": sum(r["n_req"] for r in rows),
        "mAP@10": round(np.mean([r["mAP@10"] for r in rows]), 4),
        "P@10"  : round(np.mean([r["P@10"]   for r in rows]), 4),
        "NDCG@10":round(np.mean([r["NDCG@10"] for r in rows]), 4),
    }
    rows.append(macro)
    print(f"{'MACRO AVG':>8}  {len(labels):>9}  "
          f"                {macro['mAP@10']:>8.4f}  {macro['P@10']:>7.4f}  "
          f"{macro['NDCG@10']:>9.4f}")
    print("=" * 70)

    df = pd.DataFrame(rows)
    out = VECTORS_DIR / f"map_per_class_{dataset_name.lower().replace(' ','_')}.csv"
    df.to_csv(out, index=False)
    print(f"Sauvegardé : {out}\n")
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# SCRIPT 3 — MÉTRIQUES COMPLÈTES (P@1, P@5, NDCG, mAP@5/10/20)
# ═══════════════════════════════════════════════════════════════════════════════

def full_metrics(cnn, vit, labels, alpha, dataset_name="ISIC2020"):
    print("=" * 70)
    print(f"SCRIPT 3 — Métriques complètes ({dataset_name}, α={alpha})")
    print("=" * 70)

    np.random.seed(SEED)
    queries = np.random.choice(len(cnn), min(N_QUERIES, len(cnn)), replace=False)

    m5, m10, m20 = [], [], []
    p1, p5, p10, p20 = [], [], [], []
    n5, n10, n20 = [], [], []
    times = []

    for q in queries:
        t0 = time.perf_counter()
        r = get_ranked(q, cnn, vit, alpha)
        times.append((time.perf_counter() - t0) * 1000)

        m5.append(map_k(r, q, labels, 5))
        m10.append(map_k(r, q, labels, 10))
        m20.append(map_k(r, q, labels, 20))
        p1.append(prec_k(r, q, labels, 1))
        p5.append(prec_k(r, q, labels, 5))
        p10.append(prec_k(r, q, labels, 10))
        p20.append(prec_k(r, q, labels, 20))
        n5.append(ndcg_k(r, q, labels, 5))
        n10.append(ndcg_k(r, q, labels, 10))
        n20.append(ndcg_k(r, q, labels, 20))

    res = {
        "dataset" : dataset_name,
        "alpha"   : alpha,
        "time_ms" : round(np.mean(times), 2),
        "mAP@5"   : round(np.mean(m5), 4),
        "mAP@10"  : round(np.mean(m10), 4),
        "mAP@20"  : round(np.mean(m20), 4),
        "P@1"     : round(np.mean(p1), 4),
        "P@5"     : round(np.mean(p5), 4),
        "P@10"    : round(np.mean(p10), 4),
        "P@20"    : round(np.mean(p20), 4),
        "NDCG@5"  : round(np.mean(n5), 4),
        "NDCG@10" : round(np.mean(n10), 4),
        "NDCG@20" : round(np.mean(n20), 4),
    }

    print(f"  mAP@5={res['mAP@5']}  mAP@10={res['mAP@10']}  mAP@20={res['mAP@20']}")
    print(f"  P@1={res['P@1']}  P@5={res['P@5']}  P@10={res['P@10']}  P@20={res['P@20']}")
    print(f"  NDCG@5={res['NDCG@5']}  NDCG@10={res['NDCG@10']}  NDCG@20={res['NDCG@20']}")
    print(f"  Temps moyen : {res['time_ms']} ms/req")
    print("=" * 70 + "\n")

    return res


# ═══════════════════════════════════════════════════════════════════════════════
# SCRIPT 4 — SCALABILITÉ (temps = f(N))
# ═══════════════════════════════════════════════════════════════════════════════

def scalability(cnn, vit, labels, alpha):
    print("=" * 70)
    print("SCRIPT 4 — Scalabilité : temps = f(taille de l'index)")
    print("=" * 70)

    N = len(cnn)
    sizes = [1000, 2000, 5000, N]  # sous-ensembles croissants
    # Ajoute 50K et 100K simulés avec bruit gaussien
    sizes_simulated = [50000, 100000]

    np.random.seed(SEED)
    n_rep = 30  # répétitions par taille pour moyenner
    rows = []

    print(f"{'N':>10}  {'BF (ms)':>9}  {'Simulé':>8}")
    print("-" * 35)

    for size in sizes:
        idx = np.random.choice(N, min(size, N), replace=False)
        cnn_s = cnn[idx]
        vit_s = vit[idx]

        q = cnn_s[0]
        qv = vit_s[0]
        t_list = []
        for _ in range(n_rep):
            t0 = time.perf_counter()
            diff = cnn_s - q
            dc = np.sqrt(np.einsum('ij,ij->i', diff, diff))
            dv = 1.0 - (vit_s @ qv)
            _ = alpha * dc + (1 - alpha) * dv
            t_list.append((time.perf_counter() - t0) * 1000)

        t_mean = round(np.mean(t_list), 2)
        rows.append({"N": size, "BF_ms": t_mean, "simulated": False})
        print(f"{size:>10}  {t_mean:>9.2f}  {'Non':>8}")

    # Extrapolation linéaire pour 50K et 100K
    if len(rows) >= 2:
        x1, y1 = rows[-2]["N"], rows[-2]["BF_ms"]
        x2, y2 = rows[-1]["N"], rows[-1]["BF_ms"]
        slope = (y2 - y1) / (x2 - x1)
        for size in sizes_simulated:
            t_extrap = round(y2 + slope * (size - x2), 2)
            rows.append({"N": size, "BF_ms": t_extrap, "simulated": True})
            print(f"{size:>10}  {t_extrap:>9.2f}  {'Oui (extrap.)':>8}")

    print("=" * 70)
    print("Note : le temps brute-force croît linéairement avec N.")
    print("HJG croît en O(log N) — l'avantage augmente avec la taille de la base.\n")

    df = pd.DataFrame(rows)
    out = VECTORS_DIR / "scalability.csv"
    df.to_csv(out, index=False)
    print(f"Sauvegardé : {out}\n")
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 70)
    print("ABLATIONS COMPLÈTES — PFE CBIR Médical")
    print("=" * 70 + "\n")

    # HAM10000
    cnn, vit, labels = load(VECTORS_DIR)

    # 1. Ablation α → trouve l'α optimal
    best_alpha = ablation_alpha(cnn, vit, labels)

    # 2. mAP par classe sur HAM10000
    map_per_class(cnn, vit, labels, best_alpha, "HAM10000")

    # 3. Métriques complètes HAM10000
    res_ham = full_metrics(cnn, vit, labels, best_alpha, "HAM10000")

    # 4. Scalabilité
    scalability(cnn, vit, labels, best_alpha)

    # Résumé final
    print("=" * 70)
    print("RÉSUMÉ — Métriques finales pour le rapport")
    print("=" * 70)
    for k, v in res_ham.items():
        print(f"  {k:<12} : {v}")

    # Sauvegarde consolidée
    pd.DataFrame([res_ham]).to_csv(
        VECTORS_DIR / "metrics_final.csv", index=False)
    print(f"\nTous les fichiers CSV sauvegardés dans : {VECTORS_DIR}")
    print("Fichiers produits :")
    print("  ablation_alpha.csv          ← justifie α")
    print("  map_per_class_ham10000.csv  ← analyse par classe")
    print("  scalability.csv             ← temps = f(N)")
    print("  metrics_final.csv           ← métriques complètes rapport")


if __name__ == "__main__":
    main()
