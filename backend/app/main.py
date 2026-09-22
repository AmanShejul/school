from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import logging
import os
from pathlib import Path
import secrets
import sqlite3
from typing import Optional

from dotenv import load_dotenv
from fastapi import Cookie, Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from .content import FAQ, GALLERY, NEWS, SCHOOL
from .email import notify_new_enquiry

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
DB_PATH = BASE_DIR / "jigisha.db"
SESSION_COOKIE = "jigisha_admin_session"
SESSION_HOURS = 8
STATUS_VALUES = ("new", "contacted", "closed")

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(title="Jigisha International School API", version="1.0.0")
allowed_origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)


class Enquiry(BaseModel):
    parent: str = Field(min_length=2, max_length=120)
    student: str = Field(min_length=2, max_length=120)
    email: EmailStr
    mobile: str = Field(min_length=7, max_length=20)
    grade: str = Field(min_length=2, max_length=80)
    message: str = Field(default="", max_length=1000)


class ContactMessage(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    message: str = Field(min_length=5, max_length=1000)


class AdminLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class EnquiryStatusUpdate(BaseModel):
    status: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def init_db():
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent TEXT NOT NULL, student TEXT NOT NULL, email TEXT NOT NULL,
            mobile TEXT NOT NULL, grade TEXT NOT NULL, message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        columns = {row[1] for row in connection.execute("PRAGMA table_info(enquiries)").fetchall()}
        if "status" not in columns:
            connection.execute("ALTER TABLE enquiries ADD COLUMN status TEXT NOT NULL DEFAULT 'new'")
        connection.execute("UPDATE enquiries SET status = 'new' WHERE status IS NULL OR status = ''")
        connection.execute("""CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, email TEXT NOT NULL, message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS admin_sessions (
            token_digest TEXT PRIMARY KEY,
            expires_at TEXT NOT NULL
        )""")


@app.on_event("startup")
def startup():
    init_db()


def session_digest(token: str) -> str:
    secret = os.getenv("SECRET_KEY", "")
    if not secret:
        return ""
    return hmac.new(secret.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()


def require_admin(admin_session: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE)) -> str:
    if not admin_session or not os.getenv("SECRET_KEY"):
        raise HTTPException(status_code=401, detail="Authentication required")
    digest = session_digest(admin_session)
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute("SELECT expires_at FROM admin_sessions WHERE token_digest = ?", (digest,)).fetchone()
        if row and row[0] <= utc_now().isoformat():
            connection.execute("DELETE FROM admin_sessions WHERE token_digest = ?", (digest,))
            row = None
    if not row:
        raise HTTPException(status_code=401, detail="Authentication required")
    return digest


def row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


def get_enquiry(enquiry_id: int) -> dict:
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT id, parent, student, email, mobile, grade, message, created_at, status FROM enquiries WHERE id = ?", (enquiry_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Enquiry not found")
    return row_to_dict(row)


@app.get("/api/health")
def health():
    return {"success": True, "status": "ok"}


@app.get("/api/school")
def school():
    return SCHOOL


@app.get("/api/news")
def news():
    return {"success": True, "items": NEWS}


@app.get("/api/gallery")
def gallery():
    return {"success": True, "items": GALLERY}


@app.get("/api/faq")
def faq():
    return {"success": True, "items": FAQ}


def save_enquiry(payload: Enquiry) -> dict:
    values = payload.model_dump()
    created_at = utc_now().isoformat()
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            "INSERT INTO enquiries (parent, student, email, mobile, grade, message, created_at, status) VALUES (?, ?, ?, ?, ?, ?, ?, 'new')",
            (values["parent"], values["student"], values["email"], values["mobile"], values["grade"], values["message"], created_at),
        )
        enquiry_id = cursor.lastrowid
    enquiry = {**values, "id": enquiry_id, "created_at": created_at, "status": "new"}
    notify_new_enquiry(enquiry)
    return enquiry


@app.post("/api/enquiries", status_code=201)
def create_enquiry(payload: Enquiry):
    save_enquiry(payload)
    return {"success": True, "message": "Enquiry submitted successfully"}


@app.post("/api/contact", status_code=201)
def create_contact(payload: ContactMessage):
    values = payload.model_dump()
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            "INSERT INTO contact_messages (name, email, message, created_at) VALUES (?, ?, ?, ?)",
            (values["name"], values["email"], values["message"], utc_now().isoformat()),
        )
    return {"success": True, "message": "Message submitted successfully"}


