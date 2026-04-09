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

- obj/          - core data model objects (Library, Show, Season, Movie)
- api/          - API clients for Plex, Jellyfin, Radarr, and Tautulli
- dev/          - dev tools
- clearerr.py   - Main script execution
- .env          - Needed variables such as IPs and Keys. See template in dev/
- rules.yaml    - Execution settings including "ordering" which determines in what order media is deleted

## Status

Basic function is mostly there. Library objects are created from both plex and jellyfin and and validated with eachother. Storage is calcualted and rules are applied to the library based on the yaml file.

### Remaining before stable state:

- Implement library update from jellyfin date to be applied post validation. We need the jellyfin ids to be added back to the final library (currently in neither) and might need the jellyfin docker container file paths as well.

- Library updates
    - Trigger targeted jellyfin refresh for removed items
    - Trigger targeted library updates for both plex and jellyfin based on specific differences when library object validation fails. This will be the fall back, if a ater a few seconds validation fails again then it failed for good.

- Implement do not remove lists
### Future adds

-   Add sqlite (or similar) for persistent data
    - This will allow planned removals so instead of removing off the bat, we can set an upper and lower limit. When the lower limit is met the media get picked out and added to a removal playlist. It would only be removed after some time when the upper limit is met. This would give users times to watch or exempt media on the kill list

-   Reports in addition to the current rotating logs, using the sqlite data this or a sister program could generate usage and statistical reports and send them elsewhere