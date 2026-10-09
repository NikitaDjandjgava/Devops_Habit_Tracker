# Architecture Decision Records

<!-- Add entries as you make decisions, on at least 3 distinct commit dates.
     Exactly 5 entries in total: 1 framework, 2 domain seam, 3 schema, 4 testing, 5 not built. -->

## 1. Backend language/framework choice
Date: 2026-10-09
Status: Decided
Context: The app is a small JSON API with two domains, served by one process, for roughly 2,000 users.
Decision: Python with Flask and the standard-library `sqlite3` module.
Alternatives considered: Django, rejected because its ORM, admin and auth are unused here and add far more surface area than two domains need; FastAPI, rejected because its async and typing features buy nothing for a synchronous SQLite app.
Consequences: Very little framework magic, so every line is explainable; I write my own SQL and validation, and the Flask dev server is not production-grade (acceptable for Assignment 1).
