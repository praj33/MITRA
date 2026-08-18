import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

logger = logging.getLogger(__name__)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "ai_assistant")
MONGODB_SERVER_SELECTION_TIMEOUT_MS = int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000"))
MONGODB_CONNECT_TIMEOUT_MS = int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "5000"))
MONGODB_SOCKET_TIMEOUT_MS = int(os.getenv("MONGODB_SOCKET_TIMEOUT_MS", "5000"))

# Enterprise High-Scale Motor Client with Connection Pooling
client = AsyncIOMotorClient(
    MONGODB_URI,
    maxPoolSize=int(os.getenv("MONGODB_MAX_POOL_SIZE", "100")),
    minPoolSize=int(os.getenv("MONGODB_MIN_POOL_SIZE", "10")),
    maxIdleTimeMS=int(os.getenv("MONGODB_MAX_IDLE_TIME_MS", "30000")),
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
    """Ensure compound indexes on all collections for sub-5ms 100k user scale."""
    try:
        await tasks_collection.create_index([("user_id", 1), ("created_at", -1)])
        await tasks_collection.create_index("trace_id", unique=True, sparse=True)
        await audit_collection.create_index([("user_id", 1), ("timestamp", -1)])
        await audit_collection.create_index("trace_id")
        await users_collection.create_index("email", unique=True, sparse=True)
        await users_collection.create_index("created_at")

        # Enterprise user collections indexes
        await db["user_tasks"].create_index([("user_id", 1), ("created_at", -1)])
        await db["reminders"].create_index([("user_id", 1), ("created_at", -1)])
        await db["calendar_events"].create_index([("user_id", 1), ("created_at", -1)])
        await db["companion_history"].create_index([("user_id", 1), ("updated_at", -1)])
        await db["user_facts"].create_index([("user_id", 1)])
        await db["bucket_traces"].create_index([("user_id", 1), ("timestamp", -1)])
        logger.info("Enterprise database compound indexes successfully verified.")
    except Exception as e:
        logger.warning(f"Database index creation warning: {e}")
