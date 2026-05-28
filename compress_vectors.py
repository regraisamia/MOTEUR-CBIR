import numpy as np
import os
from sklearn.decomposition import PCA
from pathlib import Path

# --- Configuration ---
VECTORS_DIR = Path(r"C:\Users\hp\Desktop\PFE\Vectors-ISIC")
CNN_DIM = 2048

print("="*60)
print("COMPRESSION DES VECTEURS POUR LE BIG DATA")
print("="*60)

# 1. Chargement de ton gros fichier
print("1. Chargement de fusion_concat.npy (2816D)...")
fusion_original = np.load(VECTORS_DIR / "fusion_concat.npy").astype(np.float32)

# On le coupe en deux
cnn_orig = fusion_original[:, :CNN_DIM]
vit_orig = fusion_original[:, CNN_DIM:]

# 2. PCA (La compression mathématique)
print("2. Application de la PCA (Compression)...")
# CNN : 2048 -> 256
pca_cnn = PCA(n_components=256, random_state=42)
cnn_comp = pca_cnn.fit_transform(cnn_orig)

# ViT : 768 -> 128
pca_vit = PCA(n_components=128, random_state=42)
vit_comp = pca_vit.fit_transform(vit_orig)

# 3. Conversion en Float16 (On divise encore la RAM par 2)
print("3. Conversion en Float16 (Demi-précision)...")
cnn_comp = cnn_comp.astype(np.float16)
vit_comp = vit_comp.astype(np.float16)

# Normalisation L2 OBLIGATOIRE après une PCA
cnn_comp /= (np.linalg.norm(cnn_comp, axis=1, keepdims=True) + 1e-4)
vit_comp /= (np.linalg.norm(vit_comp, axis=1, keepdims=True) + 1e-4)

# 4. On recolle les deux morceaux compressés (256 + 128 = 384 Dimensions)
fusion_compressed = np.concatenate([cnn_comp, vit_comp], axis=1)

# 5. Sauvegarde
out_path = VECTORS_DIR / "fusion_compressed_384D.npy"
np.save(out_path, fusion_compressed)

print("="*60)
print(f"✅ SUCCÈS ! Les vecteurs compressés sont sauvegardés !")
print(f"Fichier : {out_path}")
print(f"Nouvelle dimension : {fusion_compressed.shape[1]}D au lieu de 2816D")
print("="*60)