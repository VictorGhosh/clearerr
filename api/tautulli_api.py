import os
import requests
import json
import logging
log = logging.getLogger(__name__)

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
            log.error("Error making API request: Request timed out.")
            return None
        except requests.exceptions.RequestException as e:
            log.error(f"Error making Tautulli API request: {e}")
            return None
        
        # json parsing and structure related errors
        try:
            data = resp.json()
            
            # NOTE: seems like all the queries have this structure but pay attention
            return data['response']['data']        
        
        except json.JSONDecodeError as e:
            log.error(f"Invalid JSON returned: {e}")
            log.error(f"Raw response: {resp.text[:500]}...")
            return None
        except KeyError as e:
            log.error(f"Tautulli response structure error (missing key: {e}).")
            log.error(f"Raw data: {data}")
            return None

    def get_api_query(self, query, params={}) -> json:
        query = query.strip().lower()

        match query:
            # Library names, ids, number of childen etc.
            case 'get_libraries':
                return self._get_resp(params={'cmd': 'get_libraries'})

            # Items in library. requires params={'section_id': 'x'} where x is library id
            case 'get_library_media_info':
                # remember -1 is broken so length needs to be high
                params.update({'cmd': 'get_library_media_info', 'length': 99999})
                return self._get_resp(params=params)['data']

            # NOTE: data only for watched items else returns {}
            # Full metadata for media. requires params={'rating_key': 'x'} where x is media rating key
            case 'get_metadata':
                params.update({'cmd': 'get_metadata'})
                return self._get_resp(params=params)

            # XXX: Depreciated/Not in use
            # Not actually metadata but children basic. requires params={'rating_key': 'x'} where x is parent rating key
            case 'get_children_metadata':
                params.update({'cmd': 'get_children_metadata', 'children_content_details': 1})
                return self._get_resp(params=params)
            
            # The only thing that works for watch data in the hell that is plex apis
            # The param needs to target what is watched so, to for show give show rating key as
            # 'grandparent_rating_key', season use 'parent_rating_key' and movie/episode use 'rating_key''  
            case 'get_history':
                params.update({'cmd': 'get_history', 'length': 1, 'order_column': 'date', 'order_dir': 'desc'})
                return self._get_resp(params=params)

            case catchall:
                raise ValueError(f"Unknown api query: {catchall}")
