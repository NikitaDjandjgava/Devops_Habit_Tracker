from flask.testing import FlaskClient


def test_dashboard_renders_empty_state_without_suggestion_picker(client: FlaskClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert b"Your first small step starts here." in response.data
    assert b"data-template-select" not in response.data


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
    from datetime import date

    today = date.today().weekday()
    all_days = [str(day) for day in range(7)]
    daily = client.post(
        "/ui/habits",
        data={
            "name": "Stretch",
            "days_of_week": all_days,
            "time_of_day": "09:00",
            "alert_type": "15_before",
        },
    )
    weekly = client.post(
        "/ui/habits",
        data={
            "name": "Plan the week",
            "days_of_week": [str(today)],
            "time_of_day": "10:00",
            "alert_type": "at_time",
        },
    )

    assert daily.status_code == 302
    assert weekly.status_code == 302
    response = client.get("/")
    assert b"Stretch" in response.data
    assert b"Plan the week" in response.data
    assert b"Custom days" in response.data
    assert b"Every day" in response.data


def test_dashboard_rejects_invalid_habit_form(client: FlaskClient) -> None:
    response = client.post(
        "/ui/habits",
        data={"name": "", "days_of_week": [], "time_of_day": "99:99", "alert_type": "wrong"},
    )
    assert response.status_code == 302
    assert b"Enter a habit name" in client.get("/").data


def test_dashboard_unknown_habit_toggle_reports_error(client: FlaskClient) -> None:
    response = client.post("/ui/habits/999/toggle")
    assert response.status_code == 302
    assert b"could not be found" in client.get("/").data


def test_custom_schedule_habit_can_be_toggled_on_selected_day(client: FlaskClient) -> None:
    from datetime import date

    created = client.post(
        "/habits",
        json={
            "name": "Weekly review",
            "days_of_week": [date.today().weekday()],
            "time_of_day": "09:00",
        },
    )
    habit_id = created.get_json()["id"]

    client.post(f"/ui/habits/{habit_id}/toggle")
    response = client.get("/")
    assert b"100 percent of habits on track" in response.data

    client.post(f"/ui/habits/{habit_id}/toggle")
    assert b"0 percent of habits on track" in client.get("/").data


def test_ui_form_accepts_custom_alerts(client: FlaskClient) -> None:
    response = client.post(
        "/ui/habits",
        data={
            "name": "Take a break",
            "days_of_week": ["0", "2", "4"],
            "time_of_day": "14:00",
            "alert_type": "custom",
            "alert_amount": "2",
            "alert_unit": "hours",
        },
    )
    assert response.status_code == 302
    page = client.get("/")
    assert b"Mon, Wed, Fri" in page.data
    assert b"2 hr before" in page.data


def test_dashboard_delete_removes_habit(client: FlaskClient) -> None:
    hid = client.post("/habits", json={"name": "Old habit", "cadence": "daily"}).get_json()["id"]
    response = client.post(f"/ui/habits/{hid}/delete")
    assert response.status_code == 302
    page = client.get("/").data
    assert b"was deleted" in page
    assert b"Your first small step starts here." in page
    assert client.post(f"/ui/habits/{hid}/delete").status_code == 302
    assert b"could not be found" in client.get("/").data


def test_consecutive_habits_get_different_colors(client: FlaskClient) -> None:
    client.post("/habits", json={"name": "First", "cadence": "daily"})
    client.post("/habits", json={"name": "Second", "cadence": "daily"})
    page = client.get("/").data
    assert b"habit-card habit-color-1" in page
    assert b"habit-card habit-color-2" in page


def test_dashboard_shows_hourly_timeline(client: FlaskClient) -> None:
    client.post("/habits", json={"name": "Morning run", "cadence": "daily", "time_of_day": "06:15"})
    page = client.get("/").data
    assert b"Today's timeline" in page
    assert b'data-hour="6"' in page
    assert b"<b>06:15</b> Morning run" in page


def test_calendar_shows_habits_and_handles_month_navigation(client: FlaskClient) -> None:
    client.post("/habits", json={"name": "Yoga", "cadence": "daily", "time_of_day": "08:00"})
    page = client.get("/calendar?month=2026-02")
    assert page.status_code == 200
    assert b"February 2026" in page.data
    assert b"Yoga" in page.data
    assert b"month=2026-01" in page.data
    assert b"month=2026-03" in page.data
    assert client.get("/calendar?month=garbage").status_code == 200


def test_ui_rejects_habit_scheduled_for_another_day(client: FlaskClient) -> None:
    from datetime import date

    other_day = (date.today().weekday() + 1) % 7
    created = client.post(
        "/habits",
        json={"name": "Tomorrow", "days_of_week": [other_day], "time_of_day": "09:00"},
    )
    response = client.post(f"/ui/habits/{created.get_json()['id']}/toggle")
    assert response.status_code == 302
    assert b"not scheduled for today" in client.get("/").data
