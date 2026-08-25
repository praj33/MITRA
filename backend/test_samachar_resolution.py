import sys, io, urllib.request, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def run_test(label, msg):
    data = json.dumps({'message': msg, 'user_id': 'test_user', 'session_id': 'test_session'}).encode()
    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/companion/chat',
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    try:
        res = urllib.request.urlopen(req, timeout=45)
        resp = json.loads(res.read().decode('utf-8'))
        cap = (resp.get('capability_result') or {})
        cap_data = cap.get('data') or {}
        resolved_url = cap_data.get('url') or 'N/A'
        msg_text = resp.get('message', '')
        
        output = [
            f"=== {label} ===",
            f"User Query:          '{msg}'",
            f"Intent:              {resp.get('intent')}",
            f"Resolved URL:        {resolved_url}",
            f"Samachar API Status: {res.status} OK",
            f"Final MITRA Output:\n{msg_text[:400].strip()}",
            "--------------------------------------------------"
        ]
        print("\n".join(output), flush=True)
    except Exception as e:
        print(f"=== {label} ===\nUser Query: '{msg}'\nERROR: {e}\n--------------------------------------------------", flush=True)

print("Starting Samachar Capability Test Suite...\n", flush=True)
run_test("TEST 1: Direct Article URL", "https://www.bbc.com/news/articles/cx272np7vgyo")
run_test("TEST 2: Natural Language - Latest News", "latest news")
run_test("TEST 3: Natural Language - AI News", "What is happening with AI today?")
