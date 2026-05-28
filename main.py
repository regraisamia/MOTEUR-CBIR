"""
Script principal — lance toutes les extractions dans l'ordre.

Usage :
    python main.py

Résultat : tous les fichiers .npy dans le dossier vectors/
"""

import os
import numpy as np
import pandas as pd

from config import IMAGES_DIR, META_CSV, VECTORS_DIR, DEVICE, OUT
from extractors.classical import extract_all_classical
from extractors.cnn        import extract_resnet50, extract_densenet121
from extractors.vit        import extract_vit
from extractors.fusion     import (
    fusion_cnn_vit,
    fusion_cnn_classical,
    fusion_vit_classical,
    fusion_all,
    print_summary
)


# ─────────────────────────────────────────────
#  ÉTAPE 0 : Chargement de la liste d'images
# ─────────────────────────────────────────────

def load_image_paths():
    """
    Charge la liste de tous les chemins d'images HAM10000
    dans un ordre stable et reproductible (trié par nom).
    Retourne : (image_ids, image_paths)
    """
    print("Chargement des chemins d'images...")

    if os.path.exists(META_CSV):
        # Utilise le CSV pour avoir les labels et un ordre stable
        df = pd.read_csv(META_CSV)
        # HAM10000 : colonne 'image_id'
        image_ids = df['image_id'].tolist()
        paths = []
        for img_id in image_ids:
            path = os.path.join(IMAGES_DIR, img_id + ".jpg")
            if not os.path.exists(path):
                # Certains datasets HAM10000 ont les images dans des sous-dossiers
                path = os.path.join(IMAGES_DIR, img_id + ".jpg")
            paths.append(path)
    else:
        # Fallback : liste tous les .jpg du dossier
        files = sorted(f for f in os.listdir(IMAGES_DIR) if f.endswith(".jpg"))
        image_ids = [f.replace(".jpg", "") for f in files]
        paths = [os.path.join(IMAGES_DIR, f) for f in files]

    # Vérifie que les images existent
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        print(f"  ATTENTION : {len(missing)} images introuvables.")
        print(f"  Exemple : {missing[0]}")
        print(f"  Vérifie que IMAGES_DIR = {IMAGES_DIR} est correct.")

    print(f"  {len(paths)} images trouvées.\n")
    return image_ids, paths


# ─────────────────────────────────────────────
#  UTILITAIRES
# ─────────────────────────────────────────────

def save(name_key: str, matrix: np.ndarray):
    """Sauvegarde un vecteur numpy dans vectors/"""
    path = os.path.join(VECTORS_DIR, OUT[name_key])
    np.save(path, matrix)
    print(f"  Sauvegardé : {path}  ({matrix.shape})\n")


def load_if_exists(name_key: str):
    """Charge un vecteur déjà calculé pour éviter de recalculer."""
    path = os.path.join(VECTORS_DIR, OUT[name_key])
    if os.path.exists(path):
        print(f"  Déjà calculé, chargement : {path}")
        return np.load(path)
    return None


# ─────────────────────────────────────────────
#  PIPELINE PRINCIPAL
# ─────────────────────────────────────────────

def main():
    print(f"\nDevice utilisé : {DEVICE}\n")
    print("="*50)

    # --- 0. Chemins ---
    image_ids, image_paths = load_image_paths()
    np.save(os.path.join(VECTORS_DIR, OUT["image_ids"]),
            np.array(image_ids))

    vectors = {}   # stocke tout en mémoire pour les fusions

    # ── 1. Classiques ──────────────────────────────
    print("── 1/5  Descripteurs classiques ──")

    vec = load_if_exists("color")
    if vec is None:
        vec = extract_all_classical(image_paths, method="color")
        save("color", vec)
    vectors["classical_color (192D)"] = vec
    color_vec = vec

    vec = load_if_exists("haralick")
    if vec is None:
        vec = extract_all_classical(image_paths, method="haralick")
        save("haralick", vec)
    vectors["classical_haralick (39D)"] = vec
    haralick_vec = vec

    # Combine les deux classiques pour les fusions
    classical_combined = np.concatenate([color_vec, haralick_vec], axis=1)

    # ── 2. CNN ResNet50 ────────────────────────────
    print("── 2/5  CNN ResNet50 ──")
    vec = load_if_exists("resnet50")
    if vec is None:
        vec = extract_resnet50(image_paths, device=DEVICE)
        save("resnet50", vec)
    vectors["CNN ResNet50 (2048D)"] = vec
    resnet_vec = vec

    # ── 3. CNN DenseNet121 ─────────────────────────
    print("── 3/5  CNN DenseNet121 ──")
    vec = load_if_exists("densenet121")
    if vec is None:
        vec = extract_densenet121(image_paths, device=DEVICE)
        save("densenet121", vec)
    vectors["CNN DenseNet121 (1024D)"] = vec

    # ── 4. ViT-Base ────────────────────────────────
    print("── 4/5  ViT-Base/16 ──")
    vec = load_if_exists("vit_base")
    if vec is None:
        vec = extract_vit(image_paths, device=DEVICE)
        save("vit_base", vec)
    vectors["ViT-Base (768D)"] = vec
    vit_vec = vec

    # ── 5. Fusions ─────────────────────────────────
    print("── 5/5  Fusions ──")

    # Fusion principale : CNN ResNet50 + ViT (c'est le méga-vecteur du PFE)
    vec = fusion_cnn_vit(resnet_vec, vit_vec)
    save("fusion_cnn_vit", vec)
    vectors["Fusion CNN+ViT (2816D)"] = vec

    # Fusion CNN + classiques
    vec = fusion_cnn_classical(resnet_vec, classical_combined)
    save("fusion_cnn_cls", vec)
    vectors["Fusion CNN+Classique (2279D)"] = vec

    # Fusion totale
    vec = fusion_all(resnet_vec, vit_vec, classical_combined)
    save("fusion_all", vec)
    vectors["Fusion ALL (3055D)"] = vec

    # ── Récapitulatif ──────────────────────────────
    print_summary(vectors)
    print("Extraction terminée. Tous les vecteurs sont dans vectors/")


if __name__ == "__main__":
    main()
