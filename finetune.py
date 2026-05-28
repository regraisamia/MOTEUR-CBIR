"""
Fine-tuning par Metric Learning — Supervised Contrastive Loss
=============================================================

Objectif : apprendre un espace d'embedding où les images de même
classe (même type de lésion) sont proches, et celles de classes
différentes sont éloignées.

Méthode : SupCon Loss (NeurIPS 2020) — surpasse triplet loss et
contrastive loss classique. Utilisée dans les meilleurs papiers
CBIR médicaux récents.

Architecture :
  Backbone (ResNet50 ou ViT) → Projection Head (MLP 2 couches) → L2 norm → SupCon Loss

Résultat attendu : mAP@10 passe de ~0.58 à ~0.80-0.90

Usage :
    python finetune.py --model resnet50 --epochs 30
    python finetune.py --model vit       --epochs 30
"""

import os, sys, time, argparse
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
import torchvision.transforms as T
import timm
from torch.utils.data import Dataset, DataLoader
from PIL import Image
from sklearn.preprocessing import LabelEncoder

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import IMAGES_DIR, META_CSV, VECTORS_DIR, OUT, DEVICE, IMAGE_SIZE


# ─────────────────────────────────────────────
#  HYPERPARAMÈTRES
# ─────────────────────────────────────────────

CFG = {
    "epochs"       : 30,
    "batch_size"   : 32,       # réduis à 16 si OOM
    "lr"           : 1e-4,
    "weight_decay" : 1e-4,
    "temperature"  : 0.07,     # température SupCon (0.05-0.1)
    "embed_dim"    : 128,      # dimension de l'espace métrique final
    "num_workers"  : 0,        # 0 sur Windows pour éviter les erreurs
    "val_ratio"    : 0.15,     # 15% pour validation
    "seed"         : 42,
}


# ─────────────────────────────────────────────
#  AUGMENTATIONS DERMOSCOPIE
# ─────────────────────────────────────────────

