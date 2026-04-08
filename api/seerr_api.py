import os

# XXX REMOVE THIS
import sys
lib_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)
# XXX

import requests
import json
import logging
log = logging.getLogger(__name__)

SEERR_IP = os.environ.get("SEERR_IP")
SEERR_KEY = os.environ.get("SEERR_KEY")

BASE_URL = f"http://{SEERR_IP}:5055/api/v1"

# http://SEERR_IP:5055/api-docs 
class Seerr_API:
    def __init__(self, base_url=BASE_URL, api_key=SEERR_KEY):
        self.base_url = base_url
        self.api_key = api_key

    def _get_resp(self, params=None) -> json:
        full_params = {
            'apikey': self.api_key, 
            'out': 'json'
        }
        if params:
            full_params.update(params)

        # http requesting and network error handling
        try:
            resp = requests.get(self.base_url, params=full_params, timeout=15)
            resp.raise_for_status()
        
        except requests.exceptions.Timeout:
            log.error("Error making API request: Request timed out.")
            return None
        except requests.exceptions.RequestException as e:
            log.error(f"Error making API request: {e}")
            return None
        
        # json parsing and structure related errors
        try:
            data = resp.json()
            
            return data['response']['data']        
        
        except json.JSONDecodeError as e:
            log.error(f"Invalid JSON returned: {e}")
            log.error(f"Raw response: {resp.text[:500]}...")
            return None
        except KeyError as e:
            log.error(f"Response structure error (missing key: {e}).")
            log.error(f"Raw data: {data}")
            return None

    def get_api_query(self, query, params={}): #-> json:
        query = query.strip().lower()

        match query:
            case 'media':
                return self._get_resp(params={'cmd': 'media'})
            case catchall:
                raise ValueError(f"Unknown api query: {catchall}")

if __name__ == "__main__":
    s = Seerr_API()

    print(s._get_resp(params={'cmd': 'media'}))
    # get /media
    # find target by ratingkey
    # validate using tmdbId, tvdbId, imdbId (one should be not null)
    # take the "id"
    # use /media/{id}/file to remove from partner (sonarr/radarr)
    # use /media/{id} to remove from seerr

    # shows can be found the same way but have seasons section. each season has an id.
    # we cannot lookup the seasons directly here must parse down from season