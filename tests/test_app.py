import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_activities():
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert "Programming Class" in payload


def test_signup_for_activity_success():
    email = "paul@mergington.edu"
    response = client.post("/activities/Chess Club/signup", params={"email": email})
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Chess Club"
    assert email in activities["Chess Club"]["participants"]


def test_signup_for_activity_already_signed():
    response = client.post("/activities/Chess Club/signup", params={"email": "michael@mergington.edu"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up"


def test_signup_for_activity_not_found():
    response = client.post("/activities/Unknown/signup", params={"email": "norah@mergington.edu"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_for_activity_full():
    activity = activities["Tennis Club"]
    activity["participants"] = [f"user{i}@mergington.edu" for i in range(activity["max_participants"])]

    response = client.post("/activities/Tennis Club/signup", params={"email": "over@mergington.edu"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_unregister_from_activity_success():
    response = client.delete("/activities/Chess Club/signup", params={"email": "michael@mergington.edu"})
    assert response.status_code == 200
    assert response.json()["message"] == "Unregistered michael@mergington.edu from Chess Club"
    assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]


def test_unregister_from_activity_not_registered():
    response = client.delete("/activities/Chess Club/signup", params={"email": "nobody@mergington.edu"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up"


def test_unregister_from_activity_not_found():
    response = client.delete("/activities/Unknown/signup", params={"email": "nobody@mergington.edu"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (307, 308)
    assert response.headers.get("location") == "/static/index.html"


def test_get_activities_has_participants_and_capacity():
    response = client.get("/activities")
    payload = response.json()
    assert payload["Chess Club"]["max_participants"] == 12
    assert "michael@mergington.edu" in payload["Chess Club"]["participants"]


def test_signup_then_unregister_updates_list():
    email = "tom@mergington.edu"
    post_resp = client.post("/activities/Programming Class/signup", params={"email": email})
    assert post_resp.status_code == 200
    assert email in activities["Programming Class"]["participants"]

    del_resp = client.delete("/activities/Programming Class/signup", params={"email": email})
    assert del_resp.status_code == 200
    assert email not in activities["Programming Class"]["participants"]
