from obj.media_obj import *
from api.plex_api import Plex_API
from api.jellyfin_api import Jellyfin_API
from api.tautulli_api import Tautulli_API
from api.os_storage import OS_Storage
import logging
log = logging.getLogger(__name__)

class Library():
    def __init__(self):
        self.movies = []
        self.shows = []

    def __str__(self):
        res = f'Movies ({len(self.movies)} total):\n'
        for m in self.movies:
            res += f'{str(m)}\n'

        res += f'Shows ({len(self.shows)} total):\n'
        for s in self.shows:
            res += f'{str(s)}\n'
        return res.rstrip()

    def __eq__(self, other):
        if not isinstance(other, Library):
            return False

        if len(self.movies) != len(other.movies):
            return False
        if len(self.shows) != len(other.shows):
            return False

        for movie in self.movies:
            found = False
            for other_movie in other.movies:
                if movie == other_movie:
                    found = True
                    break
            if not found:
                log.warning(f"Failed to match: {move.title}")
                return False

        for show in self.shows:
            found = False
            for other_show in other.shows:
                if show == other_show:
                    found = True
                    break
            if not found:
                log.warning(f"Failed to match: {show.title}")
                return False

        return True

    def build_from_plex(self) -> None:
        if self.movies != [] or self.shows != []:
            raise ValueError(f"Media list is not empty")

        p = Plex_API()
        o = OS_Storage()

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

                            season.rating_key = c.get('ratingKey')
                            season.added_on = c.get('addedAt')
                            season.last_watched = c.get('lastViewedAt')

                            season.path = p.get_path(c.get('ratingKey'))

                            try:
                                season.size = o.get_size(season.path)
                            except:
                                logging.exception(f"Failed to find file size: {season.title}, {media_obj.title}")

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
                    
                    media_obj.path = p.get_path(media.get('ratingKey'))

                    try:
                        media_obj.size = o.get_size(media_obj.path)
                    except:
                        logging.exception(f"Failed to find file size: {media_obj.title}")


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
        o = OS_Storage()

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

                        try:
                            media_obj.size = o.get_size(media.get('Path'))
                        except:
                            log.exception(f"Failed to find file size: {media_obj.title}")

                        self.movies.append(media_obj)

                    elif lib_type == 'Shows':
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

                try:
                    season_obj.size = o.get_size(season.get('Path'))
                except:
                    logging.exception(f"Failed to find file size: {season_obj.title}, {parent_obj.title}")

                parent_obj.seasons.append(season_obj)

    def update_from_tautulli(self) -> None:
        t = Tautulli_API()
        
        def update_from_tautulli_helper(media, t_dat) -> None:
            try:
                t_last_watched = t_dat['data'][0]['date']
            except IndexError:
                # tautulli has not record, validate plex agrees otherwise there is a problem
                if media.last_watched is not None:
                    log.warning(f"Plex has a watch date but Tautulli does not: {media.title}")
                return

            if media.last_watched is None or t_last_watched > media.last_watched:
                media.last_watched = t_last_watched
            elif t_last_watched < media.last_watched:
                log.warning(f"Plex has a newer watch date than Tautulli: {media.title}")

        for movie in self.movies:
            t_dat = t.get_api_query('get_history', {'rating_key': movie.rating_key})
            update_from_tautulli_helper(movie, t_dat)
            

        # FIXME: For SHOW IS NOT WORKING RIGHT NOW
        for show in self.shows:
            t_show_dat = t.get_api_query('get_history', {'grandparent_rating_key': show.rating_key})
            update_from_tautulli_helper(show, t_show_dat)
             
            for season in show.seasons:
                t_season_dat = t.get_api_query('get_history', {'parent_rating_key': season.rating_key})
                update_from_tautulli_helper(season, t_season_dat)

    def update_deletion_scores(self, ordering: list) -> None:
        all_media = self.movies + self.shows
        
        for item in ordering:
            field, weight, required = item['field'], item['weight'], item['required']
            
            # collect all values for this field
            values = []
            for media in all_media:
                value = getattr(media, field, None)
                if not value:
                    if required:
                        log.exception(f"Ordering field '{field}' missing on: {media.title}")
                        raise ValueError
                else:
                    values.append(value)
            
            # NOTE: Basic normalization right now (should I z-score for file size outliers?)
            min_val, max_val = min(values), max(values)
            span = max_val - min_val
            
            # apply normalized value * weight to each media's score
            for media in all_media:

                # Avoiding type error adding float to None but I want to keep intializing to null
                if media.deletion_score is None: media.deletion_score = 0

                value = getattr(media, field, None)
                if value and span > 0:
                    media.deletion_score += ((value - min_val) / span) * weight
        
        # handle exempt after scoring
        for media in all_media:
            if media.removal_exempt:
                media.deletion_score = -1