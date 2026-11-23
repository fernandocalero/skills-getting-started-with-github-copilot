import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.app import activities, app


class UnregisterTests(unittest.TestCase):
    def setUp(self):
        self.activities = patch.dict(
            activities,
            {
                "Chess Club": {
                    "description": "Chess",
                    "schedule": "Fridays",
                    "max_participants": 2,
                    "participants": ["first@example.com", "other@example.com"],
                }
            },
            clear=True,
        )
        self.activities.start()
        self.addCleanup(self.activities.stop)
        self.client = TestClient(app)

    def test_unregister_removes_only_selected_participant_and_frees_spot(self):
        response = self.client.delete(
            "/activities/Chess%20Club/signup", params={"email": "first@example.com"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.get("/activities").json()["Chess Club"]["participants"],
            ["other@example.com"],
        )
        response = self.client.post(
            "/activities/Chess%20Club/signup", params={"email": "first@example.com"}
        )
        self.assertEqual(response.status_code, 200)

    def test_missing_activity_or_participant_does_not_change_signups(self):
        missing_activity = self.client.delete(
            "/activities/Missing/signup", params={"email": "first@example.com"}
        )
        missing_participant = self.client.delete(
            "/activities/Chess%20Club/signup", params={"email": "missing@example.com"}
        )

        self.assertEqual(missing_activity.status_code, 404)
        self.assertEqual(missing_participant.status_code, 404)
        self.assertEqual(
            activities["Chess Club"]["participants"],
            ["first@example.com", "other@example.com"],
        )

    def test_email_is_required(self):
        response = self.client.delete("/activities/Chess%20Club/signup")
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
