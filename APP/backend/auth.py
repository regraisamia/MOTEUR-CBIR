import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

load_dotenv(Path(__file__).parent / ".env")

# ── Config ──
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", 12))

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE = DATA_DIR / "users.json"
HISTORY_FILE = DATA_DIR / "history.json"
CASES_FILE = DATA_DIR / "cases.json"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)

# ── Levels & permissions ──
LEVELS = ["intern", "resident", "senior", "professor"]
ROLES = ["doctor", "admin"]

LEVEL_PERMISSIONS = {
    "intern":    {"search": True,  "annotate": False, "view_others": False, "manage_users": False},
    "resident":  {"search": True,  "annotate": True,  "view_others": False, "manage_users": False},
    "senior":    {"search": True,  "annotate": True,  "view_others": False, "manage_users": False},
    "professor": {"search": True,  "annotate": True,  "view_others": True,  "manage_users": True},
}


# ── JSON helpers ──
def _load(path: Path) -> list:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []

def _save(path: Path, data: list):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Password ──
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT ──
def create_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": user_id, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


# ── User CRUD ──
def get_users() -> list:
    return _load(USERS_FILE)

def save_users(users: list):
    _save(USERS_FILE, users)

def find_user_by_email(email: str) -> Optional[dict]:
    return next((u for u in get_users() if u["email"] == email), None)

def find_user_by_id(user_id: str) -> Optional[dict]:
    return next((u for u in get_users() if u["id"] == user_id), None)

def create_user(name: str, email: str, password: str, level: str = "intern", hospital: str = "", role: str = "doctor") -> dict:
    users = get_users()
    if any(u["email"] == email for u in users):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = {
        "id": str(uuid.uuid4()),
        "name": name,
        "email": email,
        "password": hash_password(password),
        "role": role,
        "level": level,
        "hospital": hospital,
        "specialty": "Dermatology",
        "is_active": True,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    users.append(user)
    save_users(users)
    return user

def public_user(u: dict) -> dict:
    """Return user without password."""
    return {k: v for k, v in u.items() if k != "password"}


# ── History CRUD ──
def save_search(user_id: str, filename: str, db: str, top_k: int, results: list, search_time_ms: float):
    history = _load(HISTORY_FILE)
    entry = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "filename": filename,
        "db": db,
        "top_k": top_k,
        "search_time_ms": round(search_time_ms, 1),
        "results_summary": [{"rank": r["rank"], "image_id": r["image_id"], "label_name": r["label_name"], "similarity": round(r["similarity"], 4)} for r in results[:5]],
        "results": results,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    history.append(entry)
    _save(HISTORY_FILE, history)
    return entry

def get_history(user_id: str = None) -> list:
    history = _load(HISTORY_FILE)
    if user_id:
        history = [h for h in history if h["user_id"] == user_id]
    return list(reversed(history))


# ── Cases (annotations) CRUD ──
def save_case(user_id: str, user_name: str, user_level: str, image_id: str, db: str,
              diagnosis: str, notes: str, image_url: str, metadata: dict) -> dict:
    cases = _load(CASES_FILE)
    entry = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "doctor_name": user_name,
        "doctor_level": user_level,
        "image_id": image_id,
        "db": db,
        "image_url": image_url,
        "diagnosis": diagnosis,
        "notes": notes,
        "metadata": metadata,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    cases.append(entry)
    _save(CASES_FILE, cases)
    return entry

def get_cases(user_id: str = None) -> list:
    cases = _load(CASES_FILE)
    if user_id:
        cases = [c for c in cases if c["user_id"] == user_id]
    return list(reversed(cases))


# ── FastAPI dependency ──
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = find_user_by_id(user_id)
    if not user or not user.get("is_active"):
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> Optional[dict]:
    if not credentials:
        return None
    try:
        return get_current_user(credentials)
    except:
        return None

def require_permission(permission: str):
    def checker(user: dict = Depends(get_current_user)):
        if user["role"] == "admin":
            return user
        perms = LEVEL_PERMISSIONS.get(user.get("level", "intern"), {})
        if not perms.get(permission):
            raise HTTPException(status_code=403, detail=f"Your level does not allow: {permission}")
        return user
    return checker


def reset_password(user_id: str, new_password: str) -> bool:
    users = get_users()
    for u in users:
        if u["id"] == user_id:
            u["password"] = hash_password(new_password)
            save_users(users)
            return True
    return False


# ── Seed admin on first run ──
def seed_admin():
    users = get_users()
    if not any(u["role"] == "admin" for u in users):
        admin = {
            "id": str(uuid.uuid4()),
            "name": "Admin",
            "email": "admin@dermfinder.com",
            "password": hash_password("admin123"),
            "role": "admin",
            "level": "professor",
            "hospital": "DermFinder HQ",
            "specialty": "Dermatology",
            "is_active": True,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        users.append(admin)
        save_users(users)
        print("✅ Admin seeded: admin@dermfinder.com / admin123")
