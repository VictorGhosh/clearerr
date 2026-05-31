from backend.api.os_storage import *
from settings.config import config
import shutil

class Storage():
    def __init__(self):
        self.o = OS_Storage()

        self.movies_size = None
        self.shows_size = None
        self.lib_size = None

        self.share_total = None
        self.share_used = None
        self.share_free = None

        self.movies_size = self.o.get_size(config._PATH_TO_MEDIA + config.MOVIE_DIR)
        self.shows_size = self.o.get_size(config._PATH_TO_MEDIA + config.SHOWS_DIR)
        self.lib_size = self.movies_size + self.shows_size

        # share/array stats from shutil. these will be more accurate to os including file system
        self.share_total, self.share_used, self.share_free = shutil.disk_usage(config._PATH_TO_MEDIA)