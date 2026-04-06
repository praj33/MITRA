import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "ai_assistant")
MONGODB_SERVER_SELECTION_TIMEOUT_MS = int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000"))
MONGODB_CONNECT_TIMEOUT_MS = int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "5000"))
MONGODB_SOCKET_TIMEOUT_MS = int(os.getenv("MONGODB_SOCKET_TIMEOUT_MS", "5000"))

client = AsyncIOMotorClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=MONGODB_SERVER_SELECTION_TIMEOUT_MS,
    connectTimeoutMS=MONGODB_CONNECT_TIMEOUT_MS,
    socketTimeoutMS=MONGODB_SOCKET_TIMEOUT_MS,
)
db = client[DATABASE_NAME]

# Collections
tasks_collection = db["tasks"]
audit_collection = db["audit_logs"]
users_collection = db["users"]

async def get_db():
    return db

async def create_tables():
    # MongoDB creates collections automatically
    # Create indexes for performance
    await tasks_collection.create_index("created_at")
    await tasks_collection.create_index("trace_id", unique=True)  # Add trace_id index
    await audit_collection.create_index("trace_id")
    await audit_collection.create_index("timestamp")
    await users_collection.create_index("email", unique=True)
    await users_collection.create_index("created_at")
