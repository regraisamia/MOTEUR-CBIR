import io
import time
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import torch
import torchvision.transforms as T
from PIL import Image
import timm
import torchvision.models as models

from config import (
    MODEL_PATH, UPLOADS_DIR, CNN_DIM, VIT_DIM,
    PCA_CNN_PATH_2020, PCA_VIT_PATH_2020,
    PCA_CNN_PATH_2019, PCA_VIT_PATH_2019,
)

_cnn_model = None
_vit_model = None
_pcas = {}  # keyed by db name


def _build_backbones(device="cpu"):
    global _cnn_model, _vit_model
    if _cnn_model is not None and _vit_model is not None:
        return

    # CNN backbone (ResNet50 without classifier)
    res = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
    res.fc = torch.nn.Identity()
    res.eval()

    # ViT backbone
    vit = timm.create_model("vit_base_patch16_224", pretrained=True, num_classes=0)
    vit.eval()

    _cnn_model = res
    _vit_model = vit


def _load_checkpoint_to_backbones(map_location="cpu"):
    global _cnn_model, _vit_model
    if _cnn_model is None or _vit_model is None:
        _build_backbones()

    state = torch.load(MODEL_PATH, map_location=map_location)
    # Split keys by prefix
    cnn_state = {k.replace("cnn.", ""): v for k, v in state.items() if k.startswith("cnn.")}
    vit_state = {k.replace("vit.", ""): v for k, v in state.items() if k.startswith("vit.")}

    try:
        _cnn_model.load_state_dict(cnn_state, strict=False)
    except Exception:
        pass
    try:
        _vit_model.load_state_dict(vit_state, strict=False)
    except Exception:
        pass


def _load_pcas():
    global _pcas
    if "isic2020" not in _pcas:
        _pcas["isic2020"] = (joblib.load(PCA_CNN_PATH_2020), joblib.load(PCA_VIT_PATH_2020))
    if "isic2019" not in _pcas:
        _pcas["isic2019"] = (joblib.load(PCA_CNN_PATH_2019), joblib.load(PCA_VIT_PATH_2019))


# Preprocessing (ImageNet)
_transform = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


def initialize(device: str = "cpu"):
    _build_backbones(device)
    _load_checkpoint_to_backbones(map_location=device)
    _load_pcas()



def _to_numpy(tensor: torch.Tensor) -> np.ndarray:
    if isinstance(tensor, torch.Tensor):
        return tensor.detach().cpu().numpy()
    return np.array(tensor)


def extract_raw_features_from_pil(img: Image.Image, device: str = "cpu") -> Tuple[np.ndarray, np.ndarray]:
    """Return (cnn_feat_2048, vit_feat_768) as numpy arrays."""
    if _cnn_model is None or _vit_model is None:
        initialize(device)

    img = img.convert("RGB")
    t = _transform(img).unsqueeze(0)  # (1,3,224,224)

    with torch.no_grad():
        cnn_out = _cnn_model(t)
        vit_out = _vit_model(t)

    # convert
    cnn_f = _to_numpy(cnn_out.squeeze(0))
    vit_f = _to_numpy(vit_out.squeeze(0))
    return cnn_f.astype(np.float32), vit_f.astype(np.float32)


def extract_and_compress(img: Image.Image, db: str = "isic2020") -> np.ndarray:
    """Full pipeline: raw features -> PCA (per db) -> L2 norm -> concat 384D."""
    _load_pcas()
    cnn_raw, vit_raw = extract_raw_features_from_pil(img)

    pca_cnn, pca_vit = _pcas[db]
    cnn_comp = pca_cnn.transform(cnn_raw.reshape(1, -1)).astype(np.float32)
    vit_comp = pca_vit.transform(vit_raw.reshape(1, -1)).astype(np.float32)

    cnn_comp /= (np.linalg.norm(cnn_comp, axis=1, keepdims=True) + 1e-8)
    vit_comp /= (np.linalg.norm(vit_comp, axis=1, keepdims=True) + 1e-8)

    fused = np.concatenate([cnn_comp, vit_comp], axis=1).squeeze(0)
    return fused


def save_upload(file_bytes: bytes, filename: str) -> Path:
    p = UPLOADS_DIR / filename
    with open(p, "wb") as f:
        f.write(file_bytes)
    return p
