"""
Test cases for authentication API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
def test_login(client: TestClient):
    """Test login endpoint."""
    # Arrange
    login_data = {
        "email": "admin@test.com",
        "password": "adminpass"
    }
    
    # Act
    response = client.post("/api/v1/auth/login", json=login_data)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["email"] == "admin@test.com"


@pytest.mark.api
def test_login_wrong_credentials(client: TestClient):
    """Test login endpoint with wrong credentials."""
    # Arrange
    login_data = {
        "email": "admin@test.com",
        "password": "wrongpassword"
    }
    
    # Act
    response = client.post("/api/v1/auth/login", json=login_data)
    
    # Assert
    assert response.status_code == 401


@pytest.mark.api
def test_current_user(client: TestClient, admin_authentication_headers):
    """Test getting current user endpoint."""
    # Act
    response = client.get(
        "/api/v1/auth/me", headers=admin_authentication_headers
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@test.com"
    assert data["role"] == "admin"


@pytest.mark.api
def test_current_user_unauthorized(client: TestClient):
    """Test getting current user endpoint without authentication."""
    # Act
    response = client.get("/api/v1/auth/me")
    
    # Assert
    assert response.status_code == 401