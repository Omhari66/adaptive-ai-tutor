import urllib.request
import json
import uuid

base_url = "http://localhost:8000/api"

# 1. Register a user
email = f"test_{uuid.uuid4()}@example.com"
password = "password123"

req = urllib.request.Request(f"{base_url}/auth/register", method="POST")
req.add_header("Content-Type", "application/json")
data = json.dumps({"email": email, "password": password, "name": "Test User"}).encode("utf-8")
try:
    resp = urllib.request.urlopen(req, data=data)
    print("Registered:", resp.read().decode("utf-8"))
except Exception as e:
    print("Register failed:", e.read().decode("utf-8") if hasattr(e, 'read') else str(e))

# 2. Login to get token
req = urllib.request.Request(f"{base_url}/auth/login", method="POST")
req.add_header("Content-Type", "application/json")
data = json.dumps({"email": email, "password": password}).encode("utf-8")
try:
    resp = urllib.request.urlopen(req, data=data)
    login_data = json.loads(resp.read().decode("utf-8"))
    token = login_data["access_token"]
    print("Logged in, token:", token[:10] + "...")
except Exception as e:
    print("Login failed:", e.read().decode("utf-8") if hasattr(e, 'read') else str(e))
    exit(1)

# 3. Generate Quiz
req = urllib.request.Request(f"{base_url}/quiz/generate", method="POST")
req.add_header("Content-Type", "application/json")
req.add_header("Authorization", f"Bearer {token}")
data = json.dumps({"documentIds": [], "numQuestions": 5}).encode("utf-8")
try:
    resp = urllib.request.urlopen(req, data=data)
    print("Quiz:", resp.read().decode("utf-8"))
except Exception as e:
    print("Quiz failed:")
    print("Code:", getattr(e, 'code', 'unknown'))
    print("Body:", e.read().decode("utf-8") if hasattr(e, 'read') else str(e))
