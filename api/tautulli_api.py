import os
import requests
import json

DEBUG = os.environ.get("DEBUG")
TAUTULLI_IP = os.environ.get("TAUTULLI_IP")
TAUTULLI_KEY = os.environ.get("TAUTULLI_KEY")

BASE_URL = f"http://{TAUTULLI_IP}:8181/api/v2"

class Tautulli_API:
    def __init__(self, base_url=BASE_URL, api_key=TAUTULLI_KEY):
        self.base_url = base_url
        self.api_key = api_key

    def _get_resp(self, params=None) -> json:
        '''
        Get response json data for tautulli api query with given params. This function
        is intended to handle all network and jsons parsing errors up to the full payload
        generally called 'data'.
        
        :param params: parameter field following tautulli api docs
        :return: json data as json type, payload only
        :rtype: json dict or None
        '''
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
            print("Error making API request: Request timed out.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error making Tautulli API request: {e}")
            return None
        
        # json parsing and structure related errors
        try:
            data = resp.json()
            
            # NOTE: seems like all the queries have this structure but pay attention
            return data['response']['data']        
        
        except json.JSONDecodeError as e:
            print(f"Invalid JSON returned: {e}")
            print(f"Raw response: {resp.text[:500]}...")
            return None
        except KeyError as e:
            print(f"Tautulli response structure error (missing key: {e}).")
            print(f"Raw data: {data}")
            return None

    def get_library_ids(self) -> dict:          
        data = self._get_resp(params={'cmd': 'get_libraries'})
        if data is None:
            return {}
        
        libraries = {}
        for lib in data:
            libraries[lib['section_name']] = lib['section_id']
        
        return libraries

    def get_library(self, lib_id: str) -> list:
        # length -1 is supposed to get all data but seems to be bugged
        data = self._get_resp(params={'cmd': 'get_library_media_info', 'section_id': lib_id, 'length': 99999})
        
        if data is None or 'data' not in data:
            return []

        return data['data']

    def get_metadata(self, rating_key: str) -> dict:
        data = self._get_resp({'cmd': 'get_metadata', 'rating_key': rating_key})

        if data is None: 
            return {}
        
        return data

    # We can take the rating keys from here and feed to get_metadata but the extra info is not needed for now
    def get_children_metadata(self, rating_key: str) -> list:
        data = self._get_resp({'cmd': 'get_children_metadata', 'rating_key': rating_key})

        if data is None: 
            return []

        season_keys = []
        for s in data['children_list']:
            if s['media_type'] == 'season':
                season_keys.append(s['rating_key'])
        
        res = []
        for k in season_keys:
            res.append(self.get_metadata(k))

        return res