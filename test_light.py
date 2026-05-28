import numpy as np
import time
from pathlib import Path

# --- Configuration ---
VECTORS_DIR = Path(r"C:\Users\hp\Desktop\PFE\Vectors-ISIC")
DIM_CNN = 256  # La nouvelle taille du CNN compressé
ALPHA = 0.1    # Ton poids magique

print("="*70)
print("VERIFICATION DE LA PRECISION (Vecteurs Compressés 384D)")
print("="*70)

# 1. Chargement
print("Chargement des vecteurs compressés...")
fusion = np.load(VECTORS_DIR / "fusion_compressed_384D.npy").astype(np.float32)
labels = np.load(VECTORS_DIR / "labels.npy")

cnn = fusion[:, :DIM_CNN]
vit = fusion[:, DIM_CNN:]

# 2. Fonctions de métrique
def d_joint(q_cnn, q_vit, cnn, vit, alpha):
    diff = cnn - q_cnn
    d_cnn = np.sqrt(np.einsum('ij,ij->i', diff, diff))
    d_vit = 1.0 - (vit @ q_vit)
    return alpha * d_cnn + (1 - alpha) * d_vit

def map_k(ranked, q, labels, k=10):
    top = [i for i in ranked if i != q][:k]
    hits, s = 0, 0.0
    ql = labels[q]
    for r, i in enumerate(top, 1):
        if labels[i] == ql:
            hits += 1; s += hits / r
    return s / min(k, max(1, (labels == ql).sum() - 1))

# 3. Évaluation
print("Évaluation en cours sur 300 requêtes...")
np.random.seed(42)
queries = np.random.choice(len(cnn), 300, replace=False)

m10 = []
t0 = time.time()

for q in queries:
    d = d_joint(cnn[q], vit[q], cnn, vit, ALPHA)
    d[q] = np.inf
    m10.append(map_k(np.argsort(d), q, labels, 10))

t_total = time.time() - t0
mAP_10 = np.mean(m10)

print("\n" + "="*70)
print(f"✅ RÉSULTAT DE LA COMPRESSION SUR ISIC :")
print(f"   mAP@10 Original (2816D)   : 0.9642")
print(f"   mAP@10 Compressé (384D)   : {mAP_10:.4f}")
print(f"   Vitesse (sans graphe)     : {(t_total/300)*1000:.2f} ms/req")
print("="*70)