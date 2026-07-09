"""Phase 5+6 verification script"""
from app import create_app

app = create_app()

with app.test_client() as client:
    r1 = client.get('/')
    print('GET /         ->', r1.status_code, '(expected 200)')

    r2 = client.get('/dashboard', follow_redirects=False)
    print('GET /dashboard (no auth) ->', r2.status_code, '(expected 302)')
    location = r2.headers.get('Location', '')
    print('  Redirects to:', location)
    print('  Contains /login:', '/login' in location)

    r3 = client.get('/login')
    print('GET /login    ->', r3.status_code, '(expected 200)')
    body3 = r3.data.decode()
    print('  Has FIREBASE_CONFIG:', 'FIREBASE_CONFIG' in body3)
    print('  Has SweetAlert2:', 'sweetalert2' in body3)

    r4 = client.get('/forgot-password')
    print('GET /forgot-password ->', r4.status_code, '(expected 200)')

    r5 = client.get('/logout', follow_redirects=False)
    print('GET /logout   ->', r5.status_code, '(expected 302)')

print()
all_ok = (r1.status_code == 200 and r2.status_code == 302
          and '/login' in r2.headers.get('Location', '')
          and r3.status_code == 200 and r4.status_code == 200)
print('Phase 5+6 Result:', 'ALL PASS' if all_ok else 'SOME FAILURES')
