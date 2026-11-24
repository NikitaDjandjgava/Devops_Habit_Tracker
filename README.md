# Habit Tracker

Habit Tracker is a two-service Flask application with a static browser UI.

- `services/habits` owns habits, check-ins, and habit templates.
- `services/insights` owns milestones and calls the habits service for habit data.
- `ui` is a static page served by nginx.
- SQL Server holds one database per service.

## Run locally

Copy `.env.example` to `.env`, replace placeholders, and start the stack:

    Copy-Item .env.example .env
    docker compose up --build

Open the UI at `http://localhost:8080`.
The habits API is at `http://localhost:8001` and the insights API is at `http://localhost:8002`.

SQL Server data remains in the `sqlserver-data` volume. Stop the stack with:

    docker compose down

## Environment variables

| Variable | Service | Meaning |
|---|---|---|
| `DATABASE_URL` | Both | SQL Server connection URL for the service |
| `PORT` | Both | HTTP listening port |
| `UI_ORIGIN` | Both | Allowed static UI origin |
| `HABITS_URL` | Insights | Habits service base URL |
| `HABITS_TIMEOUT_S` | Insights | Outbound timeout in seconds |
| `GIT_SHA` | Both | Version returned by `/health` |

Database passwords and Azure credentials must stay outside source control.

## Tests

The test suite covers pure schedule and insight logic plus the service boundaries:

    .\.venv\Scripts\python.exe -m pytest --cov=habits.schedule --cov=insights.stats --cov-report=term-missing --cov-fail-under=70

Lint and format checks:

    ruff check .
    ruff format --check .
    mypy

## Architecture

Insights makes one HTTP call to `GET /habits/<id>/public` before calculating weekly
data or summaries. If habits is unavailable, the insights endpoint returns a clear
503 JSON error. The UI also shows a "starting up, try again" message for cold
starts and network failures.

Each service runs migrations from its own `migrations` directory at startup.
Applied migrations are recorded in `schema_migrations`, and migrations run once
before Gunicorn starts accepting requests.
