import os
import logging
from pathlib import Path
from settings.config import config
log = logging.getLogger(__name__)

class OS_Storage():

    def __init__(self, root: str=config._PATH_TO_MEDIA):
        self.root = root

    def get_plex_path(self, path):
        '''Given the path provided by the plex api, get the path in the clearerr container.
        _PATH_TO_MEDIA should be assigned to /media and /media should be mapped to the real dir'''
        if path is None:
            return None
        
        p = Path(path)
        return os.path.join(self.root, Path(*p.parts[3:]))

    def get_size(self, path) -> int | None:

        if path is None:
            return None

        return sum(
            os.path.getsize(os.path.join(dp, f))
            for dp, _, files in os.walk(path)
            for f in files
        ) if os.path.isdir(path) else os.path.getsize(path)

def human_size(size_bytes: int) -> str | None:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        try:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
        except TypeError:
            return None
        size_bytes /= 1024