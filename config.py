import os

PORT = int(os.environ.get("PORT", 8080))

DATABASE_URL = os.environ.get("DATABASE_URL", "")

JWT_SECRET = os.environ.get(
    "JWT_SECRET",
    "TaxiServer_DEV_SECRET_CHANGE_ME"
)

ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "")

DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
