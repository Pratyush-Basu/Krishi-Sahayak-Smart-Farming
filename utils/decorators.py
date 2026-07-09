"""
utils/decorators.py — Route Protection Decorators

@login_required  : Redirects to /login if user is not authenticated
@role_required   : Redirects to /dashboard if user doesn't have the required role

Usage:
    from utils.decorators import login_required, role_required

    @app.route('/crop')
    @login_required
    def crop_page():
        ...

    @app.route('/admin')
    @login_required
    @role_required('admin')
    def admin_page():
        ...

How it works:
  - Checks Flask session for 'is_authenticated' and 'uid'
  - If not authenticated → redirect to /login with a ?next= parameter
    so the user is sent back to the original page after login
  - If wrong role → redirect to /dashboard with an error flash message
"""

from functools import wraps
from flask import redirect, url_for, flash, request
from utils.session_manager import get_current_user

def login_required(f):
    """
    Protect a route — only authenticated users can access it.

    If not logged in → redirect to /login
    The ?next= query param saves where they were trying to go.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if user is None:
            # Save the page they were trying to visit
            next_url = request.url
            return redirect(url_for("auth.login", next=next_url))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*allowed_roles):
    """
    Restrict a route to specific user roles.

    Must be used AFTER @login_required (assumes user is already authenticated).

    Args:
        *allowed_roles: one or more role strings e.g. 'admin', 'farmer'

    Example:
        @login_required
        @role_required('admin')
        def admin_panel(): ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()

            # Shouldn't happen (login_required should catch this first)
            if user is None:
                return redirect(url_for("auth.login"))

            # Check if user's role is in the allowed list
            if user.get("role") not in allowed_roles:
                flash("You don't have permission to access this page.", "danger")
                return redirect(url_for("main.dashboard"))

            return f(*args, **kwargs)
        return decorated_function
    return decorator
