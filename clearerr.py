from plex_api import *

PLEX_TOKENS = {} 

# populate PLEX_TOKENS
tokens_raw = os.getenv("PLEX_TOKENS", "")
if tokens_raw:
    for pair in tokens_raw.split(","):
        if ":" in pair:
            name, token = pair.split(":", 1)
            PLEX_TOKENS[name.strip()] = token.strip()

for usr, token in PLEX_TOKENS.items():
    print(f"parsing for user: {usr} token {token}")
    plex_data = Plex_API(token)