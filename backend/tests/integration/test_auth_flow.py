def test_user_registration_and_login(client):
    reg_response = client.post(
        "/api/auth/register",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "SecurePass123",
            "phone": "9876543210"
        }
    )
    assert reg_response.status_code == 200
    data = reg_response.json()
    assert "token" in data
    assert data["user"]["email"] == "john@example.com"

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "john@example.com",
            "password": "SecurePass123"
        }
    )
    assert login_response.status_code == 200
    assert "token" in login_response.json()

def test_invalid_login_returns_401(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "wrongpass"}
    )
    assert response.status_code == 401

def test_invalid_password_returns_401(client, test_user):
    response = client.post(
        "/api/auth/login",
        json={"email": test_user["user"]["email"], "password": "wrongpass"}
    )
    assert response.status_code == 401

def test_duplicate_email_fails(client, test_user):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Another User",
            "email": test_user["user"]["email"],
            "password": "password123",
            "phone": "9999999999"
        }
    )
    assert response.status_code == 400
