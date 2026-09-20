"""Integration test for FastAPI health and authentication endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "version" in data


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["user_count"] >= 3  # Admin, Reviewer, User seeded


def test_login_and_auth_me_flow():
    # 1. Login with seeded admin
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin@pbnc.internal", "password": "admin12345"},
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 2. Access protected /auth/me with token
    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["email"] == "admin@pbnc.internal"
    assert user_data["role"] == "admin"


def test_login_invalid_password():
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "admin@pbnc.internal", "password": "wrong_password"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]
