"""API integration tests."""

import pytest
from fastapi.testclient import TestClient

from daily_forge.database import DB_PATH, init_db
from daily_forge.main import app


@pytest.fixture(autouse=True)
def clean_db(tmp_path, monkeypatch):
    """Use a fresh SQLite file per test."""
    test_db = tmp_path / "test.db"
    monkeypatch.setattr("daily_forge.database.DB_PATH", test_db)
    init_db()
    yield
    if test_db.exists():
        test_db.unlink()


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_stats_new_user(client):
    res = client.get("/api/stats?tz=UTC")
    assert res.status_code == 200
    data = res.json()
    assert data["current_streak"] == 0
    assert data["freezes_remaining"] == 2


def test_stats_heatmap_weeks_param(client):
    res = client.get("/api/stats?tz=UTC&weeks=4")
    assert res.status_code == 200
    assert len(res.json()["heatmap"]) == 4 * 7


def test_mark_posted(client):
    res = client.post(
        "/api/post",
        json={"content": "Test post", "post_type": "single", "timezone": "UTC"},
    )
    assert res.status_code == 200
    assert res.json()["content"] == "Test post"


def test_thread_split(client):
    res = client.post(
        "/api/thread/split",
        json={"items": ["Short", "Also short"], "max_len": 280},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["chunk_count"] == 2


def test_export_markdown(client):
    client.post("/api/post", json={"content": "Exported", "timezone": "UTC"})
    res = client.get("/api/export/markdown")
    assert res.status_code == 200
    assert "Exported" in res.text
    assert "# Daily Forge" in res.text


def test_settings_update(client):
    res = client.put(
        "/api/settings",
        json={"timezone": "America/New_York", "reminder_enabled": True},
    )
    assert res.status_code == 200
    assert res.json()["timezone"] == "America/New_York"