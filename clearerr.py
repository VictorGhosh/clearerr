# from plex_api import *
from obj.library_obj import Library
from obj.media_obj import *
import json

print("Calculating storage...", end=' ')
print("Warning: not implemented")

# None of the rest of the steps will happen if storage is not below threshhold

print("Building library object (tautulli)...", end=' ')
l = Library()
l.init_from_tautulli()
print("Done")

print("Building library object (plex)...", end=' ')
print("Warning: not implemented")

print("Building library object (jellyfin)...", end=' ')
print("Warning: not implemented")

print("Validating object equivalency (plex-tautulli)...", end=' ')
print("Warning: not implemented")

print("Validating object equivalency (jellyfin-tautulli)...", end=' ')
print("Warning: not implemented")


# # j = Jellyfin_API()
# # for usr in j.get_users():
#     # print(j.get_user_playlist(usr['Id']))