import os
import requests
import json

JELLYFIN_IP = os.environ.get("JELLYFIN_IP")
JELLYFIN_KEY = os.environ.get("JELLYFIN_KEY")
JELLYFIN_LIST_NAME = os.environ.get("JELLYFIN_LIST_NAME")

BASE_URL = f"http://{JELLYFIN_IP}:8096"

class Jellyfin_API:
    def __init__(self, base_url=BASE_URL, api_key=JELLYFIN_KEY):
        self.base_url = base_url
        
        self.headers = {
            'X-Emby-Authorization': f'MediaBrowser Client="Python Client", Device="Automation Script", Version="1.0", Token="{api_key}"',
            'Accept': 'application/json'
        }

    def _get_resp(self, path: str, params: dict=None, user_id: str=None) -> json:
        '''
        Handles the http request, its errors, as well as json conversion errors
        
        :param path: api path appended to base url
        :type path: str
        :param params: needed apu paramaters
        :type params: dict
        :param user_id: if required, i.e. not looking for items
        :type user_id: str
        :return: raw response
        :rtype: Any
        '''
        full_url = f"{self.base_url}/Users/{user_id}/{path}" if path.startswith("Items") else f"{self.base_url}/{path}"
        
        # http requesting and network error handling
        try:
            # authentication in the headers
            resp = requests.get(full_url, params=params, headers=self.headers, timeout=15)
            resp.raise_for_status() 
        
        except requests.exceptions.Timeout:
            print(f"Jellyfin API request timed out for {path}.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"HTTP Error calling Jellyfin API for {path}: {e}")
            return None

        # json parsing and structure related errors
        try:
            return resp.json()
            
        except json.JSONDecodeError as e:
            print(f"Invalid JSON returned from {path}: {e}")
            print(f"Raw response: {resp.text[:500]}...")
            return None
        except KeyError as e:
            print(f"Jellyfin response structure error (missing key: {e}).")
            return None

    def get_users(self) -> list:
        '''
        get the list of of each all active users data dictonaries.
        
        :return: list of all user data
        :rtype: list
        '''
        path = "Users"
        data = self._get_resp(path=path) 

        if data is None:
            return []
        
        return data
    
    def get_user_playlist(self, user_id: str, list_name: str=JELLYFIN_LIST_NAME) -> list:
        '''
        Get all media items contained in a given playlist owned by a given user.
        This method could be, and was, split into 3 seperate ones for each of the API
        requests. Splitting it up would make this more useable but I put them together
        because as it stands my only use case is to get the do not delete lists. 
        
        :param user_id: target user/playlist owner
        :type user_id: str
        :param list_name: user given name of target list. defaults to .env value
        :type list_name: str
        :return: data on items in target playlist
        :rtype: list
        '''
        # 1. get the list group ids
        group_path = f"Users/{user_id}/Items" 
        group_params = {
            'IncludeItemTypes': 'Playlist',
            'Limit': 10000
        }
        group_data = self._get_resp(group_path, group_params)

        if group_data is None:
            print(f"Failed to get list group ids for user: {user_id}")
            return []
        
        # find the id of the playlists group based on its name
        playlists_group_id = None
        for g in group_data['Items']:
            if g['Name'] == "Playlists":
                playlists_group_id = g['Id']
                break
        
        if playlists_group_id is None:
            print(f"Failed to find playlists group for user: {user_id}")
            return []
        
        # 2. get lists in the "playlist" group
        lists_params = {
            'UserId': user_id,
            'ParentId': playlists_group_id,
            'Limit': 10000          
        }
        playlists_data = self._get_resp("Items", lists_params, user_id)
        
        if playlists_data is None:
            print(f"Failed to get playlists for group: {playlists_group_id}")
            return []

        # to avoid typos as much as we can
        target_playlist = list_name.replace(" ","").lower()
        
        found_playlists = []
        for p in playlists_data['Items']:
            if p['Name'].replace(" ","").lower() == target_playlist:
                found_playlists.append(p)

        if found_playlists == []:
            print(f"Error: Missing requested playlist for user: {user_id}")
            return []

        # to many matches we cannot be sure, return nothing
        if len(found_playlists) > 1:
            print(f"Error: Multiple playlists match for user: {user_id}\n{found_playlists}")
            return []

        # 3. get items in the found target playlist
        list_prams = {
            'ParentId': '8cf846c44575191ccbf73d5e7840df75',
            'Limit': 10000,
            'Fields': 'Path,MediaSources,Type,ProviderIds'
        }
        list_path = f"Users/{user_id}/Items"

        list_data = self._get_resp(list_path, list_prams)

        if list_data is None:
            print(f"Error: Failed to get contents of target playlist for user: {user_id}")
            return []

        return list_data["Items"]