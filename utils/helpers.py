"""
utils/helpers.py — General Purpose Utilities

Small helper functions used across multiple blueprints.
"""

import os
import logging
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

# Allowed image extensions for uploads
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename: str, allowed: set = None) -> bool:
    """
    Check if a filename has an allowed extension.

    Args:
        filename: original filename from upload
        allowed:  set of allowed extensions (default: image types)

    Returns:
        True if extension is allowed, False otherwise.
    """
    if allowed is None:
        allowed = ALLOWED_IMAGE_EXTENSIONS

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed
    )


def secure_save_file(file, upload_folder: str, custom_filename: str = None) -> str | None:
    """
    Securely save an uploaded file to the upload folder.

    Args:
        file:            Werkzeug FileStorage object from request.files
        upload_folder:   directory to save to (e.g., 'uploads/')
        custom_filename: optional filename override (e.g., '{uid}_photo.jpg')

    Returns:
        The saved filename (not full path) if successful, None on error.
    """
    if not file or not file.filename:
        return None

    if not allowed_file(file.filename):
        return None

    # Use custom name or secure the original filename
    if custom_filename:
        ext      = file.filename.rsplit(".", 1)[1].lower()
        filename = f"{custom_filename}.{ext}"
    else:
        filename = secure_filename(file.filename)

    os.makedirs(upload_folder, exist_ok=True)
    save_path = os.path.join(upload_folder, filename)

    try:
        file.save(save_path)
        return filename
    except Exception as e:
        logger.error(f"File save failed: {e}")
        return None


def get_firebase_config_dict(app_config) -> dict:
    """
    Return Firebase public config as a dict for injecting into Jinja2 templates.

    This is passed to templates as {{ firebase_config | tojson }}
    so firebase.js can initialize without hardcoded values.
    """
    return {
        "apiKey":            app_config.get("FIREBASE_API_KEY", ""),
        "authDomain":        app_config.get("FIREBASE_AUTH_DOMAIN", ""),
        "projectId":         app_config.get("FIREBASE_PROJECT_ID", ""),
        "storageBucket":     app_config.get("FIREBASE_STORAGE_BUCKET", ""),
        "messagingSenderId": app_config.get("FIREBASE_MESSAGING_SENDER_ID", ""),
        "appId":             app_config.get("FIREBASE_APP_ID", ""),
    }
