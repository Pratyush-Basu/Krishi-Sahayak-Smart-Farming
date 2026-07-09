"""
utils/validators.py — Input Validation Helpers

Simple validation functions used in auth routes.
Keeps validation logic out of route handlers.
"""

import re


def validate_email(email: str) -> tuple[bool, str]:
    """
    Check if an email address is valid.

    Returns:
        (True, "") if valid
        (False, "error message") if invalid
    """
    if not email or not email.strip():
        return False, "Email is required"

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email.strip()):
        return False, "Please enter a valid email address"

    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """
    Check if a password meets minimum requirements.

    Requirements:
      - At least 6 characters (Firebase minimum)

    Returns:
        (True, "") if valid
        (False, "error message") if invalid
    """
    if not password:
        return False, "Password is required"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, ""


def validate_name(name: str) -> tuple[bool, str]:
    """Validate a display name / full name."""
    if not name or not name.strip():
        return False, "Name is required"
    if len(name.strip()) < 2:
        return False, "Name must be at least 2 characters"
    if len(name.strip()) > 100:
        return False, "Name must be less than 100 characters"
    return True, ""


def validate_phone(phone: str) -> tuple[bool, str]:
    """Validate an Indian phone number (10 digits)."""
    if not phone:
        return True, ""   # Phone is optional
    phone_clean = re.sub(r'[\s\-+]', '', phone)
    if not re.match(r'^[0-9]{10}$', phone_clean):
        return False, "Phone number must be 10 digits"
    return True, ""
