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
    
    '''
    TODO: 
    Not that simple. and not super important until I am actually using jellyfin, so implement this then
        - Jellyfin does not seem to be scanning library on its own for updates. need to schedule 
            that and get logic in place to run a scan when the libraries do not match (not here).
        - Also need to put some thought into how this should work. The ID values themselves are consistant
            but plex and jellyfin mix an match what IDs they use for each media type. You CANNOT 
            rely on or even include titles. Capitals and spaces are not consistant (tron or TRON)
            but more importantly for some unique titles the actual words are different!
            (PLUR1BUS or PLURIBUS) For the latter there is no reasonable way to get consistant good
            results that I can think of so we must work with IDs only
    '''
    # def __eq__(self, other):
    #     if isinstance(other, type(self)):
    #         return self.title == other.title
    #     else:
    #         return false

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