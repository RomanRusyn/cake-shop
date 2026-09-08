import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from pwdlib import PasswordHash
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from config import settings
from database import Base, get_session
from main import app
from tests.credentials import ADMIN_PASSWORD, ADMIN_USERNAME


@pytest.fixture
def client(monkeypatch):
    # Temporary credentials used only during this tests.
    monkeypatch.setattr(settings, "admin_username", ADMIN_USERNAME)
    monkeypatch.setattr(
        settings,
        "admin_password_hash",
        SecretStr(PasswordHash.recommended().hash(ADMIN_PASSWORD)),
    )

    # A fresh database in memory for each tests.
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)

    def get_test_session():
        with Session(test_engine) as session:
            yield session

    # Route database requests to the temporary database.
    monkeypatch.setitem(
        app.dependency_overrides,
        get_session,
        get_test_session,
    )

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        test_engine.dispose()


@pytest.fixture
def db_session(client):
    get_test_session = app.dependency_overrides[get_session]
    yield from get_test_session()