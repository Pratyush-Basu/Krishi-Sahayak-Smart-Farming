"""
utils/session_manager.py — Centralized Session Management

One place to manage what gets stored in Flask session.

What we store in the session after login:
  - uid          : Firebase user ID (unique, permanent)
  - email        : user's email address
  - display_name : user's display name
  - photo_url    : profile photo URL
  - role         : 'farmer', 'admin', or 'guest'
  - login_time   : ISO timestamp of when they logged in
  - is_authenticated : True/False flag

All routes use get_current_user() to read session data.
"""

from flask import session
from datetime import datetime


def set_session(user_data: dict):
    """
    Store user information in Flask session after successful login.

    Args:
        user_data: dict from Firebase token verification containing
                   uid, email, display_name, photo_url, etc.
    """
    session.permanent = True    # Session respects PERMANENT_SESSION_LIFETIME
    session["uid"]          = user_data.get("uid", "")
    session["email"]        = user_data.get("email", "")
    session["display_name"] = user_data.get("display_name", "")
    session["photo_url"]    = user_data.get("photo_url", "")
    session["role"]         = user_data.get("role", "farmer")  # default: farmer
    session["login_time"]   = datetime.now().isoformat()
    session["is_authenticated"] = True


def get_current_user() -> dict | None:
    """
    Get the currently logged-in user from the session.

    Returns:
        dict with user info if logged in, None if not authenticated.

    Usage in routes:
        user = get_current_user()
        if not user:
            return redirect(url_for('auth.login'))
    """
    if session.get("is_authenticated") and session.get("uid"):
        return {
            "uid":          session.get("uid", ""),
            "email":        session.get("email", ""),
            "display_name": session.get("display_name", ""),
            "photo_url":    session.get("photo_url", ""),
            "role":         session.get("role", "farmer"),
            "login_time":   session.get("login_time", ""),
            "is_authenticated": True,
        }
    return None


def clear_session():
    """
    Clear all session data (called on logout).
    Removes every key we set during login.
    """
    keys_to_clear = ["uid", "email", "display_name", "photo_url",
                     "role", "login_time", "is_authenticated"]
    for key in keys_to_clear:
        session.pop(key, None)


def update_session(updates: dict):
    """
    Update specific session fields without clearing others.
    Used when user updates their profile name or photo.

    Args:
        updates: dict of session keys to update
    """
    allowed_keys = {"display_name", "photo_url", "role"}
    for key, value in updates.items():
        if key in allowed_keys:
            session[key] = value


def is_authenticated() -> bool:
    """Quick check: is a user currently logged in?"""
    return bool(session.get("is_authenticated") and session.get("uid"))
