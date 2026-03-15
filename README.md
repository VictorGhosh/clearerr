# clearerr

A self-hosted automation tool for managing storage on a Plexarr stack. Built out of my personal annoyance with existing options that don't account for actual disk usage or user preferences when deciding what to remove.

## The Problem

A media server with only 50% storage used is wasting expensive storage space, while the same server running at 95% requires a full time babysitter to manually and frequently cleanup. Existing tools like Maintainerr don't solve this issue as the removal logic is not ideal and data collection limited by the plex api.

## How it Works

clearerr builds a library model by querying Plex, Jellyfin, and Tautulli internal APIs. Then it will apply custom rules to identify media candidates for removal based on:
- Time since added
- Watch history stats
- Current disk utilization
- User set exemptions and requests

Removal exemptions are managed through Jellyfin. Users may mark media in a designated playlist and the tool will respect these items as removal exempt or next up for deletion, depending on the list. The use of Jellyfin for this purpose side steps the limitations of the Plex API.

## Architecture

- obj/        - core data model objects (Library, Show, Season, Movie)
- api/        - API clients for Plex, Jellyfin, Radarr, and Tautulli
- dev/        - dev tools
- clearerr.py - Main entry from script (shell in current form) 

## Status

Data collection, validation, and object modeling are complete for Plex, Jellyfin, and Tautulli. We can successfully build the library model using these sources. Removal execution and rule logic is in active development. Following this, Library object validation will also be added.

### Remaining before stable state:

- [ ] Build out sonarr api

- [ ] Library validation - This should use all apis data and validate that the library object has accurate data in terms of names, paths, and sizes. Most importantly the library must be complete

- [ ] Solve download client problem - How do we remove from the download client when clearing space. Options:
    - I know the original file name now we can just remove that - may cause issues with db junk
    - Use the download clients api to remove before removing from media - pain
    - Set a seed time, possibly infinite, to keep the media in the queue so we can get it. - Not ideal and has to be done for each indexer

- [ ] Standardize APIs - Changed multiple times while writing but I would like all of them to take the format of radarr_api. That is _get_resp() called by a second get method containing a case statesmen for all used api calls. Further parsing should wrap this second method.

- [ ] Seerr api - I need to find out if seerr is going to re-request after removal. If so we will need to stop it.

- [ ] File and disk sizes - still have not fully landed on how this will work. Can I trust any of the other apis to have accurate file size data as plex seems be just making it up.