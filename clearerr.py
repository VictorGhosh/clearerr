# region Setup and imports
import sys
import os
import logging
from types import SimpleNamespace
from api.os_storage import *
import shutil

# Add lib directory to path don't lose imports (maintine order of imports)
lib_path = os.path.join(os.path.dirname(__file__), 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

# These must come after because they are pulled from lib folder
from obj.library_obj import Library
import json
import yaml

# Logging setup
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Shush requests http connection noises
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

log = logging.getLogger(__name__)
log.info("Required pyhton libraries loaded")
# endregion


def main():
    # region pull rule variables # config.goal.free_gb or config.ordering[0].field
    def to_namespace(d):
        if isinstance(d, dict):
            return SimpleNamespace(**{k: to_namespace(v) for k, v in d.items()})
        return d

    script_dir = os.path.dirname(os.path.abspath(__file__))
    rules_path = os.path.join(script_dir, "rules.yaml")

    with open(rules_path) as f:
        config = to_namespace(yaml.safe_load(f))
    # endregion


    # region library building
    log.info("Building library object from Plex...")
    pl = Library()
    pl.build_from_plex()
    log.info("Completed building from Plex")
    log.debug(pl)

    log.info('Building library object from Jellyfin')
    jl = Library()
    jl.build_from_jellyfin()
    log.info("Completed building from Jellyfin")
    log.debug(jl)

    # Validate libraries
    if pl == jl:
        log.info("Library model validated successfully")
    else:
        log.error("Library models are not equivalent")
        log.error("No continuation plan has been implemented yet for failed validation. Exiting")
        raise ValueError
    # endregion


    # region check storage # This should be first but I want to keep testing library building
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
    log.info(f"Clearing approximately {human_size(clear_target)}s of media")
    # endregion

    # region helper
    # def jprint(input: str) -> None:
    #     print(json.dumps(input, indent=4))
    # endregion


if __name__ == "__main__":
    main()