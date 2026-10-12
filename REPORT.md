# HabitTracker Project Report

## 1. Project overview

This project delivers HabitTracker, a small Flask + SQLite habit tracker that follows the assignment constraints for a single-process, single-container application. Its responsive browser dashboard supports per-weekday schedules, times, and configurable browser/in-page reminders while open. The software is organized into two logical domains:

- `habits/`: habit records, check-ins, daily/weekly streak logic, and template data
- `insights/`: completion-rate calculations, milestone detection, and summary endpoints

The key design constraint is the seam in `habits/public.py`: the insights domain may only use this narrow public API and must not directly query `habits.repository` or the `habits` / `checkins` tables.

The project is intentionally small, explainable, and easy to reason about. It avoids background workers, external services, and infrastructure beyond the SQLite database and local Flask process.

## 2. SDLC and development approach

This project used an iterative, incremental SDLC model with a time-compressed delivery window. The work was split into a small number of coherent milestones:

1. Create the app factory, environment configuration, schema bootstrapping, and seed loading.
2. Implement the habits domain and core streak logic.
3. Add the insights domain, seam, and milestone summary logic.
4. Validate the API, apply fixes, and document the project decisions.
5. Verify the code and finalize the documentation package.

The timeline was compressed relative to the ideal assignment plan, but the process remained honest and incremental. Each milestone was validated with the existing test suite before moving forward.

### SMART goals

| Goal | Specific / measurable target | Deadline | Result |
|---|---|---|---|
| Two working domains | Habits and insights each read and write SQLite through their own repository module | 2026-10-11 | Met (commit `7903474`) |
| Clean seam | `insights/` imports nothing from `habits/` except `habits.public` | 2026-10-11 | Met |
| Test coverage | ≥70% line coverage with `pytest --cov` | 2026-10-12 | Met: 93% |
| Container contract | `run.sh` passes against the filled template | 2026-10-12 | Not yet run: Docker unavailable on the development machine |
| Commit cadence | ≥12 meaningful commits over ≥6 days, ≤40% per day | 2026-10-12 | Not met: work started 2026-10-09, so at most 4 calendar days were available |

### How the model was followed in practice

Iterations 1-3 matched the plan. The browser dashboard and scheduled reminders were added on the last day after the core domains were finished, which compressed testing and documentation into the final iteration. The late start is the main deviation from the plan and the reason the commit-cadence goal was missed.

## 3. Architecture

The application runs as a single Flask process and serves a responsive HTML dashboard together with JSON routes for habits and insights. The dashboard polls for due reminders while open; it does not use a background worker and cannot deliver reminders when the dashboard is closed. All surfaces use the same SQLite database under the configured `DATA_DIR`, which keeps the project within the single-container requirement.

```mermaid
flowchart LR
    A[Browser / API caller] --> B[Flask app in app.py]
    subgraph HabitsDomain[Habits domain]
        U[ui/routes.py dashboard]
        C[habits/routes.py]
        S[habits/schedule.py pure logic]
        E[habits/repository.py]
        F[habits/public.py]
    end
    subgraph InsightsDomain[Insights domain]
        D[insights/routes.py]
        T[insights/stats.py pure logic]
        H[insights/repository.py]
    end
    B --> U
    B --> C
    B --> D
    U --> E
    U --> S
    C --> E
    C --> S
    F --> E
    D -- "SEAM: habit_id in, ISO dates / streak / weekdays out" --> F
    D --> T
    D --> H
    E --> G1[(habits, checkins, habit_templates)]
    H --> G2[(milestones)]
    G1 -.same habits.db file.- G2
```

The seam is the arrow from `insights/routes.py` to `habits/public.py`. `insights` may only call `habit_exists`, `checkin_dates`, `current_streak`, and `scheduled_weekdays`; what crosses is a `habit_id` going in and plain values (ISO date strings, an integer streak, weekday numbers) coming out. In Assignment 2 each of these functions becomes an HTTP endpoint on the habits service, and the `milestones` table moves to the insights service's own database. The dashboard in `ui/` belongs to the habits side because it reads and writes habits and check-ins directly.

