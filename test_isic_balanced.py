"""
Test équilibré — ISIC 2020 complet — Version compressée 384D
============================================================

Objectif :
    Créer un sous-ensemble équilibré à partir de ISIC 2020 complet :
        - tous les cas malins
        - même nombre de cas bénins choisis aléatoirement

    Puis évaluer le système CBIR sur cette base équilibrée.

Entrée :
    C:\\Users\\hp\\Desktop\\PFE\\Vectors-ISIC-FULL\\fusion_compressed_384D.npy
    C:\\Users\\hp\\Desktop\\PFE\\Vectors-ISIC-FULL\\labels.npy
    C:\\Users\\hp\\Desktop\\PFE\\Vectors-ISIC-FULL\\image_ids.npy

Sortie :
    C:\\Users\\hp\\Desktop\\PFE\\Vectors-ISIC-BALANCED\\
"""

import time
import numpy as np
import pandas as pd
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

SOURCE_DIR = Path(r"C:\Users\hp\Desktop\PFE\Vectors-ISIC-FULL")
OUT_DIR = Path(r"C:\Users\hp\Desktop\PFE\Vectors-ISIC-BALANCED")
RESULTS_DIR = OUT_DIR / "analysis_results_balanced"

OUT_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

FUSION_FILE = SOURCE_DIR / "fusion_compressed_384D.npy"
LABELS_FILE = SOURCE_DIR / "labels.npy"
IMAGE_IDS_FILE = SOURCE_DIR / "image_ids.npy"

CNN_DIM = 256
EXPECTED_TOTAL_DIM = 384
EXPECTED_VIT_DIM = 128

BENIGN_LABEL = 0
MALIGNANT_LABEL = 1

ALPHA_FINAL = 0.1
SEED = 42

K_VALUES = [5, 10, 20]


# ============================================================
# CHARGEMENT ET CRÉATION DE LA BASE ÉQUILIBRÉE
# ============================================================

def create_balanced_dataset():
    print("=" * 70)
    print("CRÉATION DE LA BASE ISIC ÉQUILIBRÉE")
    print("=" * 70)

    fusion = np.load(FUSION_FILE).astype(np.float32)
    labels = np.load(LABELS_FILE)

    assert fusion.shape[1] == EXPECTED_TOTAL_DIM, (
        f"Erreur : attendu {EXPECTED_TOTAL_DIM}D, obtenu {fusion.shape[1]}D"
    )

    if IMAGE_IDS_FILE.exists():
        image_ids = np.load(IMAGE_IDS_FILE, allow_pickle=True)
    else:
        image_ids = np.array([f"img_{i}" for i in range(len(labels))])

    benign_idx = np.where(labels == BENIGN_LABEL)[0]
    malignant_idx = np.where(labels == MALIGNANT_LABEL)[0]

    print(f"Nombre total d'images : {len(labels)}")
    print(f"Bénins trouvés : {len(benign_idx)}")
    print(f"Malins trouvés : {len(malignant_idx)}")

    if len(malignant_idx) == 0:
        raise ValueError("Aucun cas malin trouvé. Vérifie que le label malin est bien 1.")

    np.random.seed(SEED)

    n_malignant = len(malignant_idx)
    selected_benign = np.random.choice(
        benign_idx,
        size=n_malignant,
        replace=False
    )

    balanced_idx = np.concatenate([selected_benign, malignant_idx])

    np.random.shuffle(balanced_idx)

    fusion_balanced = fusion[balanced_idx]
    labels_balanced = labels[balanced_idx]
    image_ids_balanced = image_ids[balanced_idx]

    np.save(OUT_DIR / "fusion_compressed_384D.npy", fusion_balanced)
    np.save(OUT_DIR / "labels.npy", labels_balanced)
    np.save(OUT_DIR / "image_ids.npy", image_ids_balanced)

    print("\nBase équilibrée créée :")
    print(f"Total : {len(labels_balanced)} images")

    unique, counts = np.unique(labels_balanced, return_counts=True)
    for cls, count in zip(unique, counts):
        print(f"Classe {cls} : {count} images")

    print("\nFichiers sauvegardés dans :")
    print(OUT_DIR)
    print("=" * 70 + "\n")

    return fusion_balanced, labels_balanced, image_ids_balanced


