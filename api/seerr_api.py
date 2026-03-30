import os

SEERR_IP = os.environ.get("SEERR_IP")
SEERR_KEY = os.environ.get("SEERR_KEY")

# http://localhost:5055/api-docs 
BASE_URL = f"http://{SEERR_IP}:5055/api/v1"


# class Seerr_API:
