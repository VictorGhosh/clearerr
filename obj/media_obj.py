class _Media():
    def __init__(self, title: str):
        self.title = title
        
        # Private; only set when needed due to intensive api calls required for shows
        self._path = None

        # IDs
        self.rating_key = None
        self.tmdb = None
        self.tvdb = None

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
        short_dict = {
            'title': self.title,
            'rating_key': self.rating_key,
            'added': self.added_on,
            'last_watched': self.last_watched
        }
        return str(short_dict)


class Movie(_Media):
    def __init__(self, title: str):
        super().__init__(title)
        self.imdb = None # Seasons do not have


class Season(_Media):
    def __init__(self, title: str):
        super().__init__(title)


class Show(_Media):
    def __init__(self, title: str):
        super().__init__(title)
        self.imdb = None # Seasons do not have
        self.seasons = []