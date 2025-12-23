from obj.media_obj import *
from api.plex_api import Plex_API

import json

class Library():
    def __init__(self):
        self.media = []
        self._build_from_plex()

    def _build_from_plex(self) -> list:
        p = Plex_API()

        for lib in p.get_api_query('get_libraries')['Directory']:
            if lib['title'] == 'Movies' or lib['title'] == 'TV Shows':
                for media in p.get_api_query('get_library_items', {'section_id': lib['key']}):

                    # settings for movies only
                    if lib['title'] == 'Movies':
                        media_obj = Movie(media['title'])
                        media_obj.path = media['Media'][0]['Part'][0]['file']
                    
                    # settings for shows only
                    elif lib['title'] == 'TV Shows':
                        media_obj = Show(media['title'])

                        for c in p.get_api_query('get_children', {'rating_key': media['ratingKey']}):
                            season = Season(c['title'])
                            # TODO: set path when its better (see method fixme)

                            season.rating_key = c.get('ratingKey')
                            season.added_on = c.get('addedAt')
                            season.last_watched = c.get('lastViewedAt')

                            for i in c.get('Guid'):
                                id = i.get('id')
                                if id.startswith('tmdb://'):
                                    season.ids['tmdb'] = id.split('tmdb://')[-1]
                                elif id.startswith('tvdb://'):
                                    season.ids['tvdb'] = id.split('tvdb://')[-1] 
                            
                            media_obj.seasons.append(season)

                    # settings for both movies and shows
                    media_obj.rating_key = media.get('ratingKey')
                    media_obj.added_on = media.get('addedAt')
                    media_obj.last_watched = media.get('lastViewedAt') # json var exists there is value

                    for i in media.get('Guid'):
                        id = i.get('id')
                        if id.startswith('tmdb://'):
                            media_obj.ids['tmdb'] = id.split('tmdb://')[-1]
                        elif id.startswith('tvdb://'):
                            media_obj.ids['tvdb'] = id.split('tvdb://')[-1] 
                        elif id.startswith('imdb://'):
                            media_obj.ids['imdb'] = id.split('imdb://')[-1]

                    self.media.append(media_obj)

    def __str__(self):
        res = ''
        for m in self.media:
            res += f'{str(m)}\n'
        return res