# Augmentations fortes pour l'entraînement (spécifiques dermoscopie)
train_transform = T.Compose([
    T.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    T.RandomHorizontalFlip(p=0.5),
    T.RandomVerticalFlip(p=0.5),
    T.RandomRotation(degrees=45),
    T.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.1),
    T.RandomAffine(degrees=0, translate=(0.1, 0.1), scale=(0.9, 1.1)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Pas d'augmentation pour l'extraction finale
val_transform = T.Compose([
    T.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


# ─────────────────────────────────────────────
#  DATASET
# ─────────────────────────────────────────────

class HAM10000Dataset(Dataset):
    def __init__(self, image_paths, labels, transform=None):
        self.paths     = image_paths
        self.labels    = labels
        self.transform = transform

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, idx):
        img = Image.open(self.paths[idx]).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, self.labels[idx]


def load_data():
    """Charge les chemins et labels, split train/val stratifié."""
    df = pd.read_csv(META_CSV)

    # Ordre stable
    ids_path = os.path.join(VECTORS_DIR, OUT["image_ids"])
    if os.path.exists(ids_path):
        saved_ids = np.load(ids_path, allow_pickle=True).tolist()
        df = df.set_index("image_id").loc[saved_ids].reset_index()

    le = LabelEncoder()
    labels = le.fit_transform(df["dx"].values)
    paths  = [os.path.join(IMAGES_DIR, img_id + ".jpg")
              for img_id in df["image_id"].values]

    # Split stratifié train / val
    np.random.seed(CFG["seed"])
    train_idx, val_idx = [], []
    for cls in np.unique(labels):
        cls_idx = np.where(labels == cls)[0]
        np.random.shuffle(cls_idx)
        n_val = max(1, int(len(cls_idx) * CFG["val_ratio"]))
        val_idx.extend(cls_idx[:n_val].tolist())
        train_idx.extend(cls_idx[n_val:].tolist())

    train_paths  = [paths[i]  for i in train_idx]
    train_labels = [labels[i] for i in train_idx]
    val_paths    = [paths[i]  for i in val_idx]
    val_labels   = [labels[i] for i in val_idx]

    print(f"Train : {len(train_paths)} images | Val : {len(val_paths)} images")
    print(f"Classes : {list(le.classes_)}\n")
    return train_paths, train_labels, val_paths, val_labels, le, paths, labels


# ─────────────────────────────────────────────
#  MODÈLES AVEC PROJECTION HEAD
# ─────────────────────────────────────────────

class MetricModel(nn.Module):
    """
    Backbone + Projection Head pour metric learning.

    Le Projection Head (MLP 2 couches) transforme les features
    brutes en un espace d'embedding de dimension réduite (128D)
    mieux adapté à la SupCon Loss.

    Après entraînement, on utilisera les features du backbone
    (avant le head) pour l'indexation — plus riches (2048D/768D).
    """
    def __init__(self, backbone_name: str, embed_dim: int = 128):
        super().__init__()
        self.backbone_name = backbone_name

        if backbone_name == "resnet50":
            backbone = models.resnet50(
                weights=models.ResNet50_Weights.IMAGENET1K_V1)
            feat_dim = backbone.fc.in_features    # 2048
            backbone.fc = nn.Identity()
            self.backbone = backbone

        elif backbone_name == "vit":
            self.backbone = timm.create_model(
                "vit_base_patch16_224",
                pretrained=True,
                num_classes=0             # sortie = 768D
            )
            feat_dim = 768

        else:
            raise ValueError(f"Backbone inconnu : {backbone_name}")

        # Projection Head : feat_dim → 512 → embed_dim → L2 norm
        self.projector = nn.Sequential(
            nn.Linear(feat_dim, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(inplace=True),
            nn.Linear(512, embed_dim),
        )
        self.feat_dim  = feat_dim
        self.embed_dim = embed_dim

    def forward(self, x):
        features = self.backbone(x)
        if features.dim() == 4:
            features = features.mean(dim=[2, 3])   # GAP si spatiale
        z = self.projector(features)
        z = F.normalize(z, dim=1)                  # L2 norm → sur la sphère unité
        return features, z                         # (features brutes, embeddings normalisés)


# ─────────────────────────────────────────────
#  SUPERVISED CONTRASTIVE LOSS
# ─────────────────────────────────────────────

class SupConLoss(nn.Module):
    """
    Supervised Contrastive Loss (Khosla et al., NeurIPS 2020).

    Pour chaque image i, on maximise la similarité avec toutes les
    images de même classe (positifs) et on minimise avec les autres
    (négatifs). Bien supérieur à triplet loss car utilise TOUS les
    positifs et négatifs du batch simultanément.

    Formule :
        L_i = -1/|P(i)| * Σ_{p∈P(i)} log[
            exp(z_i·z_p / τ) / Σ_{a≠i} exp(z_i·z_a / τ)
        ]
    où τ = température, P(i) = ensemble des positifs pour i.
    """
    def __init__(self, temperature: float = 0.07):
        super().__init__()
        self.T = temperature

    def forward(self, embeddings: torch.Tensor, labels: torch.Tensor):
        """
        embeddings : (B, D) — vecteurs L2-normalisés
        labels     : (B,)   — labels de classe
        """
        device = embeddings.device
        B = embeddings.shape[0]

        # Matrice de similarité cosinus : (B, B)
        sim = torch.mm(embeddings, embeddings.T) / self.T

        # Masque des paires positives (même classe, i≠j)
        labels = labels.view(-1, 1)
        pos_mask = (labels == labels.T).float()
        pos_mask.fill_diagonal_(0)   # exclut la diagonale (i=i)

        # Vérifie qu'il y a des positifs dans le batch
        if pos_mask.sum() == 0:
            return torch.tensor(0.0, requires_grad=True, device=device)

        # Soustrait le max pour stabilité numérique
        sim_max, _ = sim.max(dim=1, keepdim=True)
        sim = sim - sim_max.detach()

        # Dénominateur : somme sur tous les autres éléments (i≠j)
        denom_mask = torch.ones(B, B, device=device) - torch.eye(B, device=device)
        log_prob   = sim - torch.log((denom_mask * torch.exp(sim)).sum(dim=1, keepdim=True) + 1e-8)

        # Moyenne sur les paires positives
        n_positives = pos_mask.sum(dim=1)
        n_positives = torch.clamp(n_positives, min=1)
        loss = -(pos_mask * log_prob).sum(dim=1) / n_positives

        return loss.mean()


# ─────────────────────────────────────────────
#  ENTRAÎNEMENT
# ─────────────────────────────────────────────

def train_one_epoch(model, loader, optimizer, criterion, device):
    model.train()
    total_loss, n = 0.0, 0
    for imgs, labels in loader:
        imgs   = imgs.to(device)
        labels = labels.to(device)
        optimizer.zero_grad()
        _, embeddings = model(imgs)
        loss = criterion(embeddings, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * len(imgs)
        n          += len(imgs)
    return total_loss / n


@torch.no_grad()
def validate(model, loader, criterion, device):
    model.eval()
    total_loss, n = 0.0, 0
    for imgs, labels in loader:
        imgs   = imgs.to(device)
        labels = labels.to(device)
        _, embeddings = model(imgs)
        loss = criterion(embeddings, labels)
        total_loss += loss.item() * len(imgs)
        n          += len(imgs)
    return total_loss / n


# ─────────────────────────────────────────────
#  EXTRACTION AVEC LE MODÈLE FINE-TUNÉ
# ─────────────────────────────────────────────

@torch.no_grad()
def extract_finetuned(model, all_paths, device, batch_size=32):
    """
    Extrait les features du backbone (pas du projector)
    pour toutes les images — ce sont les vecteurs finaux du PFE.
    """
    model.eval()
    all_feats = []
    for start in range(0, len(all_paths), batch_size):
        batch = all_paths[start:start + batch_size]
        tensors = []
        for p in batch:
            try:
                img = Image.open(p).convert("RGB")
                tensors.append(val_transform(img))
            except:
                tensors.append(torch.zeros(3, IMAGE_SIZE, IMAGE_SIZE))
        batch_t = torch.stack(tensors).to(device)
        feats, _ = model(batch_t)
        if feats.dim() == 4:
            feats = feats.mean(dim=[2, 3])
        all_feats.append(feats.cpu().numpy())
        if start % (batch_size * 20) == 0:
            print(f"  Extraction : {start}/{len(all_paths)}...")
    return np.vstack(all_feats).astype(np.float32)


# ─────────────────────────────────────────────
#  PIPELINE PRINCIPAL
# ─────────────────────────────────────────────

def main(backbone_name: str, epochs: int):
    print(f"\n{'='*60}")
    print(f"Fine-tuning SupCon — backbone : {backbone_name}")
    print(f"Epochs : {epochs}  |  Device : {DEVICE}")
    print(f"{'='*60}\n")

    # Données
    train_paths, train_labels, val_paths, val_labels, le, all_paths, all_labels = load_data()

    train_ds = HAM10000Dataset(train_paths, train_labels, train_transform)
    val_ds   = HAM10000Dataset(val_paths,   val_labels,   val_transform)

    train_loader = DataLoader(train_ds, batch_size=CFG["batch_size"],
                              shuffle=True,  num_workers=CFG["num_workers"],
                              drop_last=True)
    val_loader   = DataLoader(val_ds,   batch_size=CFG["batch_size"],
                              shuffle=False, num_workers=CFG["num_workers"])

    # Modèle
    model     = MetricModel(backbone_name, embed_dim=CFG["embed_dim"]).to(DEVICE)
    criterion = SupConLoss(temperature=CFG["temperature"])
    optimizer = torch.optim.AdamW(model.parameters(),
                                  lr=CFG["lr"],
                                  weight_decay=CFG["weight_decay"])
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    # Entraînement
    best_val_loss = float("inf")
    ckpt_path = os.path.join(VECTORS_DIR, f"best_model_{backbone_name}.pt")

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        train_loss = train_one_epoch(model, train_loader, optimizer, criterion, DEVICE)
        val_loss   = validate(model, val_loader, criterion, DEVICE)
        scheduler.step()

        elapsed = time.time() - t0
        print(f"Epoch {epoch:3d}/{epochs} | "
              f"train_loss={train_loss:.4f} | "
              f"val_loss={val_loss:.4f} | "
              f"{elapsed:.1f}s")

        # Sauvegarde du meilleur modèle
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), ckpt_path)
            print(f"  Meilleur modèle sauvegardé ({val_loss:.4f})")

    # Chargement du meilleur modèle
    print(f"\nChargement du meilleur modèle : {ckpt_path}")
    model.load_state_dict(torch.load(ckpt_path, map_location=DEVICE))

    # Extraction des vecteurs fine-tunés
    print("\nExtraction des vecteurs fine-tunés...")
    finetuned_vectors = extract_finetuned(model, all_paths, DEVICE)

    # Sauvegarde
    out_key = f"ft_{backbone_name}"
    out_path = os.path.join(VECTORS_DIR, f"finetuned_{backbone_name}.npy")
    np.save(out_path, finetuned_vectors)
    print(f"Vecteurs sauvegardés : {out_path}  {finetuned_vectors.shape}")

    print("\nFine-tuning terminé. Lance evaluate_finetuned.py pour mesurer les gains.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model",  type=str, default="resnet50",
                        choices=["resnet50", "vit"],
                        help="Backbone à fine-tuner")
    parser.add_argument("--epochs", type=int, default=30,
                        help="Nombre d'epochs")
    args = parser.parse_args()
    CFG["epochs"] = args.epochs
    main(args.model, args.epochs)
