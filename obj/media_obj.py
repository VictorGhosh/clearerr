class _Media():
    def __init__(self, title: str):
        self.title = title
        
        self._path = None

        # IDs
        self.rating_key = None # Plex apps
        self.jellyfin_id = None # Jellyfin apps
        self.ids = {} # at least tmdb and tvdb

        # watch data
        self.added_on = None
        self.last_watched = None

    @property
    def path(self):
        return self._path
    
    @path.setter
    def path(self, path: str) -> None:
        self._path = path

    def __str__(self):
        partial = {
            'title': self.title,
            'rating_key': self.rating_key,
            'added': self.added_on,
            'last_watched': self.last_watched
        }
        partial.update(self.ids)
        return str(partial)
    
    # def __eq__(self, other):
    #     if isinstance(other, _Media):
    #         return (self.title == other.title and
    #                 self._path == other.path and
    #                 self.rating_key == other.rating_key and
    #                 self.ids['tmdb'] == other.ids['tmdb'])
    #     else:
    #         return NotImplemented

class Movie(_Media):
    def __init__(self, title: str):
        super().__init__(title)


class Season(_Media):
    def __init__(self, title: str):
        super().__init__(title)


class Show(_Media):
    def __init__(self, title: str):
        super().__init__(title)
        self.seasons = []

    def __str__(self):
        partial = super().__str__()
        
        seasons_str = ''
        for s in self.seasons:
            seasons_str += f"\n\t{s}"
            
        return f"{partial} - Seasons:{seasons_str}"