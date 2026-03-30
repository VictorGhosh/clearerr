import os
from typing import Optional
import logging
log = logging.getLogger(__name__)

LIBRARY_ROOT = os.environ.get("LIBRARY_ROOT")

class OS_Storage():

    def __init__(self, root: str=LIBRARY_ROOT):
        self.root = root

    def _full_path(self, path) -> str:
        '''
        Join path with root and validate that join did its job. Annoyingly join seems to silenty
        do nothing if there is a repeat like traiing / or root at the start if path
        '''
        full = os.path.join(self.root, path.lstrip('/'))
        if full == path or full == self.root:
            log.error(f"Join had no effect: {full}")
        return full

    def exists(self, path) -> bool:
        '''
        Returns if the given path from root is valid
        '''
        return os.path.exists(self._full_path(path))

    def get_size(self, path) -> int | None:
        '''
        Returns the byte size below the given path from root and None if it cannot be found
        '''
        full = self._full_path(path)
        if self.exists(path):
            if os.path.isfile(full):
                return os.path.getsize(full)
            total = 0
            for dirpath, dirnames, filenames in os.walk(full):
                for f in filenames:
                    total += os.path.getsize(os.path.join(dirpath, f))
            return total

# FIXME: Got all turned around trying to figure out if we are in base 1000 or 1024 and gave up
def human_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024