import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from pathlib import Path

VECTORS_DIR = Path(r"C:\Users\hp\Desktop\PFE\Vectors-ISIC")
CNN_DIM = 256
ALPHA = 0.1

print("Chargement des données compressées...")
fusion = np.load(VECTORS_DIR / "fusion_compressed_384D.npy").astype(np.float32)
labels = np.load(VECTORS_DIR / "labels.npy")

cnn = fusion[:, :CNN_DIM]
vit = fusion[:, CNN_DIM:]

def d_joint(q_cnn, q_vit, cnn, vit, alpha):
    diff = cnn - q_cnn
    d_cnn = np.sqrt(np.einsum('ij,ij->i', diff, diff))
    d_vit = 1.0 - (vit @ q_vit)
    return alpha * d_cnn + (1 - alpha) * d_vit

np.random.seed(42)
queries = np.random.choice(len(cnn), 300, replace=False)

y_true = []
y_pred = []

print("Calcul des confusions Top-1...")
for q in queries:
    d = d_joint(cnn[q], vit[q], cnn, vit, ALPHA)
    d[q] = np.inf # On ignore l'image requête
    top1_idx = np.argmin(d)
    
    y_true.append(labels[q])
    y_pred.append(labels[top1_idx])

classes = np.unique(labels) 
cm = confusion_matrix(y_true, y_pred, labels=classes)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=classes)

fig, ax = plt.subplots(figsize=(10, 8))
disp.plot(cmap='Blues', ax=ax, values_format='d')
plt.title("Matrice de Confusion CBIR (Top-1 Retrieval)")
plt.savefig("confusion_matrix.png", dpi=300)
print("✅ Matrice sauvegardée : confusion_matrix.png")