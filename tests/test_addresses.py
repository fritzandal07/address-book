"""API tests using an isolated in-memory SQLite database."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

MANILA = {"name": "Manila", "street": "1 Rizal St", "city": "Manila", "country": "Philippines",
          "latitude": 14.5995, "longitude": 120.9842}
QUEZON = {"name": "QC", "street": "2 EDSA", "city": "Quezon City", "country": "Philippines",
          "latitude": 14.6760, "longitude": 121.0437}  # ~10 km from Manila
CEBU = {"name": "Cebu", "street": "3 Colon St", "city": "Cebu", "country": "Philippines",
        "latitude": 10.3157, "longitude": 123.8854}  # ~570 km from Manila


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_and_get(client):
    created = client.post("/addresses", json=MANILA)
    assert created.status_code == 201
    fetched = client.get(f"/addresses/{created.json()['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["city"] == "Manila"


@pytest.mark.parametrize("field,value", [("latitude", 91), ("latitude", -91), ("longitude", 181),
                                         ("longitude", -181), ("street", "   "), ("city", "")])
def test_validation_rejects_bad_input(client, field, value):
    assert client.post("/addresses", json={**MANILA, field: value}).status_code == 422


def test_put_and_patch(client):
    address_id = client.post("/addresses", json=MANILA).json()["id"]
    assert client.patch(f"/addresses/{address_id}", json={"city": "Pasay"}).json()["city"] == "Pasay"
    replaced = client.put(f"/addresses/{address_id}", json={**QUEZON})
    assert replaced.json()["city"] == "Quezon City"
    assert client.patch(f"/addresses/{address_id}", json={"latitude": 200}).status_code == 422


def test_delete(client):
    address_id = client.post("/addresses", json=MANILA).json()["id"]
    assert client.delete(f"/addresses/{address_id}").status_code == 204
    assert client.get(f"/addresses/{address_id}").status_code == 404
    assert client.delete(f"/addresses/{address_id}").status_code == 404


def test_nearby_search(client):
    for payload in (MANILA, QUEZON, CEBU):
        client.post("/addresses", json=payload)

    params = {"latitude": 14.5995, "longitude": 120.9842}
    near = client.get("/addresses/find_nearby", params={**params, "distance_km": 20}).json()
    assert [a["name"] for a in near] == ["Manila", "QC"]  # nearest first, Cebu excluded
    assert 9 < near[1]["distance_km"] < 12

    wide = client.get("/addresses/find_nearby", params={**params, "distance_km": 1000}).json()
    assert len(wide) == 3


def test_nearby_validates_params(client):
    assert client.get("/addresses/find_nearby", params={"latitude": 100, "longitude": 0, "distance_km": 5}).status_code == 422
    assert client.get("/addresses/find_nearby", params={"latitude": 0, "longitude": 0, "distance_km": -1}).status_code == 422


@pytest.mark.parametrize("field", ["name", "street", "city", "country", "latitude", "longitude"])
def test_patch_rejects_null_for_required_fields(client, field):
    address_id = client.post("/addresses", json=MANILA).json()["id"]
    assert client.patch(f"/addresses/{address_id}", json={field: None}).status_code == 422


def test_patch_can_clear_optional_fields(client):
    address_id = client.post("/addresses", json={**MANILA, "state": "NCR"}).json()["id"]
    response = client.patch(f"/addresses/{address_id}", json={"state": None})
    assert response.status_code == 200
    assert response.json()["state"] is None


def test_patch_rejects_unknown_fields(client):
    address_id = client.post("/addresses", json=MANILA).json()["id"]
    assert client.patch(f"/addresses/{address_id}", json={"foo": "bar"}).status_code == 422
    assert client.patch(f"/addresses/{address_id}", json={"id": 999}).status_code == 422


def test_patch_only_changes_sent_fields(client):
    created = client.post("/addresses", json={**MANILA, "postal_code": "1000"}).json()
    patched = client.patch(f"/addresses/{created['id']}", json={"city": "Pasay"}).json()
    assert patched["city"] == "Pasay"
    assert patched["postal_code"] == "1000"  # untouched
    assert patched["street"] == MANILA["street"]  # untouched


def test_put_replaces_everything_and_clears_omitted_optionals(client):
    created = client.post("/addresses", json={**MANILA, "state": "NCR", "postal_code": "1000"}).json()
    replaced = client.put(f"/addresses/{created['id']}", json=QUEZON).json()  # no state / postal_code
    assert replaced["city"] == "Quezon City"
    assert replaced["state"] is None
    assert replaced["postal_code"] is None


def test_put_requires_all_required_fields(client):
    address_id = client.post("/addresses", json=MANILA).json()["id"]
    incomplete = {k: v for k, v in QUEZON.items() if k != "city"}
    assert client.put(f"/addresses/{address_id}", json=incomplete).status_code == 422


@pytest.mark.parametrize("method", ["put", "patch", "delete", "get"])
def test_unknown_id_returns_404(client, method):
    kwargs = {"json": QUEZON} if method == "put" else {"json": {"city": "x"}} if method == "patch" else {}
    assert getattr(client, method)("/addresses/9999", **kwargs).status_code == 404


def test_find_nearby_radius_boundary(client):
    client.post("/addresses", json=MANILA)
    client.post("/addresses", json=QUEZON)
    near = client.get("/addresses/find_nearby", params={"latitude": 14.5995, "longitude": 120.9842, "distance_km": 5})
    assert [a["name"] for a in near.json()] == ["Manila"]
    wide = client.get("/addresses/find_nearby", params={"latitude": 14.5995, "longitude": 120.9842, "distance_km": 15})
    assert [a["name"] for a in wide.json()] == ["Manila", "QC"]  # nearest first