# ============================================================
# PRÉPARATION CNN / VIT
# ============================================================

def split_and_normalize(fusion):
    cnn = fusion[:, :CNN_DIM]
    vit = fusion[:, CNN_DIM:]

    assert cnn.shape[1] == CNN_DIM, f"Erreur CNN : attendu {CNN_DIM}D"
    assert vit.shape[1] == EXPECTED_VIT_DIM, (
        f"Erreur ViT : attendu {EXPECTED_VIT_DIM}D, obtenu {vit.shape[1]}D"
    )

    cnn = cnn / (np.linalg.norm(cnn, axis=1, keepdims=True) + 1e-8)
    vit = vit / (np.linalg.norm(vit, axis=1, keepdims=True) + 1e-8)

    print("Dimensions vérifiées :")
    print(f"CNN : {cnn.shape[1]}D")
    print(f"ViT : {vit.shape[1]}D")
    print()

    return cnn, vit


# ============================================================
# DISTANCE ET MÉTRIQUES
# ============================================================

def d_joint(q_cnn, q_vit, cnn, vit, alpha):
    d_cnn = np.sqrt(np.einsum("ij,ij->i", cnn - q_cnn, cnn - q_cnn))
    d_vit = 1.0 - (vit @ q_vit)
    return alpha * d_cnn + (1.0 - alpha) * d_vit


def get_ranked(q_idx, cnn, vit, alpha):
    d = d_joint(cnn[q_idx], vit[q_idx], cnn, vit, alpha)
    d[q_idx] = np.inf
    return np.argsort(d)


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
# ABLATION ALPHA SUR BASE ÉQUILIBRÉE
# ============================================================

def run_alpha_ablation(cnn, vit, labels):
    print("=" * 70)
    print("1. ABLATION ALPHA SUR BASE ÉQUILIBRÉE")
    print("=" * 70)

    alphas = [round(i * 0.1, 1) for i in range(11)]
    queries = np.arange(len(labels))

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
    df.to_csv(RESULTS_DIR / "balanced_ablation_alpha.csv", index=False)

    best = max(rows, key=lambda x: x["mAP@10"])

    print("\nMeilleur alpha selon mAP@10 :", best["alpha"])
    print("Alpha final retenu :", ALPHA_FINAL)
    print("Fichier sauvegardé : balanced_ablation_alpha.csv\n")

    return df


# ============================================================
# MÉTRIQUES GLOBALES
# ============================================================

def run_global_metrics(cnn, vit, labels):
    print("=" * 70)
    print("2. MÉTRIQUES GLOBALES SUR BASE ÉQUILIBRÉE")
    print("=" * 70)

    queries = np.arange(len(labels))

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
        "dataset": "ISIC2020_BALANCED_LIGHT",
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

    pd.DataFrame([row]).to_csv(RESULTS_DIR / "balanced_metrics_global.csv", index=False)

    for key, value in row.items():
        print(f"{key:<15} : {value}")

    print("\nFichier sauvegardé : balanced_metrics_global.csv\n")

    return row


# ============================================================
# MÉTRIQUES PAR CLASSE
# ============================================================

def run_per_class_metrics(cnn, vit, labels):
    print("=" * 70)
    print("3. MÉTRIQUES PAR CLASSE SUR BASE ÉQUILIBRÉE")
    print("=" * 70)

    rows = []

    for cls in np.unique(labels):
        cls_idx = np.where(labels == cls)[0]

        maps, precisions, recalls, ndcgs = [], [], [], []

        for q in cls_idx:
            ranked = get_ranked(q, cnn, vit, ALPHA_FINAL)

            maps.append(map_at_k(ranked, q, labels, 10))
            precisions.append(precision_at_k(ranked, q, labels, 10))
            recalls.append(recall_at_k(ranked, q, labels, 10))
            ndcgs.append(ndcg_at_k(ranked, q, labels, 10))

        row = {
            "classe": int(cls),
            "n_images": len(cls_idx),
            "n_queries": len(cls_idx),
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
            f"R@10={row['R@10']} | "
            f"NDCG@10={row['NDCG@10']}"
        )

    macro = {
        "classe": "MACRO_AVG",
        "n_images": len(labels),
        "n_queries": len(labels),
        "mAP@10": round(np.mean([r["mAP@10"] for r in rows]), 4),
        "P@10": round(np.mean([r["P@10"] for r in rows]), 4),
        "R@10": round(np.mean([r["R@10"] for r in rows]), 4),
        "NDCG@10": round(np.mean([r["NDCG@10"] for r in rows]), 4),
    }

    rows.append(macro)

    print("\nMACRO AVG")
    print(macro)

    pd.DataFrame(rows).to_csv(RESULTS_DIR / "balanced_metrics_per_class.csv", index=False)

    print("\nFichier sauvegardé : balanced_metrics_per_class.csv\n")

    return rows


