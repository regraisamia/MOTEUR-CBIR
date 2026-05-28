from config import *

files = [
    MODEL_PATH,
    PCA_CNN_PATH,
    PCA_VIT_PATH,
    FUSION_PATH,
    LABELS_PATH,
    IMAGE_IDS_PATH,
    IMAGES_DIR,
]

for f in files:
    print(f, "OK" if f.exists() else "MANQUANT")