from backend.api.os_storage import *
from settings.config import config
import shutil

class Storage():
    def __init__(self):
        self.o = OS_Storage()

        self.movies_size: int
        self.shows_size: int
        self.lib_size: int

        self.share_total: int
        self.share_used: int
        self.share_free: int

        movies_size = self.o.get_size(config._PATH_TO_MEDIA + config.MOVIE_DIR)
        shows_size = self.o.get_size(config._PATH_TO_MEDIA + config.SHOWS_DIR)
        if movies_size is None or shows_size is None:
            raise ValueError("Failed to calculate library size")
        self.movies_size = movies_size
        self.shows_size = shows_size
        self.lib_size = movies_size + shows_size

        # share/array stats from shutil. these will be more accurate to os including file system
        self.share_total, self.share_used, self.share_free = shutil.disk_usage(config._PATH_TO_MEDIA)