# MOTEUR-CBIR - Medical Image Retrieval System

Content-Based Image Retrieval (CBIR) system for dermatology using dual-backbone deep learning (ResNet-50 + ViT) with HJG graph-based approximate nearest neighbor search.

## Features

- **Dual-Database Support**: ISIC 2020 (33K images, binary) + ISIC 2019 (25K images, multi-class)
- **Hybrid Feature Extraction**: CNN (ResNet-50) + Vision Transformer (ViT-B/16)
- **PCA Compression**: 2048D + 768D → 256D + 128D = 384D fused vectors
- **HJG Graph Search**: Hierarchical Junction Graph for sub-linear approximate NN search
- **Modern UI**: React + Vite frontend with dark medical theme, responsive design, Framer Motion animations

## Tech Stack

**Backend**
- FastAPI (Python)
- PyTorch (ResNet-50 + ViT)
- NumPy, Pandas, scikit-learn
- HJG graph indexing

**Frontend**
- React 18 + Vite
- Framer Motion
- Lucide React icons

## Setup

### Backend
```bash
cd APP/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd APP/frontend
npm install
npm run dev
```

Open http://localhost:5173

## Project Structure

```
APP/
├── backend/
│   ├── main.py              # FastAPI endpoints
│   ├── search_engine.py     # HJG search implementation
│   ├── model_utils.py       # Feature extraction (CNN + ViT)
│   ├── metadata_service.py  # Dataset metadata handling
│   └── config.py            # Paths and constants
└── frontend/
    └── src/
        ├── pages/           # Dashboard, Search, Database, About
        ├── components/      # Navbar, Footer, Cards, Modal
        └── styles.css       # Dark medical theme
```

## Notes

- **Not a medical diagnostic tool** — for research purposes only
- Requires precomputed vectors and HJG graphs (not included due to size)
- Models: `best_model.pt`, `pca_cnn.pkl`, `pca_vit.pkl` (place in `APP/backend/models/`)

## License

Academic research project (PFE)
