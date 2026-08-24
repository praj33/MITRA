import os
import asyncio
import hashlib
import logging
import re
from collections import OrderedDict
from typing import Dict, List, Optional

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None
try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None
try:
    import google.generativeai as genai
except ImportError:
    genai = None
try:
    from mistralai.client import MistralClient
except ImportError:
    MistralClient = None

logger = logging.getLogger(__name__)


class LocalKnowledgeBase:
    """Local knowledge base for generating contextual responses without API keys."""
    
    def __init__(self):
        self.knowledge: Dict[str, Dict] = {}
        self._initialize_knowledge()
    
    def _initialize_knowledge(self):
        """Initialize with comprehensive knowledge base covering all major topics."""
        self.knowledge = {
            # ===== LIFE & ORIGIN =====
            "origin_of_life": {
                "keywords": ["how life", "life on earth", "origin of life", "life came", "beginning of life", "first life", "how did life start", "abiogenesis"],
                "response": (
                    "# 🌱 How Life Originated on Earth\n\n"
                    "## Overview\n"
                    "Life on Earth began approximately **3.5-4 billion years ago** through a process called **abiogenesis** — "
                    "the natural process by which living organisms arise from non-living matter.\n\n"
                    "## Theories of Origin\n\n"
                    "### 1. Primordial Soup Theory (Oparin-Haldane)\n"
                    "- Early Earth had a reducing atmosphere (methane, ammonia, water vapor)\n"
                    "- Lightning and UV radiation energy caused chemical reactions\n"
                    "- Simple organic molecules (amino acids) formed in oceans\n"
                    "- These molecules combined to form more complex structures\n"
                    "- Eventually, self-replicating molecules emerged\n\n"
                    "### 2. Hydrothermal Vent Theory\n"
                    "- Life began at deep-sea hydrothermal vents\n"
                    "- These vents provided energy, heat, and chemical nutrients\n"
                    "- Minerals in vents acted as catalysts for chemical reactions\n"
                    "- Supported by the fact that all life requires water\n\n"
                    "### 3. RNA World Hypothesis\n"
                    "- RNA preceded both DNA and proteins\n"
                    "- RNA can store information AND catalyze reactions\n"
                    "- Self-replicating RNA molecules were the first life forms\n"
                    "- Later, DNA took over information storage, proteins took over catalysis\n\n"
                    "### 4. Panspermia\n"
                    "- Life's building blocks arrived from space\n"
                    "- Meteorites contain amino acids and organic compounds\n"
                    "- Doesn't explain HOW life started, just WHERE\n\n"
                    "## Key Milestones\n"
                    "| Time | Event |\n"
                    "|------|-------|\n"
                    "| ~4.5 billion years ago | Earth forms |\n"
                    "| ~4.0 billion years ago | First oceans form |\n"
                    "| ~3.8 billion years ago | First organic molecules |\n"
                    "| ~3.5 billion years ago | First simple cells (prokaryotes) |\n"
                    "| ~2.0 billion years ago | First complex cells (eukaryotes) |\n"
                    "| ~0.5 billion years ago | Cambrian Explosion (complex life) |\n\n"
                    "## Evidence\n"
                    "- **Fossilized bacteria** in 3.5-billion-year-old rocks\n"
                    "- **Stromatolites** (layered structures from cyanobacteria)\n"
                    "- **Chemical signatures** in ancient rocks\n"
                    "- **Miller-Urey experiment** showed amino acids form from simple gases\n\n"
                    "## Summary\n"
                    "Life likely began through natural chemical processes in Earth's early oceans, "
                    "progressing from simple molecules to self-replicating systems to the first cells."
                )
            },
            "percentage_formula": {
                "keywords": ["percentage", "percent", "formula for percentage", "find percentage", "calculate percentage", "% formula"],
                "response": (
                    "# 📊 Percentage Formulas\n\n"
                    "## Basic Percentage Formula\n"
                    "```\n"
                    "Percentage = (Part / Whole) × 100\n"
                    "```\n\n"
                    "## Common Formulas\n\n"
                    "### 1. Finding Percentage of a Number\n"
                    "```\n"
                    "Result = (Percentage / 100) × Number\n"
                    "Example: 20% of 150 = (20/100) × 150 = 30\n"
                    "```\n\n"
                    "### 2. Finding What Percent One Number is of Another\n"
                    "```\n"
                    "Percentage = (Part / Whole) × 100\n"
                    "Example: What % is 45 of 180? = (45/180) × 100 = 25%\n"
                    "```\n\n"
                    "### 3. Percentage Increase/Decrease\n"
                    "```\n"
                    "Percentage Change = ((New Value - Old Value) / Old Value) × 100\n"
                    "Increase: ((150 - 100) / 100) × 100 = 50% increase\n"
                    "Decrease: ((80 - 100) / 100) × 100 = 20% decrease\n"
                    "```\n\n"
                    "### 4. Finding Original Value After Percentage Change\n"
                    "```\n"
                    "Original = New Value / (1 + Percentage/100)  [for increase]\n"
                    "Original = New Value / (1 - Percentage/100)  [for decrease]\n"
                    "```\n\n"
                    "### 5. Percentage Points vs Percentage\n"
                    "- **Percentage point**: Absolute difference (45% to 50% = 5 percentage points)\n"
                    "- **Percentage change**: Relative change ((50-45)/45 × 100 = 11.1% increase)\n\n"
                    "## Quick Reference Table\n"
                    "| To Find | Formula |\n"
                    "|---------|---------|\n"
                    "| X% of Y | (X/100) × Y |\n"
                    "| What % is X of Y | (X/Y) × 100 |\n"
                    "| % increase | ((New-Old)/Old) × 100 |\n"
                    "| % decrease | ((Old-New)/Old) × 100 |"
                )
            },
            # ===== SCIENCE =====
            "physics": {
                "keywords": ["physics", "gravity", "force", "energy", "velocity", "acceleration", "newton", "motion", "thermodynamics", "quantum", "relativity"],
                "response": (
                    "# ⚛️ Physics\n\n"
                    "## Overview\n"
                    "Physics is the study of matter, energy, and the fundamental forces of nature.\n\n"
                    "## Key Concepts\n\n"
                    "### Newton's Laws of Motion\n"
                    "1. **First Law (Inertia)**: An object at rest stays at rest; in motion stays in motion unless acted upon\n"
                    "2. **Second Law**: F = ma (Force = mass × acceleration)\n"
                    "3. **Third Law**: Every action has an equal and opposite reaction\n\n"
                    "### Fundamental Forces\n"
                    "| Force | Description | Relative Strength |\n"
                    "|-------|-------------|-------------------|\n"
                    "| Strong Nuclear | Holds atomic nuclei together | 1 |\n"
                    "| Electromagnetic | Electric and magnetic interactions | 10⁻² |\n"
                    "| Weak Nuclear | Radioactive decay | 10⁻⁶ |\n"
                    "| Gravity | Attraction between masses | 10⁻³⁹ |\n\n"
                    "### Key Equations\n"
                    "- **Gravity**: F = G(m₁m₂)/r²\n"
                    "- **Kinetic Energy**: KE = ½mv²\n"
                    "- **Potential Energy**: PE = mgh\n"
                    "- **Ohm's Law**: V = IR\n"
                    "- **Einstein**: E = mc²\n\n"
                    "### Branches\n"
                    "- Classical Mechanics\n"
                    "- Thermodynamics\n"
                    "- Electromagnetism\n"
                    "- Quantum Mechanics\n"
                    "- Relativity\n"
                    "- Astrophysics"
                )
            },
            "chemistry": {
                "keywords": ["chemistry", "chemical", "element", "compound", "molecule", "atom", "reaction", "periodic table", "bond"],
                "response": (
                    "# 🧪 Chemistry\n\n"
                    "## Overview\n"
                    "Chemistry is the study of matter, its properties, structure, and how it changes.\n\n"
                    "## Basic Concepts\n\n"
                    "### Structure of Matter\n"
                    "- **Atom**: Smallest unit of an element (protons, neutrons, electrons)\n"
                    "- **Molecule**: Two or more atoms bonded together\n"
                    "- **Compound**: Substance made of two or more different elements\n"
                    "- **Element**: Pure substance with only one type of atom\n\n"
                    "### Chemical Bonding\n"
                    "| Type | Description | Example |\n"
                    "|------|-------------|---------|\n"
                    "| Ionic | Transfer of electrons | NaCl (salt) |\n"
                    "| Covalent | Sharing of electrons | H₂O (water) |\n"
                    "| Metallic | Delocalized electrons | Fe (iron) |\n\n"
                    "### States of Matter\n"
                    "1. **Solid**: Fixed shape and volume\n"
                    "2. **Liquid**: Fixed volume, takes shape of container\n"
                    "3. **Gas**: No fixed shape or volume\n"
                    "4. **Plasma**: Ionized gas (stars, lightning)\n\n"
                    "### Key Laws\n"
                    "- **Law of Conservation**: Mass is neither created nor destroyed\n"
                    "- **Law of Definite Proportions**: Compound always has same element ratio\n"
                    "- **Ideal Gas Law**: PV = nRT"
                )
            },
            "biology": {
                "keywords": ["biology", "cell", "dna", "evolution", "organism", "gene", "species", "ecosystem", "protein", "photosynthesis"],
                "response": (
                    "# 🧬 Biology\n\n"
                    "## Overview\n"
                    "Biology is the study of living organisms and their interactions with the environment.\n\n"
                    "## Key Concepts\n\n"
                    "### Cell Biology\n"
                    "- **Cell**: Basic unit of life\n"
                    "- **Prokaryotes**: No nucleus (bacteria)\n"
                    "- **Eukaryotes**: Have nucleus (plants, animals, fungi)\n\n"
                    "### DNA & Genetics\n"
                    "- **DNA**: Deoxyribonucleic acid - carries genetic information\n"
                    "- **Gene**: Segment of DNA that codes for a protein\n"
                    "- **Chromosome**: Structure containing many genes\n"
                    "- **Mutation**: Change in DNA sequence\n\n"
                    "### Evolution\n"
                    "- **Natural Selection**: Survival of the fittest\n"
                    "- **Adaptation**: Traits that improve survival\n"
                    "- **Speciation**: Formation of new species\n"
                    "- **Common Descent**: All life shares common ancestor\n\n"
                    "### Ecology\n"
                    "- **Ecosystem**: Community of living and non-living things\n"
                    "- **Food Chain**: Flow of energy through organisms\n"
                    "- **Biodiversity**: Variety of life in an area\n\n"
                    "### Key Processes\n"
                    "- **Photosynthesis**: 6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂\n"
                    "- **Cellular Respiration**: C₆H₁₂O₆ + 6O₂ → 6CO₂ + 6H₂O + ATP\n"
                    "- **Protein Synthesis**: DNA → mRNA → Protein"
                )
            },
            "astronomy": {
                "keywords": ["astronomy", "space", "planet", "star", "galaxy", "universe", "solar system", "moon", "sun", "earth", "mars", "jupiter"],
                "response": (
                    "# 🌌 Astronomy\n\n"
                    "## Overview\n"
                    "Astronomy is the study of celestial objects, space, and the universe.\n\n"
                    "## Solar System\n"
                    "| Planet | Distance from Sun | Key Feature |\n"
                    "|--------|-------------------|-------------|\n"
                    "| Mercury | 57.9 million km | Smallest, fastest orbit |\n"
                    "| Venus | 108.2 million km | Hottest, rotates backwards |\n"
                    "| Earth | 149.6 million km | Only known life |\n"
                    "| Mars | 227.9 million km | Red Planet, Olympus Mons |\n"
                    "| Jupiter | 778.5 million km | Largest, Great Red Spot |\n"
                    "| Saturn | 1,434 million km | Beautiful rings |\n"
                    "| Uranus | 2,871 million km | Tilted axis, ice giant |\n"
                    "| Neptune | 4,495 million km | Farthest, windiest |\n\n"
                    "## Key Concepts\n"
                    "- **Light Year**: Distance light travels in one year (9.46 trillion km)\n"
                    "- **Parsec**: 3.26 light years\n"
                    "- **Redshift**: Object moving away (universe expanding)\n"
                    "- **Black Hole**: Object with gravity so strong nothing escapes\n\n"
                    "## Universe Facts\n"
                    "- Age: ~13.8 billion years\n"
                    "- Size: ~93 billion light years in diameter\n"
                    "- Galaxies: ~2 trillion in observable universe\n"
                    "- Stars: ~200 billion trillion in universe"
                )
            },
            # ===== MATHEMATICS =====
            "math_formulas": {
                "keywords": ["formula", "equation", "calculate", "math", "algebra", "geometry", "trigonometry", "calculus", "statistics"],
                "response": (
                    "# 📐 Mathematics Formulas\n\n"
                    "## Algebra\n"
                    "| Formula | Description |\n"
                    "|---------|-------------|\n"
                    "| (a+b)² = a² + 2ab + b² | Square of sum |\n"
                    "| (a-b)² = a² - 2ab + b² | Square of difference |\n"
                    "| a² - b² = (a+b)(a-b) | Difference of squares |\n"
                    "| Quadratic: x = (-b ± √(b²-4ac)) / 2a | Solve ax²+bx+c=0 |\n\n"
                    "## Geometry\n"
                    "| Shape | Area | Perimeter/Circumference |\n"
                    "|-------|------|------------------------|\n"
                    "| Circle | πr² | 2πr |\n"
                    "| Rectangle | l × w | 2(l+w) |\n"
                    "| Triangle | ½ × b × h | a+b+c |\n"
                    "| Square | s² | 4s |\n\n"
                    "## Trigonometry\n"
                    "- sin θ = Opposite / Hypotenuse\n"
                    "- cos θ = Adjacent / Hypotenuse\n"
                    "- tan θ = Opposite / Adjacent\n"
                    "- sin²θ + cos²θ = 1\n\n"
                    "## Statistics\n"
                    "- Mean = Sum of values / Number of values\n"
                    "- Median = Middle value\n"
                    "- Mode = Most frequent value\n"
                    "- Standard Deviation = √(Σ(x-μ)²/N)\n\n"
                    "## Calculus\n"
                    "- Derivative: d/dx[xⁿ] = nxⁿ⁻¹\n"
                    "- Integral: ∫xⁿdx = xⁿ⁺¹/(n+1) + C\n"
                    "- Chain Rule: d/dx[f(g(x))] = f'(g(x)) × g'(x)"
                )
            },
            # ===== PSYCHOLOGY =====
            "psychology": {
                "keywords": ["psychology", "mental health", "brain", "behavior", "cognitive", "emotion", "memory", "learning", "therapy", "anxiety", "depression"],
                "response": (
                    "# 🧠 Psychology\n\n"
                    "## Overview\n"
                    "Psychology is the scientific study of the mind and behavior.\n\n"
                    "## Branches of Psychology\n"
                    "| Branch | Focus |\n"
                    "|--------|-------|\n"
                    "| Clinical | Mental health disorders |\n"
                    "| Cognitive | Mental processes (memory, thinking) |\n"
                    "| Developmental | Changes across lifespan |\n"
                    "| Social | How people affect each other |\n"
                    "| Behavioral | Observable behavior |\n"
                    "| Neuropsychology | Brain-behavior relationship |\n\n"
                    "## Key Concepts\n\n"
                    "### Memory\n"
                    "- **Sensory Memory**: Very brief (0.5-3 seconds)\n"
                    "- **Short-term Memory**: 15-30 seconds, 7±2 items\n"
                    "- **Long-term Memory**: Potentially unlimited capacity\n\n"
                    "### Learning Theories\n"
                    "- **Classical Conditioning** (Pavlov): Association between stimuli\n"
                    "- **Operant Conditioning** (Skinner): Rewards and punishments\n"
                    "- **Observational Learning** (Bandura): Learning by watching\n\n"
                    "### Cognitive Biases\n"
                    "- **Confirmation Bias**: Seeking confirming evidence\n"
                    "- **Anchoring**: Over-relying on first information\n"
                    "- **Availability**: Judging by easily recalled examples\n\n"
                    "### Mental Health\n"
                    "- **Anxiety Disorders**: Excessive worry and fear\n"
                    "- **Depression**: Persistent sadness and loss of interest\n"
                    "- **PTSD**: Trauma-related symptoms\n"
                    "- Treatment: Therapy, medication, lifestyle changes"
                )
            },
            # ===== TECHNOLOGY =====
            "artificial_intelligence": {
                "keywords": ["artificial intelligence", "ai", "machine learning", "deep learning", "neural network", "nlp", "computer vision"],
                "response": (
                    "# 🤖 Artificial Intelligence\n\n"
                    "## Overview\n"
                    "AI is the simulation of human intelligence by machines.\n\n"
                    "## Types of AI\n"
                    "| Type | Description | Example |\n"
                    "|------|-------------|---------|\n"
                    "| Narrow AI | Specific task | Siri, chess engines |\n"
                    "| General AI | Human-level intelligence | Not yet achieved |\n"
                    "| Super AI | Beyond human intelligence | Theoretical |\n\n"
                    "## Key Technologies\n"
                    "- **Machine Learning**: Systems learn from data\n"
                    "- **Deep Learning**: Neural networks with many layers\n"
                    "- **NLP**: Understanding human language\n"
                    "- **Computer Vision**: Interpreting images/video\n"
                    "- **Robotics**: Physical agents\n\n"
                    "## Applications\n"
                    "- Virtual assistants\n"
                    "- Self-driving cars\n"
                    "- Medical diagnosis\n"
                    "- Financial trading\n"
                    "- Game playing\n"
                    "- Content generation"
                )
            },
            "programming": {
                "keywords": ["programming", "coding", "code", "developer", "software", "algorithm", "data structure"],
                "response": (
                    "# 💻 Programming\n\n"
                    "## Overview\n"
                    "Programming is the process of creating instructions for computers.\n\n"
                    "## Popular Languages\n"
                    "| Language | Use Case |\n"
                    "|----------|----------|\n"
                    "| Python | Data science, AI, web |\n"
                    "| JavaScript | Web development |\n"
                    "| Java | Enterprise, Android |\n"
                    "| C++ | Systems, games |\n"
                    "| TypeScript | Large-scale web apps |\n"
                    "| Go | Cloud, microservices |\n"
                    "| Rust | Systems, safety-critical |\n\n"
                    "## Key Concepts\n"
                    "- **Variables**: Store data\n"
                    "- **Functions**: Reusable code blocks\n"
                    "- **Loops**: Repeat operations\n"
                    "- **Conditionals**: Decision making\n"
                    "- **OOP**: Object-oriented programming\n\n"
                    "## Data Structures\n"
                    "- Arrays, Linked Lists\n"
                    "- Stacks, Queues\n"
                    "- Trees, Graphs\n"
                    "- Hash Tables"
                )
            },
            # ===== HEALTH =====
            "health": {
                "keywords": ["health", "nutrition", "diet", "exercise", "fitness", "medical", "disease", "symptom", "treatment", "wellness"],
                "response": (
                    "# 🏥 Health & Wellness\n\n"
                    "## Overview\n"
                    "Health is a state of complete physical, mental, and social well-being.\n\n"
                    "## Physical Health\n\n"
                    "### Nutrition Guidelines\n"
                    "| Nutrient | Daily Recommendation |\n"
                    "|----------|---------------------|\n"
                    "| Calories | 2,000-2,500 (varies) |\n"
                    "| Protein | 0.8g per kg body weight |\n"
                    "| Water | 8 glasses (2 liters) |\n"
                    "| Fiber | 25-30g |\n"
                    "| Sodium | <2,300mg |\n\n"
                    "### Exercise Recommendations\n"
                    "- **Aerobic**: 150 min moderate OR 75 min vigorous per week\n"
                    "- **Strength**: 2+ days per week\n"
                    "- **Flexibility**: Stretching 2-3 times per week\n\n"
                    "## Mental Health\n"
                    "- **Sleep**: 7-9 hours for adults\n"
                    "- **Stress Management**: Meditation, exercise, social connection\n"
                    "- **Mindfulness**: Being present in the moment\n\n"
                    "## Preventive Care\n"
                    "- Regular check-ups\n"
                    "- Vaccinations\n"
                    "- screenings (blood pressure, cholesterol)\n"
                    "- Dental visits every 6 months"
                )
            },
            # ===== EXISTING TOPICS (kept for backward compatibility) =====
            "reinforcement_learning": {
                "keywords": ["reinforcement learning", "rl", "reward", "agent", "policy", "q-learning"],
                "response": (
                    "Reinforcement Learning (RL) is a type of machine learning where an agent learns to make decisions "
                    "by taking actions in an environment to maximize cumulative rewards.\n\n"
                    "Key concepts:\n"
                    "• Agent: The learner/decision-maker\n"
                    "• Environment: The world the agent interacts with\n"
                    "• Actions: Choices the agent can make\n"
                    "• Rewards: Feedback signals\n"
                    "• Policy: The strategy the agent follows\n\n"
                    "Applications: Game playing, robotics, autonomous vehicles, recommendation systems."
                )
            },
            "python": {
                "keywords": ["python", "python programming", "python language", "python code", "python script"],
                "response": (
                    "# 🐍 Python Programming Language\n\n"
                    "## Overview\n"
                    "Python is a popular, versatile programming language known for its readability and simplicity. "
                    "It's one of the most widely-used languages in the world.\n\n"
                    "## Key Features\n"
                    "- **Easy to Learn**: Simple syntax, great for beginners\n"
                    "- **Versatile**: Web dev, data science, AI, automation, scientific computing\n"
                    "- **Large Ecosystem**: Extensive libraries and frameworks\n"
                    "- **Cross-platform**: Windows, macOS, Linux\n"
                    "- **Dynamic Typing**: No need to declare variable types\n\n"
                    "## Popular Libraries\n"
                    "| Library | Use Case |\n"
                    "|---------|----------|\n"
                    "| NumPy | Numerical computing |\n"
                    "| Pandas | Data analysis |\n"
                    "| Matplotlib | Data visualization |\n"
                    "| TensorFlow/PyTorch | Machine learning |\n"
                    "| Django/Flask | Web development |\n"
                    "| FastAPI | Modern API development |\n\n"
                    "## Use Cases\n"
                    "- Data Science and Analytics\n"
                    "- Machine Learning and AI\n"
                    "- Web Development\n"
                    "- Automation and Scripting\n"
                    "- Scientific computing\n"
                    "- Game development\n\n"
                    "Python is one of the most popular languages worldwide and is used by companies like "
                    "Google, Netflix, Instagram, and Spotify."
                )
            },
            "javascript": {
                "keywords": ["javascript", "js", "react", "node", "frontend", "web development", "typescript"],
                "response": (
                    "JavaScript (JS) is a programming language primarily used for web development.\n\n"
                    "Key features:\n"
                    "• Runs in browsers and servers (Node.js)\n"
                    "• Event-driven and asynchronous\n"
                    "• Dynamic typing\n"
                    "• Prototype-based OOP\n\n"
                    "Popular frameworks/libraries:\n"
                    "• Frontend: React, Angular, Vue.js\n"
                    "• Backend: Node.js, Express.js, Fastify\n"
                    "• Mobile: React Native, Ionic\n"
                    "• Full-stack: Next.js, Nuxt.js\n\n"
                    "Use cases:\n"
                    "• Interactive web applications\n"
                    "• Single-page applications (SPAs)\n"
                    "• Server-side rendering\n"
                    "• Mobile apps\n"
                    "• Desktop apps (Electron)\n"
                    "• Game development\n\n"
                    "JavaScript is the most widely used programming language for web development, "
                    "with TypeScript adding static typing for larger projects."
                )
            },
            "api_web_services": {
                "keywords": ["api", "rest", "graphql", "endpoint", "web service", "http", "request", "response"],
                "response": (
                    "An API (Application Programming Interface) is a set of rules that allows different software "
                    "applications to communicate with each other.\n\n"
                    "Types of APIs:\n"
                    "• REST API: Uses HTTP methods (GET, POST, PUT, DELETE) with JSON/XML\n"
                    "• GraphQL: Query language for APIs, allows requesting specific data\n"
                    "• WebSocket: Real-time bidirectional communication\n"
                    "• gRPC: High-performance RPC framework\n\n"
                    "REST API Principles:\n"
                    "• Stateless: Each request contains all needed information\n"
                    "• Resource-based: URLs represent resources\n"
                    "• HTTP methods: GET (read), POST (create), PUT (update), DELETE (remove)\n"
                    "• Status codes: 200 (success), 404 (not found), 500 (error)\n\n"
                    "API Authentication:\n"
                    "• API Keys\n"
                    "• OAuth 2.0\n"
                    "• JWT (JSON Web Tokens)\n"
                    "• Basic Auth\n\n"
                    "APIs are essential for building modern applications, enabling microservices architecture, "
                    "and integrating different services together."
                )
            },
            "database": {
                "keywords": ["database", "sql", "mysql", "postgresql", "mongodb", "nosql", "data storage", "query"],
                "response": (
                    "Databases are organized collections of structured data stored electronically.\n\n"
                    "Types:\n"
                    "• Relational (SQL): MySQL, PostgreSQL, SQLite, Oracle\n"
                    "  - Uses tables with rows and columns\n"
                    "  - Structured Query Language (SQL)\n"
                    "  - ACID compliance\n\n"
                    "• Non-relational (NoSQL): MongoDB, Redis, Cassandra\n"
                    "  - Flexible schemas\n"
                    "  - Horizontal scaling\n"
                    "  - Various data models (document, key-value, graph)\n\n"
                    "Key concepts:\n"
                    "• Normalization: Organizing data to reduce redundancy\n"
                    "• Indexing: Speeding up data retrieval\n"
                    "• Transactions: Groups of operations treated as one unit\n"
                    "• Replication: Copying data for reliability\n"
                    "• Sharding: Distributing data across multiple servers\n\n"
                    "Choosing depends on your use case: SQL for structured data with relationships, "
                    "NoSQL for flexible schemas and high scalability."
                )
            },
            "networking": {
                "keywords": ["network", "networking", "internet", "tcp", "udp", "ip", "http", "protocol", "socket", "port"],
                "response": (
                    "Computer networking connects devices to share resources and communicate.\n\n"
                    "Key protocols:\n"
                    "• TCP/IP: Reliable transmission, connection-oriented\n"
                    "• UDP: Fast, connectionless, no guarantee of delivery\n"
                    "• HTTP/HTTPS: Web protocol (secure with TLS/SSL)\n"
                    "• DNS: Domain name resolution\n"
                    "• DHCP: Automatic IP configuration\n\n"
                    "Network layers (OSI model):\n"
                    "1. Physical: Cables, hardware\n"
                    "2. Data Link: MAC addresses, frames\n"
                    "3. Network: IP addresses, routing\n"
                    "4. Transport: TCP/UDP, ports\n"
                    "5. Session: Connection management\n"
                    "6. Presentation: Data formatting\n"
                    "7. Application: HTTP, FTP, SMTP\n\n"
                    "Common concepts:\n"
                    "• IP Address: Device identifier (IPv4/IPv6)\n"
                    "• Port: Application endpoint (80 for HTTP, 443 for HTTPS)\n"
                    "• Firewall: Security barrier\n"
                    "• NAT: Network Address Translation\n\n"
                    "Networking enables the internet, cloud computing, and modern distributed systems."
                )
            },
            "cybersecurity": {
                "keywords": ["security", "cybersecurity", "hack", "encryption", "firewall", "vulnerability", "malware", "password"],
                "response": (
                    "Cybersecurity protects systems, networks, and data from digital attacks.\n\n"
                    "Common threats:\n"
                    "• Malware: Viruses, ransomware, spyware\n"
                    "• Phishing: Deceptive emails/websites\n"
                    "• Man-in-the-middle: Intercepting communications\n"
                    "• DDoS: Overwhelming systems with traffic\n"
                    "• SQL Injection: Database attacks\n\n"
                    "Protection measures:\n"
                    "• Encryption: Protecting data (AES, RSA, TLS)\n"
                    "• Authentication: Verifying identity (MFA, biometrics)\n"
                    "• Firewalls: Filtering network traffic\n"
                    "• Updates: Patching vulnerabilities\n"
                    "• Backups: Data recovery\n\n"
                    "Best practices:\n"
                    "• Use strong, unique passwords\n"
                    "• Enable multi-factor authentication\n"
                    "• Be cautious of suspicious links/attachments\n"
                    "• Regular software updates\n"
                    "• VPN for secure connections\n\n"
                    "Cybersecurity is critical for protecting personal, corporate, and national assets."
                )
            },
            "cloud_computing": {
                "keywords": ["cloud", "aws", "azure", "google cloud", "hosting", "server", "deployment", "saas", "paas", "iaas"],
                "response": (
                    "Cloud computing delivers computing services over the internet.\n\n"
                    "Service models:\n"
                    "• IaaS (Infrastructure as a Service): Virtual machines, storage (AWS EC2, Azure VMs)\n"
                    "• PaaS (Platform as a Service): Development platforms (Heroku, Google App Engine)\n"
                    "• SaaS (Software as a Service): Applications (Gmail, Office 365)\n\n"
                    "Major providers:\n"
                    "• AWS (Amazon Web Services): Most comprehensive\n"
                    "• Microsoft Azure: Enterprise-focused\n"
                    "• Google Cloud Platform: AI/ML strengths\n\n"
                    "Benefits:\n"
                    "• Scalability: Adjust resources on demand\n"
                    "• Cost-effective: Pay only for what you use\n"
                    "• Reliability: Built-in redundancy\n"
                    "• Global reach: Data centers worldwide\n\n"
                    "Use cases:\n"
                    "• Web application hosting\n"
                    "• Data storage and backup\n"
                    "• Machine learning and AI\n"
                    "• DevOps and CI/CD\n"
                    "• IoT and edge computing\n\n"
                    "Cloud has become the default for modern application deployment."
                )
            },
            "data_science": {
                "keywords": ["data science", "analytics", "visualization", "statistics", "big data", "pandas", "numpy"],
                "response": (
                    "Data Science combines statistics, programming, and domain knowledge to extract insights from data.\n\n"
                    "Key components:\n"
                    "• Data Collection: Gathering relevant data\n"
                    "• Data Cleaning: Handling missing values, outliers\n"
                    "• Exploratory Data Analysis (EDA): Understanding patterns\n"
                    "• Feature Engineering: Creating useful variables\n"
                    "• Modeling: Applying ML algorithms\n"
                    "• Communication: Presenting findings\n\n"
                    "Essential tools:\n"
                    "• Python: Pandas, NumPy, Matplotlib, Seaborn\n"
                    "• R: ggplot2, dplyr\n"
                    "• SQL: Data querying\n"
                    "• Tableau/Power BI: Visualization\n"
                    "• Jupyter Notebooks: Interactive analysis\n\n"
                    "Applications:\n"
                    "• Business intelligence\n"
                    "• Predictive analytics\n"
                    "• Customer segmentation\n"
                    "• Fraud detection\n"
                    "• Healthcare analytics\n"
                    "• Scientific research\n\n"
                    "Data scientists need a mix of technical skills, statistical knowledge, and business acumen."
                )
            },
            "devops": {
                "keywords": ["devops", "ci/cd", "docker", "kubernetes", "container", "pipeline", "deployment", "automation"],
                "response": (
                    "DevOps combines development and operations to improve software delivery.\n\n"
                    "Key practices:\n"
                    "• Continuous Integration (CI): Frequent code integration and testing\n"
                    "• Continuous Delivery (CD): Automated deployment\n"
                    "• Infrastructure as Code (IaC): Automated infrastructure management\n"
                    "• Monitoring and Logging: System observability\n\n"
                    "Popular tools:\n"
                    "• Containers: Docker, Podman\n"
                    "• Orchestration: Kubernetes, Docker Swarm\n"
                    "• CI/CD: Jenkins, GitHub Actions, GitLab CI\n"
                    "• IaC: Terraform, Ansible, CloudFormation\n"
                    "• Monitoring: Prometheus, Grafana, ELK Stack\n\n"
                    "Benefits:\n"
                    "• Faster deployment cycles\n"
                    "• Improved reliability\n"
                    "• Better collaboration\n"
                    "• Automated testing and deployment\n"
                    "• Scalability\n\n"
                    "DevOps culture emphasizes communication, collaboration, and automation between development and operations teams."
                )
            },
            "phone": {
                "keywords": ["phone", "mobile", "call", "telephone", "smartphone"],
                "response": (
                    "A phone (smartphone) is a mobile device that combines communication, computing, and internet capabilities.\n\n"
                    "Key features:\n"
                    "• Voice calls and messaging\n"
                    "• Internet access and web browsing\n"
                    "• Camera and photo/video capture\n"
                    "• GPS navigation\n"
                    "• App ecosystem\n"
                    "• Touchscreen interface\n\n"
                    "Major operating systems:\n"
                    "• iOS (Apple iPhone)\n"
                    "• Android (Samsung, Google Pixel, etc.)\n\n"
                    "Common uses:\n"
                    "• Communication (calls, texts, social media)\n"
                    "• Photography and video\n"
                    "• Navigation and maps\n"
                    "• Entertainment (games, streaming)\n"
                    "• Productivity (email, documents)\n"
                    "• Online shopping and banking\n\n"
                    "Modern smartphones are powerful computers that fit in your pocket, enabling constant connectivity."
                )
            },
            "computer": {
                "keywords": ["computer", "pc", "laptop", "desktop", "hardware", "software", "operating system"],
                "response": (
                    "A computer is an electronic device that processes data to produce information.\n\n"
                    "Key components:\n"
                    "Hardware:\n"
                    "• CPU (Central Processing Unit): The brain\n"
                    "• RAM (Random Access Memory): Working memory\n"
                    "• Storage (HDD/SSD): Data storage\n"
                    "• GPU (Graphics Processing Unit): Visual processing\n"
                    "• Motherboard: Connects all components\n\n"
                    "Software:\n"
                    "• Operating System: Windows, macOS, Linux\n"
                    "• Applications: Programs for specific tasks\n"
                    "• Drivers: Hardware communication\n\n"
                    "Types:\n"
                    "• Desktop: Stationary, powerful\n"
                    "• Laptop: Portable, integrated\n"
                    "• Server: High-performance for networks\n"
                    "• Embedded: Specialized functions\n\n"
                    "Computers are essential tools for work, education, entertainment, and communication in the modern world."
                )
            },
            "internet": {
                "keywords": ["internet", "web", "website", "online", "browser", "www"],
                "response": (
                    "The internet is a global network of interconnected computer networks.\n\n"
                    "How it works:\n"
                    "• Data is broken into packets\n"
                    "• Packets travel through routers\n"
                    "• Packets are reassembled at destination\n"
                    "• Protocols (TCP/IP) ensure reliable delivery\n\n"
                    "Key technologies:\n"
                    "• HTTP/HTTPS: Web browsing\n"
                    "• DNS: Translates domain names to IP addresses\n"
                    "• SSL/TLS: Encryption for security\n"
                    "• CDN: Content delivery networks\n\n"
                    "Internet services:\n"
                    "• World Wide Web: Websites and web applications\n"
                    "• Email: Electronic messaging\n"
                    "• File Transfer: FTP, cloud storage\n"
                    "• Streaming: Video, audio, gaming\n"
                    "• Social Media: Online communities\n\n"
                    "The internet has revolutionized communication, commerce, education, and entertainment, "
                    "connecting billions of people worldwide."
                )
            },
            "blockchain": {
                "keywords": ["blockchain", "crypto", "bitcoin", "ethereum", "cryptocurrency", "token", "nft", "defi"],
                "response": (
                    "Blockchain is a distributed, immutable ledger technology.\n\n"
                    "Key concepts:\n"
                    "• Block: Group of transactions\n"
                    "• Chain: Linked blocks using cryptography\n"
                    "• Distributed: Copies across many computers\n"
                    "• Immutable: Cannot be altered once added\n\n"
                    "How it works:\n"
                    "1. Transaction is requested\n"
                    "2. Transaction is broadcast to network\n"
                    "3. Network validates the transaction\n"
                    "4. Transaction is combined with others in a block\n"
                    "5. Block is added to the chain\n"
                    "6. Transaction is complete\n\n"
                    "Applications:\n"
                    "• Cryptocurrency: Bitcoin, Ethereum\n"
                    "• Smart Contracts: Self-executing agreements\n"
                    "• Supply Chain: Tracking goods\n"
                    "• Healthcare: Medical records\n"
                    "• Voting: Secure elections\n\n"
                    "Blockchain enables trustless transactions without intermediaries."
                )
            },
            "quantum_computing": {
                "keywords": ["quantum", "qubit", "quantum computing", "superposition", "entanglement"],
                "response": (
                    "Quantum computing uses quantum mechanics to process information.\n\n"
                    "Key concepts:\n"
                    "• Qubit: Quantum bit (0, 1, or both simultaneously)\n"
                    "• Superposition: Multiple states at once\n"
                    "• Entanglement: Connected qubits\n"
                    "• Quantum Gate: Operations on qubits\n\n"
                    "Advantages:\n"
                    "• Exponential speedup for certain problems\n"
                    "• Parallel processing through superposition\n"
                    "• Better optimization and simulation\n\n"
                    "Applications:\n"
                    "• Cryptography: Breaking/creating secure codes\n"
                    "• Drug Discovery: Molecular simulation\n"
                    "• Financial Modeling: Portfolio optimization\n"
                    "• Climate Modeling: Complex simulations\n"
                    "• Artificial Intelligence: Faster training\n\n"
                    "Current limitations:\n"
                    "• Qubits are fragile (decoherence)\n"
                    "• Requires extreme cooling\n"
                    "• High error rates\n\n"
                    "Companies like IBM, Google, and startups are advancing quantum computing technology."
                )
            },
            "robotics": {
                "keywords": ["robot", "robotics", "automation", "android", "humanoid", "drone"],
                "response": (
                    "Robotics combines engineering, computer science, and AI to create machines that can perform tasks.\n\n"
                    "Types of robots:\n"
                    "• Industrial: Manufacturing, assembly lines\n"
                    "• Service: Healthcare, hospitality\n"
                    "• Military: Defense applications\n"
                    "• Medical: Surgery, rehabilitation\n"
                    "• Domestic: Vacuum cleaners, lawn mowers\n\n"
                    "Key components:\n"
                    "• Sensors: Input from environment\n"
                    "• Actuators: Movement (motors, hydraulics)\n"
                    "• Controller: Processing and decision-making\n"
                    "• Power Source: Batteries, electricity\n\n"
                    "AI in robotics:\n"
                    "• Computer Vision: Seeing and recognizing objects\n"
                    "• Motion Planning: Navigating environments\n"
                    "• Natural Language: Understanding commands\n"
                    "• Machine Learning: Improving performance\n\n"
                    "Applications:\n"
                    "• Manufacturing and logistics\n"
                    "• Healthcare and surgery\n"
                    "• Space exploration\n"
                    "• Disaster response\n"
                    "• Agriculture\n\n"
                    "Robotics is transforming industries and creating new possibilities for automation."
                )
            }
        }
    
    def find_response(self, query: str) -> Optional[str]:
        """Find a response based on query keywords using word-boundary matching."""
        query_lower = query.lower()
        
        # Score each topic by keyword matches
        import re
        scores: Dict[str, int] = {}
        for topic, data in self.knowledge.items():
            score = 0
            for keyword in data["keywords"]:
                # Use word-boundary regex to avoid substring false positives
                # e.g. "ai" should NOT match inside "explain" or "chain"
                if re.search(r'\b' + re.escape(keyword) + r'\b', query_lower):
                    # Longer keywords get more weight
                    score += len(keyword.split())
            if score > 0:
                scores[topic] = score
        
        # Return best matching response
        if scores:
            best_topic = max(scores, key=scores.get)
            response = self.knowledge[best_topic]["response"]
            
            # Simple constraint processing for offline mock
            if "2 lines" in query_lower or "two lines" in query_lower:
                lines = [line for line in response.split('\n') if line.strip()]
                return "\n".join(lines[:2])
            elif "sentence" in query_lower:
                # Approximate 1 sentence by returning the first line
                lines = [line for line in response.split('\n') if line.strip()]
                return lines[0] if lines else response
                
            return response
        
        return None


