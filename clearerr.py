# Start imports and enviroment

import sys
import os
import logging

# Add lib directory to path don't lose imports (maintine order of imports)
lib_path = os.path.join(os.path.dirname(__file__), 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

import json
from obj.library_obj import Library

# Logging setup
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Shush requests http connection noises
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

log = logging.getLogger(__name__)

# End imports and enviroment

log.info("Required pyhton libraries loaded")
log.info("Starting main execution...")

# Build from plex
log.info("Building library object from Plex...")
pl = Library()
pl.build_from_plex()
log.info("Completed building from Plex")
log.debug(pl)

# Build from jellyfin
log.info('Building library object from Jellyfin')
jl = Library()
jl.build_from_jellyfin()
log.info("Completed building from Jellyfin")
log.debug(jl)

# TODO: Validate the two libraries
# print(f"Plex lib == Jellyfin lib: {(pl == jl)}")





'''active development'''

def jprint(input: str) -> None:
    print(json.dumps(input, indent=4))

from api.os_storage import *
o = OS_Storage()

print(o.exists("/data/media/movies/Fantastic Mr. Fox (2009)/Fantastic Mr. Fox (2009) Bluray-1080p.mp4"))
size = o.get_size("/data/media/movies/Fantastic Mr. Fox (2009)/Fantastic Mr. Fox (2009) Bluray-1080p.mp4")
print(human_size(size))

print(o.exists("/data/media/tv/It's Always Sunny in Philadelphia (2005) {tvdb-75805}"))
size = o.get_size("/data/media/tv/It's Always Sunny in Philadelphia (2005) {tvdb-75805}")
print(human_size(size))

'''end active development'''


# Plex testing
# p = Plex_API()
# for lib in p.get_api_query('get_libraries')['Directory']:
#     if lib['title'] == 'Movies':
#         for media in p.get_api_query('get_library_items', {'section_id': lib['key']})['Metadata']:
#         #     print(p.get_path(media['ratingKey']))
#         #     for season in p.get_api_query('get_children', {'rating_key': media['ratingKey']}):
#         #         print(f"--season: {p.get_path(season['ratingKey'])}")

#             jprint(p.get_api_query('get_leaves', {'rating_key': media['ratingKey']}))

# jellyfin library data
# from api.jellyfin_api import Jellyfin_API
# j = Jellyfin_API()
# for vf in j.get_api_query('VirtualFolders'): 
#     if vf['Name'] == 'Movies' or vf['Name'] == 'Shows':
#         jprint(j.get_api_query('items', {'parent_id': vf['ItemId']}))
#         pass

# Do not delete playlists
# for usr in j.get_api_query('users'):
#     for list in j.get_api_query('user/items', {'user_id': usr['Id']})['Items']:
#         jprint(j.get_api_query('playlist/items', {'playlist_id': list['Id'], 'user_id': usr['Id']}))

log.info("Completed python program")