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
        '''
        get a response to api query. valid queries:
        get_libraries - no params, most data is under {'Directory': []}
        get_library_items - params section_id for library id, most data is under {Metadata: []}
        get_metadata - params rating_key for target media
        get_children - params - rating_key for target parent media

        :param params: See docstring for whats needed
        '''
        query = query.strip().lower()

        match query:
            # Library names, ids, path, etc. under {'Directory': []}
            case 'get_libraries':
                return self._get_resp("/library/sections")
            
            # Items in library including path and lastwached. most in {Metadata: []} requires params={'section_id': 'x'}
            case 'get_library_items':
                return self._get_resp(f"/library/sections/{params['section_id']}/all")

            # Full metadata for media. requires params={'rating_key': 'x'}
            case 'get_metadata':
                return self._get_resp(f"/library/metadata/{params['rating_key']}")
            
            # Children data of media at rating_key, get more with metadata. requires params={'rating_key': 'x'}
            case 'get_children':
                return self._get_resp(f"/library/metadata/{params['rating_key']}/children").get('Metadata', [])

            case catchall:
                raise ValueError(f"Unknown api query: {catchall}")
            
    def get_path(self, rating_key: str):
        '''
        Get the path for any media. Path for shows and seasons is recursively validated for 
        all children because I do not trust plex.

        Previously I wrote logic to avoid repeat api calls for meta data when not neeeded. This
        would make it much more efficent but the code was more coplicated then I think its worth
        in terms of maintainability. This method should only be used when needed i.e. not for all
        media objects
        '''
        # The main source of un-needed api calls
        metadata = self.get_api_query('get_metadata', {'rating_key': rating_key})['Metadata'][0]
        media_type = metadata['type']
        
        if media_type == 'movie':
            return metadata['Media'][0]['Part'][0]['file']

        if media_type == 'episode':
            return os.path.dirname(metadata['Media'][0]['Part'][0]['file'])

        # seasons and shows recursively find path of children then validate all match
        paths = []

        if media_type == 'season':
            for episode in self.get_api_query('get_children', {'rating_key': metadata['ratingKey']}):
                paths.append(self.get_path(episode['ratingKey']))

        if media_type == 'show':
            for season in self.get_api_query('get_children', {'rating_key': metadata['ratingKey']}):
                paths.append(os.path.dirname(self.get_path(season['ratingKey'])))
        
        # validate paths are all the same
        paths = list(set(paths))
        if len(paths) != 1:
            raise ValueError(f"Bad path parsing found: {paths}")
        return paths[0]