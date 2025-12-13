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
    metadata = t.get_metadata(raw_m['rating_key'])
    
    m = Movie(metadata['title'])
    m.populate_from_tautilli(metadata)
    
    print(m)
    # print(json.dumps(metadata, indent=4))

# for s in t.get_library(tlibrays['TV Shows']):
    # print(json.dumps(t.get_metadata(s['rating_key']), indent=4))
    # print(json.dumps(t.get_children_metadata(s['rating_key']), indent=4))

# j = Jellyfin_API()
# for usr in j.get_users():
    # print(j.get_user_playlist(usr['Id']))