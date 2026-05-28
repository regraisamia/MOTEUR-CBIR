import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.decomposition import PCA
import joblib

# ============================================================
# CONFIGURATION
# ============================================================

VECTORS_DIR = Path(r"C:\Users\hp\Desktop\PFE\Vectors-ISIC2019")

FUSION_FILE = VECTORS_DIR / "fusion_concat.npy"
LABELS_FILE = VECTORS_DIR / "labels.npy"
IMAGE_IDS_FILE = VECTORS_DIR / "image_ids.npy"
METADATA_FILE = VECTORS_DIR / "metadata.csv"

CNN_ORIG_DIM = 2048
VIT_ORIG_DIM = 768

CNN_COMP_DIM = 256
VIT_COMP_DIM = 128

OUT_FUSION = VECTORS_DIR / "fusion_compressed_384D.npy"
OUT_PCA_CNN = VECTORS_DIR / "pca_cnn_isic2019.pkl"
OUT_PCA_VIT = VECTORS_DIR / "pca_vit_isic2019.pkl"


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("COMPRESSION ISIC 2019 : 2816D -> 384D")
    print("=" * 70)

    if not FUSION_FILE.exists():
        raise FileNotFoundError(f"Fichier introuvable : {FUSION_FILE}")

    fusion = np.load(FUSION_FILE).astype(np.float32)

    print("Fusion originale :", fusion.shape)

    assert fusion.shape[1] == 2816, (
        f"Erreur : fusion_concat.npy doit être 2816D, obtenu {fusion.shape[1]}D"
    )

    cnn_orig = fusion[:, :CNN_ORIG_DIM]
    vit_orig = fusion[:, CNN_ORIG_DIM:]

    print("CNN original :", cnn_orig.shape)
    print("ViT original :", vit_orig.shape)

    print("\nApplication PCA CNN : 2048D -> 256D")
    pca_cnn = PCA(n_components=CNN_COMP_DIM, random_state=42)
    cnn_comp = pca_cnn.fit_transform(cnn_orig)

    print("Application PCA ViT : 768D -> 128D")
    pca_vit = PCA(n_components=VIT_COMP_DIM, random_state=42)
    vit_comp = pca_vit.fit_transform(vit_orig)

    print("\nVariance conservée :")
    print("CNN :", round(pca_cnn.explained_variance_ratio_.sum(), 4))
    print("ViT :", round(pca_vit.explained_variance_ratio_.sum(), 4))

    print("\nNormalisation L2 après PCA")
    cnn_comp = cnn_comp / (np.linalg.norm(cnn_comp, axis=1, keepdims=True) + 1e-8)
    vit_comp = vit_comp / (np.linalg.norm(vit_comp, axis=1, keepdims=True) + 1e-8)

    print("Conversion Float16")
    cnn_comp = cnn_comp.astype(np.float16)
    vit_comp = vit_comp.astype(np.float16)

    fusion_compressed = np.concatenate([cnn_comp, vit_comp], axis=1)

    assert fusion_compressed.shape[1] == 384, (
        f"Erreur : attendu 384D, obtenu {fusion_compressed.shape[1]}D"
    )

    np.save(OUT_FUSION, fusion_compressed)
    joblib.dump(pca_cnn, OUT_PCA_CNN)
    joblib.dump(pca_vit, OUT_PCA_VIT)

    print("\nFichiers sauvegardés :")
    print(OUT_FUSION)
    print(OUT_PCA_CNN)
    print(OUT_PCA_VIT)

    if LABELS_FILE.exists():
        labels = np.load(LABELS_FILE)
        print("\nLabels :", labels.shape)
        print("Distribution labels :")
        unique, counts = np.unique(labels, return_counts=True)
        for u, c in zip(unique, counts):
            print(f"  Classe {u} : {c}")

    if IMAGE_IDS_FILE.exists():
        image_ids = np.load(IMAGE_IDS_FILE, allow_pickle=True)
        print("\nImage IDs :", image_ids.shape)

    if METADATA_FILE.exists():
        meta = pd.read_csv(METADATA_FILE)
        print("\nMetadata :", meta.shape)
        print("Colonnes metadata :", list(meta.columns))

    print("\nOK : compression ISIC 2019 terminée.")
    print("=" * 70)


if __name__ == "__main__":
    main()