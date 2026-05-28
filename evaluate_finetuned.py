"""
Évaluation des modèles fine-tunés + comparaison avec baseline.
Lance après finetune.py.

Usage :
    python evaluate_finetuned.py
"""

import os, sys, time
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import VECTORS_DIR, META_CSV, OUT

K_VALUES  = [5, 10, 20]
N_QUERIES = 200
SEED      = 42


def load_labels():
    df = pd.read_csv(META_CSV)
    ids_path = os.path.join(VECTORS_DIR, OUT["image_ids"])
    if os.path.exists(ids_path):
        saved_ids = np.load(ids_path, allow_pickle=True).tolist()
        df = df.set_index("image_id").loc[saved_ids].reset_index()
    le = LabelEncoder()
    return le.fit_transform(df["dx"].values)


def get_sorted(query, database, metric):
    if metric == "cosine":
        q = query / (np.linalg.norm(query) + 1e-8)
        D = database / (np.linalg.norm(database, axis=1, keepdims=True) + 1e-8)
        return np.argsort(-(D @ q))
    return np.argsort(np.linalg.norm(database - query, axis=1))


def map_at_k(ranked, q_idx, labels, k):
    top  = [i for i in ranked if i != q_idx][:k]
    hits, score = 0, 0.0
    for rank, idx in enumerate(top, 1):
        if labels[idx] == labels[q_idx]:
            hits  += 1
            score += hits / rank
    denom = min(k, max(1, (labels == labels[q_idx]).sum() - 1))
    return score / denom


def precision_at_k(ranked, q_idx, labels, k):
    top = [i for i in ranked if i != q_idx][:k]
    return sum(labels[i] == labels[q_idx] for i in top) / max(1, len(top))


def evaluate(name, vectors, labels, metric):
    np.random.seed(SEED)
    queries = np.random.choice(len(vectors), size=min(N_QUERIES, len(vectors)), replace=False)
    maps = {k: [] for k in K_VALUES}
    prec = {k: [] for k in K_VALUES}
    times = []
    for q in queries:
        t0 = time.perf_counter()
        ranked = get_sorted(vectors[q], vectors, metric)
        times.append((time.perf_counter() - t0) * 1000)
        for k in K_VALUES:
            maps[k].append(map_at_k(ranked, q, labels, k))
            prec[k].append(precision_at_k(ranked, q, labels, k))
    return {
        "dim"    : vectors.shape[1],
        "time_ms": np.mean(times),
        "map"    : {k: np.mean(maps[k]) for k in K_VALUES},
        "prec"   : {k: np.mean(prec[k]) for k in K_VALUES},
    }


def print_table(results):
    sep = "=" * 90
    print("\n" + sep)
    print(f"{'Méthode':<30} {'Dim':>5} {'ms':>7}   mAP@5  mAP@10  mAP@20    P@10")
    print(sep)
    for name, res in sorted(results.items(), key=lambda x: -x[1]["map"][10]):
        print(f"{name:<30} {res['dim']:>5} {res['time_ms']:>7.1f}   "
              f"{res['map'][5]:.3f}   {res['map'][10]:.3f}   {res['map'][20]:.3f}   "
              f"{res['prec'][10]:.3f}")
    print(sep + "\n")


def main():
    labels = load_labels()
    results = {}

    # ── Baseline (déjà extrait) ──────────────────────────────
    to_eval = [
        ("Baseline ResNet50",     os.path.join(VECTORS_DIR, OUT["resnet50"]),     "euclidean"),
        ("Baseline ViT",          os.path.join(VECTORS_DIR, OUT["vit_base"]),     "cosine"),
        ("Baseline CNN+ViT",      os.path.join(VECTORS_DIR, OUT["fusion_cnn_vit"]), "cosine"),
    ]

    # ── Fine-tunés ───────────────────────────────────────────
    ft_resnet = os.path.join(VECTORS_DIR, "finetuned_resnet50.npy")
    ft_vit    = os.path.join(VECTORS_DIR, "finetuned_vit.npy")
    ft_fusion = os.path.join(VECTORS_DIR, "finetuned_fusion.npy")

    if os.path.exists(ft_resnet):
        to_eval.append(("SupCon ResNet50 (FT)",  ft_resnet, "cosine"))
    if os.path.exists(ft_vit):
        to_eval.append(("SupCon ViT (FT)",       ft_vit,    "cosine"))
    if os.path.exists(ft_fusion):
        to_eval.append(("SupCon CNN+ViT (FT)",   ft_fusion, "cosine"))

    for name, path, metric in to_eval:
        if not os.path.exists(path):
            print(f"  [{name}] introuvable, ignoré.")
            continue
        vecs = np.load(path).astype(np.float32)
        print(f"Évaluation {name} ({vecs.shape[1]}D)...")
        res = evaluate(name, vecs, labels, metric)
        results[name] = res
        print(f"  mAP@10={res['map'][10]:.3f}  P@10={res['prec'][10]:.3f}  {res['time_ms']:.1f}ms\n")

    print_table(results)

    # ── Fusion des fine-tunés ─────────────────────────────────
    if os.path.exists(ft_resnet) and os.path.exists(ft_vit):
        print("Construction fusion fine-tunée CNN+ViT...")
        v_cnn = np.load(ft_resnet).astype(np.float32)
        v_vit = np.load(ft_vit).astype(np.float32)
        # Normalisation L2 avant fusion
        v_cnn /= (np.linalg.norm(v_cnn, axis=1, keepdims=True) + 1e-8)
        v_vit /= (np.linalg.norm(v_vit, axis=1, keepdims=True) + 1e-8)
        fusion = np.concatenate([v_cnn, v_vit], axis=1)
        np.save(ft_fusion, fusion)
        print(f"Fusion sauvegardée : {ft_fusion}  {fusion.shape}\n")

        # Évalue la fusion
        print("Évaluation SupCon CNN+ViT fusionné...")
        res = evaluate("SupCon CNN+ViT (FT)", fusion, labels, "cosine")
        results["SupCon CNN+ViT (FT)"] = res
        print(f"  mAP@10={res['map'][10]:.3f}  P@10={res['prec'][10]:.3f}\n")
        print_table(results)


if __name__ == "__main__":
    main()
