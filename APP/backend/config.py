from pathlib import Path

BASE_DIR = Path(r"C:\Users\hp\Desktop\PFE")

APP_DIR = BASE_DIR / "APP" / "backend"
MODELS_DIR = APP_DIR / "models"

# ── ISIC 2020 ──
VECTORS_DIR_2020 = BASE_DIR / "Vectors-ISIC-FULL"
IMAGES_DIR_2020  = BASE_DIR / "data" / "ISIC2020_FULL" / "images"
FUSION_PATH_2020    = VECTORS_DIR_2020 / "fusion_compressed_384D.npy"
LABELS_PATH_2020    = VECTORS_DIR_2020 / "labels.npy"
IMAGE_IDS_PATH_2020 = VECTORS_DIR_2020 / "image_ids.npy"
HJG_GRAPH_PATH_2020 = VECTORS_DIR_2020 / "hjg_graph_light.pkl"
PCA_CNN_PATH_2020   = VECTORS_DIR_2020 / "pca_cnn.pkl"
PCA_VIT_PATH_2020   = VECTORS_DIR_2020 / "pca_vit.pkl"
METADATA_CSV_2020   = BASE_DIR / "data" / "ISIC2020_FULL" / "train.csv"

# ── ISIC 2019 ──
VECTORS_DIR_2019 = BASE_DIR / "Vectors-ISIC2019"
IMAGES_DIR_2019  = BASE_DIR / "data" / "ISIC2019"
FUSION_PATH_2019    = VECTORS_DIR_2019 / "fusion_compressed_384D.npy"
LABELS_PATH_2019    = VECTORS_DIR_2019 / "labels.npy"
IMAGE_IDS_PATH_2019 = VECTORS_DIR_2019 / "image_ids.npy"
HJG_GRAPH_PATH_2019 = VECTORS_DIR_2019 / "hjg_graph_light.pkl"
PCA_CNN_PATH_2019   = VECTORS_DIR_2019 / "pca_cnn_isic2019.pkl"
PCA_VIT_PATH_2019   = VECTORS_DIR_2019 / "pca_vit_isic2019.pkl"
METADATA_CSV_2019   = BASE_DIR / "data" / "ISIC2019" / "metadata_isic2019.csv"

MODEL_PATH = MODELS_DIR / "best_model.pt"

CNN_DIM = 256
VIT_DIM = 128
ALPHA = 0.1
VECTOR_DIM = CNN_DIM + VIT_DIM

UPLOADS_DIR = APP_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

TOP_K_OPTIONS = [5, 10, 20]
