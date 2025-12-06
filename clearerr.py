import os
import requests
import xml.etree.ElementTree as ET

PLEX_IP     = os.environ.get("PLEX_IP")
PLEX_TOKEN  = os.environ.get("PLEX_TOKEN")

PLEX_URL = f"http://{PLEX_IP}:32400"

plex_movie_data = {} # { move_name: lastwatched }
plex_show_data  = {} # { showname: { season: lastwatched } } 

def get_resp(url: str):
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp
    else:
        print(f"ERROR {resp.status_code} for {url}")
        print(resp.text[:200])  # first 200 chars


# Begin plex data collection 
# Get library sections
resp = get_resp(f"{PLEX_URL}/library/sections?X-Plex-Token={PLEX_TOKEN}")
root = ET.fromstring(resp.content)

# Find sections
movies_key = None
for elem in root.findall('Directory'):
    
    if elem.attrib['type'] == 'movie':
        movies_key = elem.attrib['key']
    
    elif elem.attrib['type'] == 'show':
        tv_key = elem.attrib['key']

# Get movies
if movies_key:
    resp = get_resp(f"{PLEX_URL}/library/sections/{movies_key}/all?X-Plex-Token={PLEX_TOKEN}")
    root = ET.fromstring(resp.content)
    
    for movie in root.findall('Video'):
        title = movie.attrib.get('title')
        last_viewed = movie.attrib.get('lastViewedAt')  # timestamp string (linux)
        plex_movie_data[title] = last_viewed
else:
    raise ValueError("Failed to parse movie key in plex response")

# Get shows 
if tv_key:
    resp = get_resp(f"{PLEX_URL}/library/sections/{tv_key}/all?X-Plex-Token={PLEX_TOKEN}")
    root = ET.fromstring(resp.content)
    for show in root.findall('Directory'):
        show_title = show.attrib.get('title')
        show_key = show.attrib.get('key')
        
        plex_show_data[show_title] = {}

        # Get seasons for the show
        resp_seasons = get_resp(f"{PLEX_URL}{show_key}?X-Plex-Token={PLEX_TOKEN}")
        seasons_root = ET.fromstring(resp_seasons.content)
        
        for season in seasons_root.findall('Directory'):
            season_title = season.attrib.get('title')
            season_key = season.attrib.get('key')

            # some shows have an "all episodes" psudo season. ignore it
            if (season_title == "All episodes"):
                continue

            # Get episodes for the season to compute last watched
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
            
            plex_show_data[show_title][season_title] = last_watched
else:
    raise ValueError("Failed to parse shows key in plex response")

print(f"All plex movies:\n{plex_movie_data}")
print(f"All plex shows:\n{plex_show_data}")

# End plex data collection