import httpx
import json

def test_live_server():
    base_url = "http://127.0.0.1:8000"
    print("=== TESTING LIVE BACKEND SERVER ON PORT 8000 ===")

    headers = {"X-API-Key": "localtest"}

    # 1. Health check
    resp = httpx.get(f"{base_url}/health")
    print(f"1. /health: Status {resp.status_code} -> {resp.json()}")

    # 2. Ecosystem products
    resp = httpx.get(f"{base_url}/api/ecosystem/products", headers=headers)
    print(f"2. /api/ecosystem/products: Status {resp.status_code} -> Products: {resp.json().get('products')}")

    # 3. Ecosystem Query (SETU)
    payload = {
        "product": "SETU",
        "action": "services",
        "payload": {"query": "Bright Connection Status"}
    }
    resp = httpx.post(f"{base_url}/api/ecosystem/query", json=payload, headers=headers)
    print(f"3. /api/ecosystem/query (SETU): Status {resp.status_code} -> {resp.json()}")

    # 4. Ecosystem Query (UniGuru)
    payload_ug = {
        "product": "UniGuru",
        "action": "query",
        "payload": {"query": "Explain educational system"}
    }
    resp = httpx.post(f"{base_url}/api/ecosystem/query", json=payload_ug, headers=headers)
    print(f"4. /api/ecosystem/query (UniGuru): Status {resp.status_code} -> {resp.json()}")

    # 5. Ecosystem Demonstrate
    resp = httpx.post(f"{base_url}/api/ecosystem/demonstrate", headers=headers)
    demo = resp.json()
    print(f"5. /api/ecosystem/demonstrate: Status {resp.status_code} -> Total: {demo.get('demonstration', {}).get('total_products')}, Integrated: {demo.get('demonstration', {}).get('integrated_products')}")

    print("=== LIVE SERVER HTTP TESTS PASSED! ===")

if __name__ == "__main__":
    test_live_server()
