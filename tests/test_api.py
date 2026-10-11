def make_habit(client, name="Read", cadence="daily"):
    return client.post("/habits", json={"name": name, "cadence": cadence}).get_json()["id"]


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_create_habit_validates_input(client):
    assert client.post("/habits", json={"name": ""}).status_code == 400
    assert client.post("/habits", json={"name": "x", "cadence": "hourly"}).status_code == 400


def test_checkin_is_idempotent_and_streak_counts(client):
    hid = make_habit(client)
    for _ in range(2):  # same day twice
        assert client.post(f"/habits/{hid}/checkins", json={}).status_code == 201
    assert client.get(f"/habits/{hid}/streak").get_json()["streak"] == 1


def test_checkin_unknown_habit_404(client):
    assert client.post("/habits/999/checkins", json={}).status_code == 404


def test_weekly_insight_uses_habit_data(client):
    hid = make_habit(client)
    client.post(f"/habits/{hid}/checkins", json={})
    body = client.get(f"/insights/{hid}/weekly").get_json()
    assert body["completed"] == 1
    assert body["rate"] == 1 / 7


def test_templates_route_and_summary_endpoint(client):
    templates = client.get("/habits/templates").get_json()
    assert templates
    hid = client.post(f"/habits/from-template/{templates[0]['id']}").get_json()["id"]
    summary = client.get(f"/insights/{hid}/summary").get_json()
    assert summary["habit_id"] == hid
    assert "milestones" in summary
