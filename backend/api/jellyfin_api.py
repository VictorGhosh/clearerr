import requests
from settings.config import config
import logging
log = logging.getLogger(__name__)

class Jellyfin_API:
    def __init__(self, base_url=config.JELLYFIN_URL, api_key=config.JELLYFIN_TOKEN):
        self.base_url = base_url
        self.api_key = api_key

        self.headers = {
            "X-Emby-Token": self.api_key,
            "Content-Type": "application/json"
        }

    def _get_resp(self, endpoint, params=None) -> dict | None:
        url = f"{self.base_url}{endpoint}"
        
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            log.error(f"Error making Jellyfin API request: {e}")
            return None

    def _post(self, endpoint, params=None) -> bool:
        url = f"{self.base_url}{endpoint}"
        try:
            resp = requests.post(url, headers=self.headers, params=params, timeout=15)
            resp.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            log.error(f"Error making Jellyfin POST request: {e}")
            return False

    def get_api_query(self, query, params={}) -> dict | None:
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

            case catchall:
                log.exception(f"Unknown api query: {catchall}")
                raise ValueError(f"Unknown api query: {catchall}")

    def refresh_item(self, jellyfin_id) -> bool:
        '''Trigger a metadata refresh for a specific item by Jellyfin item id.'''
        return self._post(f"/Items/{jellyfin_id}/Refresh")

    def get_saved_media_ids(self, exempt_string: str): #-> dict{str, list}:
        '''get all saved media matching the string. movies/shows and seasons in two lists'''
        exempt_string = exempt_string.lower().strip()
        # Lists shared with others can be parsed from other users. we don't need to do again
        found_lists = []
        saved_parents = []
        saved_seasons = []
    
        users = self.get_api_query("users")
        if users is None:
            log.error("Failed to fetch Jellyfin users")
            return {'parent_media': [], 'seasons': []}

        for user in users:
            user_items = self.get_api_query('user/items', {'user_id': user['Id']})
            if user_items is None:
                continue
            found = False

            for item in user_items["Items"]:
                if  exempt_string in item["Name"].lower().strip() and item['Id'] not in found_lists:
                    found_lists.append(item['Id'])
                    log.info(f"Found target target list: User: {user['Name']}, Name \"{item['Name']}\", ID: {item['Id']}")

                    playlist_items = self.get_api_query('playlist/items', {'playlist_id': item['Id'], 'user_id': user['Id']})
                    if playlist_items is None:
                        continue
                    for media in playlist_items['Items']:
                        
                        # If it has a season Id its show otherwise it is a movie
                        saved_item = media.get('SeasonId')
                        if saved_item is not None:
                            saved_parents.append(media.get('SeriesId'))
                            saved_seasons.append(saved_item)
                        else:
                            saved_parents.append(media.get('Id'))
        return {'parent_media': list(set(saved_parents)), 'seasons': list(set(saved_seasons))}