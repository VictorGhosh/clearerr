from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import sqlite3
import os
import time
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

def datetimeformat(value):
    return datetime.fromtimestamp(value).strftime("%m-%d-%y")

templates.env.filters["datetimeformat"] = datetimeformat

def get_db():
    db_path = os.path.join(BASE_DIR, "..", "db", "clearerr.db")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def obfuscate_email(email: str) -> str:
    if not email or email == "unknown":
        return "unknown"
    local = email.split("@")[0]
    if len(local) <= 3:
        return local[0] + "*" * (len(local) - 1)
    return local[:3] + "*" * (min(len(local) - 5, 5)) + local[-2:]

@app.get("/")
def index(request: Request):
    conn = get_db()
    media = conn.execute("""
        SELECT m.*, e.exempted_at, e.exempted_by, r.queued_at, r.queued_by
        FROM media m
        LEFT JOIN exempt e ON e.rating_key = m.rating_key
        LEFT JOIN removal_queue r ON r.rating_key = m.rating_key
        ORDER BY title
    """).fetchall()
    conn.close()
    return templates.TemplateResponse(request=request, name="index.html", context={"media": media})

@app.get("/search")
def search(request: Request, q: str = "", sort: str = "title"):
    conn = get_db()
    order = "title" if sort == "title" else "deletion_score ASC"
    media = conn.execute(f"""
        SELECT m.*, e.exempted_at, e.exempted_by, r.queued_at, r.queued_by
        FROM media m
        LEFT JOIN exempt e ON e.rating_key = m.rating_key
        LEFT JOIN removal_queue r ON r.rating_key = m.rating_key
        WHERE m.title LIKE ?
        ORDER BY {order}
    """, (f"%{q}%",)).fetchall()
    conn.close()
    return templates.TemplateResponse(request=request, name="partials/media_grid.html", context={"media": media})

@app.get("/exempt/confirm/{rating_key}")
def exempt_confirm(request: Request, rating_key: str):
    conn = get_db()
    item = conn.execute("""
        SELECT m.*, e.exempted_at 
        FROM media m
        LEFT JOIN exempt e ON e.rating_key = m.rating_key
        WHERE m.rating_key = ?
    """, (rating_key,)).fetchone()
    conn.close()
    return templates.TemplateResponse(request=request, name="exempt_confirm.html", context={"item": item})

@app.post("/exempt/toggle/{rating_key}")
def exempt_toggle(request: Request, rating_key: str):
    user = obfuscate_email(request.headers.get("Cf-Access-Authenticated-User-Email", "unknown"))
    conn = get_db()
    existing = conn.execute("SELECT rating_key FROM exempt WHERE rating_key = ?", (rating_key,)).fetchone()
    if existing:
        conn.execute("DELETE FROM exempt WHERE rating_key = ?", (rating_key,))
    else:
        conn.execute("INSERT INTO exempt (rating_key, exempted_at, exempted_by) VALUES (?, ?, ?)", (rating_key, int(time.time()), user))
    conn.commit()
    conn.close()
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)

@app.get("/remove/confirm/{rating_key}")
def remove_confirm(request: Request, rating_key: str):
    conn = get_db()
    item = conn.execute("""
        SELECT m.*, e.exempted_at, r.queued_at
        FROM media m
        LEFT JOIN exempt e ON e.rating_key = m.rating_key
        LEFT JOIN removal_queue r ON r.rating_key = m.rating_key
        WHERE m.rating_key = ?
    """, (rating_key,)).fetchone()
    conn.close()
    return templates.TemplateResponse(request=request, name="remove_confirm.html", context={"item": item})

@app.post("/remove/{rating_key}")
def remove_media(request: Request, rating_key: str):
    user = obfuscate_email(request.headers.get("Cf-Access-Authenticated-User-Email", "unknown"))
    conn = get_db()
    existing = conn.execute("SELECT rating_key FROM removal_queue WHERE rating_key = ?", (rating_key,)).fetchone()
    if existing:
        conn.execute("DELETE FROM removal_queue WHERE rating_key = ?", (rating_key,))
    else:
        conn.execute("INSERT INTO removal_queue (rating_key, queued_at, queued_by) VALUES (?, ?, ?)", (rating_key, int(time.time()), user))    
    conn.commit()
    conn.close()
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)