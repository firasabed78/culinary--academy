"""
Test cases for course API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
def test_get_courses(client: TestClient):
    """Test getting all courses endpoint."""
    # Act
    response = client.get("/api/v1/courses/")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 2
    assert data["total"] >= 2


@pytest.mark.api
def test_get_course(client: TestClient):
    """Test getting a specific course endpoint."""
    # Act
    response = client.get("/api/v1/courses/1")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "title" in data
    assert "description" in data


@pytest.mark.api
def test_get_course_not_found(client: TestClient):
    """Test getting a non-existent course."""
    # Act
    response = client.get("/api/v1/courses/999")
    
    # Assert
    assert response.status_code == 404


@pytest.mark.api
def test_create_course(client: TestClient, admin_authentication_headers):
    """Test creating a course endpoint."""
    # Arrange
    course_data = {
        "title": "API Test Course",
        "description": "Course created through API test",
        "instructor_id": 2,
        "duration": 30,
        "price": 950.00,
        "capacity": 25,
        "is_active": True
    }
    
    # Act
    response = client.post(
        "/api/v1/courses/",
        json=course_data,
        headers=admin_authentication_headers
    )
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "API Test Course"
    assert data["price"] == 950.00
    assert data["capacity"] == 25


@pytest.mark.api
def test_create_course_unauthorized(client: TestClient):
    """Test creating a course without authentication."""
    # Arrange
    course_data = {
        "title": "Unauthorized Course",
        "description": "This should fail",
        "instructor_id": 2,
        "duration": 10,
        "price": 100.00,
        "capacity": 5,
        "is_active": True
    }
    
    # Act
    response = client.post("/api/v1/courses/", json=course_data)
    
    # Assert
    assert response.status_code == 401


@pytest.mark.api
def test_update_course(client: TestClient, admin_authentication_headers):
    """Test updating a course endpoint."""
    # Arrange
    update_data = {
        "title": "Updated API Course",
        "price": 1050.00
    }
    
    # Act
    response = client.patch(
        "/api/v1/courses/1",
        json=update_data,
        headers=admin_authentication_headers
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Updated API Course"
    assert data["price"] == 1050.00