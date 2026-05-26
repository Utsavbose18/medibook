import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_user(client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpass123",
            "phone": "9999999999"
        }
    )
    if response.status_code == 400: # in case already exists from previous test run not cleaned up
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpass123"
            }
        )
    return response.json()

@pytest.fixture
def admin_user(client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Admin User",
            "email": "admin_test@example.com",
            "password": "adminpass123",
            "phone": "8888888888"
        }
    )
    if response.status_code == 400:
        response = client.post(
            "/api/auth/login",
            json={
                "email": "admin_test@example.com",
                "password": "adminpass123"
            }
        )

    # Manually update role to admin in db
    with TestingSessionLocal() as db:
        from app.models import User
        user = db.query(User).filter(User.email == "admin_test@example.com").first()
        user.role = "admin"
        db.commit()

    # Re-login to get admin token
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin_test@example.com",
            "password": "adminpass123"
        }
    )
    return response.json()

@pytest.fixture(autouse=True)
def clean_db(db_session):
    yield
    # clear tables after each test except users to keep test_user fixture happy
    from app.models import Appointment, Doctor
    db_session.query(Appointment).delete()
    db_session.query(Doctor).delete()
    db_session.commit()
