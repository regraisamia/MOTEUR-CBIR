import io
import json
import time
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from config import IMAGES_DIR_2020, IMAGES_DIR_2019, VECTOR_DIM, TOP_K_OPTIONS, ALPHA
from model_utils import extract_and_compress, save_upload, initialize
from search_engine import ENGINES
from metadata_service import get_metadata, load_metadata, ISIC2019_LABEL_NAMES, ISIC2019_MALIGNANT
from auth import (
    create_token, find_user_by_email, create_user, public_user,
    verify_password, get_current_user, get_current_user_optional,
    require_permission, get_users, save_users, find_user_by_id,
    save_search, get_history, save_case, get_cases,
    LEVELS, seed_admin
)

# ── Messages storage ──
MESSAGES_FILE = Path(__file__).parent / "messages.json"

def _load_messages() -> list:
    if MESSAGES_FILE.exists():
        return json.loads(MESSAGES_FILE.read_text(encoding="utf-8"))
    return []

def _save_messages(msgs: list):
    MESSAGES_FILE.write_text(json.dumps(msgs, ensure_ascii=False, indent=2), encoding="utf-8")


app = FastAPI(title="DermFinder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IMAGES_DIRS = {"isic2020": IMAGES_DIR_2020, "isic2019": IMAGES_DIR_2019}
DB_OPTIONS = ["isic2020", "isic2019"]


@app.on_event("startup")
def startup_event():
    initialize(device="cpu")
    load_metadata()
    seed_admin()


# ════════════════════════════════════════
#  AUTH
# ════════════════════════════════════════

@app.post("/api/auth/register")
def register(_: dict):
    raise HTTPException(status_code=403, detail="Self-registration is disabled. Contact your administrator.")


@app.post("/api/auth/login")
def login(data: dict):
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")
    user = find_user_by_email(email)
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.get("is_active"):
        raise HTTPException(status_code=403, detail="Account is deactivated. Contact admin.")
    token = create_token(user["id"])
    return {"token": token, "user": public_user(user)}


@app.get("/api/auth/me")
def me(user: dict = Depends(get_current_user)):
    return public_user(user)


@app.put("/api/auth/me")
def update_profile(data: dict, user: dict = Depends(get_current_user)):
    users = get_users()
    for u in users:
        if u["id"] == user["id"]:
            if data.get("name"):    u["name"]     = data["name"].strip()
            if data.get("hospital"): u["hospital"] = data["hospital"].strip()
            if data.get("password"): 
                from auth import hash_password
                u["password"] = hash_password(data["password"])
            save_users(users)
            return public_user(u)
    raise HTTPException(status_code=404, detail="User not found")


# ════════════════════════════════════════
#  ADMIN — User management
# ════════════════════════════════════════

def require_admin_or_professor(user: dict = Depends(get_current_user)):
    if user["role"] != "admin" and user.get("level") != "professor":
        raise HTTPException(status_code=403, detail="Admin or Professor access required")
    return user


@app.get("/api/admin/users")
def admin_get_users(user: dict = Depends(require_admin_or_professor)):
    return [public_user(u) for u in get_users()]


@app.patch("/api/admin/users/{user_id}")
def admin_update_user(user_id: str, data: dict, current: dict = Depends(require_admin_or_professor)):
    users = get_users()
    for u in users:
        if u["id"] == user_id:
            if "level" in data and data["level"] in LEVELS:
                u["level"] = data["level"]
            if "is_active" in data:
                u["is_active"] = bool(data["is_active"])
            if "role" in data and current["role"] == "admin":
                u["role"] = data["role"]
            save_users(users)
            return public_user(u)
    raise HTTPException(status_code=404, detail="User not found")


@app.post("/api/admin/users/create")
def admin_create_user(data: dict, current: dict = Depends(require_admin_or_professor)):
    if current["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create users")
    name     = data.get("name", "").strip()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")
    level    = data.get("level", "intern")
    hospital = data.get("hospital", "").strip()
    if not all([name, email, password]):
        raise HTTPException(status_code=400, detail="Name, email and password are required")
    if level not in LEVELS:
        raise HTTPException(status_code=400, detail=f"Level must be one of {LEVELS}")
    user = create_user(name=name, email=email, password=password, level=level, hospital=hospital)
    return public_user(user)


@app.delete("/api/admin/users/{user_id}")
def admin_delete_user(user_id: str, current: dict = Depends(require_admin_or_professor)):
    if current["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete users")
    users = [u for u in get_users() if u["id"] != user_id]
    save_users(users)
    return {"status": "deleted"}


@app.get("/api/admin/stats")
def admin_stats(user: dict = Depends(require_admin_or_professor)):
    all_users = get_users()
    all_history = get_history()
    all_cases = get_cases()
    return {
        "total_users": len(all_users),
        "active_users": sum(1 for u in all_users if u.get("is_active")),
        "total_searches": len(all_history),
        "total_cases": len(all_cases),
        "by_level": {lvl: sum(1 for u in all_users if u.get("level") == lvl) for lvl in LEVELS},
    }


# ════════════════════════════════════════
#  HISTORY
# ════════════════════════════════════════

@app.get("/api/history")
def get_my_history(user: dict = Depends(get_current_user)):
    if user["role"] == "admin" or user.get("level") in ["professor"]:
        return get_history()
    return get_history(user_id=user["id"])


@app.get("/api/history/{user_id}")
def get_user_history(user_id: str, current: dict = Depends(require_admin_or_professor)):
    return get_history(user_id=user_id)


# ════════════════════════════════════════
#  CASES (Annotations / Registrations)
# ════════════════════════════════════════

@app.post("/api/cases")
def register_case(data: dict, user: dict = Depends(require_permission("annotate"))):
    image_id  = data.get("image_id", "")
    db        = data.get("db", "isic2020")
    diagnosis = data.get("diagnosis", "").strip()
    notes     = data.get("notes", "").strip()
    image_url = data.get("image_url", "")
    metadata  = data.get("metadata", {})
    top_results = data.get("top_results", [])

    if not image_id or not diagnosis:
        raise HTTPException(status_code=400, detail="image_id and diagnosis are required")

    cases = _load_cases()
    entry = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "doctor_name": user["name"],
        "doctor_level": user["level"],
        "image_id": image_id,
        "db": db,
        "image_url": image_url,
        "diagnosis": diagnosis,
        "notes": notes,
        "metadata": metadata,
        "top_results": top_results,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    cases.append(entry)
    _save_cases(cases)
    return entry


@app.put("/api/cases/{case_id}")
def update_case(case_id: str, data: dict, user: dict = Depends(get_current_user)):
    cases = _load_cases()
    for c in cases:
        if c["id"] == case_id:
            # check permission: own case OR higher level
            if c["user_id"] != user["id"]:
                if user["role"] != "admin" and user.get("level") != "professor":
                    raise HTTPException(status_code=403, detail="You can only edit your own cases")
                # professor can only edit lower levels
                level_order = ["intern", "resident", "senior", "professor"]
                if user.get("level") == "professor":
                    case_owner = find_user_by_id(c["user_id"])
                    if case_owner and level_order.index(case_owner.get("level", "intern")) >= level_order.index("professor"):
                        raise HTTPException(status_code=403, detail="Cannot edit cases from same or higher level")
            if data.get("diagnosis"): c["diagnosis"] = data["diagnosis"]
            if "notes" in data: c["notes"] = data["notes"]
            c["updated_at"] = datetime.now().isoformat(timespec="seconds")
            c["updated_by"] = user["name"]
            _save_cases(cases)
            return c
    raise HTTPException(status_code=404, detail="Case not found")


@app.delete("/api/cases/{case_id}")
def delete_case(case_id: str, user: dict = Depends(get_current_user)):
    cases = _load_cases()
    case = next((c for c in cases if c["id"] == case_id), None)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case["user_id"] != user["id"]:
        if user["role"] != "admin" and user.get("level") != "professor":
            raise HTTPException(status_code=403, detail="You can only delete your own cases")
    cases = [c for c in cases if c["id"] != case_id]
    _save_cases(cases)
    return {"status": "deleted"}


@app.get("/api/cases")
def get_my_cases(user: dict = Depends(get_current_user)):
    if user["role"] == "admin" or user.get("level") == "professor":
        return get_cases()
    return get_cases(user_id=user["id"])


@app.get("/api/cases/{user_id}")
def get_user_cases(user_id: str, current: dict = Depends(require_admin_or_professor)):
    return get_cases(user_id=user_id)


# ════════════════════════════════════════
#  EXISTING ENDPOINTS (unchanged)
# ════════════════════════════════════════

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/stats")
def stats(db: str = Query("isic2020", enum=DB_OPTIONS)):
    engine = ENGINES[db]
    labels = engine.labels
    total = int(len(labels))
    if db == "isic2019":
        malignant = int(sum(1 for l in labels if int(l) in ISIC2019_MALIGNANT))
    else:
        malignant = int((labels == 1).sum())
    benign = total - malignant
    return {"total_images": total, "benign": benign, "malignant": malignant,
            "vector_dim": VECTOR_DIM, "alpha": ALPHA, "method": "HJG Light", "db": db}


@app.get("/api/image/{image_id}")
def get_image(image_id: str, db: str = Query("isic2020", enum=DB_OPTIONS)):
    p = IMAGES_DIRS[db] / f"{image_id}.jpg"
    if not p.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(p)


@app.get("/api/metadata/{image_id}")
def api_metadata(image_id: str, db: str = Query("isic2020", enum=DB_OPTIONS)):
    md = get_metadata(image_id, db)
    if not md:
        raise HTTPException(status_code=404, detail="Metadata not found")
    return md


@app.get("/api/sample")
def api_sample(n: int = 12, db: str = Query("isic2020", enum=DB_OPTIONS)):
    engine = ENGINES[db]
    ids = [str(x) for x in engine.image_ids[:n].tolist()]
    items = []
    for image_id in ids:
        md = get_metadata(image_id, db)
        items.append({"image_id": image_id, "metadata": md, "image_url": f"/api/image/{image_id}?db={db}"})
    return {"items": items}


@app.post("/api/search")
async def api_search(
    file: UploadFile = File(...),
    top_k: int = Query(10, enum=TOP_K_OPTIONS),
    db: str = Query("isic2020", enum=DB_OPTIONS),
    user: dict = Depends(get_current_user_optional),
):
    if file.content_type.split("/")[0] != "image":
        raise HTTPException(status_code=400, detail="File must be an image")

    data = await file.read()
    try:
        pil = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e}")

    save_upload(data, file.filename)

    t0 = time.perf_counter()
    try:
        q_vec = extract_and_compress(pil, db=db)
        engine = ENGINES[db]
        res = engine.search_hjg(q_vec, top_k=top_k)
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    elapsed = (time.perf_counter() - t0) * 1000.0

    results = []
    for rank, (dist, idx) in enumerate(res, start=1):
        image_id = str(engine.image_ids[int(idx)])
        md = get_metadata(image_id, db)
        sim = 1.0 - dist
        raw_label = int(engine.labels[int(idx)])
        if db == "isic2019":
            is_malignant = raw_label in ISIC2019_MALIGNANT
            label = 1 if is_malignant else 0
            label_name = "Malignant" if is_malignant else "Benign"
        else:
            label = raw_label
            label_name = "Malignant" if label == 1 else "Benign"
        results.append({
            "rank": rank, "image_id": image_id,
            "image_url": f"/api/image/{image_id}?db={db}",
            "label": label, "label_name": label_name,
            "distance": float(dist), "similarity": float(sim), "metadata": md,
        })

    # Auto-save to history if logged in
    if user:
        save_search(user["id"], file.filename, db, top_k, results, elapsed)

    return JSONResponse({
        "query_info": {"filename": file.filename},
        "method": "HJG Light", "search_time_ms": elapsed,
        "top_k": top_k, "db": db, "results": results,
    })


