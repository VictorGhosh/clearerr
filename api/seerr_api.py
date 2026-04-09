import os
import requests
import json
import logging
log = logging.getLogger(__name__)

SEERR_IP = os.environ.get("SEERR_IP")
SEERR_KEY = os.environ.get("SEERR_KEY")

BASE_URL = f"http://{SEERR_IP}:5055/api/v1"

# http://SEERR_IP:5055/api-docs 
class Seerr_API:
    '''Seerr api mainly for removing media.
    NOTE: No implementation has been done for seasons yet. I have not found an endpoint that can make
    it work even though the seasons do have their own seerr ids.'''

    def __init__(self, base_url=BASE_URL, api_key=SEERR_KEY):
        self.base_url = base_url
        self.headers = {
            "X-Api-Key": api_key,
            "Content-Type": "application/json"
        }

    def _get_resp(self, endpoint, params=None) -> json:
        url = f"{self.base_url}{endpoint}"

        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            log.error("Seerr API request timed out.")
            return None
        except requests.exceptions.RequestException as e:
            log.error(f"Error making Seerr API request: {e}")
            return None
        except json.JSONDecodeError as e:
            log.error(f"Invalid JSON returned from Seerr: {e}")
            return None

    def _delete(self, endpoint) -> bool:
        url = f"{self.base_url}{endpoint}"
        try:
            resp = requests.delete(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            log.error(f"Error making Seerr DELETE request: {e}")
            return False

    def get_api_query(self, query, params={}) -> json:
        query = query.strip().lower()
        match query:
            case 'get_media':
                return self._get_resp("/media", params=params)  # {'take': -1} works for all one page?
            case 'get_media_by_id':
                return self._get_resp(f"/media/{params['id']}")
            case catchall:
                log.exception(f"Unknown api query: {catchall}")
                raise ValueError(f"Unknown api query: {catchall}")

    def find_by_external_id(self, rating_key, ids: dict):
        data = self.get_api_query('get_media', {'take': -1})
        if not data or not data.get('results'):
            log.error("No media returned from Seerr")
            return None
        for item in data['results']:
            if str(item.get('ratingKey')) != str(rating_key):
                continue

            # found a match, validate all ids that exist on either side
            mismatches = []
            if ids.get('tmdb') and item.get('tmdbId') and str(item['tmdbId']) != str(ids['tmdb']):
                mismatches.append(f"tmdb: expected {ids['tmdb']} got {item['tmdbId']}")
            if ids.get('tvdb') and item.get('tvdbId') and str(item['tvdbId']) != str(ids['tvdb']):
                mismatches.append(f"tvdb: expected {ids['tvdb']} got {item['tvdbId']}")
            if ids.get('imdb') and item.get('imdbId') and str(item['imdbId']) != str(ids['imdb']):
                mismatches.append(f"imdb: expected {ids['imdb']} got {item['imdbId']}")
            if mismatches:
                log.error(f"ID mismatch for rating_key {rating_key}: {', '.join(mismatches)}")
                return None
            return item
        log.error(f"Could not find media in Seerr with rating_key={rating_key}")
        return None

    def delete_media(self, seerr_id) -> bool:
        '''Delete media files then remove from Seerr. Works for both movies and shows.
        NOTE: class note about removing seasons'''
        if not self._delete(f"/media/{seerr_id}/file"):
            log.error(f"File deletion failed for seerr id {seerr_id}, aborting Seerr removal")
            return False
        return self._delete(f"/media/{seerr_id}")


if __name__ == "__main__":
    s = Seerr_API()

    # m = s.find_by_external_id(rating_key=451, ids={'imdb': 'tt0887883', 'tmdb': '4944', 'tvdb': '1147'})
    media = s.find_by_external_id(rating_key=1165, ids={'imdb': 'tt5348176', 'tmdb': '73107', 'tvdb': '333072'})
    # season = s.get_season_seerr_id(media, 2)
    
    print(s.delete_media(media['id']))