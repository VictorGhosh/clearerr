from obj.media_obj import *
from api.plex_api import Plex_API
from api.jellyfin_api import Jellyfin_API

class Library():
    def __init__(self):
        self.movies = []
        self.shows = []

    def build_from_plex(self) -> None:
        if self.movies != [] or self.shows != []:
            raise ValueError(f"Media list is not empty")

        p = Plex_API()

        for lib in p.get_api_query('get_libraries')['Directory']:
            lib_type = lib['title']

            if lib_type == 'Movies' or lib_type == 'TV Shows':
                for media in p.get_api_query('get_library_items', {'section_id': lib['key']}):

                    if lib_type == 'Movies':
                        media_obj = Movie(media['title'])
                        media_obj.path = media['Media'][0]['Part'][0]['file']

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

                    if lib_type == 'Movies':
                        self.movies.append(media_obj)
                    elif lib_type == 'TV Shows':
                        self.shows.append(media_obj)

    def build_from_jellyfin(self) -> None:
        if self.movies != [] or self.shows != []:
            raise ValueError(f"Media list is not empty")

        j = Jellyfin_API()

        for vf in j.get_api_query('VirtualFolders'):

            lib_type = vf['Name']

            season_data = []

            if lib_type == 'Movies' or lib_type == 'Shows':
                for media in j.get_api_query('items', {'parent_id': vf['ItemId']})['Items']:

                    if lib_type == 'Movies':
                        media_obj = Movie(media['Name'])
                        media_obj.path = media.get('Path')
                        media_obj.ids = {'imdb': media.get('ProviderIds').get('Imdb'),
                                         'tmdb': media.get('ProviderIds').get('Tmdb')}
                        media_obj.jellyfin_id = media.get('Id')
                        self.movies.append(media_obj)

                    elif lib_type == 'Shows':

                        # jprint(media)
                        
                        if media['Type'] == 'Series':
                            media_obj = Show(media['Name'])
                            media_obj.ids = {'imdb': media.get('ProviderIds').get('Imdb'),
                                             'tmdb': media.get('ProviderIds').get('Tmdb'),
                                             'tvdb': media.get('ProviderIds').get('Tvdb')}
                            media_obj.jellyfin_id = media.get('Id')
                            self.shows.append(media_obj)
                        
                        elif media['Type'] == 'Season':
                            season_data.append(media)

            # After basic parsing add seasons to series, they seem to come after the show but to be safe I am doing seperate
            for season in season_data:
                
                # Find parent object from list
                parent_obj = None
                for show in self.shows:

                    if not isinstance(show, Show):
                        raise TypeError(f'Expected only shows but found {show}')
    
                    if season.get('SeriesId') == show.jellyfin_id:
                        parent_obj = show
                        break

                if parent_obj is None:
                    raise ValueError(f"Failed to find parent for {season}")
                
                season_obj = Season(season['Name'])
                season_obj.path = season.get('Path')
                season_obj.ids = {'tvdb': season.get('ProviderIds').get('Tvdb')}
                season_obj.jellyfin_id = media.get('Id')

                parent_obj.seasons.append(season_obj)
    
    def __str__(self):
        res = f'Movies ({len(self.movies)} total):\n'
        for m in self.movies:
            res += f'{str(m)}\n'

        res += f'Shows ({len(self.shows)} total):\n'
        for s in self.shows:
            res += f'{str(s)}\n'
        return res

    def __eq__(self, other):
        raise NotImplementedError("Must implement eq in media objects first")
        
        if not isinstance(other, Library):
            return False

        return self.movies == other.movies and self.shows == other.shows
        