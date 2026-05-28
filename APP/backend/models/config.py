from pathlib import Path

BASE_DIR = Path(r"C:\Users\hp\Desktop\PFE")

APP_DIR = BASE_DIR / "APP" / "backend"

MODELS_DIR = APP_DIR / "models"

VECTORS_DIR = BASE_DIR / "Vectors-ISIC-FULL"

IMAGES_DIR = BASE_DIR / "data" / "ISIC2020_FULL" / "images"

MODEL_PATH = MODELS_DIR / "best_model.pt"
PCA_CNN_PATH = MODELS_DIR / "pca_cnn.pkl"
PCA_VIT_PATH = MODELS_DIR / "pca_vit.pkl"

FUSION_PATH = VECTORS_DIR / "fusion_compressed_384D.npy"
LABELS_PATH = VECTORS_DIR / "labels.npy"
IMAGE_IDS_PATH = VECTORS_DIR / "image_ids.npy"

CNN_DIM = 256
ALPHA = 0.1
TOP_K = 10