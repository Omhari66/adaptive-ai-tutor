import requests
import time
import json

base_url = "http://127.0.0.1:8000/api"

print("Uploading document...")
with open("../test_upload.txt", "rb") as f:
    files = {"file": ("test_upload.txt", f, "text/plain")}
    res = requests.post(f"{base_url}/documents/upload", files=files)
    
print("Upload status:", res.status_code)
print("Upload response text:", res.text)
try:
    doc_id = res.json().get("docId")
except:
    import sys; sys.exit(1)

print("Waiting for document to process...")
for i in range(15):
    res_docs = requests.get(f"{base_url}/documents").json()
    doc_status = next((d["status"] for d in res_docs["documents"] if d["id"] == doc_id), "unknown")
    print(f"Status: {doc_status}")
    if doc_status in ["READY", "FAILED", "ready", "failed", "Ready"]:
        break
    time.sleep(2)

print("Starting chat...")
chat_res = requests.post(f"{base_url}/chat", json={
    "query": "What is photosynthesis?",
    "documentIds": [doc_id]
}, headers={"Accept": "application/json"})

print("Chat response:")
try:
    print(json.dumps(chat_res.json(), indent=2))
except:
    print(chat_res.text)
