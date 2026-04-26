# Clearerr v2

A self-hosted automation tool for managing storage on a Plexarr stack. Built out of my personal annoyance with existing options that don't account for actual disk usage or user preferences when deciding what to remove.

## The Problem

A media server with only 50% storage used is wasting expensive disk space, while the same server running at 95% requires a full time babysitter to manually and frequently cleanup. Existing tools like Maintainerr don't solve this issue as the removal logic is not ideal and data collection limited by the plex api.

## How it Works

### APIs

The plex api does not provide watch statistics for any users besides the owner, even if they are in the same plex home account, and has wildly inacctuate storage estemates.

Clearerr builds library models by hitting internal APIs for Plex, Jellyfin, and Tautulli. It validates the library models are equivalent (all media accounted for and pointing to the same locations) and puts out targeted updates to Plex and Jellyfin when there are discrepancies until all the apps are synced. Accurate watch data is derived as the most recent value between the three providers.

The seererr api is used to safely remove and unmonitor selected items. Afterwards targeted update requests are put to Plex and Jellyfin and the entire library is validated again.

### Storage and Rules

Clearerr walks the actual library directories to see the real space used by the media and compares it to the free space on the share to determine if and how much removal is required.

It uses a weighted rules engine (defined in settings/rules.yaml) to pick what gets deleted. These rule settings are normalized and weighted such that any media attribute can be added to the yaml file and used as a deciding factor. My current rules include:

- Time since added
- Watch history stats
- Current disk utilization
- User set exemptions and requests

### User Interface

A previous iteration relied on users making specially named Jellyfin playlists to mark media as exempt as Plex will not provide other users collection or playlist data. This method was functional but clunky and required multiple accounts for each user.

In this iteration the media exemptions are set by a custom built and hosted web interface. The data and images are set by the backend script via an internal SQLite database, while the frontend app updates the exemptions on a similar table. Users can log in and mark or unmark media as exempt. Note this container has no front end security at the moment, in production that is being handled by cloudflare tunnel authentication which supports google oauth.

<p align="center">
    <img src=".images/sort_name_iphone.jpg" width="260" alt="Mobile front page sorted by title">
    <img src=".images/sort_remove_iphone.jpg" width="260" alt="Mobile front page sorted by closest removal">
    <img src=".images/change_page_iphone.jpg" width="260" alt="Changes confirmation page">
</p>

### Usage

The container was built on an unraid system with a segmented macvlan network and no os management IP, so accounting for my strict networking topology would be the biggest hurdle for anyone trying use this themselves. However, as long as the api urls in the template are set such that the container has access, everything should work (testing to come). It also requires the media directory have subdirectories for movies and shows. Those directory's names can be set in the template.

## Things to add

- [x] Add logic to run initial scan if no db exists (or just when container starts I guess)
- [ ] Add container path generation for Jellyfin
- [ ] Add targeted library scan logic for if the validation fails on start
- [ ] Add periodic health checks, especially for less used api connections like Seererr
- [ ] Migrate to Tautulli for image api instead of direct to tmdb (less WAN calls and fewer accounts needed)
- [ ] A ways away from not requiring Plex but add logic now to not require Jellyfin (no validation)
- [ ] Add logic to not require Tautulli (will require tmdb key as backup for images)
- [ ] Longer term: test on a non macvlan segmented system
- [ ] Support for saving and removing seasons (the hold up here is this cannot be done with seerr as my networking topology has it on a separate vlan to Sonarr)

## Bugs

- [ ] If somone leaves the app open or two people make changes at the same time, the second one will undo the changes of the first. Best and simplist fix would be to only update values that were touched in a session. Maybe force periodic reloads if possible.