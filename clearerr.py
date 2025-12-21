# from plex_api import *
from obj.library_obj import Library
from obj.media_obj import *
import json

from api.radarr_api import Radarr_API

# print("Calculating storage...", end=' ')
# print("Warning: not implemented")

# # None of the rest of the steps will happen if storage is not below threshhold

# print("Building library object (tautulli)...", end=' ')
# l = Library()
# l.init_from_tautulli()
# print("Done")

# print("Building library object (plex)...", end=' ')
# print("Warning: not implemented")

# print("Building library object (jellyfin)...", end=' ')
# print("Warning: not implemented")

# print("Validating object equivalency (plex-tautulli)...", end=' ')
# print("Warning: not implemented")

# print("Validating object equivalency (jellyfin-tautulli)...", end=' ')
# print("Warning: not implemented")

# r = Radarr_API()
# print(json.dumps(r.get_api_query("queue", [18]), indent=4))

# print()

# print(json.dumps(r.get_api_query("movie"), indent=4))

# print(json.dumps(r.delete_movie(""), indent=4))

# from api.tautulli_api import Tautulli_API
# t = Tautulli_API()

# for lib in t.get_api_query("get_libraries"):
#     if lib['section_name'] == 'Movies' or lib['section_name'] == 'TV Shows':
#         for media in t.get_api_query('get_library_media_info', params={'section_id': lib['section_id']}):            

#             foo = t.get_api_query('get_metadatajs', {'rating_key': media['rating_key']})
#             if foo != {}:
#                 print(f"META--{foo}")
#             # print(t.get_path(media['rating_key']))

from api.plex_api import Plex_API

p = Plex_API()
for lib in p.get_api_query('get_libraries')['Directory']:
    if lib['title'] == 'Movies' or lib['title'] == 'TV Shows':
        print(json.dumps(p.get_api_query('get_library_items', {'section_id': lib['key']}), indent=4))

print(json.dumps(p.get_api_query('get_metadata', {'rating_key': '391'}), indent=4))