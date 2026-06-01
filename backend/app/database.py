import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

# We will import models later to initialize beanie
# from .models import User, Doctor, Appointment

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/medibook")

async def init_db():
    client = AsyncIOMotorClient(MONGODB_URI)
    # The database name defaults to the one in the URI or "medibook"
    db_name = client.get_database().name if client.get_database().name else "medibook"
    db = client[db_name]

    # Initialize beanie with the models
    # We delay the model import to avoid circular dependency since models might need something from here if any
    from .models import User, Doctor, Appointment
    await init_beanie(database=db, document_models=[User, Doctor, Appointment])
