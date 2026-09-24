from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import logging
import os
from pathlib import Path
import secrets
import sqlite3
from typing import Optional, Literal

from dotenv import load_dotenv
from fastapi import Cookie, Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from .content import FAQ, GALLERY, NEWS, SCHOOL
from .email import notify_new_enquiry, notify_new_review

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
DB_PATH = BASE_DIR / "jigisha.db"
SESSION_COOKIE = "jigisha_admin_session"
SESSION_HOURS = 8
STATUS_VALUES = ("new", "contacted", "closed")
REVIEW_ROLE_VALUES = ("Student", "Parent", "Alumni", "Teacher", "Other")
REVIEW_STATUS_VALUES = ("pending", "approved", "rejected")

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


class AdminCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    role: Literal["admin", "super_admin"] = "admin"


class AdminUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    role: Optional[Literal["admin", "super_admin"]] = None
    is_active: Optional[bool] = None


class AdminPasswordReset(BaseModel):
    password: str = Field(min_length=8, max_length=200)


class EnquiryStatusUpdate(BaseModel):
    status: str


class ReviewSubmission(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    role: str = Field(min_length=1, max_length=20)
    rating: int = Field(ge=1, le=5)
    review: str = Field(min_length=10, max_length=2000)
    consent: bool


class ReviewStatusUpdate(BaseModel):
    status: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    """Hash passwords with a salted, deliberately expensive scrypt derivation."""
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=16384, r=8, p=1)
    return f"scrypt$16384$8$1${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, n_value, r_value, p_value, salt_hex, digest_hex = stored_hash.split("$", 5)
        if algorithm != "scrypt":
            return False
        candidate = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n_value),
            r=int(r_value),
            p=int(p_value),
            dklen=len(bytes.fromhex(digest_hex)),
        )
        return hmac.compare_digest(candidate, bytes.fromhex(digest_hex))
    except (TypeError, ValueError):
        return False


def normalise_email(email: str) -> str:
    return email.strip().lower()


DUMMY_PASSWORD_HASH = hash_password("jigisha-invalid-login-password")


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
        connection.execute("""CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            review TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
            created_at TEXT NOT NULL
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS admin_sessions (
            token_digest TEXT PRIMARY KEY,
            expires_at TEXT NOT NULL,
            admin_id INTEGER
        )""")
        session_columns = {row[1] for row in connection.execute("PRAGMA table_info(admin_sessions)").fetchall()}
        if "admin_id" not in session_columns:
            connection.execute("ALTER TABLE admin_sessions ADD COLUMN admin_id INTEGER")

        connection.execute("""CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'admin' CHECK (role IN ('admin', 'super_admin')),
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )""")
        migrate_environment_admin(connection, "ADMIN_EMAIL", "ADMIN_PASSWORD", "super_admin", "School Super Admin")
        migrate_environment_admin(connection, "SCHOOL_ADMIN_EMAIL", "SCHOOL_ADMIN_PASSWORD", "admin", "School Admin")


def migrate_environment_admin(connection: sqlite3.Connection, email_key: str, password_key: str, role: str, default_name: str):
    email = normalise_email(os.getenv(email_key, ""))
    password = os.getenv(password_key, "")
    if not email or not password:
        return
    existing = connection.execute("SELECT id, role FROM admins WHERE email = ?", (email,)).fetchone()
    if existing:
        if role == "super_admin":
            connection.execute(
                "UPDATE admins SET role = 'super_admin', is_active = 1, updated_at = ? WHERE id = ?",
                (utc_now().isoformat(), existing[0]),
            )
        return
    now = utc_now().isoformat()
    connection.execute(
        "INSERT INTO admins (name, email, password_hash, role, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, 1, ?, ?)",
        (default_name, email, hash_password(password), role, now, now),
    )


@app.on_event("startup")
def startup():
    init_db()


def session_digest(token: str) -> str:
    secret = os.getenv("SECRET_KEY", "")
    if not secret:
        return ""
    return hmac.new(secret.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()


def _authenticated_admin(admin_session: Optional[str]) -> dict:
    if not admin_session or not os.getenv("SECRET_KEY"):
        raise HTTPException(status_code=401, detail="Authentication required")
    digest = session_digest(admin_session)
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """SELECT s.expires_at, a.id, a.name, a.email, a.role, a.is_active
               FROM admin_sessions s JOIN admins a ON a.id = s.admin_id
               WHERE s.token_digest = ?""",
            (digest,),
        ).fetchone()
        if row and row["expires_at"] <= utc_now().isoformat():
            connection.execute("DELETE FROM admin_sessions WHERE token_digest = ?", (digest,))
            row = None
    if not row or not row["is_active"]:
        raise HTTPException(status_code=401, detail="Authentication required")
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
        "token_digest": digest,
    }


def require_admin(admin_session: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE)) -> dict:
    return _authenticated_admin(admin_session)


