from .obj.library_obj import Library
from settings.config import config
from types import SimpleNamespace
from .api.os_storage import *
import yaml
import logging
log = logging.getLogger(__name__)

class Actions:
    def initialize_db(self):

        def to_namespace(d):
            if isinstance(d, dict):
                return SimpleNamespace(**{k: to_namespace(v) for k, v in d.items()})
            return d

        with open(config._RULES_PATH) as f:
            rules = to_namespace(yaml.safe_load(f))

        log.info("Building library model from Plex....")
        pl = Library()
        pl.build_from_plex()
        log.debug(pl)

        log.info('Building library model from Jellyfin...')
        jl = Library()
        jl.build_from_jellyfin()
        log.debug(jl)

        # Validate and update libraries
        if pl == jl:
            log.info("Library model validated successfully")
        else:
            # TODO: What to do when library updates are out of sync
            log.error("Library model validation failed. They are not equivalent")
            log.error("No continuation plan has been implemented for failed validation yet. Exiting")
            raise NotImplementedError

        log.info("Setting Jellyfin IDs in Plex library object...")
        pl.jellyfin_ids_to_pl(jl)

        log.info("Updating Plex watch statistics with Tautulli... (Expect warnings if Plex was watched without Tautulli running)")
        pl.update_from_tautulli()
        log.info("Completed Tautulli to Plex statistics update")
        log.debug(pl)

        log.info("Generating tmdb poster data...")
        pl.update_poster_urls()

        try:
            log.info("Updating library with exemption data from database")
            pl.update_exempt_status(config._DB_PATH)
        except:
            log.error("Failed to update library with exemption data. Expected if db is new")

        log.info("Generating media deletion scores...")
        deletion_scoring_rules = rules.ordering
        log.info(f"Using rules: {deletion_scoring_rules}")
        pl.update_deletion_scores(deletion_scoring_rules)
        log.debug(pl)

        log.info("Library object generation complete. Writing to database")
        pl.write_to_sqlite(config._DB_PATH)