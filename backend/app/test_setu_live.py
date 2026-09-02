import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

async def test_setu():
    from app.ecosystem.adapter_registry import AdapterRegistry, register_all_adapters
    from app.capabilities.setu_capability import SetuCapability
    from app.ecosystem.base_adapter import IntegrationRequest

    register_all_adapters()

    registry = AdapterRegistry()
    adapter = registry.get_adapter("SETU")
    print("SETU Manifest Base URL:", adapter._manifest.base_url)

    req = IntegrationRequest(
        source_product="mitra",
        target_product="SETU",
        action="services",
        payload={"user_id": "test_user"},
        trace_id="live_setu_check_101"
    )

    res = await adapter.query(req)
    print("Direct Adapter Query Success:", res.success)
    print("Direct Adapter Response Data/Error:", res.data or res.error)

    setu_cap = SetuCapability()
    cap_res = await setu_cap.execute("setu", {"message": "Get Bright Connection status"}, "trace_cap_101")
    print("SetuCapability Status:", cap_res.status)
    print("SetuCapability Summary:", cap_res.summary)
    print("SetuCapability Data:", cap_res.data)

if __name__ == "__main__":
    asyncio.run(test_setu())
