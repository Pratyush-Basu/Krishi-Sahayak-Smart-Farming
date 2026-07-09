"""
routes/auth.py — Authentication Blueprint

Routes:
  GET  /login          → Login page
  POST /auth/session   → Firebase token → Flask session (AJAX call from JS)
  GET  /register       → Register page
  GET  /forgot-password → Forgot password page
  GET  /logout         → Clear session, redirect to /

Auth Flow:
  1. User enters email/password on /login page
  2. Browser JS calls Firebase signInWithEmailAndPassword()
  3. On Firebase success: JS calls user.getIdToken() → gets a JWT
  4. JS POSTs that JWT to POST /auth/session
  5. Flask verifies the JWT using Firebase Admin SDK
  6. Flask stores uid/email/name/photo in session
  7. Flask returns JSON {success: true, redirect: "/dashboard"}
  8. JS redirects browser to /dashboard

  If Firebase Admin SDK is not set up (no service account JSON),
  the system falls back to trusting the client-side data directly.
  This is fine for development/demos.
"""

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, jsonify, flash, current_app
)
from utils.session_manager import set_session, clear_session, get_current_user
from utils.helpers import get_firebase_config_dict
from services.firebase_service import verify_firebase_token, is_firebase_ready
from services.profile_service import create_or_update_profile

auth_bp = Blueprint("auth", __name__)


def _firebase_config():
    """Helper to get Firebase config for injecting into templates."""
    return get_firebase_config_dict(current_app.config)


# ── Login ─────────────────────────────────────────────────────────────

@auth_bp.route("/login")
def login():
    """
    Display the login page.
    If user is already logged in, send them to dashboard.
    """
    if get_current_user():
        return redirect(url_for("main.dashboard"))
    return render_template("auth/login.html", firebase_config=_firebase_config())


@auth_bp.route("/auth/session", methods=["POST"])
def create_session():
    """
    Receive Firebase ID token from frontend JS, verify it,
    and create a Flask server-side session.

    Request body (JSON):
        {
            "idToken":      "...",
            "uid":          "firebase_uid",
            "email":        "user@example.com",
            "display_name": "Farmer Name",
            "photo_url":    "https://...",
        }

    Response:
        {"success": true, "redirect": "/dashboard"}   on success
        {"success": false, "error": "..."}            on failure
    """
    data = request.get_json(silent=True) or {}

    uid          = data.get("uid", "")
    email        = data.get("email", "")
    display_name = data.get("display_name", "")
    photo_url    = data.get("photo_url", "")
    id_token     = data.get("idToken", "")

    # ── Verify with Firebase Admin (if available) ─────────────────
    if is_firebase_ready() and id_token:
        verified = verify_firebase_token(id_token)
        if not verified:
            return jsonify({"success": False, "error": "Invalid or expired token. Please login again."})
        # Use verified data (more secure)
        uid          = verified["uid"]
        email        = verified["email"]
        display_name = verified.get("display_name") or display_name
        photo_url    = verified.get("photo_url") or photo_url
    elif not uid:
        # No Admin SDK and no uid — can't create session
        return jsonify({"success": False, "error": "Authentication failed. Missing user data."})

    # ── Build user dict and store in session ──────────────────────
    user_dict = {
        "uid":          uid,
        "email":        email,
        "display_name": display_name,
        "photo_url":    photo_url,
        "role":         "farmer",  # Default role
    }
    set_session(user_dict)

    # ── Save/update profile (creates profile if first login) ──────
    create_or_update_profile(uid, {
        "email":        email,
        "display_name": display_name,
        "photo_url":    photo_url,
    })

    current_app.logger.info(f"User logged in: {email} (uid: {uid})")
    return jsonify({"success": True, "redirect": url_for("main.dashboard")})


# ── Register ──────────────────────────────────────────────────────────

@auth_bp.route("/register")
def register():
    """
    Display the registration page.
    If already logged in, redirect to dashboard.
    """
    if get_current_user():
        return redirect(url_for("main.dashboard"))
    return render_template("auth/register.html", firebase_config=_firebase_config())


# ── Forgot Password ───────────────────────────────────────────────────

@auth_bp.route("/forgot-password")
def forgot_password():
    """
    Display the forgot password page.
    Password reset email is sent by Firebase JS on the client side.
    """
    return render_template("auth/forgot_password.html", firebase_config=_firebase_config())


# ── Logout ────────────────────────────────────────────────────────────

@auth_bp.route("/logout")
def logout():
    """
    Clear Flask session and redirect to landing page.

    Note: This clears the SERVER-SIDE session.
    The client-side Firebase session is signed out by the JS in the navbar.
    """
    user = get_current_user()
    if user:
        current_app.logger.info(f"User logged out: {user.get('email')}")
    clear_session()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("main.index"))
