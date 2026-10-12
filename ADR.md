# Architecture Decision Records

<!-- Add entries as you make decisions, on at least 3 distinct commit dates.
     Exactly 5 entries in total: 1 framework, 2 domain seam, 3 schema, 4 testing, 5 not built. -->

## 1. Backend language/framework choice
Date: 2026-10-09
Status: Decided
Context: The app is a small JSON API with two domains, served by one process, for roughly 2,000 users. The assignment emphasizes simple, explainable code over clever framework abstractions.
Decision: Python with Flask and the standard-library `sqlite3` module.
Alternatives considered: Django, rejected because its ORM, admin, and auth features are not needed for a single-process habit tracker; FastAPI, rejected because its async typing and dependency injection add complexity without improving a simple SQLite-backed service.
Consequences: The app stays small and readable, and most of the logic is in pure functions and explicit SQL; the trade-off is that the Flask development server is not production-grade, but that is acceptable for Assignment 1.

## 2. Domain scoping and seam between habits and insights
Date: 2026-10-11
Status: Decided
Context: The assignment requires two domains that are logically separable, and the insights domain must not become coupled to habits internals. We need a narrow seam that can still support future service boundaries in Assignment 2.
Decision: Keep all database reads and writes for habits in `habits/repository.py`, and expose only a small `habits/public.py` API for other domains. Insights imports only from that seam and never from `habits.repository` or `checkins` tables directly.
Alternatives considered: Having insights query `checkins` and `habits` tables directly, rejected because it creates hidden cross-domain coupling and makes later extraction into separate services harder; giving insights direct repository access, rejected because it breaks the “single seam” rule and makes the architecture harder to reason about.
Consequences: The project stays modular enough for the assignment, while the seam provides a clean future boundary for Assignment 2; the cost is that a few helper functions such as `habit_exists` and `current_streak` must be explicitly added.

## 3. SQLite schema and data-model decision
Date: 2026-10-11
Status: Decided
Context: The habit tracker needs idempotent check-ins, seedable reference labels, and a separate insights-owned table for milestone tracking without creating a hard dependency from insights to the habits tables.
Decision: Use the schema in `schema.sql`: `habits` and `checkins` remain in the habits domain, `habit_templates` stores seed data, and `milestones` is owned by insights but intentionally has no foreign key on `habit_id`.
Alternatives considered: Adding a foreign key from `milestones.habit_id` to `habits(id)`, rejected because it couples the insights domain to this schema at the database level; storing milestones in a habits table, rejected because it violates the logical separation required by the assignment.
Consequences: The database remains simple and explainable, and it supports idempotent daily tracking (`UNIQUE(habit_id, checked_on)`) and future service splits; the cost is that the schema relies on logical references rather than a database-enforced link for insights data.

## 4. Testing strategy and scope
Date: 2026-10-11
Status: Decided
Context: The rubric emphasizes business logic tests rather than framework glue, but there are still integration checks for route behavior and idempotent boot logic. The project needs to keep coverage high without testing Flask details too heavily.
Decision: Prioritize pure-function tests for `current_scheduled_streak`, `parse_schedule`, `due_reminders`, `completion_rate`, `scheduled_day_count`, and milestone derivation, and keep a small number of route-level tests for API validation and idempotent boot behavior.
Alternatives considered: Testing only HTTP routes, rejected because it would miss core logic errors and would not provide meaningful coverage of the business rules; testing every implementation detail, rejected because it is brittle and far slower to maintain.
Consequences: The project gets reliable, readable coverage while the tests remain fast and easy to explain in class; the trade-off is that some framework plumbing is intentionally thin and not the main focus of the suite.

## 5. Deliberately not built: server-side reminder delivery
Date: 2026-10-12
Status: Decided
Context: Users asked for reminders at a habit's scheduled time, but the assignment allows only one process and rules out background job runners, cron containers, and message brokers.
Decision: Reminders are computed by `due_reminders` and polled by the open dashboard through `/ui/reminders`; we do not build server-side delivery (email, mobile push, or alerts while the browser is closed), and we also skip accounts and per-user time zones.
Alternatives considered: An in-process scheduler thread that sends emails, rejected because it needs an external mail service and duplicates work if the app ever runs more than one instance; a cron container, rejected because a second container is out of scope.
Consequences: Reminders only fire while the dashboard tab is open, which is documented as a limitation; in Assignment 2 a separate notification service can take over delivery using the same `due_reminders` logic.
