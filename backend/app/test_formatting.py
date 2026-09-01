import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.core.llm_bridge import llm_bridge

async def test_format():
    query = "explain quantum computing in simple terms."
    raw_sample = """Web Information Intelligence Summary:
- Quantum Computing Explained in Simple Terms: A Complete Beginner's Guide (2026) | SpinQ: SpinQ SpinQ Products & Services Superconducting Quantum Computers NMR Quantum Computers Online Quantum Experiment Platform & Software Solutions Quantum Education Solution Fintech-based Solution Biomedical-based Solution AI-based Solution News About Us Online Platform 中文; En;) Es;) # Quantum Computing Explained in Simple Terms: A Complete Beginner's Guide (2026) 2026.03.13 - Blog explain quantum computing in simple terms [...] and engaging with this transformative technology. [...] ## Quantum Computing Challenges Despite all the excitement, quantum computing is still maturing. Key challenges include:
- Quantum computing made simple: What it is and why it matters: It can be tough to get your head around. Try to think of quantum computing like trying every possible answer to a difficult question all at the same time, rather than one by one. It does this by using particles that can hold multiple states at once. This happens due to a weird property of quantum physics called superposition, which we'll explain in more detail below. [...] This allows quantum computers to handle enormous amounts of information and explore countless possible solutions all at once. They can tackle problems in areas like chemistry and logistics that would take classical computers millions of years to solve. ## Why it matters to you
- Quantum Computers Explained: How Quantum Computing Works: # Quantum Computers Explained: How Quantum Computing Works ## Science ABC 539000 subscribers 10985 likes ### Description 885111 views Posted: 23 Sep 2024 What is a quantum computer and how does it work? In this video, we explain quantum computing in simple words — from qubits and superposition to quantum entanglement and quantum supremacy. Learn how quantum computers differ from classical computers and why they will revolutionize AI, cybersecurity, and medical research.
- Quantum computing - Wikipedia: Quantum mechanics and computer science formed distinct academic communities until the advent of quantum computing. Quantum theory was developed in the 1920s to explain perplexing physical phenomena. Computers emerged decades later. Both disciplines had practical applications during World War II; computers played a major role in wartime cryptography, while quantum physics was essential for nuclear physics. [...] Wikipedia® is a registered trademark of the Wikimedia Foundation, Inc., a non-profit organization."""

    result = llm_bridge._synthesize_search_into_markdown(query, raw_sample)
    print("=== SYNTHESIZED MARKDOWN OUTPUT ===")
    print(result)

if __name__ == "__main__":
    asyncio.run(test_format())
