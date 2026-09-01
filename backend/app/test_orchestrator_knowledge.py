import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from app.companion.companion_orchestrator import companion_orchestrator

async def test_knowledge_flow():
    print("=== TESTING COMPANION ORCHESTRATOR FOR KNOWLEDGE QUERY ===")
    prompt = "what is quantum computing?"
    res = await companion_orchestrator.process(
        user_id="user_knowledge_test",
        message=prompt
    )
    print("=== ORCHESTRATOR RESPONSE ===")
    print("Intent:", res.intent)
    print("Response text:\n", res.message)
    print("=== SUCCESS ===")

if __name__ == "__main__":
    asyncio.run(test_knowledge_flow())
