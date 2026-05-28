# ==============================================================================
# SCRIPT VISUALISATION : t-SNE de l'espace latent (HAM10000)
# ==============================================================================

import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
import os

print("="*60)
print("🎨 GÉNÉRATION DE LA CARTE t-SNE (Espace Hybride 2816D)")
print("="*60)

# --- 1. Chargement des données ---
# On utilise HAM10000 car il a 7 classes bien distinctes pour une belle visualisation
folder = r"C:\Users\hp\Desktop\PFE\Vectors-C"

print("Chargement des vecteurs...")
vectors = np.load(os.path.join(folder, "fusion_concat.npy"))
labels = np.load(os.path.join(folder, "labels.npy"))

# On prend un échantillon aléatoire de 3000 images pour que le calcul 
# prenne 2 minutes au lieu de 45 minutes, tout en restant magnifique.
np.random.seed(42)
indices = np.random.choice(len(vectors), 3000, replace=False)
vectors_sample = vectors[indices]
labels_sample = labels[indices]

print(f"Échantillon sélectionné : {len(vectors_sample)} images.")

# --- 2. Réduction de dimensionnalité (t-SNE) ---
print("Calcul du t-SNE en cours (Patiente environ 1 à 2 minutes)...")
# perplexity=40 et n_iter=1000 sont les meilleurs paramètres pour l'imagerie médicale
tsne = TSNE(n_components=2, perplexity=40, n_iter=1000, random_state=42)
vecs_2d = tsne.fit_transform(vectors_sample)

# --- 3. Génération du graphique esthétique ---
print("Génération de l'image PNG...")
plt.figure(figsize=(12, 10))

# Définition des couleurs pour les 7 classes du HAM10000
scatter = plt.scatter(vecs_2d[:, 0], vecs_2d[:, 1], 
                      c=labels_sample, cmap='Set1', 
                      s=20, alpha=0.7, edgecolors='none')

# Noms officiels des classes dermatologiques
class_names = ['AKIEC (Kératose)', 'BCC (Carcinome)', 'BKL (Lésion bénigne)', 
               'DF (Dermatofibrome)', 'MEL (Mélanome)', 'NV (Naevus)', 
               'VASC (Lésion vasculaire)']

# Ajout d'une légende propre
cbar = plt.colorbar(scatter, ticks=range(7))
cbar.ax.set_yticklabels(class_names)
cbar.set_label('Classes Diagnostiques', rotation=270, labelpad=20, fontsize=12)

plt.title("Visualisation t-SNE de l'espace latent hybride (CNN + ViT)", fontsize=16, pad=20)
plt.xlabel("Dimension t-SNE 1", fontsize=12)
plt.ylabel("Dimension t-SNE 2", fontsize=12)

# Design épuré
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()

# --- 4. Sauvegarde ---
output_path = r"C:\Users\hp\Desktop\PFE\tsne_fusion.png"
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print("="*60)
print(f"✅ SUCCÈS ! Image sauvegardée avec succès sur :")
print(f"   --> {output_path}")
print("="*60)