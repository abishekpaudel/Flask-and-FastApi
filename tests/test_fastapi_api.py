import pytest
from fastapi.testclient import TestClient

from fastapi_app import main as fastapi_module


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(fastapi_module, "init_db", lambda: None)
    monkeypatch.setattr(fastapi_module, "list_parts", lambda: [
        {"id": 1, "name": "Marine Pump", "sku": "PUMP-001",
         "quantity": 10, "price": 249.99}
    ])
    monkeypatch.setattr(fastapi_module, "get_part", lambda part_id: (
        {"id": part_id, "name": "Marine Pump", "sku": "PUMP-001",
         "quantity": 10, "price": 249.99} if part_id == 1 else None
    ))
    monkeypatch.setattr(fastapi_module, "create_part", lambda data: {
        "id": 2, **data
    })
    monkeypatch.setattr(fastapi_module, "update_part", lambda part_id, data: (
        {"id": part_id, **data} if part_id == 1 else None
    ))
    monkeypatch.setattr(fastapi_module, "delete_part", lambda part_id: part_id == 1)

    with TestClient(fastapi_module.app) as test_client:
        yield test_client


def valid_part():
    return {
        "name": "Marine Pump",
        "sku": "PUMP-001",
        "quantity": 10,
        "price": 249.99,
    }


def test_list_parts_returns_200_and_json(client):
    response = client.get("/parts")
    assert response.status_code == 200
    assert response.json()[0]["sku"] == "PUMP-001"


def test_get_missing_part_returns_404(client):
    response = client.get("/parts/99")
    assert response.status_code == 404
    assert response.json()["detail"] == "Part not found"


def test_create_part_returns_201(client):
    response = client.post("/parts", json=valid_part())
    assert response.status_code == 201
    assert response.json()["id"] == 2


def test_create_part_rejects_invalid_quantity(client):
    payload = valid_part()
    payload["quantity"] = -1
    response = client.post("/parts", json=payload)
    assert response.status_code == 422


def test_create_part_rejects_missing_required_field(client):
    payload = valid_part()
    del payload["sku"]
    response = client.post("/parts", json=payload)
    assert response.status_code == 422


def test_update_missing_part_returns_404(client):
    response = client.put("/parts/99", json=valid_part())
    assert response.status_code == 404


def test_delete_part_returns_204(client):
    response = client.delete("/parts/1")
    assert response.status_code == 204
    assert response.content == b""


def test_delete_missing_part_returns_404(client):
    response = client.delete("/parts/99")
    assert response.status_code == 404
