import sys
import logging
import shutil
import yaml

from time import sleep, time
from types import SimpleNamespace

from .api.os_storage import *
from .api.seerr_api import Seerr_API
from .obj.library_obj import Library
from settings.config import config

from .log_setup import setup_logging
setup_logging(config)
log = logging.getLogger(__name__)
removals_log = logging.getLogger("removals")
exemptions_log = logging.getLogger("exemptions")

log.info("Required pyhton libraries loaded")

class Actions:
    def full_build_lib(self) -> Library:

        # Cant pull this from below because this action is run when db is missing i.e. on its own
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
            log.info("Setting Jellyfin IDs in Plex library object...")
            pl.jellyfin_ids_to_pl(jl)
        else:
            log.error("Library model validation failed. They are not equivalent")

        log.info("Updating Plex watch statistics with Tautulli... (Expect warnings if Plex was watched without Tautulli running)")
        pl.update_from_tautulli()
        log.info("Completed Tautulli to Plex statistics update")
        log.debug(pl)

        log.info("Generating tmdb poster data...")
        pl.update_poster_urls()
            
        try:
            log.info("Updating library with exemption data from database...")
            pl.update_exempt_status(config._DB_PATH)
        except:
            log.error("Failed to update library with exemption data. Expected if db is new")

        log.info("Updating library with scheduled removals from database...")
        pl.update_removal_scheduled_status(config._DB_PATH)
             
        log.info("Generating media deletion scores...")
        deletion_scoring_rules = rules.ordering
        log.info(f"Using rules: {deletion_scoring_rules}")
        pl.update_deletion_scores(deletion_scoring_rules)
        log.debug(pl)
             
        log.info("Library object generation complete. Writing to database")
        pl.write_to_sqlite(config._DB_PATH)

        return pl

    def process_user_lists(self, pl: Library, rules) -> bool:
        """Mark user set exemptions and removals in logs and remove if nessesary. Library will be updated
        if anything is removed.

        Args:
            pl (Library): from full_build_lib
            rules (SimpleNamespace): rules namespace

        Returns:
            bool: True if media was removed and a new lib should be made and False otherwise
        """
        exempt_media = []
        remove_media = []
        for m in pl.movies + pl.shows:
            if m.removal_exempt:
                exempt_media.append(m)
            if m.removal_scheduled > -1:
                remove_media.append(m)

        exemptions_log.info(f"Exempt: {exempt_media}")
        removals_log.info(f"Scheduled {remove_media}")

        actual_removals = []
        for m in remove_media:
            if time > m.removal_scheduled + (rules.thresholds.process_scheduled_removal_after_hours * 3600):
                if rules.goal.dry_run:
                    log.info(f"Scheduled removal of {m.title} expected, cancled for dry run")
                    removals_log.info(f"Scheduled removal of {m.title} expected, cancled for dry run")
                else:
                    s = Seerr_API()
                    log.info(f"Removing {m.title} due to schedule...")
                    removals_log.info(f"Removing {m.title} from {m.path}")
                    seerr_item = s.find_by_external_id(m.rating_key, m.ids)
                    s.delete_media(seerr_item['id'])
                    actual_removals.append(m)

        if actual_removals:
            log.info("Triggering focused library updates for removed media...")
            for media in actual_removals:
                pl.trigger_media_refresh(media)

            log.info("Waiting 30 seconds for refreshes to complete...")
            sleep(30)

            log.info("Rebuilding library model from Plex....")
            pl2 = Library()
            pl2.build_from_plex()
            log.debug(pl)

            removed = [m for m in actual_removals if m in pl2.movies + pl2.shows]
            if removed:
                log.error(f"Media still present after deletion: {[m.title for m in removed]}")
            else:
                log.info("All targeted media removal validated")

            return True
        return False

def main():
    def to_namespace(d):
        if isinstance(d, dict):
            return SimpleNamespace(**{k: to_namespace(v) for k, v in d.items()})
        return d
    
    with open(config._RULES_PATH) as f:
        rules = to_namespace(yaml.safe_load(f))

    # region 1: Library building
    pl = Actions().full_build_lib()
    # endregion

    if Actions().process_user_lists(pl, rules):
        pl = Actions().full_build_lib()

    # region 3: Storage check
    o = OS_Storage()
    
    # get library sizes from os
    movies_size = o.get_size(config._PATH_TO_MEDIA + config.MOVIE_DIR)
    shows_size = o.get_size(config._PATH_TO_MEDIA + config.SHOWS_DIR)
    lib_size = movies_size + shows_size
    ls, ms, ss = human_size(lib_size), human_size(movies_size), human_size(shows_size)
    log.info(f"Calculated library sizes: Total: {ls}, Movies: {ms}, Shows: {ss}")

    # get share/array stats from shutil. these will be more accurate to os including file system
    share_total, share_used, share_free = shutil.disk_usage(config._PATH_TO_MEDIA)
    st, su, sf = human_size(share_total), human_size(share_used), human_size(share_free) 
    log.info(f"Calculated share data: Total: {st}, Used: {su}, Free: {sf}")

    # share will be larger than lib but if by too much there may be a leak so alert
    if abs(int(share_used) - lib_size) > (rules.thresholds.notify_if_lib_size_dif_larger_than_gb * 1024 ** 3):
        log.warning("Library size and share usage difference exceeded threshold. Please investigate possible leak")

    # NOTE: Here I will use share data as usage because its larger.
    target_free = rules.goal.free_percentage * 0.01 * share_total

    # if target works out to be too low, alert
    threshold_free_space = rules.thresholds.notify_if_target_free_space_below_gb * 1024 ** 3
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
    if rules.goal.dry_run:
        log.info(f"Dry run is enabled, nothing will be removed")
    # endregion

    # region 4: Media selection
    combined_lib = pl.movies + pl.shows
    combined_lib.sort(key=lambda x: x.deletion_score, reverse=False)

    combined_lib_str = f'Media ({len(combined_lib)} total):\n'
    for m in combined_lib:
        combined_lib_str += f'{str(m)}\n'
    log.debug(f"Sorted library: {combined_lib_str.rstrip()}")

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
    if rules.goal.dry_run:
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
    movies_size2 = o.get_size(config._PATH_TO_MEDIA + config.MOVIE_DIR)
    shows_size2 = o.get_size(config._PATH_TO_MEDIA + config.SHOWS_DIR)
    lib_size2 = movies_size2 + shows_size2
    ls2, ms2, ss2 = human_size(lib_size2), human_size(movies_size2), human_size(shows_size2)
    log.info(f"Calculated library sizes: Total: {ls2}, Movies: {ms2}, Shows: {ss2}")
    log.info(f"{human_size(lib_size - lib_size2)}s Cleared - os walk")

    # get share/array stats from shutil. these will be more accurate to os including file system
    share_total2, share_used2, share_free2 = shutil.disk_usage(config._PATH_TO_MEDIA)
    st2, su2, sf2 = human_size(share_total2), human_size(share_used2), human_size(share_free2) 
    log.info(f"Calculated share data: Total: {st2}, Used: {su2}, Free: {sf2}")
    log.info(f"{human_size(share_used - share_used2)}s Cleared - share")
    log.info(f"We're done!")
    # endregion

if __name__ == "__main__":
    # main()

    def to_namespace(d):
        if isinstance(d, dict):
            return SimpleNamespace(**{k: to_namespace(v) for k, v in d.items()})
        return d
    
    with open(config._RULES_PATH) as f:
        rules = to_namespace(yaml.safe_load(f))
    
    print(rules.thresholds)