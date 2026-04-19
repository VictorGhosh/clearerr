import os
from pathlib import Path
# from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# load_dotenv(BASE_DIR / ".env")

class Config:

    # App
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper() # INFO DEBUG
    LOG_SIZE_MB = int(os.environ.get("LOG_SIZE_MB", "5"))
    
    # Paths should not be changed just mapped (do logs and db need to be mapped?)
    LOG_PATH = os.environ.get("LOG_PATH", str(BASE_DIR / "logs" / "clearerr.log"))
    DB_PATH = os.environ.get("DB_PATH", str(BASE_DIR / "db" / "clearerr.db"))
    RULES_PATH = os.environ.get("DB_PATH", str(BASE_DIR / "settings" / "rules.yaml"))
    
    # TODO: This needs to be cleaned up. Should be one requried for /mnt/user/data/media then movies and tv optional if not basic
    LIBRARY_ROOT = os.environ.get("LIBRARY_ROOT", "/mnt/user/") # in os_storage to append to plex paths 
    LIBRARY_SHARE = os.environ.get("LIBRARY_SHARE", "/mnt/user/data/media")
    PATH_TO_MOVIES = os.environ.get("PATH_TO_MOVIES", "/data/media/movies")
    PATH_TO_SHOWS = os.environ.get("PATH_TO_SHOWS", "/data/media/tv")
    # REPLACESES ABOVE
    _PATH_TO_MEDIA = os.environ.get("_PATH_TO_MEDIA", "/media") # /mnt/user/data/media
    
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


config = Config()