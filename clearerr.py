import sys
import os

# Add lib directory to path
lib_path = os.path.join(os.path.dirname(__file__), 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

# from plex_api import *
from obj.library_obj import Library
from obj.media_obj import *
import json
from api.plex_api import Plex_API 

def jprint(input: str) -> None:
    print(json.dumps(input, indent=4))

print("From Plex")
l = Library()
l.build_from_plex()
print(l)

print('From Jellyfin')
jl = Library()
jl.build_from_jellyfin()
print(jl)

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

