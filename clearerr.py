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

r = Radarr_API()
print(json.dumps(r.get_api_query("queue", [18]), indent=4))

print()

print(json.dumps(r.get_api_query("movie"), indent=4))

# print(json.dumps(r.delete_movie(""), indent=4))