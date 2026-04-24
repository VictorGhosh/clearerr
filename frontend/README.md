# Front end

The web interface for Clearerr.

This is a FastAPI app that acts as the user-facing portal to the exemption list. It allows users to interact with a centralized SQLite database to mark media as exempt, so the back end cleanup script respects user preferences

- Exemption Toggle: A one-click override that saves media from the automated "deletability" scoring logic.

- Sync: Changes made here are reflected in the backend models immediately while the frontend library is updated when ever the backend script is scheduled to run.

- Sorting: Media can be sorted by title or by likelihood of removal, based on their deletion scores from the last back end run. Additionally there is a search feature. Media is always segmented into collapsible "movies" and "shows" sections

## Security

In production, this front end is exposed via a Cloudflare Tunnel with Google OAuth.

### Disclaimer

I cannot be bothered to crawl through xml projects and templates to make this visually acceptable, so the UI xml was largely written by AI.
