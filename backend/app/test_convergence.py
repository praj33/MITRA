import asyncio
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_convergence():
    print("=== MITRA LIVE CONVERGENCE VERIFICATION ===")

    # 1. Register adapters & capabilities
    from app.ecosystem.adapter_registry import AdapterRegistry, register_all_adapters
    from app.capabilities import register_all_capabilities
    from app.companion.capability_registry import capability_registry

    register_all_adapters()
    register_all_capabilities()

    print(f"[OK] Adapter Registry Products: {AdapterRegistry().list_products()}")
    print(f"[OK] Capability Registry Capabilities: {capability_registry.get_capabilities()}")

    # 2. Test UniGuru Capability Execution
    print("\n--- Testing Path A: UniGuru Knowledge Capability ---")
    uniguru_res = await capability_registry.execute(
        intent="uniguru",
        params={"message": "Explain quantum entanglement in simple terms."},
        trace_id="trace_uniguru_test_001"
    )
    if uniguru_res:
        print(f"Status: {uniguru_res.status}")
        print(f"Summary: {uniguru_res.summary}")
        print(f"Trace ID: {uniguru_res.trace_id}")
        print(f"Source: {uniguru_res.data.get('source')}")

    # 3. Test SETU / Bright Connection Capability Execution
    print("\n--- Testing Path B: SETU / Bright Connection Capability ---")
    setu_res = await capability_registry.execute(
        intent="setu",
        params={"message": "Fetch latest Tally MDU data for Bright Connection"},
        trace_id="trace_setu_test_002"
    )
    if setu_res:
        print(f"Status: {setu_res.status}")
        print(f"Summary: {setu_res.summary}")
        print(f"Trace ID: {setu_res.trace_id}")
        print(f"Provenance Chain: {setu_res.data.get('provenance_chain') or setu_res.data.get('provenance')}")

    # 4. Demonstrate Full Ecosystem Integration Proofs
    print("\n--- Testing Runtime Proofs & Ecosystem Service ---")
    from app.services.ecosystem_integration_service import get_ecosystem_integration_service
    service = get_ecosystem_integration_service()
    demo_results = await service.demonstrate_ecosystem_integration()
    print(f"Total Products Tested: {demo_results['total_products']}")
    print(f"Integrated Products: {demo_results['integrated_products']}")

    print("\n=== CONVERGENCE VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(test_convergence())
