"""
Quick API test script — run this AFTER starting the server locally.
Usage: python tests/test_api.py
"""

import httpx
import json

BASE = "http://localhost:8000"


def check(label, response):
    print(f"\n{'='*50}")
    print(f"TEST: {label}")
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(response.text)


# 1 — Health check
r = httpx.get(f"{BASE}/health")
check("Health Check", r)

# 2 — List CVs
r = httpx.get(f"{BASE}/cv/list")
check("List CVs", r)

# 3 — Ask a question (will return "no CVs" message if nothing uploaded yet)
payload = {
    "question": "What are the candidate's main skills?",
    "top_k": 3,
}
r = httpx.post(f"{BASE}/query/ask", json=payload, timeout=60)
check("RAG Query — English", r)

# 4 — Arabic query test
payload_ar = {
    "question": "ما هي مهارات المرشح؟",
    "top_k": 3,
}
r = httpx.post(f"{BASE}/query/ask", json=payload_ar, timeout=60)
check("RAG Query — Arabic", r)

print("\n✅ All tests complete.")