## 4. Database model

The schema intentionally keeps the two domains separated while sharing one SQLite file. The habits domain owns the habit records and check-ins, while the insights domain owns milestone records. The `milestones.habit_id` field intentionally has no foreign key to enforce the service boundary and allow future extraction in Assignment 2.

```mermaid
erDiagram
    HABITS ||--o{ CHECKINS : has

    HABITS {
        INTEGER id PK
        TEXT name
        TEXT cadence
        TEXT days_of_week
        TEXT time_of_day
        TEXT alert_type
        INTEGER alert_offset_minutes
        TEXT created_at
    }

    CHECKINS {
        INTEGER id PK
        INTEGER habit_id FK,UK "UNIQUE(habit_id, checked_on)"
        TEXT checked_on UK
    }

    HABIT_TEMPLATES {
        INTEGER id PK
        TEXT name UK
        TEXT cadence
    }

    MILESTONES {
        INTEGER id PK
        INTEGER habit_id UK "logical reference, no FK"
        TEXT kind UK "UNIQUE(habit_id, kind)"
        TEXT achieved_on
    }
```

`HABIT_TEMPLATES` is a standalone reference-data table. `MILESTONES.habit_id` is a logical reference only and has no foreign key. The `UNIQUE(habit_id, checked_on)` constraint makes repeated check-ins on the same day idempotent.

## 5. Business logic highlights

The habits logic is intentionally pure and unit-testable:

- `parse_schedule()` validates weekday, time, and alert inputs and normalizes custom offsets.
- `current_scheduled_streak()` counts consecutive scheduled dates, ignoring unscheduled days.
- `due_reminders()` matches current local minutes to each incomplete habit's alert time, including alerts that cross midnight.
- `completion_rate()` computes the fraction of completed days in a window.
- `scheduled_day_count()` counts how many days in the window the habit was actually due, so a Monday-only habit is measured out of 1 day, not 7.

The insights logic then builds on those values:

- `best_weekday()` identifies the weekday with the largest number of check-ins.
- `milestone_kinds()` derives milestone names such as `streak_7`, `streak_30`, etc.
- `insights.routes` exposes summary endpoints without importing the habits repository directly.

## 6. Testing and validation

The project uses `pytest` and `pytest-cov` to validate the core business logic and key route behavior. The suite checks:

- app creation and environment configuration
- database bootstrapping, idempotent seeding, and additive migration of an existing schema
- streak logic for daily and weekly behaviors
- schedule validation, persistence, scheduled-day toggles, and reminder timing
- completion-rate calculations
- habit creation, check-in idempotency, and errors for missing records
- template creation and insight summary endpoints

The current local validation command is:

```bash
ruff check .
ruff format --check .
mypy
pytest --cov=. --cov-report=term-missing
```

Latest validation (2026-10-12): 42 tests passed with 93% total coverage; Ruff lint, formatting, mypy, Python compilation, and `git diff --check` passed. Ruff lint/format/security checks and mypy are configured as local pre-commit gates. Docker validation requires Docker to be installed on the machine running the checker; it was unavailable in the development environment.

## 7. AI disclosure and evidence

The detailed, per-interaction log is in [AI_USAGE.md](./AI_USAGE.md).

> I acknowledge the use of [AI SYSTEMS, e.g. Claude and Cursor] to [HOW YOU USED THEM, e.g. generate the initial Flask skeleton, implement scheduled streaks and reminders, and review the project against the assignment rules]. The prompts used include [2-3 REAL PROMPTS]. The output of these prompts was used to [WHAT YOU KEPT, CHANGED, OR REJECTED].

## 8. Conclusion

The project successfully demonstrates a minimal but honest implementation of a Flask + SQLite habit tracker with a clean domain split, a narrow seam, idempotent data loading, and a testable business-logic layer. It remains aligned with the assignment constraints and is ready for final human review and final git-based handoff.
