from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import sqlite3
import os
import time
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def datetimeformat(value):
    return datetime.fromtimestamp(value).strftime("%d-%m-%y")

templates.env.filters["datetimeformat"] = datetimeformat

def get_db():
    conn = sqlite3.connect(os.environ.get("DB_PATH"))
    conn.row_factory = sqlite3.Row  # makes rows like dicts
    return conn

@app.get("/")
def index(request: Request):
    conn = get_db()
    media = conn.execute("""
        SELECT m.*, e.exempted_at 
        FROM media m
        LEFT JOIN exempt e ON e.rating_key = m.rating_key
        ORDER BY title
    """).fetchall()
    conn.close()
    return templates.TemplateResponse(request=request, name="index.html", context={"media": media})

@app.get("/search")
def search(request: Request, q: str = "", sort: str = "title"):
    conn = get_db()
    order = "title" if sort == "title" else "deletion_score ASC"
    media = conn.execute(f"""
        SELECT m.*, e.exempted_at 
        FROM media m
        LEFT JOIN exempt e ON e.rating_key = m.rating_key
        WHERE m.title LIKE ?
        ORDER BY {order}
    """, (f"%{q}%",)).fetchall()
    conn.close()
    return templates.TemplateResponse(request=request, name="partials/media_grid.html", context={"media": media})

@app.post("/exempt/update")
async def update_exempt(request: Request):
    form = await request.form()
    checked_keys = set(form.getlist("exempt"))
    visible_keys = set(form.getlist("visible"))

    conn = get_db()
    
    existing = {row['rating_key'] for row in conn.execute("SELECT rating_key FROM exempt").fetchall()}

    # need to cut out invisible ones because html it looks like its unchecked
    newly_exempt = checked_keys - existing
    newly_unexempt = (existing & visible_keys) - checked_keys
    
    for rating_key in newly_exempt:
        conn.execute("""
            INSERT INTO exempt (rating_key, exempted_at)
            VALUES (?, ?)
        """, (rating_key, int(time.time())))
    
    for rating_key in newly_unexempt:
        conn.execute("DELETE FROM exempt WHERE rating_key = ?", (rating_key,))
    
    conn.commit()

    # get titles for confirmation page
    added = conn.execute(
        f"SELECT title FROM media WHERE rating_key IN ({','.join('?'*len(newly_exempt))})",
        list(newly_exempt)
    ).fetchall() if newly_exempt else []

    removed = conn.execute(
        f"SELECT title FROM media WHERE rating_key IN ({','.join('?'*len(newly_unexempt))})",
        list(newly_unexempt)
    ).fetchall() if newly_unexempt else []

    conn.close()
    
    return templates.TemplateResponse(request=request, name="confirm.html", context={
        "added": sorted(added, key=lambda r: r['title']),
        "removed": sorted(removed, key=lambda r: r['title'])
    })