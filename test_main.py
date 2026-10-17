from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_add_and_list_items():
    response = client.post("/items", params={"name": "pomme"})
    assert response.status_code == 200
    assert response.json() == {"added": "pomme"}

    response = client.get("/items")
    assert "pomme" in response.json()