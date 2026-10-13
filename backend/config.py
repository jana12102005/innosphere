# backend/config.py

import os
from dotenv import load_dotenv

load_dotenv()

# =========================
# FLASK CONFIG
# =========================
SECRET_KEY = os.environ.get("SECRET_KEY", "")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"


# =========================
# AIVEN MYSQL CONFIG
# =========================
MYSQL_HOST     = os.environ.get("MYSQL_HOST")
MYSQL_PORT     = int(os.environ.get("MYSQL_PORT"))
MYSQL_DB       = os.environ.get("MYSQL_DB")
MYSQL_USER     = os.environ.get("MYSQL_USER")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")


# =========================
# SSL CONFIG (PyMySQL-compatible)
# =========================
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CA_CERT_PATH = os.path.join(BASE_DIR, "backend", "ca.pem")

SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
if not SQLALCHEMY_DATABASE_URI:
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )

if "mysql" in SQLALCHEMY_DATABASE_URI:
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "ssl": {
                "ca": CA_CERT_PATH
            }
        }
    }
else:
    SQLALCHEMY_ENGINE_OPTIONS = {}

SQLALCHEMY_TRACK_MODIFICATIONS = False


# =========================
# PATHS
# =========================
UPLOAD_PATHS = {
    "projects": "static/uploads/projects",
    "events":   "static/uploads/events",
    "certs":    "static/uploads/certs",
    "gallery":  "static/uploads/gallery",
    "team":     "static/uploads/team"
}

CERT_DIR_ABS = os.path.join(BASE_DIR, "static", "uploads", "certs")


# =========================
# EMAIL CONFIG
# =========================
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_EMAIL    = os.environ.get("SMTP_EMAIL", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
ADMIN_EMAIL   = os.environ.get("ADMIN_EMAIL", "")


# =========================
# GROQ API
# =========================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")


# =========================
# CLOUDINARY
# =========================
CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY    = os.environ.get("CLOUDINARY_API_KEY",    "")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "")
