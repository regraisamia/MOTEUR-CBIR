import numpy as np
from pathlib import Path

# Dossiers
IMAGES_DIR = Path(r"C:\Users\hp\Desktop\PFE\data\ISIC2020_FULL\images")
VECTORS_DIR = Path(r"C:\Users\hp\Desktop\PFE\Vectors-ISIC-FULL")

# Fichiers
IMAGE_IDS_FILE = VECTORS_DIR / "image_ids.npy"
LABELS_FILE = VECTORS_DIR / "labels.npy"
VECTORS_FILE = VECTORS_DIR / "fusion_compressed_384D.npy"

print("=" * 70)
print("VÉRIFICATION DES IMAGES ISIC 2020 COMPLET")
print("=" * 70)

# Charger les fichiers
image_ids = np.load(IMAGE_IDS_FILE, allow_pickle=True)
labels = np.load(LABELS_FILE)
vectors = np.load(VECTORS_FILE)

print(f"Nombre image_ids : {len(image_ids)}")
print(f"Nombre labels    : {len(labels)}")
print(f"Nombre vecteurs  : {vectors.shape[0]}")
print(f"Dimension vecteur: {vectors.shape[1]}D")

# Compter les images dans le dossier
jpg_files = list(IMAGES_DIR.glob("*.jpg"))
print(f"Nombre images JPG dans le dossier : {len(jpg_files)}")

# Vérifier images manquantes
missing = []
for img_id in image_ids:
    img_path = IMAGES_DIR / f"{img_id}.jpg"
    if not img_path.exists():
        missing.append(img_id)

# Vérifier images en trop
expected_names = set(f"{img_id}.jpg" for img_id in image_ids)
actual_names = set(p.name for p in jpg_files)
extra = actual_names - expected_names

print("-" * 70)
print(f"Images manquantes : {len(missing)}")
print(f"Images en trop    : {len(extra)}")

if missing:
    print("\nExemples images manquantes :")
    for x in missing[:10]:
        print(x)

if extra:
    print("\nExemples images en trop :")
    for x in list(extra)[:10]:
        print(x)

print("-" * 70)

if (
    len(image_ids) == 33126
    and len(labels) == 33126
    and vectors.shape[0] == 33126
    and len(jpg_files) == 33126
    and len(missing) == 0
):
    print("OK : base ISIC complète prête pour l'interface.")
else:
    print("PROBLÈME : vérifie les nombres affichés ci-dessus.")

print("=" * 70)
