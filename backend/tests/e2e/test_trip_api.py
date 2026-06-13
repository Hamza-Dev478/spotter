"""End-to-end API tests through DRF, with providers faked at the factory."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from infrastructure import factory
from tests.fakes import FakeGeocoder, FakeRouter

PLAN_URL = "/api/v1/trips/plan/"


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def fake_providers(monkeypatch):
    monkeypatch.setattr(factory, "get_geocoder", lambda: FakeGeocoder())
    monkeypatch.setattr(factory, "get_router", lambda: FakeRouter())


def _payload(**over):
    return {
        "currentLocation": "Chicago",
        "pickupLocation": "St Louis",
        "dropoffLocation": "Dallas",
        "currentCycleUsedHrs": 10,
        **over,
    }


@pytest.mark.django_db
def test_plan_trip_returns_full_payload(client, fake_providers):
    resp = client.post(PLAN_URL, _payload(), format="json")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"summary", "route", "stops", "dailyLogs", "logMeta"}
    assert body["dailyLogs"]
    for day in body["dailyLogs"]:
        assert abs(sum(day["totals"].values()) - 24.0) < 0.05


@pytest.mark.django_db
def test_plan_trip_persists_history(client, fake_providers):
    client.post(PLAN_URL, _payload(), format="json")
    resp = client.get("/api/v1/trips/")
    assert resp.status_code == 200
    trips = resp.json()["trips"]
    assert len(trips) == 1
    assert trips[0]["pickupLocation"] == "St Louis"


@pytest.mark.django_db
def test_history_pagination_and_total(client, fake_providers):
    for _ in range(3):
        client.post(PLAN_URL, _payload(), format="json")
    body = client.get("/api/v1/trips/", {"limit": 2, "offset": 0}).json()
    assert body["total"] == 3
    assert len(body["trips"]) == 2
    page2 = client.get("/api/v1/trips/", {"limit": 2, "offset": 2}).json()
    assert len(page2["trips"]) == 1


@pytest.mark.django_db
def test_detail_returns_original_request(client, fake_providers):
    client.post(PLAN_URL, _payload(currentCycleUsedHrs=12), format="json")
    tid = client.get("/api/v1/trips/").json()["trips"][0]["id"]
    detail = client.get(f"/api/v1/trips/{tid}/").json()
    assert detail["request"]["pickupLocation"] == "St Louis"
    assert detail["request"]["currentCycleUsedHrs"] == 12
    assert "result" in detail


@pytest.mark.django_db
def test_delete_single_trip(client, fake_providers):
    client.post(PLAN_URL, _payload(), format="json")
    tid = client.get("/api/v1/trips/").json()["trips"][0]["id"]
    assert client.delete(f"/api/v1/trips/{tid}/").status_code == 204
    assert client.get("/api/v1/trips/").json()["total"] == 0
    assert client.delete(f"/api/v1/trips/{tid}/").status_code == 404


@pytest.mark.django_db
def test_clear_all_history(client, fake_providers):
    client.post(PLAN_URL, _payload(), format="json")
    client.post(PLAN_URL, _payload(), format="json")
    assert client.delete("/api/v1/trips/").status_code == 204
    assert client.get("/api/v1/trips/").json()["total"] == 0


@pytest.mark.django_db
def test_validation_error_returns_400(client, fake_providers):
    resp = client.post(PLAN_URL, _payload(currentLocation="", currentCycleUsedHrs=99), format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_unresolvable_address_returns_422(client, monkeypatch):
    monkeypatch.setattr(factory, "get_geocoder", lambda: FakeGeocoder(fail_on="dallas"))
    monkeypatch.setattr(factory, "get_router", lambda: FakeRouter())
    resp = client.post(PLAN_URL, _payload(), format="json")
    assert resp.status_code == 422
    assert "Dallas" in resp.json()["error"] or "dallas" in resp.json()["error"]


@pytest.mark.django_db
def test_geocode_suggest_endpoint(client, fake_providers):
    resp = client.get("/api/v1/geocode/", {"q": "Chicago"})
    assert resp.status_code == 200
    assert "suggestions" in resp.json()


def test_health(client):
    assert client.get("/api/v1/health/").status_code == 200