# ============================================================
# ANALYSE DES CAS MALINS
# ============================================================

def run_malignant_analysis(cnn, vit, labels):
    print("=" * 70)
    print("4. ANALYSE DES CAS MALINS SUR BASE ÉQUILIBRÉE")
    print("=" * 70)

    malignant_queries = np.where(labels == MALIGNANT_LABEL)[0]

    maps, precisions, recalls, ndcgs = [], [], [], []
    malignant_counts_top10 = []
    times = []

    for q in malignant_queries:
        t0 = time.perf_counter()
        ranked = get_ranked(q, cnn, vit, ALPHA_FINAL)
        times.append((time.perf_counter() - t0) * 1000)

        top10 = [i for i in ranked if i != q][:10]
        n_malignant_top10 = sum(labels[i] == MALIGNANT_LABEL for i in top10)

        malignant_counts_top10.append(n_malignant_top10)
        maps.append(map_at_k(ranked, q, labels, 10))
        precisions.append(precision_at_k(ranked, q, labels, 10))
        recalls.append(recall_at_k(ranked, q, labels, 10))
        ndcgs.append(ndcg_at_k(ranked, q, labels, 10))

    row = {
        "dataset": "ISIC2020_BALANCED_LIGHT",
        "classe": "malignant",
        "label": MALIGNANT_LABEL,
        "n_queries": len(malignant_queries),
        "alpha": ALPHA_FINAL,
        "mAP@10_malin": round(np.mean(maps), 4),
        "P@10_malin": round(np.mean(precisions), 4),
        "R@10_malin": round(np.mean(recalls), 4),
        "NDCG@10_malin": round(np.mean(ndcgs), 4),
        "malins_moyens_top10": round(np.mean(malignant_counts_top10), 2),
        "time_ms": round(np.mean(times), 2),
    }

    pd.DataFrame([row]).to_csv(RESULTS_DIR / "balanced_metrics_malignant.csv", index=False)

    for key, value in row.items():
        print(f"{key:<22} : {value}")

    print("\nFichier sauvegardé : balanced_metrics_malignant.csv\n")

    return row


# ============================================================
# MAIN
# ============================================================

def main():
    print("\n")
    print("=" * 70)
    print("TEST ÉQUILIBRÉ — ISIC 2020 COMPLET — VERSION 384D")
    print("=" * 70)
    print("\n")

    fusion_balanced, labels_balanced, image_ids_balanced = create_balanced_dataset()

    cnn, vit = split_and_normalize(fusion_balanced)

    run_alpha_ablation(cnn, vit, labels_balanced)

    global_results = run_global_metrics(cnn, vit, labels_balanced)

    run_per_class_metrics(cnn, vit, labels_balanced)

    malignant_results = run_malignant_analysis(cnn, vit, labels_balanced)

    print("=" * 70)
    print("RÉSUMÉ FINAL — TEST ÉQUILIBRÉ")
    print("=" * 70)

    print("Résultats globaux :")
    for key, value in global_results.items():
        print(f"{key:<18} : {value}")

    print("\nRésultats cas malins :")
    for key, value in malignant_results.items():
        print(f"{key:<22} : {value}")

    print("\nDossier des résultats :")
    print(RESULTS_DIR)
    print("=" * 70)


if __name__ == "__main__":
    main()