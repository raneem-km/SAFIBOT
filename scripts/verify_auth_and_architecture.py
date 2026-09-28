import urllib.request
import urllib.error
import json
import sqlite3

BASE_URL = "http://127.0.0.1:8000/api"

def api_call(endpoint, method="GET", data=None, token=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    req_body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=req_body, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as resp:
            status_code = resp.status
            resp_body = resp.read().decode("utf-8")
            return status_code, json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"error": body}
        return e.code, parsed

def run_tests():
    print("=" * 60)
    print("SAFIBOT DUAL STORAGE & AUTHENTICATION VERIFICATION")
    print("=" * 60)
    
    # 1. Verify SQLite Structured Storage
    print("\n--- 1. Testing SQLite Structured Storage (Students & Deadlines) ---")
    conn = sqlite3.connect("backend/database/safibot.db")
    cur = conn.cursor()
    cur.execute("SELECT id, name, roll_number, admission_number, course, department, semester, batch FROM students;")
    students = cur.fetchall()
    print(f"Total students in SQLite: {len(students)}")
    for s in students:
        print(f"  - [{s[0]}] {s[1]} | Roll: {s[2]} | Adm: {s[3]} | {s[4]} S{s[6]} ({s[5]})")
        assert s[2] is not None, f"Roll number missing for {s[1]}"
        assert s[3] is not None, f"Admission number missing for {s[1]}"
        
    cur.execute("SELECT count(*) FROM deadlines;")
    deadline_count = cur.fetchone()[0]
    print(f"Total deadlines in SQLite view: {deadline_count}")
    assert deadline_count > 0, "Deadlines view returned 0 rows"
    conn.close()
    print(" SQLite Structured Storage Verified!")

    # 2. Student Registration
    print("\n--- 2. Testing Student Registration ---")
    import random
    test_num = random.randint(1000, 9999)
    reg_payload = {
        "name": f"Test Student {test_num}",
        "roll_number": f"BCA-24-{test_num}",
        "admission_number": f"ADM{test_num}",
        "email": f"teststudent{test_num}@sias.edu.in",
        "password": "Password@123",
        "course": "BCA",
        "department": "Computer Applications",
        "semester": 3,
        "batch": "2024-2027",
        "interests": "Cloud Computing, Full-Stack Development"
    }
    
    code, res = api_call("/auth/register", method="POST", data=reg_payload)
    print(f"Register status: {code}")
    assert code == 200, f"Register failed: {res}"
    student_token = res["access_token"]
    registered_user = res["user"]
    print(f"Registered Student: {registered_user['name']} (Adm: {registered_user['admission_number']}, Roll: {registered_user['roll_number']})")
    assert "password" not in registered_user, "Password exposed in response!"
    assert "password_hash" not in registered_user, "Password hash exposed in response!"
    
    # Verify password was hashed in SQLite
    conn = sqlite3.connect("backend/database/safibot.db")
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE id = ?;", (registered_user["id"],))
    pw_hash = cur.fetchone()[0]
    conn.close()
    assert pw_hash.startswith("$2b$") or pw_hash.startswith("$2a$"), "Password was NOT securely hashed with bcrypt!"
    print(f" Password securely hashed with bcrypt ({pw_hash[:15]}...)")

    # 3. Student Login via Email
    print("\n--- 3. Testing Student Login via Email ---")
    login_payload_email = {
        "identifier": reg_payload["email"],
        "password": "Password@123"
    }
    code, res = api_call("/auth/login", method="POST", data=login_payload_email)
    print(f"Login via Email status: {code}")
    assert code == 200, f"Login via email failed: {res}"
    print(f" Login successful: Welcome {res['user']['name']}")

    # 4. Student Login via Admission Number
    print("\n--- 4. Testing Student Login via Admission Number ---")
    login_payload_adm = {
        "identifier": reg_payload["admission_number"],
        "password": "Password@123"
    }
    code, res = api_call("/auth/login", method="POST", data=login_payload_adm)
    print(f"Login via Admission Number status: {code}")
    assert code == 200, f"Login via admission number failed: {res}"
    print(f" Login successful: Welcome {res['user']['name']}")

    # 5. Student Profile & Dashboard Endpoints
    print("\n--- 5. Testing Student Profile & Personalized Dashboard ---")
    code, profile = api_call("/profile", method="GET", token=student_token)
    print(f"Profile status: {code} | Name: {profile['name']} | Adm: {profile['admission_number']} | Course: {profile['course']}")
    assert code == 200
    assert profile["admission_number"] == reg_payload["admission_number"]

    code, dashboard = api_call("/dashboard/me", method="GET", token=student_token)
    print(f"Dashboard/me status: {code}")
    assert code == 200
    print(f"Personalized Notices: {len(dashboard['notices'])}, Events: {len(dashboard['events'])}, Deadlines: {len(dashboard['deadlines'])}")

    # 6. Admin Route Security Enforcement (Student Calling Admin Endpoint MUST FAIL with 403 Forbidden)
    print("\n--- 6. Testing Admin Authorization Security ---")
    code, err_res = api_call("/admin/sync-website", method="POST", data={}, token=student_token)
    print(f"Student calling /admin/sync-website: HTTP {code}")
    assert code == 403, f"Security Breach! Expected HTTP 403 Forbidden, got {code}"
    print(f" Access correctly FORBIDDEN for student token: {err_res.get('detail')}")

    # 7. Admin Login and Access Verification
    print("\n--- 7. Testing Admin Login and Access ---")
    admin_login_payload = {
        "identifier": "admin@sias.edu.in",
        "password": "Admin@Safi2026"
    }
    code, admin_res = api_call("/auth/admin/login", method="POST", data=admin_login_payload)
    print(f"Admin login status: {code}")
    assert code == 200, f"Admin login failed: {admin_res}"
    admin_token = admin_res["access_token"]
    print(f"Admin logged in: {admin_res['user']['name']} (Role: {admin_res['user']['role']})")

    # 8. Admin accessing protected endpoint
    code, sync_res = api_call("/admin/sync-website", method="POST", data={}, token=admin_token)
    print(f"Admin calling /admin/sync-website: HTTP {code} ({sync_res.get('status')})")
    assert code == 200, f"Admin should have access: {sync_res}"

    # 9. Verify Deadlines Endpoint
    print("\n--- 9. Testing Deadlines Endpoint ---")
    code, deadlines = api_call("/deadlines", method="GET")
    print(f"Deadlines status: {code}, items: {len(deadlines)}")
    assert code == 200
    for d in deadlines[:3]:
        print(f"  - [{d['item_type'].upper()}] {d['title']} | Due: {d['due_date']}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY! AUTH & ARCHITECTURE 100% OPERATIONAL")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
