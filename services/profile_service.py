"""
services/profile_service.py — User Profile Storage (File-Based)

Stores user profiles as JSON files in instance/profiles/{uid}.json.

Why file-based now:
  - Simple, zero dependencies, works without a database
  - Perfect for a student project / final year demo

MongoDB-ready interface:
  - All routes call profile_service.get_profile(uid) etc.
  - When you're ready for MongoDB, create MongoProfileService
    with the same method signatures and swap it in create_app()
  - Zero changes needed in routes or blueprints

Profile data structure:
  {
    "uid":       "firebase_uid",
    "email":     "user@example.com",
    "display_name": "Farmer Name",
    "phone":     "9876543210",
    "state":     "West Bengal",
    "district":  "Kolkata",
    "language":  "english",
    "photo_filename": "uid_photo.jpg" or None,
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00"
  }
"""

import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Profiles are stored in instance/profiles/ (git-ignored folder)
PROFILES_DIR = os.path.join("instance", "profiles")


def _profile_path(uid: str) -> str:
    """Return the file path for a user's profile JSON."""
    return os.path.join(PROFILES_DIR, f"{uid}.json")


def _ensure_profiles_dir():
    """Create the profiles directory if it doesn't exist."""
    os.makedirs(PROFILES_DIR, exist_ok=True)


def get_profile(uid: str) -> dict:
    """
    Get a user's profile by Firebase UID.

    Returns the profile dict, or a minimal default dict if not found.
    Never returns None — routes can always safely access the result.
    """
    _ensure_profiles_dir()
    path = _profile_path(uid)

    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read profile for {uid}: {e}")

    # Return default profile structure
    return {
        "uid": uid,
        "email": "",
        "display_name": "",
        "phone": "",
        "state": "",
        "district": "",
        "language": "english",
        "photo_filename": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


def create_or_update_profile(uid: str, data: dict) -> bool:
    """
    Create or update a user profile.
    Merges provided data with existing profile (partial update supported).

    Args:
        uid:  Firebase UID
        data: dict of fields to update (only provided fields are changed)

    Returns:
        True if saved successfully, False on error.
    """
    _ensure_profiles_dir()

    # Load existing profile (or default)
    profile = get_profile(uid)

    # Merge — only update fields that are provided
    allowed_fields = {"email", "display_name", "phone", "state", "district", "language", "photo_filename"}
    for key, value in data.items():
        if key in allowed_fields:
            profile[key] = value

    profile["uid"]        = uid
    profile["updated_at"] = datetime.now().isoformat()

    try:
        with open(_profile_path(uid), "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to save profile for {uid}: {e}")
        return False


def get_photo_url(uid: str, photo_filename: str = None) -> str:
    """
    Return the URL path for a user's profile photo.
    Falls back to '/static/images/default_avatar.png' if no photo.

    Args:
        uid:            Firebase UID
        photo_filename: filename stored in profile (or None)

    Returns:
        URL string suitable for use in <img src="...">
    """
    if photo_filename and os.path.exists(os.path.join("uploads", photo_filename)):
        return f"/uploads/{photo_filename}"
    return "/static/images/default_avatar.svg"


def delete_profile(uid: str) -> bool:
    """Delete a user's profile (used for account deletion)."""
    path = _profile_path(uid)
    try:
        if os.path.exists(path):
            os.remove(path)
        return True
    except Exception as e:
        logger.error(f"Failed to delete profile for {uid}: {e}")
        return False
