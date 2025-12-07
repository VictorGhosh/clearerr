import os
import requests
import xml.etree.ElementTree as ET

DEBUG       = os.environ.get("DEBUG")
PLEX_IP     = os.environ.get("PLEX_IP")

PLEX_URL = f"http://{PLEX_IP}:32400"


class Plex_API():

    def __init__(self, plex_token: str):
        self.plex_token = plex_token
        self.movies = []
        self.shows  = []
        self.movies_key = None
        self.shows_key = None

        self._parse_keys() # sets movies_key and shows_key attrs
        self._parse_movies(self.movies_key) # sets movies attr
        self._parse_shows(self.shows_key) # sets shows sttr

    def _get_resp(self, url: str):
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp
        else:
            print(f"ERROR {resp.status_code} for {url}")
            print(resp.text[:200])

    def _parse_keys(self):
        # Get library sections  
        resp = self._get_resp(f"{PLEX_URL}/library/sections?X-Plex-Token={self.plex_token}")
        root = ET.fromstring(resp.content)

        # find sections
        for elem in root.findall('Directory'):

            if elem.attrib['type'] == 'movie':
                self.movies_key = elem.attrib['key']

            elif elem.attrib['type'] == 'show':
                self.shows_key = elem.attrib['key']

    def _parse_movies(self, movies_key):

        if movies_key:
            resp = self._get_resp(f"{PLEX_URL}/library/sections/{movies_key}/all?X-Plex-Token={self.plex_token}")
            root = ET.fromstring(resp.content)

            for movie in root.findall('Video'):
                title = movie.attrib.get('title')
                last_viewed = movie.attrib.get('lastViewedAt')
                date_added = movie.attrib.get('addedAt')

                # Get file path from further down
                part = movie.find("./Media/Part")
                if part is not None:
                    file_path = part.attrib.get("file")
                else:
                    file_path = None
                    print(f"Warning: Failed to parse file path for {title}")

                self.movies.append(Movie(title, file_path, date_added, last_viewed))
        else:
            raise ValueError("Failed to parse movie key in plex response")
        
        if (str(DEBUG) == "1"):
            print("Plex movie data")
        for i in self.movies:
            print(i)

    def _parse_shows(self, shows_key):
        if shows_key:
            resp = self._get_resp(f"{PLEX_URL}/library/sections/{shows_key}/all?X-Plex-Token={self.plex_token}")
            root = ET.fromstring(resp.content)
            for show in root.findall('Directory'):
                show_title = show.attrib.get('title')
                show_key = show.attrib.get('key')

                # get seasons
                season_objs = []
                resp_seasons = self._get_resp(f"{PLEX_URL}{show_key}?X-Plex-Token={self.plex_token}")
                seasons_root = ET.fromstring(resp_seasons.content)

                for season in seasons_root.findall('Directory'):
                    season_title = season.attrib.get('title')
                    season_key = season.attrib.get('key')
                    season_date = season.attrib.get('addedAt')

                    # some shows have an "all episodes" psudo season. ignore it
                    if (season_title == "All episodes"):
                        continue
                    
                    # get episodes for the season to compute last watched
                    resp_eps = self._get_resp(f"{PLEX_URL}{season_key}?X-Plex-Token={self.plex_token}")
                    eps_root = ET.fromstring(resp_eps.content)

                    last_viewed_list = [
                        int(ep.attrib.get('lastViewedAt'))
                        for ep in eps_root.findall('Video')
                        if ep.attrib.get('lastViewedAt')
                    ]

                    if last_viewed_list:
                        last_watched = max(last_viewed_list)
                    else:
                        last_watched = None

                    # get library path for each epsisode in season (seasons do not have paths from api)
                    ep_paths = []
                    for ep in eps_root.findall('Video'):
                        media = ep.find('Media')
                        if media is not None:
                            part = media.find('Part')
                            if part is not None:
                                file_path = part.attrib.get('file')
                                if file_path:
                                    ep_paths.append(file_path)

                    # get directory containing each. so one level up
                    season_dirs = {os.path.dirname(p) for p in ep_paths}
                    season_dir = next(iter(season_dirs))

                    # should only be one uniqie. more remaining means at least one episode is stored seperate 
                    if len(season_dirs) != 1:
                        print(f"Warning: Episode location mismatch for {show_title} - {season_title}")

                    season_objs.append(Season(season_title, season_dir, season_date, last_watched))

                # get show location. first check that all the seasons agree on path as again show does not have own location
                season_paths = []
                season_dates = []
                season_last_watched = []
                for i in season_objs:
                    season_paths.append(i.path)
                    season_dates.append(i.date_added)

                    # Only add to list if season has been watched before
                    if i.last_watched is not None:
                        season_last_watched.append(i.last_watched)

                # avoid errors when series has not been watched at all
                if not season_last_watched:
                    season_last_watched = None
                else:
                    last_watched = max(season_last_watched)

                show_dirs = {os.path.dirname(s) for s in season_paths}
                show_dir = next(iter(show_dirs))
                if len(show_dirs) != 1:
                    print(f"Warning: Season location mismatch for {show_title}")

                # show date added is set to newest added season
                show_obj = Show(show_title, show_dir, max(season_dates), last_watched, season_objs)
                self.shows.append(show_obj)

        else:
            raise ValueError("Failed to parse shows key in plex response")

        if (str(DEBUG) == "1"):
            print("Plex show data")
            for i in self.shows:
                print(i)


class _Media():
    def __init__(self, name: str, path: str, date_added: str, last_watched: str):
        self.name = name
        self.path = path
        self.date_added = date_added
        self.last_watched = last_watched

    def __str__(self):
        return f"{self.name} - added: {self.date_added} - watched: {self.last_watched} - path: {self.path}"


class Movie(_Media):
    def __init__(self, name: str, path: str, date_added: str, last_watched: int):
        super().__init__(name, path, date_added, last_watched)

    def __str__(self):
        return super().__str__()
    

class Season(_Media):
    def __init__(self, name: str, path: str, date_added: str, last_watched: int):
        super().__init__(name, path, date_added, last_watched)

    def __str__(self):
        return super().__str__()

class Show(_Media):
    def __init__(self, name: str, path: str, date_added: str, last_watched: int, seasons: list[Season]):
        super().__init__(name, path, date_added, last_watched)
        self.seasons = seasons

    def __str__(self):  
        seasons_str = ""
        for i in self.seasons:
            seasons_str += f"{i}, " 

        return f"{super().__str__()} - seasons: {seasons_str}"
