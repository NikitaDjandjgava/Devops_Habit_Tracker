from flask.testing import FlaskClient


def test_dashboard_renders_empty_state_and_templates(client: FlaskClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert b"Your first small step starts here." in response.data
    assert b"Drink 2L of water" in response.data


def test_dashboard_lists_habits_and_can_toggle_completion(client: FlaskClient) -> None:
    created = client.post("/habits", json={"name": "Read", "cadence": "daily"})
    habit_id = created.get_json()["id"]

    response = client.get("/")
    assert b"Read" in response.data
    assert b"Mark done" in response.data

    completed = client.post(f"/ui/habits/{habit_id}/toggle")
    assert completed.status_code == 302
    assert b"Done" in client.get("/").data

    incomplete = client.post(f"/ui/habits/{habit_id}/toggle")
    assert incomplete.status_code == 302
    assert b"Mark done" in client.get("/").data


def test_dashboard_can_create_daily_and_weekly_habits(client: FlaskClient) -> None:
    daily = client.post("/ui/habits", data={"name": "Stretch", "cadence": "daily"})
    weekly = client.post("/ui/habits", data={"name": "Plan the week", "cadence": "weekly"})

    assert daily.status_code == 302
    assert weekly.status_code == 302
    response = client.get("/")
    assert b"Stretch" in response.data
    assert b"Plan the week" in response.data
    assert b"week streak" in response.data


def test_dashboard_rejects_invalid_habit_form(client: FlaskClient) -> None:
    response = client.post("/ui/habits", data={"name": "", "cadence": "hourly"})
    assert response.status_code == 302
    assert b"Enter a habit name" in client.get("/").data


def test_dashboard_unknown_habit_toggle_reports_error(client: FlaskClient) -> None:
    response = client.post("/ui/habits/999/toggle")
    assert response.status_code == 302
    assert b"could not be found" in client.get("/").data


def test_weekly_habit_can_be_toggled_for_the_current_week(client: FlaskClient) -> None:
    created = client.post("/habits", json={"name": "Weekly review", "cadence": "weekly"})
    habit_id = created.get_json()["id"]

    client.post(f"/ui/habits/{habit_id}/toggle")
    response = client.get("/")
    assert b"week streak" in response.data
    assert b"100 percent of habits on track" in response.data

    client.post(f"/ui/habits/{habit_id}/toggle")
    assert b"0 percent of habits on track" in client.get("/").data
