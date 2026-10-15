import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "activities",
        {
            "Chess Club": {
                "max_participants": 2,
                "participants": ["existing@mergington.edu"],
            }
        },
    )
    return TestClient(app_module.app)


def test_signup_adds_participant_when_activity_has_space(client):
    response = client.post(
        "/activities/Chess%20Club/signup?email=new%40mergington.edu"
    )

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Signed up new@mergington.edu for Chess Club"
    )
    assert app_module.activities["Chess Club"]["participants"] == [
        "existing@mergington.edu",
        "new@mergington.edu",
    ]


def test_signup_rejects_full_activity_without_adding_participant(client):
    app_module.activities["Chess Club"]["max_participants"] = 1

    response = client.post(
        "/activities/Chess%20Club/signup?email=new%40mergington.edu"
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Activity is full"
    assert app_module.activities["Chess Club"]["participants"] == [
        "existing@mergington.edu"
    ]


def test_signup_returns_not_found_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown/signup?email=new%40mergington.edu"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "existing@mergington.edu"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up"


def test_unregister_removes_participant(client):
    response = client.delete(
        "/activities/Chess%20Club/participants/existing%40mergington.edu"
    )

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Unregistered existing@mergington.edu from Chess Club"
    )
    assert app_module.activities["Chess Club"]["participants"] == []


def test_unregister_returns_not_found_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown/participants/existing%40mergington.edu"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_not_found_for_unsigned_participant(client):
    response = client.delete(
        "/activities/Chess%20Club/participants/unknown%40mergington.edu"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_activity_listing_reflects_signup_and_unregistration(client):
    client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "new@mergington.edu"},
    )

    activity = client.get("/activities").json()["Chess Club"]
    assert activity["participants"] == [
        "existing@mergington.edu",
        "new@mergington.edu",
    ]

    client.delete(
        "/activities/Chess%20Club/participants/new%40mergington.edu"
    )

    activity = client.get("/activities").json()["Chess Club"]
    assert activity["participants"] == ["existing@mergington.edu"]
