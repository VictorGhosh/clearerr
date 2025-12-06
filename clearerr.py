import os
import requests
import xml.etree.ElementTree as ET


PLEX_IP     = os.environ.get("PLEX_IP")
PLEX_TOKEN  = os.environ.get("PLEX_TOKEN")

PLEX_URL = f"http://{PLEX_IP}:32400"


def get_resp(url: str):
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp
    else:
        print(f"Error: {response.status_code}")

# url = f"http://{PLEX_IP}:32400/library/sections?X-Plex-Token={PLEX_TOKEN}"

# response = requests.get(url)

# if response.status_code == 200:
#     print("Success! Library XML:")
#     print(response.text)
# else:
#     print(f"Error: {response.status_code}")

# Get library sections
resp = get_resp(f"{PLEX_URL}/library/sections?X-Plex-Token={PLEX_TOKEN}")
root = ET.fromstring(resp.content)

# Find Movies section
movies_key = None
for elem in root.findall('Directory'):
    if elem.attrib['type'] == 'movie':
        movies_key = elem.attrib['key']
        print("Movies library key:", movies_key)

# Get all movies
if movies_key:
    resp = get_resp(f"{PLEX_URL}/library/sections/{movies_key}/all?X-Plex-Token={PLEX_TOKEN}")
    root = ET.fromstring(resp.content)
    for movie in root.findall('Video'):
        title = movie.attrib.get('title')
        last_viewed = movie.attrib.get('lastViewedAt')  # timestamp string (linux)
        print(f"{title} - Last Watched: {last_viewed}")
