import os
import requests
import xml.etree.ElementTree as ET
from media_structs import *

DEBUG       = os.environ.get("DEBUG")
PLEX_IP     = os.environ.get("PLEX_IP")
PLEX_TOKEN  = os.environ.get("PLEX_TOKEN")

PLEX_URL = f"http://{PLEX_IP}:32400"

plex_movies = []
plex_shows  = []

def get_resp(url: str):
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp
    else:
        print(f"ERROR {resp.status_code} for {url}")
        print(resp.text[:200])

# begin plex data collection 
# Get library sections
resp = get_resp(f"{PLEX_URL}/library/sections?X-Plex-Token={PLEX_TOKEN}")
root = ET.fromstring(resp.content)

# find sections
movies_key = None
for elem in root.findall('Directory'):
    
    if elem.attrib['type'] == 'movie':
        movies_key = elem.attrib['key']
    
    elif elem.attrib['type'] == 'show':
        tv_key = elem.attrib['key']

# get movies
if movies_key:
    resp = get_resp(f"{PLEX_URL}/library/sections/{movies_key}/all?X-Plex-Token={PLEX_TOKEN}")
    root = ET.fromstring(resp.content)
    
    for movie in root.findall('Video'):
        title = movie.attrib.get('title')
        last_viewed = movie.attrib.get('lastViewedAt')

        # Get file path from further down
        part = movie.find("./Media/Part")
        if part is not None:
            file_path = part.attrib.get("file")
        else:
            file_path = None
            print(f"Warning: Failed to parse file path for {title}")

        plex_movies.append(Movie(title, last_viewed, file_path))
else:
    raise ValueError("Failed to parse movie key in plex response")

# get shows 
if tv_key:
    resp = get_resp(f"{PLEX_URL}/library/sections/{tv_key}/all?X-Plex-Token={PLEX_TOKEN}")
    root = ET.fromstring(resp.content)
    for show in root.findall('Directory'):
        show_title = show.attrib.get('title')
        show_key = show.attrib.get('key')

        # get seasons
        season_objs = []
        resp_seasons = get_resp(f"{PLEX_URL}{show_key}?X-Plex-Token={PLEX_TOKEN}")
        seasons_root = ET.fromstring(resp_seasons.content)
        
        for season in seasons_root.findall('Directory'):
            season_title = season.attrib.get('title')
            season_key = season.attrib.get('key')

            # some shows have an "all episodes" psudo season. ignore it
            if (season_title == "All episodes"):
                continue

            # get episodes for the season to compute last watched
            resp_eps = get_resp(f"{PLEX_URL}{season_key}?X-Plex-Token={PLEX_TOKEN}")
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

            season_objs.append(Season(season_title, last_watched, season_dir))

        # get show location. first check that all the seasons agree on path as again show does not have own location
        season_paths = []
        for i in season_objs:
            season_paths.append(i.path)
        show_dirs = {os.path.dirname(s) for s in season_paths}
        show_dir = next(iter(show_dirs))
        if len(show_dirs) != 1:
            print(f"Warning: Season location mismatch for {show_title}")

        show_obj = Show(show_title, show_dir, season_objs)
        plex_shows.append(show_obj)
    
else:
    raise ValueError("Failed to parse shows key in plex response")

if (str(DEBUG) == "1"):
    print("Plex movie data")
    for i in plex_movies:
        print(i)

    print("Plex show data")
    for i in plex_shows:
        print(i)

# end plex data collection