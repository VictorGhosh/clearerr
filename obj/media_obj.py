import os
import time
from api.os_storage import human_size
import logging
log = logging.getLogger(__name__)

class _Media():
    def __init__(self, title: str):
        self.title = title
        
        self.path = None
        self.size = None

        # IDs
        self.rating_key = None # Plex apps
        self.ids = {} # at least tmdb and tvdb

        # watch data
        self.added_on = None
        self.last_watched = None

        # use setter. scaled score or -1 for exempt
        self.deletion_score = None

    def __str__(self):
        partial = {
            'title': self.title,
            'rating_key': self.rating_key,
            'added': self.added_on,
            'last_watched': self.last_watched,
            'size': human_size(self.size),
            'deletion_score': self.deletion_score
        }
        partial.update(self.ids)
        partial.update({'path': self.path})
        return str(partial)
    
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        # Only end of paths can match because of the containers root naming. oops
        if self.path and other.path:
            tail_a = '/'.join(self.path.split('/')[-2:])
            tail_b = '/'.join(other.path.split('/')[-2:])
            if tail_a != tail_b:
                return False

        # At least one id matches (not none) and none of the filled ids do not match
        match = False
        for key in self.ids.keys() & other.ids.keys():
            a = self.ids.get(key)
            b = other.ids.get(key)
            if a is not None and b is not None:
                if a != b:
                    return False
                match = True

        return match

    def set_deletion_score(self, ordering: list, removal_exempt: bool=False) -> None:
        if removal_exempt:
            self.deletion_score = -1
            return
        score = 0
        for item in ordering:
            field, weight, required = item['field'], item['weight'], item['required']
            value = getattr(self, field, None)
            if not value:
                if required:
                    log.exception(f"Ordering field '{field}' is missing or None on: {self.title}")
                    raise ValueError
                continue
            score += value * weight
        self.deletion_score = score


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

    def __eq__(self, other):
        if not super().__eq__(other):
            return False

        if len(self.seasons) != len(other.seasons):
            log.warning(f"Mismatched number of seasons: {self.title}")
            return False

        # each season must have equal match
        for season_a in self.seasons:
            found = False
            for season_b in other.seasons:
                if season_a == season_b:
                    found = True
                    break
            if not found:
                log.warning(f"Failed to match season: {season_a.title}, {self.title}")
                return False
        return True