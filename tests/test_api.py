from __future__ import annotations

from fastapi.testclient import TestClient

from app import app
from src.spec import load_pipeline_spec

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"ok": True}


def test_spec_endpoint_matches_pipeline_contract():
    spec = load_pipeline_spec()
    res = client.get("/api/spec")
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == spec.id
    assert body["version"] == spec.version
    assert body["title"] == spec.title
    assert body["kicker"] == spec.kicker
    assert body["lede"] == spec.lede
    assert body["samples"] == spec.samples


def test_configs_endpoint_lists_profiles():
    res = client.get("/api/configs")
    assert res.status_code == 200
    names = {row["name"] for row in res.json()}
    assert names == {"v1", "v2", "v3"}


def test_ask_rejects_empty_question():
    res = client.post("/api/ask", json={"question": "   ", "config": "v1"})
    assert res.status_code == 400


def test_ask_unknown_config():
    res = client.post("/api/ask", json={"question": "What is the return window?", "config": "v9"})
    assert res.status_code == 404


def test_ui_served():
    res = client.get("/")
    assert res.status_code == 200
    assert "ask-form" in res.text
    assert "/api/spec" in res.text