def require_super_admin(admin: dict = Depends(require_admin)) -> dict:
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    return admin


def row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


def get_enquiry(enquiry_id: int) -> dict:
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT id, parent, student, email, mobile, grade, message, created_at, status FROM enquiries WHERE id = ?", (enquiry_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Enquiry not found")
    return row_to_dict(row)


def get_review(review_id: int) -> dict:
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT id, name, role, rating, review, status, created_at FROM reviews WHERE id = ?", (review_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Review not found")
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


@app.post("/api/reviews", status_code=201)
def create_review(payload: ReviewSubmission):
    values = payload.model_dump()
    if values["role"] not in REVIEW_ROLE_VALUES:
        raise HTTPException(status_code=422, detail="Invalid review role")
    if not values["consent"]:
        raise HTTPException(status_code=422, detail="Consent is required")
    created_at = utc_now().isoformat()
    name = values["name"].strip()
    review_text = values["review"].strip()
    if len(name) < 2:
        raise HTTPException(status_code=422, detail="Name is too short")
    if len(review_text) < 10:
        raise HTTPException(status_code=422, detail="Review is too short")
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            "INSERT INTO reviews (name, role, rating, review, status, created_at) VALUES (?, ?, ?, ?, 'pending', ?)",
            (name, values["role"], values["rating"], review_text, created_at),
        )
        review_id = cursor.lastrowid
    review = {"id": review_id, "name": name, "role": values["role"], "rating": values["rating"], "review": review_text, "status": "pending", "created_at": created_at}
    notify_new_review(review)
    return {"success": True, "message": "Review submitted successfully"}


@app.get("/api/reviews")
def public_reviews():
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT id, name, role, rating, review, created_at FROM reviews WHERE status = 'approved' ORDER BY datetime(created_at) DESC, id DESC"
        ).fetchall()
    return {"success": True, "items": [row_to_dict(row) for row in rows]}


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
    if not os.getenv("SECRET_KEY"):
        logger.error("Admin login is unavailable because SECRET_KEY is missing.")
        raise HTTPException(
            status_code=503,
            detail="Admin authentication is not configured"
        )

    entered_email = normalise_email(payload.email)
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        account = connection.execute(
            "SELECT id, name, email, password_hash, role, is_active FROM admins WHERE email = ?",
            (entered_email,),
        ).fetchone()
    password_hash = account["password_hash"] if account else DUMMY_PASSWORD_HASH
    password_valid = verify_password(payload.password, password_hash)
    if not account or not account["is_active"] or not password_valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = secrets.token_urlsafe(32)
    expires_at = (utc_now() + timedelta(hours=SESSION_HOURS)).isoformat()

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO admin_sessions (token_digest, expires_at, admin_id) VALUES (?, ?, ?)",
            (session_digest(token), expires_at, account["id"]),
        )

    secure_cookie = os.getenv("COOKIE_SECURE", "false").lower() == "true"

    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_HOURS * 3600,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        path="/",
    )

    return {
        "success": True,
        "admin": {
            "id": account["id"],
            "name": account["name"],
            "email": account["email"],
            "role": account["role"],
        },
    }


@app.post("/api/admin/logout")
def admin_logout(response: Response, admin: dict = Depends(require_admin)):
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("DELETE FROM admin_sessions WHERE token_digest = ?", (admin["token_digest"],))
    response.delete_cookie(SESSION_COOKIE, httponly=True, secure=os.getenv("COOKIE_SECURE", "false").lower() == "true", samesite="lax", path="/")
    return {"success": True}


@app.get("/api/admin/me")
def admin_me(admin: dict = Depends(require_admin)):
    return {key: admin[key] for key in ("id", "name", "email", "role")}


def public_admin(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def is_protected_super_admin(email: str) -> bool:
    bootstrap_email = normalise_email(os.getenv("ADMIN_EMAIL", ""))
    return bool(bootstrap_email and email == bootstrap_email)


def super_admin_count(connection: sqlite3.Connection) -> int:
    return connection.execute("SELECT COUNT(*) FROM admins WHERE role = 'super_admin'").fetchone()[0]


@app.get("/api/admin/admins")
def list_admins(_: dict = Depends(require_super_admin)):
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT id, name, email, role, is_active, created_at, updated_at FROM admins ORDER BY datetime(created_at), id"
        ).fetchall()
    return {"items": [public_admin(row) for row in rows]}


@app.post("/api/admin/admins", status_code=201)
def create_admin(payload: AdminCreate, _: dict = Depends(require_super_admin)):
    name = payload.name.strip()
    email = normalise_email(payload.email)
    if len(name) < 2:
        raise HTTPException(status_code=422, detail="Name is too short")
    now = utc_now().isoformat()
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.execute(
                """INSERT INTO admins (name, email, password_hash, role, is_active, created_at, updated_at)
                   VALUES (?, ?, ?, ?, 1, ?, ?)""",
                (name, email, hash_password(payload.password), payload.role, now, now),
            )
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT id, name, email, role, is_active, created_at, updated_at FROM admins WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="An admin with that email already exists")
    return public_admin(row)


