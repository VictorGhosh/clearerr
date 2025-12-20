import os
import requests
import json

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

            # Full metadata for media. requires params={'rating_key': 'x'} where x is media rating key
            case 'get_metadata':
                params.update({'cmd': 'get_metadata'})
                print(self._get_resp({'rating_key': '69', 'cmd': 'get_metadata'}))
                return self._get_resp(params=params)

            # Not actually metadata but children basic. requires params={'rating_key': 'x'} where x is parent rating key
            case 'get_children_metadata':
                patams.update({'cmd': 'get_children_metadata', 'children_content_details': 1})
                return self._get_resp(patams=params)

            case _:
                raise ValueError(f"Unknown api query: {query}")

    def get_metadata(self, rating_key: str) -> dict:

        data = self._get_resp({'cmd': 'get_metadata', 'rating_key': rating_key})

        if data is None: 
            return {}
        
        return data

    # FIXME: This needs to be split, see get_path calling this many time; 2x api calls each when only one is needed
    def get_children_metadata(self, rating_key: str) -> list:
        '''
        Series will have children for each season this (probebly episodes past that) this will
        grab those using get_children_metadata api call. The response from the api is not super
        detailed and in consistant with the rest of the data so we then call get_metadata using
        the found rating key and return that instead. 
                
        :param rating_key: rating key of parent, current use case that is a season
        :type rating_key: str
        :return: list of metadata dicts for each child
        :rtype: list
        '''
        data = self._get_resp({'cmd': 'get_children_metadata', 'rating_key': rating_key, 'children_content_details': 1})

        if data is None: 
            return []

        child_keys = []
        for s in data['children_list']:
            if s['media_type'] == 'season' or s['media_type'] == 'episode':
                child_keys.append(s['rating_key'])
        
        res = []
        for k in child_keys:
            res.append(self.get_api_query('get_metadata', {'rating_key': k}))

        return res

    def get_path(self, rating_key: str) -> str:
        '''
        get the path for a media at rating key. Validates this path for shows by checking every
        season/eisode recursivly to make sure they are all in the same spot. will raise an error
        otherise. This is fairly intensive and will need to be done simiarly for plex and jellyfin.
        The plan is to only use when actually needed i.e. when deleting.

        FIXME:See above fix for get_children_metadata. AFTER that this also does not need to get
        meta data if we already have it e.g. movies

        FIXME: There is definitely a less time consuming method. not plex but maybe jellyfin. worst
        case with some parsing we could just read the file system itself. this could be uses to validate
        when needed
        '''
        meta = self.get_api_query('get_metadata', {'rating_key': rating_key})

        print(meta)

        if meta['media_type'] == 'movie':
            return meta['media_info'][0]['parts'][0]['file']
        
        # returns parent of episde, so season folder
        if meta['media_type'] == 'episode':
            return os.path.dirname(meta['media_info'][0]['parts'][0]['file'])

        # get each episode in season recursivly get its location. validate they are all the same
        if meta['media_type'] == 'season':
            paths = []
            for ep in self.get_children_metadata(rating_key):
                paths.append(self.get_path(ep['rating_key']))

            # only take unique paths and therine should be only one left else something is wrong
            paths = list(set(paths))
            if len(paths) != 1:
                raise ValueError(f"Bad path parsing found: {paths}")
            return paths[0]

        # same recursive logic as was used for season above but back out one
        if meta['media_type'] == 'show':
            paths = []
            for season in self.get_children_metadata(rating_key):
                paths.append(os.path.dirname(self.get_path(season['rating_key'])))

            paths = list(set(paths))
            if len(paths) != 1:
                raise ValueError(f"Bad path parsing found: {paths}")
            return paths[0]

