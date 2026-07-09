"""
routes/main.py — Main Blueprint

Handles:
  - GET /          → Landing page (public)
  - GET /dashboard → Dashboard (protected with @login_required)
  - GET /uploads/<filename> → Serve uploaded profile photos

Phase 6: Dashboard added with @login_required protection.
"""

import os
from flask import Blueprint, render_template, redirect, url_for, send_from_directory, current_app
from utils.decorators import login_required
from utils.session_manager import get_current_user
from services.profile_service import get_profile, get_photo_url

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Public landing page — anyone can see this."""
    return render_template("index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """
    Protected dashboard — requires login.

    Without @login_required: anyone with the URL can open it.
    With    @login_required: redirects to /login if not in session.

    Passes user profile data to template for the navbar and welcome message.
    """
    user = get_current_user()

    # Get full profile (includes phone, state, district, etc.)
    profile = get_profile(user["uid"])

    # Build profile photo URL (default avatar if no photo uploaded)
    photo_url = get_photo_url(user["uid"], profile.get("photo_filename"))

    firebase_config = {
    "apiKey": current_app.config.get("FIREBASE_API_KEY", ""),
    "authDomain": current_app.config.get("FIREBASE_AUTH_DOMAIN", ""),
    "projectId": current_app.config.get("FIREBASE_PROJECT_ID", ""),
    "storageBucket": current_app.config.get("FIREBASE_STORAGE_BUCKET", ""),
    "messagingSenderId": current_app.config.get("FIREBASE_MESSAGING_SENDER_ID", ""),
    "appId": current_app.config.get("FIREBASE_APP_ID", ""),
    }

    return render_template(
    "dashboard.html",
    user=user,
    profile=profile,
    photo_url=photo_url,
    firebase_config=firebase_config,
    )


@main_bp.route("/uploads/<path:filename>")
def uploaded_file(filename):
    """
    Serve profile photo uploads.
    Files are stored in the 'uploads/' folder (git-ignored).
    """
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
    return send_from_directory(upload_folder, filename)
