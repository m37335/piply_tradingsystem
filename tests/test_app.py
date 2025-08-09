import json

import pytest

from app import app


@pytest.fixture
def client():
    """テスト用のFlaskクライアント"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_hello_endpoint(client):
    """基本エンドポイントのテスト"""
    response = client.get("/")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert "message" in data
    assert "status" in data
    assert data["status"] == "healthy"


def test_health_check_endpoint(client):
    """ヘルスチェックエンドポイントのテスト"""
    response = client.get("/api/health")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["status"] == "ok"
    assert data["service"] == "exchanging-app"
    assert "version" in data
