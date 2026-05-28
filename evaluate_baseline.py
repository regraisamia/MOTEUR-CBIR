"""
Évaluation baseline — Brute-force K-NN sur tous les vecteurs extraits.

Pour chaque méthode d'extraction, on mesure :
  - Recall@K   : % des vraies images similaires retrouvées dans le Top-K
  - Precision@K: % des résultats Top-K qui sont vraiment similaires
  - Temps moyen par requête (ms)

Définition de "similaire" : même classe de lésion (dx) dans les métadonnées HAM10000.
Les 7 classes : mel, nv, bcc, akiec, bkl, df, vasc

Usage :
    python evaluate_baseline.py
"""

import os
import sys
import time
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings("ignore")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import VECTORS_DIR, META_CSV, OUT


# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────

K_VALUES      = [1, 5, 10, 20]   # valeurs de K à évaluer
N_QUERIES     = 200               # nombre de requêtes de test (subset aléatoire)
RANDOM_SEED   = 42
DISTANCE_MAP  = {
    # Pour chaque méthode : quelle distance utiliser
    "classical_color"       : "euclidean",
    "classical_haralick"    : "euclidean",
    "cnn_resnet50"          : "euclidean",
    "cnn_densenet121"       : "euclidean",
    "vit_base"              : "cosine",      # cosinus pour les embeddings ViT
    "fusion_cnn_vit"        : "cosine",      # cosinus après normalisation L2
    "fusion_cnn_classical"  : "cosine",
    "fusion_all"            : "cosine",
}


# ─────────────────────────────────────────────
#  CHARGEMENT DES DONNÉES
# ─────────────────────────────────────────────

def load_labels():
    """
    Charge les labels de classe depuis le CSV HAM10000.
    Retourne un array (N,) avec la classe de chaque image dans l'ordre du CSV.
    """
    df = pd.read_csv(META_CSV)

    # Charge l'ordre des image_ids sauvegardé lors de l'extraction
    ids_path = os.path.join(VECTORS_DIR, OUT["image_ids"])
    if os.path.exists(ids_path):
        saved_ids = np.load(ids_path, allow_pickle=True).tolist()
        df = df.set_index("image_id").loc[saved_ids].reset_index()

    le = LabelEncoder()
    labels = le.fit_transform(df["dx"].values)

    print(f"Classes trouvées : {dict(zip(le.classes_, range(len(le.classes_))))}")
    print(f"Distribution : {dict(zip(*np.unique(labels, return_counts=True)))}\n")
    return labels, le.classes_


def load_vector(name_key: str):
    """Charge un fichier .npy depuis vectors/"""
    path = os.path.join(VECTORS_DIR, OUT[name_key])
    if not os.path.exists(path):
        return None
    vec = np.load(path).astype(np.float32)
    return vec


# ─────────────────────────────────────────────
#  CALCUL DE DISTANCE
# ─────────────────────────────────────────────

def compute_distances(query_vec, database_vec, metric: str):
    """
    Calcule les distances entre un vecteur requête et toute la base.
    Retourne les indices triés du plus proche au plus loin.
    """
    if metric == "cosine":
        # similarité cosinus → on veut les plus grands
        sims = cosine_similarity(query_vec.reshape(1, -1), database_vec)[0]
        sorted_indices = np.argsort(-sims)   # ordre décroissant
    else:
        # distance euclidienne → on veut les plus petits
        dists = np.linalg.norm(database_vec - query_vec, axis=1)
        sorted_indices = np.argsort(dists)   # ordre croissant

    return sorted_indices


# ─────────────────────────────────────────────
#  MÉTRIQUES
# ─────────────────────────────────────────────

def recall_at_k(retrieved_indices, query_idx, labels, k):
    """
    Recall@K standard CBIR :
    = résultats corrects dans Top-K / min(K, total vrais positifs)

    Exemple : classe "nv" a 6700 images.
    Recall@10 = images_nv_dans_top10 / min(10, 6699)
              = images_nv_dans_top10 / 10

    Sans ce min(), Recall@10 = x/6699 ≈ 0 même si tous les top-10 sont corrects.
    """
    query_label = labels[query_idx]

    true_positives = set(np.where(labels == query_label)[0]) - {query_idx}
    if len(true_positives) == 0:
        return 0.0

    top_k = [i for i in retrieved_indices if i != query_idx][:k]
    retrieved_set = set(top_k)

    # Dénominateur corrigé : min(K, nb vrais positifs)
    denominator = min(k, len(true_positives))
    recall = len(retrieved_set & true_positives) / denominator
    return recall


def precision_at_k(retrieved_indices, query_idx, labels, k):
    """
    Precision@K : parmi les K résultats, combien ont la bonne classe ?
    """
    query_label = labels[query_idx]
    top_k = [i for i in retrieved_indices if i != query_idx][:k]
    if len(top_k) == 0:
        return 0.0
    correct = sum(1 for i in top_k if labels[i] == query_label)
    return correct / len(top_k)


