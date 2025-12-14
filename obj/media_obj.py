class _Media():
    def __init__(self, title: str):
        self.title = title
        
        # Private; only set when needed due to intensive api calls required
        self._path = None

        # data for validation
        self.raw_tautilli_data = None

        #IDs. Should consolidate these once I know which to use
        self.rating_key = None
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
            'tvdb': self.tvdb,
            'added': self.added_on,
            'last_watched': self.last_watched
        }
        return str(short_dict)

    def populate_from_tautilli(self, metadata: dict) -> None:
        '''
        At the moment tautilli is the chosen starter for media objects but others will be used to validate.
        This method initalizes the attributes that can be grabbed from that app. In adding to this method
        we should try to keep with the order of attribute declarations as much as possible.
        
        :param metadata: metadata from tautilli api
        :type metadata: dict
        '''
        # validate we got the right metadata file
        if metadata['title'] != self.title:
            raise ValueError(f"Expected title {self.title} got {metadata['title']}")

        self.path = metadata['media_info'][0]['parts'][0]['file']
        
        self.raw_tautilli_data = metadata
        
        self.rating_key = metadata['rating_key']
        for i in metadata['guids']:
            if i.startswith('tvdb://'):
                self.tvdb = i.split('tvdb://')[-1]
                break

        self.added_on = metadata['added_at']
        self.last_watched = metadata['last_viewed_at']

        # make sure manditory fields are not empty
        required = [
            self.title, 
            self.raw_tautilli_data,
            self.rating_key, 
            self.tvdb,
            self.added_on
            ]
        for index, var in enumerate(required):
            if var is None:
                raise ValueError(f"Missing value for media {self.title} index: {index} (see required list here)")

class Movie(_Media):
    def __init__(self, title: str):
        super().__init__(title)
        # IDs
        self.imdb = None
        self.tmdb = None

    def __str__(self):
        pior = super().__str__()
        partial = {
            'imdb': self.imdb,
            'tmdb': self.tmdb
            }
        return f"{pior} - {partial}"

    def populate_from_tautilli(self, metadata: dict) -> None:
        super().populate_from_tautilli(metadata)
        
        if metadata['media_type'] != 'movie':
            raise ValueError(f"Expected type was movie, got {metadata['media_type']}")

        # guids stored in an odd list
        for i in metadata['guids']:
            if i.startswith('imdb://'):
                self.imdb = i.split('imdb://')[-1]
            elif i.startswith('tmdb://'):
                self.tmdb = i.split('tmdb://')[-1]

        # make sure fields are not empty
        required = [self.imdb, self.tmdb]
        for index, var in enumerate(required):
            if var is None:
                raise ValueError(f"Missing value for media {self.title} index: {index}")

class _Season(_Media):
    def __init__(self, title: str):
        super().__init__(title)

class Show(_Media):
    def __init__(self, title: str):
        super().__init__(title)
        # IDs
        self.imdb = None
        self.tmdb = None
        
        # owns _Season objects
        self.seasons = []

    def populate_from_tautilli(self, metadata: dict) -> None:
        super().populate_from_tautilli(metadata)