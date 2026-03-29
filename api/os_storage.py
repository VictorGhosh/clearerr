import os
import Optional

LIBRARY_ROOT = os.environ.get("LIBRARY_ROOT")

class OS_Storage():

    def __init__(self, root: str=LIBRARY_ROOT):
        self.root = root

    def exists(self, path) -> bool:
        '''
        Returns if the given path from root is valid
        '''
        return os.path.exists(os.path.join(self.root, path))

    def get_size(self, path) -> int | None:
        '''
        Returns the byte size below the given path from root and None if it cannot be found
        '''
        if self.exists(path):
            return os.path.getsize(os.path.join(self.root, path))
