from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base
from app.deps import get_db


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(test_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_openapi_available(client: TestClient):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert r.json()["info"]["title"] == "Task Manager API"


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] in {"ok", "degraded"}


def test_create_get_etag(client: TestClient):
    payload = {"title": "Написать тесты", "description": "Покрыть CRUD", "status": "created"}
    r = client.post("/tasks/", json=payload)
    assert r.status_code == 201
    data = r.json()
    tid = data["id"]
    uuid.UUID(tid)

    r2 = client.get(f"/tasks/{tid}")
    assert r2.status_code == 200
    assert "ETag" in r2.headers
    assert int(r2.headers["ETag"]) == data["version"]


def test_list_with_meta(client: TestClient):
    # создадим несколько задач
    for i in range(5):
        client.post("/tasks/", json={"title": f"T{i}", "status": "created"})
    r = client.get("/tasks/?offset=1&limit=3")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "meta" in body
    assert len(body["items"]) == 3
    assert isinstance(body["meta"]["total"], int)
    assert body["meta"]["offset"] == 1
    assert body["meta"]["limit"] == 3


def test_invalid_transition_conflict(client: TestClient):
    r = client.post("/tasks/", json={"title": "Done", "status": "completed"})
    tid = r.json()["id"]

    # попытка вернуться в in_progress -> 409
    r2 = client.patch(f"/tasks/{tid}", json={"status": "in_progress"})
    assert r2.status_code == 409
    assert "Transition" in r2.json()["detail"]


def test_patch_with_etag_precondition(client: TestClient):
    r = client.post("/tasks/", json={"title": "With ETag", "status": "created"})
    tid = r.json()["id"]

    # получим версию
    r2 = client.get(f"/tasks/{tid}")
    etag = r2.headers["ETag"]
    assert etag

    # неверная версия -> 412
    r3 = client.patch(f"/tasks/{tid}", json={"title": "New"}, headers={"If-Match": "999"})
    assert r3.status_code == 412

    # корректная версия -> 200, и версия инкрементится
    r4 = client.patch(f"/tasks/{tid}", json={"title": "New"}, headers={"If-Match": etag})
    assert r4.status_code == 200
    assert int(r4.headers["ETag"]) == r4.json()["version"]
    assert int(r4.headers["ETag"]) == int(etag) + 1


def test_delete_and_not_found(client: TestClient):
    r = client.post("/tasks/", json={"title": "Remove me"})
    tid = r.json()["id"]

    r2 = client.delete(f"/tasks/{tid}")
    assert r2.status_code == 204

    assert client.get(f"/tasks/{tid}").status_code == 404


def test_validation_errors(client: TestClient):
    assert client.post("/tasks/", json={"title": ""}).status_code == 422
    assert client.post("/tasks/", json={"title": "ok", "status": "wrong"}).status_code == 422

    r = client.post("/tasks/", json={"title": "Patch"})
    tid = r.json()["id"]
    assert client.patch(f"/tasks/{tid}", json={"status": "done"}).status_code == 422
