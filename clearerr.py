# from plex_api import *
from api.tautulli_api import Tautulli_API
from api.jellyfin_api import Jellyfin_API
import json

# client = Tautulli_API()
# library_ids = client.get_library_ids()
j = Jellyfin_API()

# for usr in j.get_users():
#     print(f"{usr['Name']}: {usr['Id']}")
#     for item in j.get_list_ids(usr['Id']):
#         print(item['Id'])
#         print(j.get_list_contents(item['Id'], usr['Id']))
        # print(item)

for usr in j.get_users():
    print(j.get_user_playlist(usr['Id']))


# print(j.get_list_contents('1071671e7bffa0532e930debee501d2e', 'dbdf147aa8384befb22ce1a48f790a0c'))