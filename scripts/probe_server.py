import urllib.request
import urllib.error
import json
import sys

urls_to_test = [
    ('http://127.0.0.1:8000/', 200, 'Landing Page'),
    ('http://127.0.0.1:8000/login/', 200, 'Login Page'),
    ('http://127.0.0.1:8000/register/', 200, 'Register Page'),
    ('http://127.0.0.1:8000/api/v1/opportunities/', 200, 'Opportunities API'),
    ('http://127.0.0.1:8000/api/v1/evaluations/latest/', 200, 'Evaluations API'),
]

all_passed = True
for url, expected_status, label in urls_to_test:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'MatchForgeProber/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.getcode()
            passed = (status == expected_status)
            print(f"[{'PASS' if passed else 'FAIL'}] {label} ({url}) -> Status: {status}")
            if not passed:
                all_passed = False
    except Exception as e:
        print(f"[FAIL] {label} ({url}) -> Error: {e}")
        all_passed = False

if all_passed:
    print("\nALL SERVER ENDPOINTS RESPONDING CLEANLY.")
else:
    sys.exit(1)
