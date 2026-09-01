import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

async def test_uniguru():
    from app.ecosystem.adapter_registry import AdapterRegistry, register_all_adapters
    from app.capabilities.uniguru_capability import UniGuruCapability
    from app.ecosystem.base_adapter import IntegrationRequest

    register_all_adapters()

    registry = AdapterRegistry()
    adapter = registry.get_adapter("UniGuru")
    print("UniGuru Manifest Base URL:", adapter._manifest.base_url)

    req = IntegrationRequest(
        source_product="mitra",
        target_product="UniGuru",
        action="query",
        payload={"query": "Explain machine learning in simple terms"},
        trace_id="live_uniguru_check_202"
    )

    res = await adapter.query(req)
    print("Direct Adapter Query Success:", res.success)
    print("Direct Adapter Response Data/Error:", res.data or res.error)

    uniguru_cap = UniGuruCapability()
    cap_res = await uniguru_cap.execute("uniguru", {"message": "Explain machine learning"}, "trace_uniguru_cap_202")
    print("UniGuruCapability Status:", cap_res.status)
    print("UniGuruCapability Summary:", cap_res.summary)

if __name__ == "__main__":
    asyncio.run(test_uniguru())
