# HabitTracker

A minimal, single-process Flask + SQLite application for recording scheduled habits and viewing completion insights. Habits can be assigned any combination of weekdays, a time of day, and an alert at the event time, 15 minutes before, or a custom interval before.

The responsive browser dashboard is the primary interface. Browser notifications and in-page reminders are checked while the dashboard is open; reminders are not delivered when the app or browser is closed. Without notification permission, reminders appear as in-page notices.

The application is divided into two logically separable domains:

- **habits/**: habits, check-ins, streaks (owns `habits`, `checkins`, `habit_templates`)
- **insights/**: weekly completion stats, milestones (owns `milestones`)
- **Seam:** `habits/public.py`. Insights may only import from there.

## Run directly
    pip install -r requirements.txt
    python app.py            # http://localhost:8000

Open `http://127.0.0.1:8000/` for the dashboard. Add a habit, select its weekdays, time, and alert, then mark it complete on scheduled days. The JSON API remains available for other clients. Seeded habit templates remain accessible through the API for compatibility but are not presented in the dashboard.

## Run in Docker
    docker build -t habit-tracker .
    docker run -p 8000:8000 -v habit-data:/data -e DATA_DIR=/data habit-tracker

## Environment variables
| Variable | Default | Meaning |
|---|---|---|
| `PORT` | `8000` | Listening port |
| `DATA_DIR` | `data` | Directory holding the SQLite file |
| `FLASK_SECRET_KEY` | random per process | Optional persistent signing key for temporary UI messages; do not commit its value |

SQLite path: `$DATA_DIR/habits.db`. Seed data: `seed.json`, loaded only if `habit_templates` is empty.

## Tests
    pytest --cov=. --cov-report=term-missing

Coverage result: 98% total (30 tests passed in the latest local run).

## Code quality checks
Install the root dependencies, then run these checks before committing changes:

    ruff check .
    ruff format --check .
    mypy
    pytest --cov=. --cov-report=term-missing

Ruff provides linting, formatting, basic security checks, and checks for module and public-function docstrings. It ignores S104 only for `app.py` because binding to `0.0.0.0` is required by the container contract. Mypy checks type annotations in the application packages and tests. The assignment prohibits adding CI workflows, so these local commands are the project quality gate. Run them before each commit.

## Container contract (§7) evidence
The repo now includes a working Dockerfile and `./container/run.sh` checker. The script is designed to build the image, start the app on `0.0.0.0:$PORT`, and verify `http://127.0.0.1:$PORT/health`.

Local validation note: Docker is not installed in this environment (`docker: command not recognized`), so the checker could not be executed here. The command is ready to run on any machine with Docker installed:

    ./container/run.sh /path/to/habit-tracker

## API
| Method | Path | Input | Successful JSON response | Errors |
|---|---|---|---|---|
| GET | `/health` | None | `{"status":"ok"}` | — |
| POST | `/habits` | `{"name":"Read","days_of_week":[0,2,4],"time_of_day":"07:30","alert_type":"custom","alert_amount":2,"alert_unit":"hours"}` (or legacy `cadence`) | Habit object including schedule fields | 400 invalid body/name/schedule |
| GET | `/habits` | None | Array of habit objects including `days_of_week`, `time_of_day`, and alert fields | — |
| GET | `/habits/templates` | None | Array of `{id,name,cadence}` | — |
| POST | `/habits/from-template/<id>` | Template ID in path | `{"id":1,"name":"Read 20 minutes","cadence":"daily"}` | 404 unknown template |
| POST | `/habits/<id>/checkins` | Optional `{"date":"YYYY-MM-DD"}` | `{"habit_id":1,"date":"YYYY-MM-DD"}` | 400 invalid body/date; 404 unknown habit |
| GET | `/habits/<id>/streak` | Habit ID in path | `{"habit_id":1,"streak":3}` | 404 unknown habit |
| GET | `/insights/<id>/weekly` | Habit ID in path | `{"habit_id":1,"window_days":7,"completed":1,"rate":0.14}` | 404 unknown habit |
| GET | `/insights/<id>/milestones` | Habit ID in path | `{"milestones":[...]}` | 404 unknown habit |
| GET | `/insights/<id>/summary` | Habit ID in path | `{"habit_id":1,"streak":3,"best_weekday":"Friday","milestones":[...]}` | 404 unknown habit |
| GET | `/` | None | Responsive daily habit dashboard | — |
| POST | `/ui/habits` | Form fields `name`, repeated `days_of_week`, `time_of_day`, and alert fields | Redirects to dashboard with status message | Invalid form is reported on dashboard |
| POST | `/ui/habits/<id>/toggle` | Habit ID in path | Redirects after toggling today's scheduled check-in | Unknown or unscheduled habit is reported on dashboard |
| GET | `/ui/reminders` | Browser-local `now=YYYY-MM-DDTHH:MM` | `{"reminders":[...]}` for the current minute | 400 invalid local date/time |

## Inputs, responses, and limitations
Habit creation accepts a JSON object with a non-empty `name` and a non-empty, duplicate-free list of weekday numbers (`0` Monday through `6` Sunday). `time_of_day` uses 24-hour `HH:MM`. Alerts are `at_time`, `15_before`, or `custom`; custom amounts are 1–1440 minutes or 1–24 hours. Legacy clients can omit `days_of_week` and provide `cadence` (`daily` maps to all days; `weekly` maps to Monday). Check-ins accept an optional canonical `YYYY-MM-DD` date. Invalid input returns HTTP 400; unknown habit or template IDs return HTTP 404. IDs in route paths must be positive integers.

Dates and streaks use the server's local date; reminders use the browser's local clock, and the app does not provide accounts or per-user time-zone storage. Reminder polling runs only while the dashboard is open. Existing databases receive additive schedule columns on startup; old daily habits migrate to all weekdays and old weekly habits to Monday. The health endpoint detects whether the process responds; the container checker separately verifies the HTTP health response. For maintenance, run the quality-check commands above after code changes and keep dependencies reviewed and updated.

## Project report
See [REPORT.md](./REPORT.md) for the architecture overview, database diagram, SDLC notes, and final project summary.