@app.post("/api/admissions/enquiry", status_code=201)
def admission_enquiry(payload: Enquiry):
    save_enquiry(payload)
    return {"success": True, "message": "Enquiry submitted successfully"}


@app.post("/api/admin/login")
def admin_login(payload: AdminLogin, response: Response):
    configured_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    configured_password = os.getenv("ADMIN_PASSWORD", "")
    if not configured_email or not configured_password or not os.getenv("SECRET_KEY"):
        logger.error("Admin login is unavailable because required authentication settings are missing.")
        raise HTTPException(status_code=503, detail="Admin authentication is not configured")
    email_matches = hmac.compare_digest(payload.email.lower(), configured_email)
    password_matches = hmac.compare_digest(payload.password, configured_password)
    if not email_matches or not password_matches:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = secrets.token_urlsafe(32)
    expires_at = (utc_now() + timedelta(hours=SESSION_HOURS)).isoformat()
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("INSERT OR REPLACE INTO admin_sessions (token_digest, expires_at) VALUES (?, ?)", (session_digest(token), expires_at))
    secure_cookie = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    response.set_cookie(SESSION_COOKIE, token, max_age=SESSION_HOURS * 3600, httponly=True, secure=secure_cookie, samesite="lax", path="/")
    return {"success": True, "admin": {"email": configured_email}}


@app.post("/api/admin/logout")
def admin_logout(response: Response, admin_session: str = Depends(require_admin)):
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("DELETE FROM admin_sessions WHERE token_digest = ?", (admin_session,))
    response.delete_cookie(SESSION_COOKIE, httponly=True, secure=os.getenv("COOKIE_SECURE", "false").lower() == "true", samesite="lax", path="/")
    return {"success": True}


@app.get("/api/admin/stats")
def admin_stats(_: str = Depends(require_admin)):
    with sqlite3.connect(DB_PATH) as connection:
        total = connection.execute("SELECT COUNT(*) FROM enquiries").fetchone()[0]
        counts = {status: connection.execute("SELECT COUNT(*) FROM enquiries WHERE status = ?", (status,)).fetchone()[0] for status in STATUS_VALUES}
    return {"total_enquiries": total, "new_enquiries": counts["new"], "contacted_enquiries": counts["contacted"], "closed_enquiries": counts["closed"]}


@app.get("/api/admin/enquiries")
def admin_enquiries(
    search: str = Query(default="", max_length=120),
    status: Optional[str] = Query(default=None),
    grade: Optional[str] = Query(default=None, max_length=80),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: str = Depends(require_admin),
):
    if status and status not in STATUS_VALUES:
        raise HTTPException(status_code=422, detail="Invalid enquiry status")
    filters = []
    params: list[str] = []
    if search.strip():
        term = f"%{search.strip()}%"
        filters.append("(parent LIKE ? OR student LIKE ? OR email LIKE ? OR mobile LIKE ?)")
        params.extend([term, term, term, term])
    if status:
        filters.append("status = ?")
        params.append(status)
    if grade:
        filters.append("grade = ?")
        params.append(grade)
    where = f" WHERE {' AND '.join(filters)}" if filters else ""
    offset = (page - 1) * page_size
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        total = connection.execute(f"SELECT COUNT(*) FROM enquiries{where}", params).fetchone()[0]
        rows = connection.execute(f"SELECT id, parent, student, email, mobile, grade, message, created_at, status FROM enquiries{where} ORDER BY datetime(created_at) DESC, id DESC LIMIT ? OFFSET ?", [*params, page_size, offset]).fetchall()
    return {"items": [row_to_dict(row) for row in rows], "total": total, "page": page, "page_size": page_size}


@app.get("/api/admin/enquiries/{enquiry_id}")
def admin_enquiry(enquiry_id: int, _: str = Depends(require_admin)):
    return get_enquiry(enquiry_id)


@app.patch("/api/admin/enquiries/{enquiry_id}")
def update_admin_enquiry(enquiry_id: int, payload: EnquiryStatusUpdate, _: str = Depends(require_admin)):
    if payload.status not in STATUS_VALUES:
        raise HTTPException(status_code=422, detail="Invalid enquiry status")
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute("UPDATE enquiries SET status = ? WHERE id = ?", (payload.status, enquiry_id))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Enquiry not found")
    return get_enquiry(enquiry_id)


@app.delete("/api/admin/enquiries/{enquiry_id}")
def delete_admin_enquiry(enquiry_id: int, _: str = Depends(require_admin)):
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute("DELETE FROM enquiries WHERE id = ?", (enquiry_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Enquiry not found")
    return {"success": True, "message": "Enquiry deleted"}
