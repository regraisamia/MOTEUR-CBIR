# CBIR Backend

Installation:

1. Créez un environnement Python (recommandé)
2. Installez les dépendances:

```bash
cd C:\Users\hp\Desktop\PFE\APP\backend
pip install -r requirements.txt
```

Lancer le serveur:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Endpoints:
- `GET /api/health`
- `GET /api/stats`
- `GET /api/image/{image_id}`
- `GET /api/metadata/{image_id}`
- `POST /api/search` (form upload)
