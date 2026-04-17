# In progress branch
### This branch in the process of being merged with the web-ui docker container. Steps to be completed below
- [X] Inital merge of clearerr-web to cleaerr
- [X] Reogranize file structure to preferend layout
- [X] Test cleaerr script as a user script to make sure file paths are working still
- [X] Remove lib and dev folders along with other userscripts required stuff
- [X] Test frontend localy
- [X] Make new dockerhub repo and build front end
    - [X] Rememeber to edit build context in docker hub to ./frontend
- [ ] Get docker xml working wor in unraid
    - [ ] Clean up refereances in backend
- [ ] Schedule cron library runs
- [ ] Add logic to run inital scan if no db exists when container starts (or just when container starts I guess)

# clearerr

A self-hosted automation tool for managing storage on a Plexarr stack. Built out of my personal annoyance with existing options that don't account for actual disk usage or user preferences when deciding what to remove.

## The Problem

A media server with only 50% storage used is wasting expensive storage space, while the same server running at 95% requires a full time babysitter to manually and frequently cleanup. Existing tools like Maintainerr don't solve this issue as the removal logic is not ideal and data collection limited by the plex api.

## How it Works

clearerr builds a library model by querying Plex, Jellyfin, and Tautulli internal APIs. Then it will apply custom rules (rules.yaml) to identify media candidates for removal based on:
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

### Future adds

- The main focus in v2 is removing the usage of Jellyfin for list making. While is solves the issue of the limited Plex api, it is a not designed for this. v2 will likely include a small docker app build only for making lists

-   Add sqlite (or similar) for persistent data
    - This will allow planned removals so instead of removing off the bat, we can set an upper and lower limit. When the lower limit is met the media get picked out and added to a removal playlist. It would only be removed after some time when the upper limit is met. This would give users times to watch or exempt media on the kill list

-   Reports in addition to the current rotating logs, using the sqlite data this or a sister program could generate usage and statistical reports and send them elsewhere