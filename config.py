"""
config.py — Configuration Classes for Krishi-Sahayak

All secrets are loaded from .env using python-dotenv.
NEVER hardcode API keys or secrets here.

Three configs:
  - Config          : base settings shared by all environments
  - DevelopmentConfig : debug=True, used locally
  - ProductionConfig  : debug=False, stricter cookies
"""

import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()


class Config:
    """Base configuration — shared by all environments."""

    # ── Flask Core ──────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production-please")

    # ── Session Cookie Security ─────────────────────────────────────
    SESSION_COOKIE_HTTPONLY = True        # JS cannot read the cookie
    SESSION_COOKIE_SAMESITE = "Lax"      # Prevents CSRF from other sites
    PERMANENT_SESSION_LIFETIME = 86400   # Session expires after 24 hours (in seconds)

    # ── File Uploads ─────────────────────────────────────────────────
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))  # 5 MB

    # ── Firebase Public Config (used in frontend JS templates) ───────
    FIREBASE_API_KEY            = os.getenv("FIREBASE_API_KEY", "")
    FIREBASE_AUTH_DOMAIN        = os.getenv("FIREBASE_AUTH_DOMAIN", "")
    FIREBASE_PROJECT_ID         = os.getenv("FIREBASE_PROJECT_ID", "")
    FIREBASE_STORAGE_BUCKET     = os.getenv("FIREBASE_STORAGE_BUCKET", "")
    FIREBASE_MESSAGING_SENDER_ID = os.getenv("FIREBASE_MESSAGING_SENDER_ID", "")
    FIREBASE_APP_ID             = os.getenv("FIREBASE_APP_ID", "")

    # Firebase Admin (server-side) — path to service account JSON
    FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_PATH", "instance/firebase_service_account.json"
    )

    # ── ML Model Paths ───────────────────────────────────────────────
    CROP_MODEL_PATH   = os.getenv("CROP_MODEL_PATH",   "trained_models/crop_model.pkl")
    CROP_LE_PATH      = os.getenv("CROP_LE_PATH",      "trained_models/crop_le.pkl")
    CROP_NPK_CSV      = os.getenv("CROP_NPK_CSV",      "trained_models/ideal_npk.csv")
    DISEASE_MODEL_PATH = os.getenv("DISEASE_MODEL_PATH", "trained_models/disease_model.keras")

    # ── External API Keys ────────────────────────────────────────────
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")
    MANDI_API_KEY  = os.getenv("MANDI_API_KEY", "")

    # ── Mandi API ────────────────────────────────────────────────────
    MANDI_BASE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"


class DevelopmentConfig(Config):
    """Development — used when running locally with python run.py"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False  # HTTP is fine locally


class ProductionConfig(Config):
    """Production — used when deploying to a server."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True   # Require HTTPS in production


# ── Config selector ──────────────────────────────────────────────────
config_map = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "default":     DevelopmentConfig,
}


def get_config():
    """Return the config class based on FLASK_ENV environment variable."""
    env = os.getenv("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)
