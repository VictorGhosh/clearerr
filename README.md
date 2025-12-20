# clearerr

Unsatisfied with current open source options for media deletion/space creation on plexarr stacks,  I’ve decided to make my own.

I believe the ideal server in this use should always sit at %80-%90 capacity. Any less and you’re wasting storage that already been paid for. Any more and you have to manually and consistently clear space to allow for new material. To that end I need the removal automation to consider the current library storage usage.

It should also remove media in an organized sorted fashion, probably based on when it was added to the library and when or if it was watched.

I also wanted the ability for users to mark media as “do not delete”, or even “please delete”. These would be things they plan on watching but have not gotten around to, or that they plan on rewatching in the future

This has proven to be the most annoying process. Maintainerr offers an “is watchlisted” flag but this only considers the root users watchlist (if that) as Plex watchlists are cloud based and not accessible through the API. I did attempt to use collections instead but Plex, in their infinite wisdom, have decided not to allow users to create or add to collections unless they are Plex Pass holders; even if they are in the home group.

Ultimately I turned to Jellyfin for this need among other uses as Plex becomes less and less of a step up. I create accounts for my Plex users in Jellyfin and they add the media to save from removal to a folder called “Removal Exempt” or something similar. These playlists are local and API callable and the process is not overly painful as both services are being hosted on the same server with the same library.

## Task List
In no particular order:
- [ ] Build sonarr api

- [ ] Library validation - This should use all apis data and validate that the library object has accurate data in terms of names, paths, and sizes. Most importantly the library must be complete

- [ ] Solve download client problem - How do we remove from the download client when clearing space. Options:
    - I know the original file name now we can just remove that - may cause issues with db junk
    - Use the download clients api to remove before removing from media - pain
    - Set a seed time, possibly infinite, to keep the media in the queue so we can get it. - Not ideal and has to be done for each indexer

- [ ] Standardize APIs - Changed multiple times while writing but I would like all of them to take the format of radarr_api. That is _get_resp() called by a second get method containing a case statesmen for all used api calls. Further parsing should wrap this second method.

- [ ] Seerr api - I need to find out if seerr is going to re-request after removal. If so we will need to stop it.

- [ ] File and disk sizes - still have not fully landed on how this will work. Can I trust any of the other apis to have accurate file size data as plex seems be just making it up 