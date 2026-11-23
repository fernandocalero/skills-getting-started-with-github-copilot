from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    test_activities = {
        "Chess Club": {
            "description": "Chess",
            "schedule": "Fridays",
            "max_participants": 2,
            "participants": ["first@example.com"],
        }
    }
    with patch.dict(activities, test_activities, clear=True):
        with TestClient(app) as test_client:
            yield test_client


def test_root_redirects_to_served_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)
    index = client.get(expected_location)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location
    assert index.status_code == 200
    assert "Mergington High School" in index.text


def test_get_activities_returns_activity_details(client):
    # Arrange
    expected = {
        "Chess Club": {
            "description": "Chess",
            "schedule": "Fridays",
            "max_participants": 2,
            "participants": ["first@example.com"],
        }
    }

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected


def test_signup_adds_participant(client):
    # Arrange
    email = "new@example.com"

    # Act
    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert activities["Chess Club"]["participants"] == ["first@example.com", email]


@pytest.mark.parametrize(
    ("participants", "email", "detail"),
    [
        (["first@example.com"], "first@example.com", "Student already signed up for this activity"),
        (["first@example.com", "other@example.com"], "new@example.com", "Activity is full"),
    ],
)
def test_signup_rejects_duplicate_or_full_activity(client, participants, email, detail):
    # Arrange
    activities["Chess Club"]["participants"] = participants.copy()

    # Act
    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": detail}
    assert activities["Chess Club"]["participants"] == participants


@pytest.mark.parametrize("method", ["post", "delete"])
def test_missing_activity_does_not_change_participants(client, method):
    # Arrange
    participants = activities["Chess Club"]["participants"].copy()

    # Act
    response = client.request(
        method, "/activities/Missing/signup", params={"email": "first@example.com"}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activities["Chess Club"]["participants"] == participants


@pytest.mark.parametrize("method", ["post", "delete"])
def test_missing_email_does_not_change_participants(client, method):
    # Arrange
    participants = activities["Chess Club"]["participants"].copy()

    # Act
    response = client.request(method, "/activities/Chess%20Club/signup")

    # Assert
    assert response.status_code == 422
    assert activities["Chess Club"]["participants"] == participants


def test_unregister_removes_participant(client):
    # Arrange
    email = "first@example.com"

    # Act
    response = client.delete("/activities/Chess%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert activities["Chess Club"]["participants"] == []


def test_unregister_missing_participant_does_not_change_signups(client):
    # Arrange
    participants = activities["Chess Club"]["participants"].copy()

    # Act
    response = client.delete(
        "/activities/Chess%20Club/signup", params={"email": "missing@example.com"}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student not signed up for this activity"}
    assert activities["Chess Club"]["participants"] == participants
