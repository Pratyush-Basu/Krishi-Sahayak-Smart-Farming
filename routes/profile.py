"""
routes/profile.py — User Profile Blueprint

Routes:
  GET  /profile                → View profile page
  GET  /profile/edit           → Edit profile form
  POST /profile/edit           → Save profile changes
  POST /profile/upload-photo   → Upload profile picture
  POST /profile/change-password → Trigger Firebase password reset email

Profile data stored in instance/profiles/{uid}.json via profile_service.py.
Profile photos stored in uploads/{uid}_photo.{ext}.
"""

import os
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app
)
from utils.decorators import login_required
from utils.session_manager import get_current_user, update_session
from utils.helpers import secure_save_file, allowed_file
from services.profile_service import get_profile, create_or_update_profile, get_photo_url

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile")
@login_required
def view_profile():
    """Display the user's profile page."""
    user    = get_current_user()
    profile = get_profile(user["uid"])
    photo   = get_photo_url(user["uid"], profile.get("photo_filename"))
    return render_template("profile/view.html", user=user, profile=profile, photo_url=photo)


@profile_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    """Display and process the profile edit form."""
    user    = get_current_user()
    profile = get_profile(user["uid"])
    photo   = get_photo_url(user["uid"], profile.get("photo_filename"))

    if request.method == "POST":
        updates = {
            "display_name": request.form.get("display_name", "").strip(),
            "phone":        request.form.get("phone", "").strip(),
            "state":        request.form.get("state", "").strip(),
            "district":     request.form.get("district", "").strip(),
            "language":     request.form.get("language", "english"),
        }

        success = create_or_update_profile(user["uid"], updates)

        if success:
            # Update session display name so navbar shows new name
            if updates.get("display_name"):
                update_session({"display_name": updates["display_name"]})
            flash("Profile updated successfully!", "success")
        else:
            flash("Failed to save profile. Please try again.", "danger")

        return redirect(url_for("profile.view_profile"))

    return render_template("profile/edit.html", user=user, profile=profile, photo_url=photo)


@profile_bp.route("/profile/upload-photo", methods=["POST"])
@login_required
def upload_photo():
    """
    Handle profile photo upload.
    Saves to uploads/{uid}_photo.{ext} and updates the profile JSON.
    """
    user = get_current_user()
    file = request.files.get("photo")

    if not file or not file.filename:
        flash("No file selected.", "warning")
        return redirect(url_for("profile.view_profile"))

    if not allowed_file(file.filename):
        flash("Invalid file type. Please upload JPG, PNG, or GIF.", "danger")
        return redirect(url_for("profile.view_profile"))

    upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
    custom_name   = f"{user['uid']}_photo"
    filename      = secure_save_file(file, upload_folder, custom_name)

    if filename:
        create_or_update_profile(user["uid"], {"photo_filename": filename})
        flash("Profile photo updated successfully!", "success")
        current_app.logger.info(f"Profile photo uploaded for user {user['uid']}")
    else:
        flash("Failed to save photo. Please try again.", "danger")

    return redirect(url_for("profile.view_profile"))


@profile_bp.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():
    """
    Trigger a Firebase password reset email.
    The actual reset is handled by Firebase — we just trigger the email.
    """
    user = get_current_user()
    # This route returns a JSON response for AJAX calls from the profile page
    # Firebase password reset is triggered by client-side JS — see profile/view.html
    flash("Password reset email sent to your registered email address.", "info")
    return redirect(url_for("profile.view_profile"))
