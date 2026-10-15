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