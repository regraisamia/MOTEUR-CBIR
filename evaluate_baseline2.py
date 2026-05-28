"""
Évaluation baseline CBIR — métriques correctes pour HAM10000.

Métriques utilisées :
  - Precision@K : % des K résultats qui ont la bonne classe  (déjà correct)
  - Recall@K    : résultats corrects / min(K, vrais positifs) (CORRIGÉ)
  - mAP@K       : mean Average Precision — métrique standard CBIR

Usage : python evaluate_baseline2.py
"""

import os, sys, time
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings("ignore")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import VECTORS_DIR, META_CSV, OUT

K_VALUES   = [5, 10, 20]
N_QUERIES  = 200
SEED       = 42

# ── Chargement labels ───────────────────────────────────────────────────────

def load_labels():
    df = pd.read_csv(META_CSV)
    ids_path = os.path.join(VECTORS_DIR, OUT["image_ids"])
    if os.path.exists(ids_path):
        saved_ids = np.load(ids_path, allow_pickle=True).tolist()
        df = df.set_index("image_id").loc[saved_ids].reset_index()
    le = LabelEncoder()
    labels = le.fit_transform(df["dx"].values)
    counts = dict(zip(*np.unique(labels, return_counts=True)))
    print("Distribution des classes :")
    for cls, idx in zip(le.classes_, range(len(le.classes_))):
        print(f"  {cls:8s} ({idx}) : {counts[idx]} images")
    print()
    return labels, le.classes_

def load_vec(key):
    path = os.path.join(VECTORS_DIR, OUT[key])
    return np.load(path).astype(np.float32) if os.path.exists(path) else None

# ── Distance ────────────────────────────────────────────────────────────────

def get_sorted_indices(query, database, metric):
    if metric == "cosine":
        # normalise puis produit scalaire = cosinus
        q = query / (np.linalg.norm(query) + 1e-8)
        D = database / (np.linalg.norm(database, axis=1, keepdims=True) + 1e-8)
        sims = D @ q
        return np.argsort(-sims)
    else:
        dists = np.linalg.norm(database - query, axis=1)
        return np.argsort(dists)

# ── Métriques ───────────────────────────────────────────────────────────────

def precision_at_k(ranked, q_idx, labels, k):
    top = [i for i in ranked if i != q_idx][:k]
    if not top:
        return 0.0
    return sum(labels[i] == labels[q_idx] for i in top) / len(top)

def recall_at_k(ranked, q_idx, labels, k):
    """
    Recall@K corrigé pour CBIR :
    = corrects_dans_top_k / min(K, nb_images_de_même_classe)

    Exemple : classe "nv" a 6700 images.
    Recall@10 = images_nv_dans_top10 / min(10, 6699) = x/10
    Pas x/6699 — ce serait toujours ≈ 0.
    """
    top = [i for i in ranked if i != q_idx][:k]
    if not top:
        return 0.0
    n_relevant = max(1, min(k, (labels == labels[q_idx]).sum() - 1))
    correct = sum(labels[i] == labels[q_idx] for i in top)
    return correct / n_relevant

def average_precision(ranked, q_idx, labels, k):
    """
    AP@K : métrique CBIR standard.
    Moyenne des Precision@i pour chaque position i où le résultat est correct.
    """
    top = [i for i in ranked if i != q_idx][:k]
    if not top:
        return 0.0
    hits, score = 0, 0.0
    for rank, idx in enumerate(top, 1):
        if labels[idx] == labels[q_idx]:
            hits += 1
            score += hits / rank
    n_relevant = min(k, (labels == labels[q_idx]).sum() - 1)
    return score / max(1, n_relevant)

# ── Évaluation d'une méthode ────────────────────────────────────────────────

