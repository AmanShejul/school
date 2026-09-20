from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from .content import FAQ, GALLERY, NEWS, SCHOOL

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "jigisha.db"

app = FastAPI(title="Jigisha International School API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
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


def init_db():
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent TEXT NOT NULL, student TEXT NOT NULL, email TEXT NOT NULL,
            mobile TEXT NOT NULL, grade TEXT NOT NULL, message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, email TEXT NOT NULL, message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")


@app.on_event("startup")
def startup():
    init_db()


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


@app.post("/api/enquiries", status_code=201)
def create_enquiry(payload: Enquiry):
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("INSERT INTO enquiries (parent, student, email, mobile, grade, message, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (*payload.model_dump().values(), datetime.now(timezone.utc).isoformat()))
    return {"success": True, "message": "Enquiry submitted successfully"}


@app.post("/api/contact", status_code=201)
def create_contact(payload: ContactMessage):
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("INSERT INTO contact_messages (name, email, message, created_at) VALUES (?, ?, ?, ?)", (*payload.model_dump().values(), datetime.now(timezone.utc).isoformat()))
    return {"success": True, "message": "Message submitted successfully"}


@app.post("/api/admissions/enquiry", status_code=201)
def admission_enquiry(payload: Enquiry):
    return create_enquiry(payload)
