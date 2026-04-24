# Back end

The clearing and library scanning part

The main execution is container by clearerr.py and split in to regions:

1. Library building
    - Two library objects are generated, one using the Plex api and the other using jellyfin
    - The two are compared to each other to make sure there are no discrepancies
    - The final library contains all the data from both, and is then updated with watch statistics from Tautulli. Finaly poster urls are grabbed from TMDB
    - Pull user exemption choices from the database and deletions scores are generating using the attributes and weights defined in settings/rules.yaml
    - Write the up to date library to the database. Missing media is also remove from the db tables.
2. Storage check
    - Calculate library section sizes by walking the directories
    - Calculate the share usage using shutil. This value will include extra, non-media, files in the share
    - Determine if and how much clearing is needed and set a target
3. Media Selection
    - Heuristic Ranking: Orders media based on the calculated deletion scores. It selects candidates top-down until the storage target is met. "Exempt" media as defined by users is sent to the bottom of the list, but the order in maintained.
4. Removal
    - Using Seererr first delete the media files and then the data itself so it does not get re-requested
    - This also removes them from Sonarr/Radarr
5. Validation
    - Send targeted partial updated to Plex and Jellyfin. These trigger a search for update in only the path of the media that was removed, avoiding unneeded scans.
    - Validate that that the media is now gone
    - Final calculations confirm storage space has been cleared