def evaluate(name, vectors, labels, metric):
    np.random.seed(SEED)
    queries = np.random.choice(len(vectors), size=min(N_QUERIES, len(vectors)), replace=False)

    results = {k: {"p": [], "r": [], "ap": []} for k in K_VALUES}
    times = []

    for q_idx in queries:
        t0 = time.perf_counter()
        ranked = get_sorted_indices(vectors[q_idx], vectors, metric)
        times.append((time.perf_counter() - t0) * 1000)

        for k in K_VALUES:
            results[k]["p"].append(precision_at_k(ranked, q_idx, labels, k))
            results[k]["r"].append(recall_at_k(ranked, q_idx, labels, k))
            results[k]["ap"].append(average_precision(ranked, q_idx, labels, k))

    return {
        "dim"    : vectors.shape[1],
        "metric" : metric,
        "time_ms": np.mean(times),
        "metrics": {k: {
            "P@K" : np.mean(results[k]["p"]),
            "R@K" : np.mean(results[k]["r"]),
            "mAP" : np.mean(results[k]["ap"]),
        } for k in K_VALUES}
    }

# ── Affichage ───────────────────────────────────────────────────────────────

def print_table(all_res):
    k_show = [5, 10, 20]
    sep = "=" * 108
    header = f"{'Méthode':<26} {'Dim':>5}  {'ms':>7}  "
    for k in k_show:
        header += f"  P@{k:<3} R@{k:<3} mAP@{k:<3}"
    print("\n" + sep)
    print(header)
    print(sep)

    sorted_res = sorted(all_res.items(),
                        key=lambda x: x[1]["metrics"][10]["mAP"], reverse=True)

    for name, res in sorted_res:
        row = f"{name:<26} {res['dim']:>5}  {res['time_ms']:>7.1f}  "
        for k in k_show:
            m = res["metrics"][k]
            row += f"  {m['P@K']:.3f} {m['R@K']:.3f} {m['mAP']:.3f}   "
        print(row)
    print(sep)
    print("P@K=Precision, R@K=Recall corrigé, mAP=mean Average Precision (métrique principale CBIR)\n")

def save_csv(all_res):
    rows = []
    for name, res in all_res.items():
        row = {"methode": name, "dim": res["dim"],
               "metric": res["metric"], "time_ms": round(res["time_ms"], 2)}
        for k in K_VALUES:
            m = res["metrics"][k]
            row[f"P@{k}"]   = round(m["P@K"], 4)
            row[f"R@{k}"]   = round(m["R@K"], 4)
            row[f"mAP@{k}"] = round(m["mAP"], 4)
        rows.append(row)
    df = pd.DataFrame(rows).sort_values("mAP@10", ascending=False)
    out = os.path.join(VECTORS_DIR, "baseline_results.csv")
    df.to_csv(out, index=False)
    print(f"CSV sauvegardé : {out}")

# ── Main ────────────────────────────────────────────────────────────────────

METHODS = [
    ("classical_color",    "color",          "euclidean"),
    ("classical_haralick", "haralick",       "euclidean"),
    ("resnet50",           "resnet50",       "euclidean"),
    ("densenet121",        "densenet121",    "euclidean"),
    ("vit_base",           "vit_base",       "cosine"),
    ("fusion_cnn_vit",     "fusion_cnn_vit", "cosine"),
    ("fusion_cnn_cls",     "fusion_cnn_cls", "cosine"),
    ("fusion_all",         "fusion_all",     "cosine"),
]

def main():
    print("=== Évaluation baseline CBIR ===\n")
    labels, classes = load_labels()
    all_res = {}

    for display, key, metric in METHODS:
        vecs = load_vec(key)
        if vecs is None:
            print(f"  [{display}] introuvable, ignoré.\n")
            continue
        print(f"Évaluation {display} ({vecs.shape[1]}D, {metric})...")
        res = evaluate(display, vecs, labels, metric)
        all_res[display] = res
        m10 = res["metrics"][10]
        print(f"  P@10={m10['P@K']:.3f}  R@10={m10['R@K']:.3f}  mAP@10={m10['mAP']:.3f}"
              f"  ({res['time_ms']:.1f}ms/req)\n")

    print_table(all_res)
    save_csv(all_res)

if __name__ == "__main__":
    main()