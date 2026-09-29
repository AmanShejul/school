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
from fastapi import Cookie, Depends, FastAPI, File, Form, HTTPException, Query, Request, Response, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from .content import FAQ, SCHOOL
from .email import notify_new_enquiry, notify_new_review

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
DB_PATH = BASE_DIR / "jigisha.db"
gallery_upload_dir = Path(os.getenv("GALLERY_UPLOAD_DIR", "uploads/gallery")).expanduser()
GALLERY_UPLOAD_DIR = gallery_upload_dir if gallery_upload_dir.is_absolute() else BASE_DIR / gallery_upload_dir
SESSION_COOKIE = "jigisha_admin_session"
SESSION_HOURS = 8
GALLERY_MAX_IMAGE_SIZE = int(os.getenv("GALLERY_MAX_IMAGE_SIZE_MB", "10")) * 1024 * 1024
GALLERY_CATEGORIES = (
    "Campus", "Classrooms", "Laboratories", "Library", "Sports",
    "Events", "Cultural Activities", "Achievements", "Student Life", "Other",
)
GALLERY_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
GALLERY_ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
NEWS_UPLOAD_DIR = GALLERY_UPLOAD_DIR / "news"
NEWS_TYPES = ("news", "event")
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
GALLERY_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
NEWS_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads/gallery", StaticFiles(directory=GALLERY_UPLOAD_DIR), name="gallery-uploads")


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


class GalleryUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=160)
    description: Optional[str] = Field(default=None, max_length=1000)
    category: Optional[str] = Field(default=None, max_length=60)
    is_published: Optional[bool] = None


class NewsEventUpdate(BaseModel):
    type: Optional[Literal["news", "event"]] = None
    title: Optional[str] = Field(default=None, max_length=160)
    description: Optional[str] = Field(default=None, max_length=4000)
    published_date: Optional[str] = None
    event_date: Optional[str] = None
    event_time: Optional[str] = None
    location: Optional[str] = Field(default=None, max_length=180)
    is_published: Optional[bool] = None


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
        connection.execute("""CREATE TABLE IF NOT EXISTS gallery_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_url TEXT NOT NULL,
            storage_path TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL,
            is_published INTEGER NOT NULL DEFAULT 1,
            created_by INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (created_by) REFERENCES admins(id)
        )""")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_gallery_images_published ON gallery_images (is_published, category, created_at)")
        connection.execute("""CREATE TABLE IF NOT EXISTS news_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL CHECK (type IN ('news', 'event')),
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            image_url TEXT NOT NULL DEFAULT '',
            image_storage_path TEXT NOT NULL DEFAULT '',
            published_date TEXT NOT NULL,
            event_date TEXT,
            event_time TEXT,
            location TEXT NOT NULL DEFAULT '',
            is_published INTEGER NOT NULL DEFAULT 0,
            created_by INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (created_by) REFERENCES admins(id)
        )""")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_news_events_publication ON news_events (is_published, type, published_date, event_date)")
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


def require_news_editor(admin: dict = Depends(require_admin)) -> dict:
    if admin["role"] not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="News management access required")
    return admin


def row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


def gallery_public_item(row: sqlite3.Row, request: Request) -> dict:
    item = row_to_dict(row)
    item["is_published"] = bool(item["is_published"])
    item["image_url"] = f"{str(request.base_url).rstrip('/')}/uploads/gallery/{item['storage_path']}"
    item.pop("storage_path", None)
    item.pop("created_by", None)
    return item


def gallery_file_path(storage_path: str) -> Optional[Path]:
    candidate = (GALLERY_UPLOAD_DIR / Path(storage_path).name).resolve()
    upload_root = GALLERY_UPLOAD_DIR.resolve()
    if candidate.parent != upload_root:
        return None
    return candidate


def valid_image_signature(extension: str, contents: bytes) -> bool:
    if extension in {".jpg", ".jpeg"}:
        return contents.startswith(b"\xff\xd8\xff")
    if extension == ".png":
        return contents.startswith(b"\x89PNG\r\n\x1a\n")
    if extension == ".webp":
        return len(contents) >= 12 and contents[:4] == b"RIFF" and contents[8:12] == b"WEBP"
    return False


