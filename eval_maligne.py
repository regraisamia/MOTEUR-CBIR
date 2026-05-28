import numpy as np
import pickle
from pathlib import Path

VECTORS_DIR = Path(r"C:\Users\hp\Desktop\PFE\Vectors-ISIC")
CFG = {"cnn_dim": 256, "w_cnn": 0.1, "w_vit": 0.9, "k_query": 10}

print("Chargement...")
fusion = np.load(VECTORS_DIR / "fusion_compressed_384D.npy").astype(np.float32)
labels = np.load(VECTORS_DIR / "labels.npy")
with open(VECTORS_DIR / "hjg_graph_light.pkl", "rb") as f:
    hjg = pickle.load(f)

cnn, vit = fusion[:, :CFG["cnn_dim"]], fusion[:, CFG["cnn_dim"]:]
# Les cas malins sont la classe 1 (vérifie si c'est bien l'index 1 dans tes labels)
malignant_queries = np.where(labels == 1)[0] 
print(f"Nombre de requêtes malignes trouvées : {len(malignant_queries)}")

def d_joint(q_cnn, q_vit, cnn, vit, idx):
    dc = np.sqrt(np.einsum('ij,ij->i', cnn[idx] - q_cnn, cnn[idx] - q_cnn))
    dv = 1.0 - (vit[idx] @ q_vit)
    return CFG["w_cnn"] * dc + CFG["w_vit"] * dv

# Recherche simplifiée pour le test
recalls, precisions = [], []
for q in malignant_queries:
    dj = d_joint(cnn[q], vit[q], cnn, vit, np.arange(len(cnn)))
    dj[q] = np.inf
    top10 = np.argpartition(dj, 10)[:10]
    
    # Combien de cas malins dans le top 10 ?
    malins_trouves = sum(labels[i] == 1 for i in top10)
    
    precisions.append(malins_trouves / 10.0)
    # Recall max possible est limité par le nb total de malins (187)
    recalls.append(malins_trouves / min(10, len(malignant_queries) - 1))

print("="*50)
print("PERFORMANCES CLINIQUES SUR CAS MALINS (Zero-Shot)")
print("="*50)
print(f"Precision@10 (Malin) : {np.mean(precisions):.4f}")
print(f"Recall@10 (Malin)    : {np.mean(recalls):.4f}")
print("="*50)