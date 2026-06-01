import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from mongomock_motor import AsyncMongoMockClient
from beanie import init_beanie

from app.main import app
from app.models import User, Doctor, Appointment
from app.seed import seed_data

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    client = AsyncMongoMockClient()
    db = client.test_medibook

    await init_beanie(database=db, document_models=[User, Doctor, Appointment])

    # We clear the collections to start fresh on every test function
    await User.delete_all()
    await Doctor.delete_all()
    await Appointment.delete_all()

    # Optional: If you want tests to start with seeded data, uncomment the following line
    # await seed_data()
    yield

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def test_user(client):
    response = await client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpass123",
            "phone": "9999999999"
        }
    )
    if response.status_code == 400: # in case already exists
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpass123"
            }
        )
    return response.json()

@pytest_asyncio.fixture
async def admin_user(client):
    response = await client.post(
        "/api/auth/register",
        json={
            "name": "Admin User",
            "email": "admin_test@example.com",
            "password": "adminpass123",
            "phone": "8888888888"
        }
    )
    if response.status_code == 400:
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "admin_test@example.com",
                "password": "adminpass123"
            }
        )

    # Manually update role to admin in db
    user = await User.find_one(User.email == "admin_test@example.com")
    if user:
        user.role = "admin"
        await user.save()

    # Re-login to get admin token
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "admin_test@example.com",
            "password": "adminpass123"
        }
    )
    return response.json()