def news_file_path(storage_path: str) -> Optional[Path]:
    candidate = (NEWS_UPLOAD_DIR / Path(storage_path).name).resolve()
    upload_root = NEWS_UPLOAD_DIR.resolve()
    if candidate.parent != upload_root:
        return None
    return candidate


def validate_news_fields(
    item_type: str,
    title: str,
    description: str,
    published_date: str,
    event_date: str,
    event_time: str,
    location: str,
) -> dict:
    clean_type = item_type.strip().lower()
    if clean_type not in NEWS_TYPES:
        raise HTTPException(status_code=422, detail="Type must be News or Event")
    clean_title = title.strip()
    clean_description = description.strip()
    clean_published_date = published_date.strip()
    clean_event_date = event_date.strip()
    clean_event_time = event_time.strip()
    clean_location = location.strip()
    if not clean_title:
        raise HTTPException(status_code=422, detail="Title is required")
    if not clean_description:
        raise HTTPException(status_code=422, detail="Description is required")
    for value, label in ((clean_published_date, "Published date"), (clean_event_date, "Event date")):
        if value:
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=422, detail=f"{label} must be a valid date")
    if not clean_published_date:
        raise HTTPException(status_code=422, detail="Published date is required")
    if clean_type == "event" and not clean_event_date:
        raise HTTPException(status_code=422, detail="Event date is required for events")
    if clean_event_time:
        try:
            datetime.strptime(clean_event_time, "%H:%M")
        except ValueError:
            raise HTTPException(status_code=422, detail="Event time must be in HH:MM format")
    return {
        "type": clean_type,
        "title": clean_title[:160],
        "description": clean_description[:4000],
        "published_date": clean_published_date,
        "event_date": clean_event_date if clean_type == "event" else "",
        "event_time": clean_event_time if clean_type == "event" else "",
        "location": clean_location[:180] if clean_type == "event" else "",
    }


async def store_news_image(upload: Optional[UploadFile]) -> Optional[tuple[str, Path]]:
    if not upload or not upload.filename:
        return None
    extension = Path(upload.filename).suffix.lower()
    if extension not in GALLERY_ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=422, detail="Unsupported image type. Use JPG, PNG, or WEBP.")
    if (upload.content_type or "").lower() not in GALLERY_ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=422, detail="The uploaded image MIME type is not supported.")
    contents = await upload.read()
    if not contents:
        raise HTTPException(status_code=422, detail="The uploaded image is empty.")
    if len(contents) > GALLERY_MAX_IMAGE_SIZE:
        raise HTTPException(status_code=422, detail=f"Image exceeds the {GALLERY_MAX_IMAGE_SIZE // (1024 * 1024)} MB limit.")
    if not valid_image_signature(extension, contents):
        raise HTTPException(status_code=422, detail="The file contents do not match the selected image type.")
    storage_name = f"{secrets.token_hex(20)}{extension}"
    file_path = NEWS_UPLOAD_DIR / storage_name
    try:
        file_path.write_bytes(contents)
    except OSError:
        raise HTTPException(status_code=503, detail="The image could not be stored")
    return storage_name, file_path


def news_public_item(row: sqlite3.Row, request: Request) -> dict:
    item = row_to_dict(row)
    item["is_published"] = bool(item["is_published"])
    image_url = ""
    if item.get("image_storage_path"):
        image_url = f"{str(request.base_url).rstrip('/')}/uploads/gallery/news/{item['image_storage_path']}"
    item["image_url"] = image_url
    item["image"] = image_url
    item["date"] = item["event_date"] if item["type"] == "event" and item.get("event_date") else item["published_date"]
    item["category"] = "Event" if item["type"] == "event" else "News"
    event_details = " · ".join(value for value in (item.get("event_time"), item.get("location")) if value)
    item["text"] = f"{item['description']} ({event_details})" if item["type"] == "event" and event_details else item["description"]
    item.pop("image_storage_path", None)
    item.pop("created_by", None)
    return item