@app.patch("/api/admin/admins/{admin_id}")
def update_admin_account(admin_id: int, payload: AdminUpdate, current_admin: dict = Depends(require_super_admin)):
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        target = connection.execute(
            "SELECT id, name, email, role, is_active, created_at, updated_at FROM admins WHERE id = ?",
            (admin_id,),
        ).fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="Admin not found")
        changes = {}
        if payload.name is not None:
            name = payload.name.strip()
            if len(name) < 2:
                raise HTTPException(status_code=422, detail="Name is too short")
            changes["name"] = name
        next_role = payload.role or target["role"]
        next_active = target["is_active"] if payload.is_active is None else int(payload.is_active)
        if is_protected_super_admin(target["email"]):
            if next_role != "super_admin" or not next_active:
                raise HTTPException(status_code=409, detail="The primary Super Admin must remain active")
        if target["role"] == "super_admin" and next_role != "super_admin" and super_admin_count(connection) <= 1:
            raise HTTPException(status_code=409, detail="At least one Super Admin must remain")
        if target["role"] == "super_admin" and not next_active and super_admin_count(connection) <= 1:
            raise HTTPException(status_code=409, detail="At least one Super Admin must remain active")
        if admin_id == current_admin["id"] and next_role != "super_admin" and super_admin_count(connection) <= 1:
            raise HTTPException(status_code=409, detail="You cannot demote the last Super Admin")
        changes.update({"role": next_role, "is_active": next_active, "updated_at": utc_now().isoformat()})
        assignments = ", ".join(f"{column} = ?" for column in changes)
        connection.execute(f"UPDATE admins SET {assignments} WHERE id = ?", [*changes.values(), admin_id])
        updated = connection.execute(
            "SELECT id, name, email, role, is_active, created_at, updated_at FROM admins WHERE id = ?",
            (admin_id,),
        ).fetchone()
    return public_admin(updated)


@app.delete("/api/admin/admins/{admin_id}")
def delete_admin_account(admin_id: int, response: Response, current_admin: dict = Depends(require_super_admin)):
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        target = connection.execute("SELECT id, email, role FROM admins WHERE id = ?", (admin_id,)).fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="Admin not found")
        if is_protected_super_admin(target["email"]):
            raise HTTPException(status_code=409, detail="The primary Super Admin cannot be deleted")
        if target["role"] == "super_admin" and super_admin_count(connection) <= 1:
            raise HTTPException(status_code=409, detail="At least one Super Admin must remain")
        connection.execute("DELETE FROM admin_sessions WHERE admin_id = ?", (admin_id,))
        connection.execute("DELETE FROM admins WHERE id = ?", (admin_id,))
    if admin_id == current_admin["id"]:
        response.delete_cookie(SESSION_COOKIE, httponly=True, secure=os.getenv("COOKIE_SECURE", "false").lower() == "true", samesite="lax", path="/")
    return {"success": True, "message": "Admin deleted"}


@app.post("/api/admin/admins/{admin_id}/reset-password")
def reset_admin_password(admin_id: int, payload: AdminPasswordReset, _: dict = Depends(require_super_admin)):
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            "UPDATE admins SET password_hash = ?, updated_at = ? WHERE id = ?",
            (hash_password(payload.password), utc_now().isoformat(), admin_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Admin not found")
        connection.execute("DELETE FROM admin_sessions WHERE admin_id = ?", (admin_id,))
    return {"success": True, "message": "Password reset successfully"}


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


@app.get("/api/admin/reviews")
def admin_reviews(status: Optional[str] = Query(default=None), _: str = Depends(require_admin)):
    if status and status not in REVIEW_STATUS_VALUES:
        raise HTTPException(status_code=422, detail="Invalid review status")
    where = " WHERE status = ?" if status else ""
    params = [status] if status else []
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            f"SELECT id, name, role, rating, review, status, created_at FROM reviews{where} ORDER BY datetime(created_at) DESC, id DESC",
            params,
        ).fetchall()
    return {"items": [row_to_dict(row) for row in rows], "total": len(rows), "status": status or "all"}


@app.patch("/api/admin/reviews/{review_id}")
def update_admin_review(review_id: int, payload: ReviewStatusUpdate, _: str = Depends(require_admin)):
    if payload.status not in REVIEW_STATUS_VALUES:
        raise HTTPException(status_code=422, detail="Invalid review status")
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute("UPDATE reviews SET status = ? WHERE id = ?", (payload.status, review_id))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Review not found")
    return get_review(review_id)


@app.delete("/api/admin/reviews/{review_id}")
def delete_admin_review(review_id: int, _: str = Depends(require_admin)):
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Review not found")
    return {"success": True, "message": "Review deleted"}
