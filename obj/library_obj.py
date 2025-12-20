from api.tautulli_api import Tautulli_API
from api.radarr_api import Radarr_API
from obj.media_obj import *

class Library():
    def __init__(self):
        self.media = []

        self._t = Tautulli_API()
        # self.raw_tautilli = 

        self._r = Radarr_API()
        self.raw_radarr = self._r.get_api_query("movie")

    # def _generate_tautulli_data(self)

    # def init_from_tautulli(self) -> None:
    #     tlibraries = self._t.get_library_ids()

    #     for raw_m in self._t.get_library(tlibraries['Movies']):
    #         metadata = self._t.get_metadata(raw_m['rating_key'])
    #         m = Movie(metadata['title'])
    #         m.populate_from_tautilli(metadata)
    #         self.media.append(m)

    #     for raw_s in self._t.get_library(tlibraries['TV Shows']):
    #         metadata = self._t.get_metadata(raw_s['rating_key'])
    #         s = Show(metadata['title'])
    #         s.populate_from_tautilli(metadata)

    #         for season_meta in self._t.get_children_metadata(s.rating_key):
    #             season = Season(season_meta['title'])
    #             season.populate_from_tautilli(season_meta)
    #             s.seasons.append(season)
            
    #         self.media.append(s)        

    def __str__(self):
        res = ''
        for m in self.media:
            res += f'{str(m)}\n'
        return res