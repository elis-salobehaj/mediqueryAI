import pytest
from fastapi.testclient import TestClient
from main import app
from services.auth_service import auth_service
from services.database import db_service

client = TestClient(app)

# Reset DB for tests
@pytest.fixture(scope="module", autouse=True)
def setup_db():
    # Use in-memory DB or temporary file for testing could be better, 
    # but for now we rely on the implementation.
    # We'll create a test user.
    auth_service.create_user("testuser", "testpass", "Test User", "test@example.com")
    yield

def test_login_success():
    response = client.post(
        "/auth/token",
        data={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_failure():
    response = client.post(
        "/auth/token",
        data={"username": "testuser", "password": "wrongpassword"}
    )
    assert response.status_code == 401

def test_protected_route_without_token():
    response = client.get("/history")
    assert response.status_code == 401

def test_protected_route_with_token():
    # Login first
    login_res = client.post(
        "/auth/token",
        data={"username": "testuser", "password": "testpass"}
    )
    token = login_res.json()["access_token"]
    
    # Access protected route
    response = client.get(
        "/history",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

def test_register_duplicate_user():
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "password": "newpass"}
    )
    assert response.status_code == 400
