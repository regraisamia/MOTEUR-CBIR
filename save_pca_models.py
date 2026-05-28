import numpy as np
from pathlib import Path
from sklearn.decomposition import PCA
import joblib

VECTORS_DIR = Path(r"C:\Users\hp\Desktop\PFE\Vectors-ISIC-FULL")
CNN_DIM = 2048

fusion = np.load(VECTORS_DIR / "fusion_concat.npy").astype(np.float32)

cnn_orig = fusion[:, :CNN_DIM]
vit_orig = fusion[:, CNN_DIM:]

print("CNN original :", cnn_orig.shape)
print("ViT original :", vit_orig.shape)

pca_cnn = PCA(n_components=256, random_state=42)
cnn_comp = pca_cnn.fit_transform(cnn_orig)

pca_vit = PCA(n_components=128, random_state=42)
vit_comp = pca_vit.fit_transform(vit_orig)

joblib.dump(pca_cnn, VECTORS_DIR / "pca_cnn.pkl")
joblib.dump(pca_vit, VECTORS_DIR / "pca_vit.pkl")

print("OK : pca_cnn.pkl sauvegardé")
print("OK : pca_vit.pkl sauvegardé")
print("Variance CNN :", round(pca_cnn.explained_variance_ratio_.sum(), 4))
print("Variance ViT :", round(pca_vit.explained_variance_ratio_.sum(), 4))