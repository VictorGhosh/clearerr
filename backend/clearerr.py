import sys
import logging
import yaml

from time import sleep, time
from types import SimpleNamespace

from .api.os_storage import human_size  # TODO: this should be in storage_obj
from .api.seerr_api import Seerr_API

from .obj.library_obj import Library
from .obj.storage_obj import Storage

from settings.config import config

from .util.db_util import DB_Handler
from .util.log_util import setup_logging
setup_logging(config)
log = logging.getLogger(__name__)
removals_log = logging.getLogger("removals")
exemptions_log = logging.getLogger("exemptions")

log.info("Required pyhton libraries loaded")

class Actions:
    @staticmethod
    def full_build_lib() -> Library:

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
        DB_Handler.write_to_sqlite(pl, config._DB_PATH)

        return pl

    @staticmethod
    def process_user_lists(pl: Library, rules: SimpleNamespace) -> bool:
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
            if time() > m.removal_scheduled + (rules.thresholds.process_scheduled_removal_after_hours * 3600):
                if rules.goal.dry_run:
                    log.info(f"Scheduled removal of {m.title} expected, canceled for dry run")
                    removals_log.info(f"Scheduled removal of {m.title} expected, canceled for dry run")
                else:
                    s = Seerr_API()
                    log.info(f"Removing {m.title} due to schedule...")
                    removals_log.info(f"Removing {m.title} from {m.path}")
                    seerr_item = s.find_by_external_id(m.rating_key, m.ids)
                    if seerr_item is None:
                        log.error(f"Could not find {m.title} in Seerr, skipping removal")
                        continue
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
            log.debug(pl2)

            removed = [m for m in actual_removals if m in pl2.movies + pl2.shows]
            if removed:
                log.error(f"Media still present after deletion: {[m.title for m in removed]}")
            else:
                log.info("All targeted media removal validated")

            return True
        return False

    @staticmethod
    def process_storage_needs(rules: SimpleNamespace) -> tuple[float, Storage]:
        s = Storage()

        # get library sizes from os
        ls, ms, ss = human_size(s.lib_size), human_size(s.movies_size), human_size(s.shows_size)
        log.info(f"Calculated library sizes: Total: {ls}, Movies: {ms}, Shows: {ss}")

        # get share/array stats from shutil. these will be more accurate to os including file system
        st, su, sf = human_size(s.share_total), human_size(s.share_used), human_size(s.share_free) 
        log.info(f"Calculated share data: Total: {st}, Used: {su}, Free: {sf}")

        # share will be larger than lib but if by too much there may be a leak so alert
        if abs(int(s.share_used) - s.lib_size) > (rules.thresholds.notify_if_lib_size_dif_larger_than_gb * 1024 ** 3):
            log.warning("Library size and share usage difference exceeded threshold. Please investigate possible leak")

        # Here use share data as usage because its larger.
        target_free = rules.goal.free_percentage * 0.01 * s.share_total

        # if target works out to be too low, alert
        threshold_free_space = rules.thresholds.notify_if_target_free_space_below_gb * 1024 ** 3
        if (target_free < threshold_free_space):
            log.warning(f"Target free space ({human_size(target_free)}) is below threshold ({human_size(threshold_free_space)})")

        if (target_free < s.share_free):
            log.info(f"Free space on share ({sf}) is greater than the target ({human_size(target_free)})")
            log.info(f"No action - We're done!")
            sys.exit(0)
        else:
            log.info(f"Free space on share ({sf}) is less than the target ({human_size(target_free)})")

        clear_target = target_free - s.share_free
        if clear_target <= 0:
            log.error("Something has gone very wrong, we aim to clear negative space")
            raise ValueError
        log.info(f"Attempting to clear approximately {human_size(clear_target)}s of media")
        if rules.goal.dry_run:
            log.info(f"Dry run is enabled, nothing will be removed")
        return clear_target, s

    @staticmethod
    def media_selection(pl: Library, clear_target: float) -> list:
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

        return selected
    
    @staticmethod
    def removal_and_validation(pl: Library, selected: list, rules: SimpleNamespace) -> None:
        if rules.goal.dry_run:
            log.info(f"Dry run is enabled, stopping here") 
            sys.exit(0)

        s = Seerr_API()
        for media in selected:
            log.info(f"Removing {media.title}...")
            seerr_item = s.find_by_external_id(media.rating_key, media.ids)
            if seerr_item is None:
                log.error(f"Could not find {media.title} in Seerr, skipping removal")
                continue
            s.delete_media(seerr_item['id'])

        # Validation
        log.info("Triggering focused library updates for removed media...")
        for media in selected:
            pl.trigger_media_refresh(media)

        log.info("Waiting 30 seconds for refreshes to complete...")
        sleep(30)

        log.info("Rebuilding library model from Plex....")
        pl2 = Library()
        pl2.build_from_plex()
        log.debug(pl2)

        # confusing but removed is things that were not removed. sorry idk why I did thta
        removed = [m for m in selected if m in pl2.movies + pl2.shows]
        if removed:
            log.error(f"Media still present after deletion: {[m.title for m in removed]}")
        else:
            log.info("All targeted media removal validated")

    @staticmethod
    def process_storage_results(s: Storage) -> None:
        s2 = Storage()

        ls2, ms2, ss2 = human_size(s2.lib_size), human_size(s2.movies_size), human_size(s2.shows_size)
        log.info(f"Calculated library sizes: Total: {ls2}, Movies: {ms2}, Shows: {ss2}")
        log.info(f"{human_size(s.lib_size - s2.lib_size)}s Cleared - os walk")
    
        # get share/array stats from shutil. these will be more accurate to os including file system
        st2, su2, sf2 = human_size(s2.share_total), human_size(s2.share_used), human_size(s2.share_free) 
        log.info(f"Calculated share data: Total: {st2}, Used: {su2}, Free: {sf2}")
        log.info(f"{human_size(s.share_used - s2.share_used)}s Cleared - share")
        log.info(f"We're done!")

def main():
    def to_namespace(d):
        if isinstance(d, dict):
            return SimpleNamespace(**{k: to_namespace(v) for k, v in d.items()})
        return d
    
    with open(config._RULES_PATH) as f:
        rules = to_namespace(yaml.safe_load(f))

    # Build and validate library
    pl = Actions.full_build_lib()

    # Update library with front end data
    if Actions.process_user_lists(pl, rules):
        pl = Actions.full_build_lib()

    # Set target or stop if no removal needed
    clear_target, s = Actions.process_storage_needs(rules)

    # Select removal items
    selected = Actions.media_selection(pl, clear_target)

    # Remove selected items and validate their removal
    Actions.removal_and_validation(pl, selected, rules)

    Actions.process_storage_results(s)

if __name__ == "__main__":
    main()
