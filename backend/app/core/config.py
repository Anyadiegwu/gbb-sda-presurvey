import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD")

DATABASE_URL = os.getenv("DATABASE_URL")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

# GOOGLE_MAPS_SERVER_KEY = os.getenv("GOOGLE_MAPS_SERVER_KEY")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

LOCATIONIQ_API_KEY = os.getenv("LOCATIONIQ_API_KEY", "")

# Routing. The public OSRM demo server is for light testing only -- point this
# at your own OSRM instance (or another OSRM-compatible service) for real traffic.
OSRM_BASE_URL = os.getenv("OSRM_BASE_URL", "https://router.project-osrm.org").rstrip("/")

# Restrict geocoding to these countries (comma-separated ISO codes) so
# "Ikeja" doesn't resolve to a town on another continent. Empty = worldwide.
GEOCODE_COUNTRY_CODES = os.getenv("GEOCODE_COUNTRY_CODES", "ng")
