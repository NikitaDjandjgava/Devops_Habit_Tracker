# AI Usage Log

| Date/commit | Tool | Prompt | Disposition (Accepted/Modified/Rejected) | What changed & why (if modified) | In my own words, how this works |
|---|---|---|---|---|---|
| 2026-10-09 / `5d6081d` | [TOOL] | [PROMPT that produced the Flask skeleton, `schema.sql`, `seed.json`, `db.py`] | [ ] | [ ] | [Explain `create_app`, `init_db` (`CREATE TABLE IF NOT EXISTS`), and the `_seed_habit_templates` empty-table guard] |
| 2026-10-11 / `47f61ec` | [TOOL] | [PROMPT for filling the Dockerfile TODOs / container contract] | [ ] | [ ] | [Explain why `app.py` binds `0.0.0.0` and reads `PORT` and `DATA_DIR`] |
| 2026-10-11 / `7903474` | [TOOL] | [PROMPT for weekly streaks, milestones, and the `habits/public.py` seam] | [ ] | [ ] | [Explain `current_streak`, `record_milestones` with `INSERT OR IGNORE`, and why `milestones.habit_id` has no FK] |
| 2026-10-11 / `9c5580b` | [TOOL] | [PROMPT for ADR entries 2-5] | [ ] | [ ] | [Which ADR text you rewrote yourself] |
| 2026-10-12 / `20befe2` | [TOOL] | [PROMPT for README/REPORT and validation] | [ ] | [ ] | [ ] |
| 2026-10-12 / `da0c70b` | [TOOL] | [PROMPT for applying RULES.md: ruff, mypy, docstrings] | [ ] | [ ] | [ ] |
| 2026-10-12 / `db6b3db` | [TOOL] | [PROMPT for the dashboard UI] | [ ] | [ ] | [Explain `dashboard()` and `toggle_checkin` (add vs. `delete_checkin`)] |
| 2026-10-12 / `6656e51` | [TOOL] | [PROMPT for scheduled habits and browser reminders] | [ ] | [ ] | [Explain `parse_schedule`, `current_scheduled_streak` skipping unscheduled days, and `due_reminders` checking today and tomorrow for alerts that cross midnight] |
| 2026-10-12 / [commit] | Cursor agent (Claude) | "Considering these rules that my project will be graded on as well as the rules from Rules.md, go over the entire project and see what else is missing, while making sure that everything already there works" | [ ] | Fixed the weekly rate to divide by scheduled days instead of 7; rewrote ADR-5 because it said notifications were not built; corrected ADR-2/3 dates to their commit date; fixed README/REPORT numbers, diagrams, and invalid Mermaid syntax | [DRAFT, REWRITE: `scheduled_day_count` walks each date from `start` to `end` and counts the ones whose `weekday()` is in the habit's `days_of_week`, which `insights/routes.py` gets through `habits_api.scheduled_weekdays`; `completion_rate` then divides check-ins by that count] |
