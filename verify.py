"""
Script de vérification rapide — teste tout sur 5 images
avant de lancer l'extraction complète sur les 10 000 images.

Usage :
    python verify.py
"""

import os, sys
import numpy as np
from PIL import Image

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import IMAGES_DIR, DEVICE


def test_on_n_images(n=5):

    # Récupère n images de test
    files = [f for f in os.listdir(IMAGES_DIR) if f.endswith(".jpg")][:n]
    if not files:
        print(f"ERREUR : aucune image .jpg dans {IMAGES_DIR}")
        print("Vérifie que tu as bien placé tes images dans ce dossier.")
        return
    paths = [os.path.join(IMAGES_DIR, f) for f in files]
    print(f"Test sur {len(paths)} images : {files}\n")

    # ── Test 1 : Classiques ──
    print("Test classiques...")
    from extractors.classical import color_histogram, haralick_texture
    v = color_histogram(paths[0])
    print(f"  color_histogram   : {v.shape}  min={v.min():.3f} max={v.max():.3f}")
    v = haralick_texture(paths[0])
    print(f"  haralick_texture  : {v.shape}  min={v.min():.3f} max={v.max():.3f}")

    # ── Test 2 : CNN ──
    print("\nTest CNN (ResNet50)...")
    from extractors.cnn import load_resnet50, extract_cnn_features
    model = load_resnet50(DEVICE)
    vecs = extract_cnn_features(paths, model, DEVICE, batch_size=n)
    print(f"  ResNet50 batch    : {vecs.shape}")

    # ── Test 3 : ViT ──
    print("\nTest ViT...")
    from extractors.vit import load_vit, extract_vit_features
    model_vit = load_vit(device=DEVICE)
    vecs_vit = extract_vit_features(paths, model_vit, DEVICE, batch_size=n)
    print(f"  ViT-Base batch    : {vecs_vit.shape}")

    # ── Test 4 : Fusion ──
    print("\nTest fusion CNN+ViT...")
    from extractors.fusion import fusion_cnn_vit
    fused = fusion_cnn_vit(vecs, vecs_vit)
    print(f"  Fusion CNN+ViT    : {fused.shape}")

    print("\nTout fonctionne. Lance main.py pour l'extraction complète.")


if __name__ == "__main__":
    test_on_n_images(5)
