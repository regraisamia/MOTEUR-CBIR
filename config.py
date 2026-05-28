import os

# --- Chemins ---
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.join(BASE_DIR, "data", "HAM10000")
IMAGES_DIR  = os.path.join(DATA_DIR, "images")
META_CSV    = os.path.join(DATA_DIR, "HAM10000_metadata.csv")
VECTORS_DIR = os.path.join(BASE_DIR, "vectors")

os.makedirs(VECTORS_DIR, exist_ok=True)

# --- Paramètres extraction ---
IMAGE_SIZE  = 224          # taille standard CNN et ViT
BATCH_SIZE  = 32           # images traitées en parallèle (réduis à 16 si RAM insuffisante)
DEVICE      = "cpu"       # "cuda" si GPU dispo, sinon "cpu"

# --- Paramètres descripteurs classiques ---
COLOR_BINS  = 64           # bins par canal pour l'histogramme couleur → vecteur 192D
HARALICK_DISTANCES = [1, 2, 4]   # distances pour la texture Haralick

# --- Noms des fichiers de sortie ---
OUT = {
    "color"           : "classical_color.npy",
    "haralick"        : "classical_haralick.npy",
    "resnet50"        : "cnn_resnet50.npy",
    "densenet121"     : "cnn_densenet121.npy",
    "vit_base"        : "vit_base.npy",
    "fusion_cnn_vit"  : "fusion_cnn_vit.npy",
    "fusion_cnn_cls"  : "fusion_cnn_classical.npy",
    "fusion_all"      : "fusion_all.npy",
    "image_ids"       : "image_ids.npy",   # garde l'ordre des images
}
