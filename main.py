from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/")
def index(request: Request):
    # eventually this comes from sqlite
    media = [
        {"title": "Breaking Bad", "poster": "https://image.tmdb.org/t/p/w200/ggFHVNu6YYI5L9pCfOacjizRGt.jpg", "exempt": False},
        {"title": "The Godfather", "poster": "https://image.tmdb.org/t/p/w200/3bhkrj58Vtu7enYsLePmd2e9UZ.jpg", "exempt": True},
    ]
    return templates.TemplateResponse("index.html", {"request": request, "media": media})