NEWS_SELECT = "SELECT id, type, title, description, image_url, image_storage_path, published_date, event_date, event_time, location, is_published, created_by, created_at, updated_at FROM news_events"


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
def news(request: Request):
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            f"{NEWS_SELECT} WHERE is_published = 1 ORDER BY date(CASE WHEN type = 'event' AND event_date != '' THEN event_date ELSE published_date END) DESC, id DESC"
        ).fetchall()
    return {"success": True, "items": [news_public_item(row, request) for row in rows]}


@app.get("/api/admin/news")
def admin_news(
    request: Request,
    item_type: Optional[str] = Query(default=None, alias="type"),
    publication: Optional[str] = Query(default=None),
    _: dict = Depends(require_news_editor),
):
    if item_type and item_type not in NEWS_TYPES:
        raise HTTPException(status_code=422, detail="Invalid news type")
    if publication and publication not in ("published", "draft"):
        raise HTTPException(status_code=422, detail="Invalid publication filter")
    filters = []
    params: list[str | int] = []
    if item_type:
        filters.append("type = ?")
        params.append(item_type)
    if publication:
        filters.append("is_published = ?")
        params.append(1 if publication == "published" else 0)
    where = f" WHERE {' AND '.join(filters)}" if filters else ""
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            f"{NEWS_SELECT}{where} ORDER BY datetime(updated_at) DESC, id DESC", params
        ).fetchall()
    return {"success": True, "items": [news_public_item(row, request) for row in rows]}


@app.post("/api/news", status_code=201)
async def create_news_event(
    request: Request,
    item_type: str = Form(default="news", alias="type"),
    title: str = Form(default=""),
    description: str = Form(default=""),
    published_date: str = Form(default=""),
    event_date: str = Form(default=""),
    event_time: str = Form(default=""),
    location: str = Form(default=""),
    is_published: bool = Form(default=False),
    image: Optional[UploadFile] = File(default=None),
    admin: dict = Depends(require_news_editor),
):
    values = validate_news_fields(item_type, title, description, published_date, event_date, event_time, location)
    stored_image = None
    try:
        stored_image = await store_news_image(image)
        storage_path = stored_image[0] if stored_image else ""
        now = utc_now().isoformat()
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.execute(
                f"INSERT INTO news_events (type, title, description, image_url, image_storage_path, published_date, event_date, event_time, location, is_published, created_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (values["type"], values["title"], values["description"], f"/uploads/gallery/news/{storage_path}" if storage_path else "", storage_path, values["published_date"], values["event_date"], values["event_time"], values["location"], int(is_published), admin["id"], now, now),
            )
            connection.row_factory = sqlite3.Row
            row = connection.execute(f"{NEWS_SELECT} WHERE id = ?", (cursor.lastrowid,)).fetchone()
    except Exception:
        if stored_image:
            stored_image[1].unlink(missing_ok=True)
        raise
    finally:
        if image:
            await image.close()
    return news_public_item(row, request)


