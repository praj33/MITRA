import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from app.core.llm_bridge import llm_bridge

async def test_groq_llm():
    print("=== TESTING DIRECT GROQ LLM GENERATION ===")
    prompt = "explain quantum computing in simple terms."
    res = await llm_bridge.call_llm_with_messages(
        model="groq",
        messages=[{"role": "user", "content": prompt}]
    )
    print("=== LLM RESPONSE OUTPUT ===")
    print(res)
    print("=== SUCCESS ===")

if __name__ == "__main__":
    asyncio.run(test_groq_llm())
