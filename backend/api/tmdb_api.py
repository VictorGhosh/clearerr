import requests
import json
from settings.config import config
import logging
log = logging.getLogger(__name__)

BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p/" + config.TMDB_IMAGE_SIZE

class Tmdb_API:

    def __init__(self, api_key=config.TMDB_TOKEN):
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }

    def _get_resp(self, endpoint, params=None) -> dict | None:
        url = f"{BASE_URL}{endpoint}"
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            log.error(f"Error making TMDB API request: {e}")
            return None

    def get_poster_url(self, tmdb_id, media_type: str) -> str | None:
        '''media_type should be movie or tv'''
        data = self._get_resp(f"/{media_type}/{tmdb_id}")
        if not data or not data.get('poster_path'):
            log.error(f"No poster found for {media_type} tmdb_id={tmdb_id}")
            return None
        return f"{IMG_BASE}{data['poster_path']}"

    def get_poster_url_by_imdb(self, imdb_id, media_type: str) -> str | None:
        '''Fallback when only an IMDB id is available. media_type should be movie or tv'''
        data = self._get_resp(f"/find/{imdb_id}", params={"external_source": "imdb_id"})
        if not data:
            log.error(f"No TMDB find response for imdb_id={imdb_id}")
            return None

        results_key = "movie_results" if media_type == "movie" else "tv_results"
        results = data.get(results_key) or []
        if not results or not results[0].get('poster_path'):
            log.error(f"No poster found via imdb_id={imdb_id} ({media_type})")
            return None
        return f"{IMG_BASE}{results[0]['poster_path']}"