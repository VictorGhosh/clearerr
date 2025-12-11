# from plex_api import *
from tautulli_api import *

client = Tautulli_API()
library_ids = client.get_library_ids()
