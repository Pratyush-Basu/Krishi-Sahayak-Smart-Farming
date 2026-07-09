"""Test all routes for basic functionality (no crashes, correct redirects)."""
import warnings
warnings.filterwarnings("ignore")

from app import create_app

app = create_app()

# Public routes (no login needed)
public_routes = [
    ("GET",  "/",                 200),
    ("GET",  "/login",            200),
    ("GET",  "/register",         200),
    ("GET",  "/forgot-password",  200),
    ("GET",  "/irrigation/ping",  200),
]

# Protected routes (should redirect to /login -> 302)
protected_routes = [
    ("GET",  "/dashboard"),
    ("GET",  "/crop"),
    ("GET",  "/fertilizer"),
    ("GET",  "/mandi"),
    ("GET",  "/disease"),
    ("GET",  "/irrigation"),
    ("GET",  "/chatbot"),
    ("GET",  "/weather"),
    ("GET",  "/profit"),
    ("GET",  "/nearby"),
    ("GET",  "/profile"),
    ("GET",  "/settings"),
]

errors = []

with app.test_client() as c:
    print("=== PUBLIC ROUTES ===")
    for method, path, expected in public_routes:
        try:
            r = c.get(path) if method == "GET" else c.post(path)
            status = "OK" if r.status_code == expected else f"FAIL (got {r.status_code})"
            print(f"  {method:4s} {path:25s} -> {r.status_code} {status}")
            if r.status_code != expected:
                errors.append(f"{path}: expected {expected}, got {r.status_code}")
        except Exception as e:
            print(f"  {method:4s} {path:25s} -> CRASH: {e}")
            errors.append(f"{path}: CRASH {e}")

    print()
    print("=== PROTECTED ROUTES (no auth -> should 302) ===")
    for method, path in protected_routes:
        try:
            r = c.get(path, follow_redirects=False) if method == "GET" else c.post(path, follow_redirects=False)
            location = r.headers.get("Location", "")
            if r.status_code == 302 and "/login" in location:
                print(f"  {method:4s} {path:25s} -> 302 -> /login OK")
            else:
                print(f"  {method:4s} {path:25s} -> {r.status_code} UNEXPECTED (Location: {location})")
                errors.append(f"{path}: expected 302->/login, got {r.status_code}")
        except Exception as e:
            print(f"  {method:4s} {path:25s} -> CRASH: {e}")
            errors.append(f"{path}: CRASH {e}")

    print()
    print("=== PROTECTED ROUTES WITH MOCK SESSION ===")
    # Simulate a logged-in user
    with c.session_transaction() as sess:
        sess["uid"] = "test_user_123"
        sess["email"] = "test@test.com"
        sess["display_name"] = "Test Farmer"
        sess["photo_url"] = ""
        sess["role"] = "farmer"
        sess["login_time"] = "2025-01-01T00:00:00"
        sess["is_authenticated"] = True

    for method, path in protected_routes:
        try:
            r = c.get(path, follow_redirects=False) if method == "GET" else c.post(path, follow_redirects=False)
            if r.status_code == 200:
                print(f"  {method:4s} {path:25s} -> 200 OK")
            elif r.status_code == 302:
                print(f"  {method:4s} {path:25s} -> 302 (redirect to {r.headers.get('Location', '')})")
            else:
                print(f"  {method:4s} {path:25s} -> {r.status_code} UNEXPECTED")
                errors.append(f"{path} (authed): got {r.status_code}")
        except Exception as e:
            print(f"  {method:4s} {path:25s} -> CRASH: {e}")
            errors.append(f"{path} (authed): CRASH {e}")

print()
if errors:
    print(f"RESULT: {len(errors)} ERRORS FOUND")
    for e in errors:
        print(f"  - {e}")
else:
    print("RESULT: ALL PASS")