@app.patch("/api/news/{news_id}")
async def update_news_event(
    news_id: int,
    request: Request,
    item_type: Optional[str] = Form(default=None, alias="type"),
    title: Optional[str] = Form(default=None),
    description: Optional[str] = Form(default=None),
    published_date: Optional[str] = Form(default=None),
    event_date: Optional[str] = Form(default=None),
    event_time: Optional[str] = Form(default=None),
    location: Optional[str] = Form(default=None),
    is_published: Optional[bool] = Form(default=None),
    remove_image: bool = Form(default=False),
    image: Optional[UploadFile] = File(default=None),
    _: dict = Depends(require_news_editor),
):
    stored_image = None
    old_storage_path = ""
    try:
        with sqlite3.connect(DB_PATH) as connection:
            connection.row_factory = sqlite3.Row
            existing = connection.execute(f"{NEWS_SELECT} WHERE id = ?", (news_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="News or event not found")
        current = row_to_dict(existing)
        values = validate_news_fields(
            item_type if item_type is not None else current["type"],
            title if title is not None else current["title"],
            description if description is not None else current["description"],
            published_date if published_date is not None else current["published_date"],
            event_date if event_date is not None else current["event_date"] or "",
            event_time if event_time is not None else current["event_time"] or "",
            location if location is not None else current["location"] or "",
        )
        stored_image = await store_news_image(image)
        old_storage_path = current["image_storage_path"] or ""
        next_storage_path = stored_image[0] if stored_image else ("" if remove_image else old_storage_path)
        now = utc_now().isoformat()
        with sqlite3.connect(DB_PATH) as connection:
            connection.execute(
                """UPDATE news_events SET type = ?, title = ?, description = ?, image_url = ?, image_storage_path = ?,
                   published_date = ?, event_date = ?, event_time = ?, location = ?, is_published = ?, updated_at = ?
                   WHERE id = ?""",
                (values["type"], values["title"], values["description"], f"/uploads/gallery/news/{next_storage_path}" if next_storage_path else "", next_storage_path, values["published_date"], values["event_date"], values["event_time"], values["location"], int(current["is_published"] if is_published is None else is_published), now, news_id),
            )
            connection.row_factory = sqlite3.Row
            row = connection.execute(f"{NEWS_SELECT} WHERE id = ?", (news_id,)).fetchone()
        if stored_image or remove_image:
            old_file = news_file_path(old_storage_path)
            if old_file:
                try:
                    old_file.unlink(missing_ok=True)
                except OSError:
                    logger.warning("Unable to remove replaced news image for item %s", news_id)
    except Exception:
        if stored_image:
            stored_image[1].unlink(missing_ok=True)
        raise
    finally:
        if image:
            await image.close()
    return news_public_item(row, request)


@app.delete("/api/news/{news_id}")
def delete_news_event(news_id: int, _: dict = Depends(require_news_editor)):
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT image_storage_path FROM news_events WHERE id = ?", (news_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="News or event not found")
        connection.execute("DELETE FROM news_events WHERE id = ?", (news_id,))
    image_path = news_file_path(row["image_storage_path"] or "")
    if image_path:
        try:
            image_path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Unable to remove news image after deleting item %s", news_id)
    return {"success": True, "message": "News or event deleted"}


@app.get("/api/gallery")
def gallery(request: Request, category: Optional[str] = Query(default=None, max_length=60)):
    if category and category not in GALLERY_CATEGORIES:
        raise HTTPException(status_code=422, detail="Invalid gallery category")
    where = " WHERE is_published = 1"
    params: list[str] = []
    if category:
        where += " AND category = ?"
        params.append(category)
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            f"SELECT id, image_url, storage_path, title, description, category, is_published, created_by, created_at, updated_at FROM gallery_images{where} ORDER BY datetime(created_at) DESC, id DESC",
            params,
        ).fetchall()
    return {"success": True, "items": [gallery_public_item(row, request) for row in rows], "categories": list(GALLERY_CATEGORIES)}


@app.get("/api/admin/gallery")
def admin_gallery(request: Request, category: Optional[str] = Query(default=None, max_length=60), _: dict = Depends(require_admin)):
    if category and category not in GALLERY_CATEGORIES:
        raise HTTPException(status_code=422, detail="Invalid gallery category")
    where = ""
    params: list[str] = []
    if category:
        where = " WHERE category = ?"
        params.append(category)
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            f"SELECT id, image_url, storage_path, title, description, category, is_published, created_by, created_at, updated_at FROM gallery_images{where} ORDER BY datetime(created_at) DESC, id DESC",
            params,
        ).fetchall()
    return {"success": True, "items": [gallery_public_item(row, request) for row in rows], "categories": list(GALLERY_CATEGORIES)}


