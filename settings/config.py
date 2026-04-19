import os
from pathlib import Path
# from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# load_dotenv(BASE_DIR / ".env")

class Config:

    # App
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper() # INFO DEBUG
    LOG_SIZE_MB = int(os.environ.get("LOG_SIZE_MB", "5"))
    
    # Internal APIs
    PLEX_URL = os.environ.get("PLEX_URL") # "http://x.x.x.x:32400"
    PLEX_TOKEN = os.environ.get("PLEX_TOKEN")

    JELLYFIN_URL = os.environ.get("JELLYFIN_URL") # "http://x.x.x.x:8096"
    JELLYFIN_TOKEN = os.environ.get("JELLYFIN_TOKEN")
    
    TAUTULLI_URL = os.environ.get("TAUTULLI_URL") # "http://x.x.x.x:8181"
    TAUTULLI_KEY = os.environ.get("TAUTULLI_KEY")

    SEERR_URL = os.environ.get("SEERR_URL") # "http://x.x.x.x:5055"
    SEERR_KEY = os.environ.get("SEERR_KEY")

    # External APIs
    TMDB_TOKEN = os.environ.get("TMDB_TOKEN")
    TMDB_IMAGE_SIZE = os.environ.get("TMDB_IMAGE_SIZE", "w342") # w92, w154, w185, w342, w500, w780, original

    # Paths should not be changed
    _LOG_PATH = os.environ.get("_LOG_PATH", str(BASE_DIR / "logs" / "clearerr.log"))
    _DB_PATH = os.environ.get("_DB_PATH", str(BASE_DIR / "db" / "clearerr.db"))
    _RULES_PATH = os.environ.get("_RULES_PATH", str(BASE_DIR / "settings" / "rules.yaml"))
    _PATH_TO_MEDIA = os.environ.get("_PATH_TO_MEDIA", "/media") # map /media

    # FIXME These are optional but do not need to be private
    _MOVIE_DIR = os.environ.get("_MOVIE_DIR", "/movies")
    _SHOWS_DIR = os.environ.get("_SHOWS_DIR", "/tv")


config = Config()