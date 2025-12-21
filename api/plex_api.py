import os
import requests
import json

PLEX_IP     = os.environ.get("PLEX_IP")
PLEX_TOKEN  = os.environ.get("PLEX_TOKEN")

BASE_URL = f"http://{PLEX_IP}:32400"

class Plex_API():

    def __init__(self, base_url=BASE_URL, api_key=PLEX_TOKEN):
        self.base_url = base_url
        self.api_key = api_key

    def _get_resp(self, endpoint=None, params={}) -> json:
        # plex default is xml not json
        headers = {
            "X-Plex-Token": self.api_key,
            "Accept": "application/json" 
        }

        # http requesting and network error handling    
        try:
            resp = requests.get(f"{self.base_url}{endpoint}", headers=headers, params=params, timeout=15)
            resp.raise_for_status()

        except requests.exceptions.RequestException as e:
            print(f"Error making Plex API request: {e}")
            return None
        
        # json parsing and structure related errors
        try:
            data = resp.json()
            return data.get('MediaContainer', data)
        
        except json.JSONDecodeError:
            print("Invalid JSON returned from Plex.")
            return None

    def get_api_query(self, query, params={}) -> json:
        query = query.strip().lower()

        match query:
            # Library names, ids, path, etc. under {'Directory': []}
            case "get_libraries":
                return self._get_resp("/library/sections")
            
            # Items in library including path and lastwached. requires params={'section_id': 'x'}
            case "get_library_items":
                return self._get_resp(f"/library/sections/{params['section_id']}/all")

            # NOTE: Not currently needed most info can come from a single get_library_items call
            # Full metadata for media. requires params={'rating_key': 'x'}
            case "get_metadata":
                data = self._get_resp(f"/library/metadata/{params['rating_key']}")
                return data.get('Metadata', [{}])[0] if data else None

            case catchall:
                raise ValueError(f"Unknown api query: {catchall}")