# ─────────────────────────────────────────────
#  ÉVALUATION D'UNE MÉTHODE
# ─────────────────────────────────────────────

def evaluate_method(name_key: str, vectors: np.ndarray, labels: np.ndarray, metric: str):
    """
    Évalue une méthode d'extraction sur N_QUERIES requêtes aléatoires.
    Retourne un dict de résultats.
    """
    np.random.seed(RANDOM_SEED)
    n = len(vectors)
    query_indices = np.random.choice(n, size=min(N_QUERIES, n), replace=False)

    recalls    = {k: [] for k in K_VALUES}
    precisions = {k: [] for k in K_VALUES}
    times      = []

    for q_idx in query_indices:
        query_vec = vectors[q_idx]

        t0 = time.perf_counter()
        sorted_idx = compute_distances(query_vec, vectors, metric)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        times.append(elapsed_ms)

        for k in K_VALUES:
            recalls[k].append(recall_at_k(sorted_idx, q_idx, labels, k))
            precisions[k].append(precision_at_k(sorted_idx, q_idx, labels, k))

    results = {
        "dim"  : vectors.shape[1],
        "metric": metric,
        "time_ms": np.mean(times),
        "recalls"    : {k: np.mean(v) for k, v in recalls.items()},
        "precisions" : {k: np.mean(v) for k, v in precisions.items()},
    }
    return results


# ─────────────────────────────────────────────
#  AFFICHAGE DU TABLEAU
# ─────────────────────────────────────────────

def print_results_table(all_results: dict):
    """Affiche un tableau récapitulatif bien formaté."""

    k_show = [5, 10, 20]   # K à afficher dans le tableau

    # En-tête
    header = f"{'Méthode':<28} {'Dim':>5}  {'Dist':>9}  {'ms/req':>7}"
    for k in k_show:
        header += f"  {'R@'+str(k):>6}  {'P@'+str(k):>6}"
    print("\n" + "="*len(header))
    print(header)
    print("="*len(header))

    # Tri par Recall@10 décroissant
    sorted_methods = sorted(
        all_results.items(),
        key=lambda x: x[1]["recalls"].get(10, 0),
        reverse=True
    )

    for name, res in sorted_methods:
        row = f"{name:<28} {res['dim']:>5}  {res['metric']:>9}  {res['time_ms']:>7.1f}"
        for k in k_show:
            r = res["recalls"].get(k, 0)
            p = res["precisions"].get(k, 0)
            row += f"  {r:>6.3f}  {p:>6.3f}"
        print(row)

    print("="*len(header))
    print(f"\nR@K = Recall@K,  P@K = Precision@K,  ms/req = temps moyen par requête")
    print(f"Évaluation sur {N_QUERIES} requêtes aléatoires, seed={RANDOM_SEED}\n")


def save_results_csv(all_results: dict):
    """Sauvegarde les résultats dans un CSV pour le rapport."""
    rows = []
    for name, res in all_results.items():
        row = {
            "methode"   : name,
            "dimensions": res["dim"],
            "distance"  : res["metric"],
            "temps_ms"  : round(res["time_ms"], 2),
        }
        for k in K_VALUES:
            row[f"recall_{k}"]    = round(res["recalls"].get(k, 0), 4)
            row[f"precision_{k}"] = round(res["precisions"].get(k, 0), 4)
        rows.append(row)

    df = pd.DataFrame(rows).sort_values("recall_10", ascending=False)
    out_path = os.path.join(VECTORS_DIR, "baseline_results.csv")
    df.to_csv(out_path, index=False)
    print(f"Résultats sauvegardés : {out_path}")


# ─────────────────────────────────────────────
#  PIPELINE PRINCIPAL
# ─────────────────────────────────────────────

def main():
    print("Chargement des labels...")
    labels, classes = load_labels()

    all_results = {}

    methods = [
        ("classical_color",    "color"),
        ("classical_haralick", "haralick"),
        ("resnet50",           "cnn_resnet50"),
        ("densenet121",        "cnn_densenet121"),
        ("vit_base",           "vit_base"),
        ("fusion_cnn_vit",     "fusion_cnn_vit"),
        ("fusion_cnn_cls",     "fusion_cnn_classical"),
        ("fusion_all",         "fusion_all"),
    ]

    for display_name, key in methods:
        vectors = load_vector(key)
        if vectors is None:
            print(f"  [{display_name}] fichier introuvable, ignoré.")
            continue

        metric = DISTANCE_MAP.get(key, "euclidean")
        print(f"Évaluation {display_name} ({vectors.shape[1]}D, {metric})...")

        res = evaluate_method(key, vectors, labels, metric)
        all_results[display_name] = res

        # Affichage rapide
        r5  = res["recalls"].get(5, 0)
        r10 = res["recalls"].get(10, 0)
        print(f"  → Recall@5={r5:.3f}  Recall@10={r10:.3f}  {res['time_ms']:.1f}ms/req\n")

    print_results_table(all_results)
    save_results_csv(all_results)


if __name__ == "__main__":
    main()