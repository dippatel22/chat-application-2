"""
Database connection and utilities for MongoDB.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import settings
import logging

logger = logging.getLogger(__name__)

# Global database client
client: AsyncIOMotorClient = None
database: AsyncIOMotorDatabase = None


async def connect_to_mongo():
    """Establish connection to MongoDB."""
    global client, database
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        database = client[settings.DATABASE_NAME]
        # Test the connection
        await client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """Get the database instance."""
    return database


async def create_indexes():
    """Create necessary database indexes for performance."""
    db = get_database()
    
    # Users collection indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username")
    
    # Messages collection indexes
    await db.messages.create_index([("sender", 1), ("timestamp", -1)])
    await db.messages.create_index([("recipient", 1), ("timestamp", -1)])
    await db.messages.create_index("timestamp")
    
    # Activity logs collection indexes
    await db.activity_logs.create_index([("timestamp", -1)])
    await db.activity_logs.create_index("user_email")
    
    logger.info("Database indexes created successfully")







