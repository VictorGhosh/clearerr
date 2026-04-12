import os
import requests
import json
import logging
log = logging.getLogger(__name__)

TMDB_TOKEN = os.environ.get("TMDB_TOKEN")
BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p/" + os.environ.get("IMAGE_SIZE")

class Tmdb_API:

    def __init__(self, api_key=TMDB_TOKEN):
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }

    def _get_resp(self, endpoint, params=None) -> json:
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

if __name__ == "__main__":
    t = Tmdb_API()
    print(t.get_poster_url('28415', 'movie'))