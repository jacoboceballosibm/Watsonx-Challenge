"""Shared pytest fixtures for ProM backend tests."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "test_prom.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("DEMO_PASSWORD", "password")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "")

    # Ensure database module picks up the temp path
    import app.services.database as database

    monkeypatch.setattr(database, "DATABASE_URL", f"sqlite:///{db_path}")

    from app.main import app
    from app.services.application_service import seed_applications
    from app.services.auth_service import seed_users
    from app.services.cv_service import seed_cvs_from_profiles
    from app.services.database import init_database
    from app.services.profile_service import seed_profiles
    from app.services.seat_service import seed_seats

    init_database()
    seed_profiles()
    seed_cvs_from_profiles()
    seed_users()
    seed_seats()
    seed_applications()

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def owner_token(client: TestClient) -> str:
    res = client.post("/api/auth/login", json={"username": "mchen", "password": "password"})
    assert res.status_code == 200
    return res.json()["token"]


@pytest.fixture()
def candidate_token(client: TestClient) -> dict:
    res = client.post("/api/auth/login", json={"username": "jsmith", "password": "password"})
    assert res.status_code == 200
    return res.json()
