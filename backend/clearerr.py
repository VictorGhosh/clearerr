# region 0 Setup and imports
import sys
import os
import logging
import shutil
from time import sleep
from logging.handlers import RotatingFileHandler
from types import SimpleNamespace
from api.os_storage import *


# Add lib directory to path don't lose imports (maintine order of imports)
log.info(os.path.dirname(os.path.dirname(__file__)))
lib_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

# These must come after because they are pulled from lib folder
from obj.library_obj import Library
from api.seerr_api import Seerr_API
from api.plex_api import Plex_API
import yaml

# Logging setup
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clearerr.log")
max_log_bytes = int(os.environ.get("LOG_SIZE_MB")) * 1024 * 1024
log_level = getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

file_handler = RotatingFileHandler(log_path, maxBytes=max_log_bytes, backupCount=3)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logging.getLogger().setLevel(log_level)
logging.getLogger().addHandler(file_handler)
logging.getLogger().addHandler(stream_handler)

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
log = logging.getLogger(__name__)
log.info("Required pyhton libraries loaded")
# endregion

def main():
    # region 1: Pull rules
    def to_namespace(d):
        if isinstance(d, dict):
            return SimpleNamespace(**{k: to_namespace(v) for k, v in d.items()})
        return d

    script_dir = os.path.dirname(os.path.abspath(__file__))
    rules_path = os.path.join(script_dir, "rules.yaml")

    with open(rules_path) as f:
        config = to_namespace(yaml.safe_load(f))
    # endregion

    # region 2: Library building
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

    log.info("Updating library with exemption data from database")
    pl.update_exempt_status(os.environ.get("DB_PATH"))

    log.info("Generating media deletion scores...")
    deletion_scoring_rules = config.ordering
    log.info(f"Using rules: {deletion_scoring_rules}")
    pl.update_deletion_scores(deletion_scoring_rules)
    log.debug(pl)

    log.info("Library object generation complete. Writing to database")
    pl.write_to_sqlite(os.environ.get("DB_PATH"))
    # endregion

    # region 3: Storage check
    o = OS_Storage()
    
    # get library sizes from os
    movies_size = o.get_size(os.environ.get("PATH_TO_MOVIES"))
    shows_size = o.get_size(os.environ.get("PATH_TO_SHOWS"))
    lib_size = movies_size + shows_size
    ls, ms, ss = human_size(lib_size), human_size(movies_size), human_size(shows_size)
    log.info(f"Calculated library sizes: Total: {ls}, Movies: {ms}, Shows: {ss}")

    # get share/array stats from shutil. these will be more accurate to os including file system
    share_total, share_used, share_free = shutil.disk_usage(os.environ.get("LIBRARY_SHARE"))
    st, su, sf = human_size(share_total), human_size(share_used), human_size(share_free) 
    log.info(f"Calculated share data: Total: {st}, Used: {su}, Free: {sf}")

    # share will be larger than lib but if by too much there may be a leak so alert
    if abs(int(share_used) - lib_size) > (config.thresholds.notify_if_lib_size_dif_larger_than_gb * 1024 ** 3):
        log.warning("Library size and share usage difference exceeded threshold. Please investigate possible leak")

    # NOTE: Here I will use share data as usage because its larger.
    target_free = config.goal.free_percentage * 0.01 * share_total

    # if target works out to be too low, alert
    threshold_free_space = config.thresholds.notify_if_target_free_space_below_gb * 1024 ** 3
    if (target_free < threshold_free_space):
        log.warning(f"Target free space ({human_size(target_free)}) is below threshold ({human_size(threshold_free_space)})")

    if (target_free < share_free):
        log.info(f"Free space on share ({sf}) is greater than the target ({human_size(target_free)})")
        log.info(f"No action - We're done!")
        sys.exit(0)
    else:
        log.info(f"Free space on share ({sf}) is less than the target ({human_size(target_free)})")

    clear_target = target_free - share_free
    if clear_target <= 0:
        log.error("Something has gone very wrong, we aim to clear negative space")
        raise ValueError
    log.info(f"Attempting to clear approximately {human_size(clear_target)}s of media")
    if config.goal.dry_run:
        log.info(f"Dry run is enabled, nothing will be removed")
    # endregion

    # region 4: Media selection
    combined_lib = pl.movies + pl.shows
    combined_lib.sort(key=lambda x: x.deletion_score, reverse=False)

    combined_lib_str = f'Media ({len(combined_lib)} total):\n'
    for m in combined_lib:
        combined_lib_str += f'{str(m)}\n'
    log.info(f"Sorted library: {combined_lib_str.rstrip()}")

    selected = []
    sum_selected = 0
    for media in combined_lib:
        selected.append(media)
        sum_selected += media.size

        if sum_selected >= clear_target: 
            break

    selected_str = f'Media ({len(selected)} total):\n'
    for m in selected:
        selected_str += f'{str(m)}\n'
    log.info(f"Selected for removal ({human_size(sum_selected)}) {selected_str.rstrip()}")
    # endregion

    # region 5: Media removal
    if config.goal.dry_run:
        log.info(f"Dry run is enabled, stopping here") 
        sys.exit(0)

    s = Seerr_API()
    for media in selected:
        log.info(f"Removing {media.title}...")
        seerr_item = s.find_by_external_id(media.rating_key, media.ids)
        s.delete_media(seerr_item['id'])
    # endregion 

    # region 6: Removal validation
    log.info("Triggering focused library updates for removed media...")
    for media in selected:
        pl.trigger_media_refresh(media)

    log.info("Waiting 30 seconds for refreshes to complete...")
    sleep(30)

    log.info("Rebuilding library model from Plex....")
    pl2 = Library()
    pl2.build_from_plex()
    log.debug(pl)
    
    removed = [m for m in selected if m in pl2.movies + pl2.shows]
    if removed:
        log.error(f"Media still present after deletion: {[m.title for m in removed]}")
    else:
        log.info("All targeted media removal validated")

    # Recalculating from section 3
    movies_size2 = o.get_size(os.environ.get("PATH_TO_MOVIES"))
    shows_size2 = o.get_size(os.environ.get("PATH_TO_SHOWS"))
    lib_size2 = movies_size2 + shows_size2
    ls2, ms2, ss2 = human_size(lib_size2), human_size(movies_size2), human_size(shows_size2)
    log.info(f"Calculated library sizes: Total: {ls2}, Movies: {ms2}, Shows: {ss2}")
    log.info(f"{human_size(lib_size - lib_size2)}s Cleared - os walk")

    # get share/array stats from shutil. these will be more accurate to os including file system
    share_total2, share_used2, share_free2 = shutil.disk_usage(os.environ.get("LIBRARY_SHARE"))
    st2, su2, sf2 = human_size(share_total2), human_size(share_used2), human_size(share_free2) 
    log.info(f"Calculated share data: Total: {st2}, Used: {su2}, Free: {sf2}")
    log.info(f"{human_size(share_used - share_used2)}s Cleared - share")
    log.info(f"We're done!")
    # endregion

if __name__ == "__main__":
    main()