# Global knowledge base instance
knowledge_base = LocalKnowledgeBase()


class LLMBridge:
    # Bounded LRU cache to prevent memory leaks
    MAX_CACHE_SIZE = int(os.getenv("LLM_CACHE_MAX_SIZE", "500"))

    def __init__(self):
        openai_key = os.getenv("OPENAI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip() or "llama-3.1-8b-instant"

        self.openai_client = AsyncOpenAI(api_key=openai_key) if AsyncOpenAI and openai_key else None
        self.groq_client = AsyncGroq(api_key=groq_key) if AsyncGroq and groq_key else None
        self.google_key = os.getenv("GOOGLE_API_KEY")
        mistral_key = os.getenv("MISTRAL_API_KEY")
        self.mistral_client = MistralClient(api_key=mistral_key) if MistralClient and mistral_key else None

        if genai and self.google_key:
            genai.configure(api_key=self.google_key)

        # Bounded LRU cache (OrderedDict)
        self.cache: OrderedDict[str, str] = OrderedDict()

    async def call_llm(self, model: str, prompt: str) -> str:
        if not prompt or not isinstance(prompt, str):
            raise ValueError("Prompt must be a non-empty string")

        prompt = prompt.strip()
        key = hashlib.sha256(f"{model}:{prompt}".encode()).hexdigest()

        if key in self.cache:
            return self.cache[key]

        try:
            # ----- OPENAI -----
            if model == "chatgpt":
                if not self.openai_client:
                    if AsyncOpenAI is None:
                        raise ImportError("openai package is not installed")
                    raise ValueError("OPENAI_API_KEY is not configured")
                response = await self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                output = response.choices[0].message.content

            # ----- GROQ -----
            elif model == "groq":
                if not self.groq_client:
                    if AsyncGroq is None:
                        raise ImportError("groq package is not installed")
                    raise ValueError("GROQ_API_KEY is not configured")
                response = await self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                output = response.choices[0].message.content

            # ----- GEMINI -----
            elif model == "gemini":
                if not genai:
                    raise ImportError("google-generativeai not installed")
                gemini_model = genai.GenerativeModel("gemini-pro")
                result = await asyncio.to_thread(
                    gemini_model.generate_content,
                    prompt,
                    generation_config={"temperature": 0},
                )
                output = result.text

            # ----- MISTRAL -----
            elif model == "mistral":
                if not self.mistral_client:
                    raise ImportError("mistralai not installed")
                result = await asyncio.to_thread(
                    self.mistral_client.chat,
                    model="mistral-medium",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                output = result.choices[0].message["content"]

            # ----- UNIGURU -----
            elif model == "uniguru":
                # Use local knowledge base for meaningful responses
                # Extract the user query from the prompt
                user_query_match = re.search(r"User (?:request|question):\s*(.+?)(?:\n|$)", prompt)
                if user_query_match:
                    user_query = user_query_match.group(1).strip()
                else:
                    # Try to extract from the end of the prompt
                    lines = prompt.strip().split("\n")
                    user_query = lines[-1] if lines else prompt[:100]
                
                # Check cache first
                key = hashlib.sha256(f"uniguru:{user_query}".encode()).hexdigest()
                if key in self.cache:
                    output = self.cache[key]
                else:
                    # Try to find a response from knowledge base
                    kb_response = knowledge_base.find_response(user_query)
                    if kb_response:
                        output = kb_response
                    else:
                        # Generic helpful response
                        output = (
                            f"[uniguru mock] Regarding your question about '{user_query[:50]}...': "
                            f"I can help with that! While I don't have real-time internet access, "
                            f"I can provide information based on my training data.\n\n"
                            f"Could you be more specific about what aspect you'd like me to explain?"
                        )

            else:
                raise ValueError(f"Unsupported model: {model}")

        except Exception as e:
            logger.warning("LLM fallback triggered for model %s: %s", model, e)
            # Fallback to mock response on any error
            output = f"[{model.capitalize()} Mock] Response to: Context: {prompt[:50]}..."

        # Cache with LRU eviction
        # Don't cache uniguru responses to ensure fresh knowledge base responses
        if model != "uniguru":
            self.cache[key] = output
            if len(self.cache) > self.MAX_CACHE_SIZE:
                self.cache.popitem(last=False)  # Remove oldest entry

        return output


llm_bridge = LLMBridge()