# ════════════════════════════════════════
#  CONTACT & MESSAGES (unchanged)
# ════════════════════════════════════════

@app.post("/api/contact")
async def contact_form(data: dict):
    name    = data.get("name", "").strip()
    email   = data.get("email", "").strip()
    subject = data.get("subject", "").strip()
    message = data.get("message", "").strip()
    if not all([name, email, subject, message]):
        raise HTTPException(status_code=400, detail="All fields are required")
    msgs = _load_messages()
    entry = {"id": len(msgs) + 1, "name": name, "email": email, "subject": subject,
             "message": message, "timestamp": datetime.now().isoformat(timespec="seconds"), "read": False}
    msgs.append(entry)
    _save_messages(msgs)
    return {"status": "success", "message": "Your message has been received. We'll get back to you within 24-48 hours."}


@app.get("/api/messages")
def get_messages():
    msgs = _load_messages()
    return {"total": len(msgs), "unread": sum(1 for m in msgs if not m["read"]), "messages": list(reversed(msgs))}


@app.patch("/api/messages/{msg_id}/read")
def mark_read(msg_id: int):
    msgs = _load_messages()
    for m in msgs:
        if m["id"] == msg_id:
            m["read"] = True
            _save_messages(msgs)
            return {"status": "ok"}
    raise HTTPException(status_code=404, detail="Message not found")
