import os
import requests
import json

RADARR_IP = os.environ.get("RADARR_IP")
RADARR_KEY = os.environ.get("RADARR_KEY")

BASE_URL = f"http://{RADARR_IP}:7878/api/v3"

class Radarr_API:
    def __init__(self, base_url=BASE_URL, api_key=RADARR_KEY):
        self.base_url = base_url
        self.api_key = api_key

    def _get_resp(self, endpoint=None) -> json:
        headers = {"X-Api-Key": self.api_key}
        
        # http requesting and network error handling
        try:
            resp = requests.get(f"{self.base_url}{endpoint}", headers=headers, timeout=15)
            resp.raise_for_status() 
            
        except requests.exceptions.Timeout:
            print("Error making API request: Request timed out.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {e}")
            return None
        
        # json parsing and structure related errors
        try:
            data = resp.json()
            return data
        
        except json.JSONDecodeError as e:
            print(f"Invalid JSON returned: {e}")
            print(f"Raw response: {resp.text[:500]}...")
            return None
        except KeyError as e:
            print(f"Radarr response structure error (missing key: {e}).")
            print(f"Raw data: {data}")
            return None

    def get_api_query(self, query, params={}) -> json:
        '''
        get a response to api query.
        valid queries:
        filesystem/mediafiles - no params
        movie - "tmdbId" for single movie no params for all
        queue - [movieIds] for specific movieIds no params for all

        :param query: Description
        :param params: Description
        :rtype: jsons
        '''
        query = query.strip().lower()

        match query:
            # all movies and their paths
            case "filesystem/mediafiles":
                return self._get_resp("/filesystem/mediafiles?path=%2Fdata%2Fmedia%2Fmovies")
            
            # basically all movie data; paths, ids, original and new names etc.
            case "movie":
                if "tmdbId" in params:
                    return self._get_resp(f"/movie?tmdbId={params['tmdbId']}&excludeLocalCovers=false")
                return self._get_resp("/movie")

            case "queue":
                final_paramaters = ""
                
                if "movieIds" in params:
                    final_paramaters = "?"
                    for p in params['movieIds']:
                        final_paramaters += f"movieIds={p}&"

                    final_paramaters = final_paramaters[:-1] # remove last &
        
                return self._get_resp(f"/queue{final_paramaters}")

            case catchall:
                raise ValueError(f"Unknown api query: {catchall}")


    def delete_movie(self, movie_id: str):
        '''
        Delete and unmonitor movie from radarr and media folder. Does not remove from
        download client and whether or not seerr will re-request is unknown
        
        :param movie_id: radarr movie id. Not a standardized number just the radarr one
        :type movie_id: str
        '''
        headers = {"X-Api-Key": self.api_key}
        endpoint = f"/movie/{movie_id}?deleteFiles=true&addImportExclusion=false"

        try:
            resp = requests.delete(f"{self.base_url}{endpoint}", headers=headers, timeout=15)
            resp.raise_for_status() 
        except requests.exceptions.Timeout:
            print("Error making API request: Request timed out.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {e}")
            return None

        return resp