@app.post("/api/gallery", status_code=201)
async def create_gallery_images(
    request: Request,
    files: list[UploadFile] = File(default=[]),
    category: str = Form(default="Other"),
    title: str = Form(default=""),
    description: str = Form(default=""),
    is_published: bool = Form(default=True),
    admin: dict = Depends(require_admin),
):
    if not files:
        raise HTTPException(status_code=400, detail="Select at least one image")
    if category not in GALLERY_CATEGORIES:
        raise HTTPException(status_code=422, detail="Invalid gallery category")
    clean_title = title.strip()[:160]
    clean_description = description.strip()[:1000]
    created_items = []
    errors = []
    for index, upload in enumerate(files):
        original_name = upload.filename or f"photo-{index + 1}"
        extension = Path(original_name).suffix.lower()
        try:
            if extension not in GALLERY_ALLOWED_EXTENSIONS:
                raise ValueError("Unsupported image type. Use JPG, PNG, or WEBP.")
            if (upload.content_type or "").lower() not in GALLERY_ALLOWED_MIME_TYPES:
                raise ValueError("The uploaded MIME type is not supported.")
            contents = await upload.read()
            if not contents:
                raise ValueError("The file is empty.")
            if len(contents) > GALLERY_MAX_IMAGE_SIZE:
                raise ValueError(f"Image exceeds the {GALLERY_MAX_IMAGE_SIZE // (1024 * 1024)} MB limit.")
            if not valid_image_signature(extension, contents):
                raise ValueError("The file contents do not match the selected image type.")
            storage_name = f"{secrets.token_hex(20)}{extension}"
            file_path = GALLERY_UPLOAD_DIR / storage_name
            file_path.write_bytes(contents)
            now = utc_now().isoformat()
            item_title = clean_title or Path(original_name).stem.replace("_", " ").replace("-", " ").strip()[:160]
            try:
                with sqlite3.connect(DB_PATH) as connection:
                    cursor = connection.execute(
                        """INSERT INTO gallery_images
                           (image_url, storage_path, title, description, category, is_published, created_by, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (f"/uploads/gallery/{storage_name}", storage_name, item_title, clean_description, category, int(is_published), admin["id"], now, now),
                    )
                    image_id = cursor.lastrowid
                    connection.row_factory = sqlite3.Row
                    row = connection.execute(
                        "SELECT id, image_url, storage_path, title, description, category, is_published, created_by, created_at, updated_at FROM gallery_images WHERE id = ?",
                        (image_id,),
                    ).fetchone()
                created_items.append(gallery_public_item(row, request))
            except Exception:
                file_path.unlink(missing_ok=True)
                raise
        except (OSError, ValueError) as error:
            errors.append({"filename": original_name, "error": str(error)})
        finally:
            await upload.close()
    if not created_items and errors:
        raise HTTPException(status_code=422, detail={"message": "No images were uploaded", "errors": errors})
    return {"success": True, "items": created_items, "errors": errors}


@app.patch("/api/gallery/{image_id}")
def update_gallery_image(image_id: int, payload: GalleryUpdate, request: Request, _: dict = Depends(require_admin)):
    values = payload.model_dump(exclude_unset=True)
    changes = {}
    if "title" in values:
        changes["title"] = (values["title"] or "").strip()[:160]
    if "description" in values:
        changes["description"] = (values["description"] or "").strip()[:1000]
    if "category" in values:
        if values["category"] not in GALLERY_CATEGORIES:
            raise HTTPException(status_code=422, detail="Invalid gallery category")
        changes["category"] = values["category"]
    if "is_published" in values:
        changes["is_published"] = int(bool(values["is_published"]))
    if not changes:
        raise HTTPException(status_code=400, detail="No gallery changes supplied")
    changes["updated_at"] = utc_now().isoformat()
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        target = connection.execute("SELECT id FROM gallery_images WHERE id = ?", (image_id,)).fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="Gallery image not found")
        assignments = ", ".join(f"{column} = ?" for column in changes)
        connection.execute(f"UPDATE gallery_images SET {assignments} WHERE id = ?", [*changes.values(), image_id])
        row = connection.execute(
            "SELECT id, image_url, storage_path, title, description, category, is_published, created_by, created_at, updated_at FROM gallery_images WHERE id = ?",
            (image_id,),
        ).fetchone()
    return gallery_public_item(row, request)


@app.delete("/api/gallery/{image_id}")
def delete_gallery_image(image_id: int, _: dict = Depends(require_admin)):
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT storage_path FROM gallery_images WHERE id = ?", (image_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Gallery image not found")
        connection.execute("DELETE FROM gallery_images WHERE id = ?", (image_id,))
    file_path = gallery_file_path(row["storage_path"])
    if file_path:
        try:
            file_path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Unable to remove gallery file after deleting image %s", image_id)
    return {"success": True, "message": "Gallery image deleted"}


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
