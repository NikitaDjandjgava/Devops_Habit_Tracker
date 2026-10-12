from flask.testing import FlaskClient


def make_habit(client: FlaskClient, name: str = "Read", cadence: str = "daily") -> int:
    return client.post("/habits", json={"name": name, "cadence": cadence}).get_json()["id"]


def test_health(client: FlaskClient) -> None:
    assert client.get("/health").get_json() == {"status": "ok"}


def test_create_habit_validates_input(client: FlaskClient) -> None:
    assert client.post("/habits", json={"name": ""}).status_code == 400
    assert client.post("/habits", json={"name": "x", "cadence": "hourly"}).status_code == 400
    assert client.post("/habits", json={"name": 123}).status_code == 400
    assert client.post("/habits", json=["not", "an", "object"]).status_code == 400


def test_create_habit_persists_weekdays_time_and_alert(client: FlaskClient) -> None:
    response = client.post(
        "/habits",
        json={
            "name": "Walk",
            "days_of_week": [0, 2, 4],
            "time_of_day": "07:30",
            "alert_type": "custom",
            "alert_amount": 2,
            "alert_unit": "hours",
        },
    )
    assert response.status_code == 201
    assert response.get_json()["days_of_week"] == [0, 2, 4]
    assert response.get_json()["time_of_day"] == "07:30"
    assert response.get_json()["alert_offset_minutes"] == 120


def test_create_habit_rejects_invalid_schedule(client: FlaskClient) -> None:
    response = client.post(
        "/habits",
        json={"name": "Walk", "days_of_week": [], "time_of_day": "25:90"},
    )
    assert response.status_code == 400


def test_checkin_is_idempotent_and_streak_counts(client: FlaskClient) -> None:
    hid = make_habit(client)
    for _ in range(2):  # same day twice
        assert client.post(f"/habits/{hid}/checkins", json={}).status_code == 201
    assert client.get(f"/habits/{hid}/streak").get_json()["streak"] == 1


def test_delete_habit_removes_it_and_its_checkins(client: FlaskClient) -> None:
    hid = make_habit(client)
    client.post(f"/habits/{hid}/checkins", json={})
    assert client.delete(f"/habits/{hid}").status_code == 204
    assert client.get("/habits").get_json() == []
    assert client.get(f"/habits/{hid}/streak").status_code == 404
    assert client.delete(f"/habits/{hid}").status_code == 404


def test_checkin_unknown_habit_404(client: FlaskClient) -> None:
    assert client.post("/habits/999/checkins", json={}).status_code == 404


def test_checkin_rejects_non_string_date(client: FlaskClient) -> None:
    habit_id = make_habit(client)
    response = client.post(f"/habits/{habit_id}/checkins", json={"date": 123})
    assert response.status_code == 400
    assert response.get_json()["error"] == "date must be YYYY-MM-DD"


def test_checkin_rejects_noncanonical_iso_date(client: FlaskClient) -> None:
    habit_id = make_habit(client)
    response = client.post(f"/habits/{habit_id}/checkins", json={"date": "20261009"})
    assert response.status_code == 400
    assert client.post(f"/habits/{habit_id}/checkins", json={"date": ""}).status_code == 400


def test_checkin_rejects_malformed_json(client: FlaskClient) -> None:
    habit_id = make_habit(client)
    response = client.post(
        f"/habits/{habit_id}/checkins",
        data='{"date":',
        content_type="application/json",
    )
    assert response.status_code == 400


def test_weekly_insight_uses_habit_data(client: FlaskClient) -> None:
    hid = make_habit(client)
    client.post(f"/habits/{hid}/checkins", json={})
    body = client.get(f"/insights/{hid}/weekly").get_json()
    assert body["completed"] == 1
    assert body["rate"] == 1 / 7


def test_weekly_insight_divides_by_scheduled_days(client: FlaskClient) -> None:
    hid = make_habit(client, cadence="weekly")
    client.post(f"/habits/{hid}/checkins", json={})
    body = client.get(f"/insights/{hid}/weekly").get_json()
    assert body["scheduled_days"] == 1
    assert body["rate"] == 1.0


def test_templates_route_and_summary_endpoint(client: FlaskClient) -> None:
    templates = client.get("/habits/templates").get_json()
    assert templates
    hid = client.post(f"/habits/from-template/{templates[0]['id']}").get_json()["id"]
    summary = client.get(f"/insights/{hid}/summary").get_json()
    assert summary["habit_id"] == hid
    assert "milestones" in summary


def test_insight_routes_return_404_for_unknown_habit(client: FlaskClient) -> None:
    assert client.get("/insights/999/weekly").status_code == 404
    assert client.get("/insights/999/milestones").status_code == 404
    assert client.get("/insights/999/summary").status_code == 404
