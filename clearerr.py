# from plex_api import *
from api.tautulli_api import Tautulli_API
from api.jellyfin_api import Jellyfin_API
from obj.library_obj import Library
from obj.media_obj import *
import json

l = Library()

# Pull data from tautulli to fill initial fill library
t = Tautulli_API()
tlibraries = t.get_library_ids()

for raw_m in t.get_library(tlibraries['Movies']):
    # metadata = t.get_metadata(raw_m['rating_key'])
    print(f"Movie: {json.dumps(t.get_path(raw_m['rating_key']), indent=4)}")
    # m = Movie(metadata['title'])
#     m.populate_from_tautilli(metadata)

#     print(m)
#     print(json.dumps(metadata, indent=4))

# for raw_s in t.get_library(tlibraries['TV Shows']):
#     metadata = t.get_metadata(raw_s['rating_key'])
    
#     s = Show(metadata['title'])
#     # s.populate_from_tautilli(metadata)

#     print(json.dumps(metadata, indent=4))


for show in t.get_library(tlibraries['TV Shows']):
    print(f"Show: {json.dumps(t.get_path(show['rating_key']), indent=4)}")
    for season in t.get_children_metadata(show['rating_key']):
        print(f"Season: {json.dumps(t.get_path(season['rating_key']), indent=4)}")
        # print(t.get_children_metadata(season['rating_key']))
        # for episode in t.get_children_metadata(season['rating_key']):
            # print(json.dumps(t.get_metadata(episode['rating_key'])))


# j = Jellyfin_API()
# for usr in j.get_users():
    # print(j.get_user_playlist(usr['Id']))