# Habit Tracker

Flask + SQLite habit tracker with two logically separable domains:

- **habits/**: habits, check-ins, streaks (owns `habits`, `checkins`, `habit_templates`)
- **insights/**: weekly completion stats, milestones (owns `milestones`)
- **Seam:** `habits/public.py`. Insights may only import from there.

## Run directly
    pip install -r requirements.txt
    python app.py            # http://localhost:8000

## Run in Docker
    cp container/Dockerfile ./Dockerfile   # provided template; fill its 4 TODOs
    docker build -t habit-tracker .
    docker run -p 8000:8000 -v habit-data:/data -e DATA_DIR=/data habit-tracker

## Environment variables
| Variable | Default | Meaning |
|---|---|---|
| `PORT` | `8000` | Listening port |
| `DATA_DIR` | `data` | Directory holding the SQLite file |

SQLite path: `$DATA_DIR/habits.db`. Seed data: `seed.json`, loaded only if `habit_templates` is empty.

## Tests
    pytest --cov=. --cov-report=term-missing

Coverage result: TODO

## Container contract (§7) evidence
TODO: paste the passing `./container/run.sh` output.

## API (so far)
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness |
| POST/GET | `/habits` | create / list habits |
| POST | `/habits/<id>/checkins` | check in (body: optional `date`) |
| GET | `/habits/<id>/streak` | current daily streak |
| GET | `/insights/<id>/weekly` | 7-day completion rate |
