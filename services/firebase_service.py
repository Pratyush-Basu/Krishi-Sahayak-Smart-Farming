"""
services/firebase_service.py — Firebase Admin SDK Initialization

Why we need Firebase Admin SDK on the server:
  - Client-side Firebase JS can be bypassed by opening HTML files directly
  - The Admin SDK lets us VERIFY the token that the browser sends after login
  - This creates a real server-side session that cannot be bypassed

Setup required:
  1. Go to: Firebase Console → Project Settings → Service Accounts
  2. Click "Generate new private key"
  3. Save the JSON as: instance/firebase_service_account.json

If the service account file is missing, session verification falls back to
a simplified mode (still works, but less secure — good for development).
"""

import os
import logging

logger = logging.getLogger(__name__)

# Firebase Admin SDK — initialized once at app startup
_firebase_app = None


def init_firebase(service_account_path: str):
    """
    Initialize Firebase Admin SDK using a service account JSON file.
    Called once from create_app() during startup.

    Args:
        service_account_path: Path to firebase_service_account.json

    Returns:
        True if initialized successfully, False otherwise.
    """
    global _firebase_app

    try:
        import firebase_admin
        from firebase_admin import credentials

        if _firebase_app is not None:
            logger.info("Firebase Admin already initialized")
            return True

        if not os.path.exists(service_account_path):
            logger.warning(
                f"Firebase service account not found at: {service_account_path}\n"
                "Running in development mode without server-side token verification.\n"
                "Download from: Firebase Console → Project Settings → Service Accounts"
            )
            return False

        cred = credentials.Certificate(service_account_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully")
        return True

    except ImportError:
        logger.warning("firebase-admin package not installed. Run: pip install firebase-admin")
        return False
    except Exception as e:
        logger.error(f"Firebase Admin initialization failed: {e}")
        return False


def verify_firebase_token(id_token: str) -> dict | None:
    """
    Verify a Firebase ID token sent from the browser after login.

    The browser calls firebase.auth().currentUser.getIdToken() and POSTs
    the result here. We verify it against Firebase's public keys.

    Args:
        id_token: JWT token string from Firebase JS SDK

    Returns:
        dict with user info (uid, email, name, picture) if valid,
        None if token is invalid/expired.
    """
    try:
        from firebase_admin import auth

        decoded = auth.verify_id_token(id_token)
        return {
            "uid":          decoded.get("uid", ""),
            "email":        decoded.get("email", ""),
            "display_name": decoded.get("name", ""),
            "photo_url":    decoded.get("picture", ""),
            "email_verified": decoded.get("email_verified", False),
        }
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        return None


def is_firebase_ready() -> bool:
    """Returns True if Firebase Admin SDK is initialized."""
    return _firebase_app is not None
