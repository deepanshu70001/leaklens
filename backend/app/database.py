"""
Motor (async MongoDB driver) client and database lifecycle management.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None


async def connect_to_mongo():
    """Open the Motor client and bind the database reference."""
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.DATABASE_NAME]

    # Create indexes for query speed (§4)
    await db.transactions.create_index("user_id")
    await db.subscriptions.create_index("user_id")
    await db.leak_scores.create_index("subscription_id")
    await db.price_history.create_index("subscription_id")
    await db.actions.create_index("user_id")
    await db.actions.create_index("subscription_id")

    print(f"✓ Connected to MongoDB: {settings.DATABASE_NAME}")


async def close_mongo_connection():
    """Gracefully shut down the Motor client."""
    global client
    if client:
        client.close()
        print("✗ Disconnected from MongoDB")


def get_database() -> AsyncIOMotorDatabase:
    """FastAPI dependency — returns the active database handle."""
    return db
