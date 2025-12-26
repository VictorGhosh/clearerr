import os
import requests
import json

JELLYFIN_IP = os.environ.get("JELLYFIN_IP")
JELLYFIN_KEY = os.environ.get("JELLYFIN_KEY")

BASE_URL = f"http://{JELLYFIN_IP}:8096"

class Jellyfin_API:
    def __init__(self, base_url=BASE_URL, api_key=JELLYFIN_KEY):
        self.base_url = base_url
        self.api_key = api_key

        self.headers = {
            "X-Emby-Token": self.api_key,
            "Content-Type": "application/json"
        }

    def _get_resp(self, endpoint, params=None) -> json:
        url = f"{self.base_url}{endpoint}"
        
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making Jellyfin API request: {e}")
            return None

    def get_api_query(self, query, params={}) -> json:
        query = query.strip().lower()

        match query:
            # all top-level libraries
            case 'virtualfolders':
                return self._get_resp("/Library/VirtualFolders")
            
            # all users includes id and name
            case 'users':
                return self._get_resp("/Users")

            # media items in a virtual folder requires {'parent_id': x }, most in {'Items': []}
            case 'items':
                final_params = {
                    "ParentId": params['parent_id'],
                    "Recursive": True,
                    "Fields": "Path,ProviderIds,UserData", # FIXME UserData not working might need user
                    "IncludeItemTypes": "Movie,Series,Season" # no "Episode"
                }
                final_params.update(params)
                return self._get_resp("/Items", params=final_params)
             
            # playlists owned by user, requires {'user_id': x} most in {'Items': []}
            case 'user/items':
                final_params = {
                    "UserId": params['user_id'],
                    "IncludeItemTypes": "Playlist",
                    "Recursive": True
                }
                return self._get_resp(f"/Users/{params['user_id']}/Items", params=final_params)
            
            # items in user playlist, requires {'playlist_id': x, 'user_id': y}
            case 'playlist/items':
                return self._get_resp(f"/Playlists/{params['playlist_id']}/Items", params={"UserId": params['user_id']})