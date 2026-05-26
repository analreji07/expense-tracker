# Expense Tracker

A small personal expense tracker. Add, edit, delete, filter expenses, and see a monthly summary with category breakdown.

## Stack

- **Backend:** Python 3.9+, Flask, SQLite (stdlib `sqlite3`)
- **Frontend:** Server-rendered HTML (Jinja2 template) with a small amount of inline CSS — no JS framework, no build step.
- **Storage:** A single `expenses.db` SQLite file created next to `app.py` on first run.

## How to run (exact commands)

```bash
cd expense-tracker

# 1. Create & activate a virtualenv (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Install deps
pip install -r requirements.txt

# 3. Run the app
python app.py
```

Then open <http://127.0.0.1:5000> in your browser. The SQLite database is created automatically on first launch.

## Features

| Requirement | Status |
|---|---|
| Add expense (title, amount, category, date, note) | Done |
| List sorted by date desc | Done |
| Edit / delete any expense | Done |
| Monthly summary: total + per-category breakdown | Done (current calendar month) |
| Filter by category, date range, partial title match | Done |
| Categories enum: Food, Transport, Shopping, Bills, Entertainment, Other | Done |
| Date defaults to today | Done |
| Server-side validation (length, numeric, enum, date format) | Done |

## Stack choices & tradeoffs

- **Flask over FastAPI/Django** — Smallest amount of code for a server-rendered CRUD app; no ORM ceremony. FastAPI would have shone if this were a JSON API; Django is overkill for ~150 LOC.
- **SQLite via stdlib `sqlite3`** — Zero setup, single-file DB, perfect for a personal app. Tradeoff: no migrations and single-writer; fine for one user.
- **Server-rendered HTML, no JS framework** — Brief said "frontend (HTML)", so I kept it that way: one Jinja template, plain `<form>` POSTs. No build pipeline, no SPA state to manage. Tradeoff: every action is a full page reload (snappy locally, would feel dated on a slow network).
- **Inline CSS in the template** — Single-file simplicity. For anything bigger I'd extract to `static/style.css`.
- **No authentication** — Personal, single-user, localhost-only. Adding auth would have doubled the surface area for little benefit here.

## Done vs skipped

**Done**
- All 5 required user stories.
- Server-side input validation with sensible error responses.
- Confirm dialog before delete.
- Empty-state message when filters return nothing.
- Mobile-friendly responsive layout.

**Skipped (and why)**
- **Multi-currency** — Brief explicitly says single local currency. Amount is displayed unformatted (e.g. `12.50`) without a currency symbol so it's locale-agnostic.
- **Authentication / multi-user** — Not in scope.
- **Charts** — A numeric category breakdown is enough for the summary; a bar/pie chart would have required adding Chart.js.
- **Pagination** — Personal expense lists stay small; sorting + filters cover the use case. Would add `LIMIT/OFFSET` if the table grows past a few thousand rows.
- **Tests** — Skipped for time. The natural starting point would be pytest around `parse_expense_form` and the route handlers using Flask's test client.
- **CSV import/export** — Not requested.
- **Editing via inline modal with JS** — Edit currently navigates to `/edit/<id>` which re-renders the index with a modal open. A JS-driven inline modal would be smoother but adds a dependency.

## Known rough edges

- **Filters don't affect the monthly summary** — Intentional (the brief asks for "current month" summary), but it can feel inconsistent. A toggle to "summarize filtered results" would be a nice add.
- **Validation errors return a plain-text 400 page** rather than re-rendering the form with field-level errors. Quick to fix but adds template plumbing.
- **No CSRF protection** — Flask doesn't include CSRF out of the box and this is localhost-only; I'd add Flask-WTF before deploying anywhere.
- **Amount stored as REAL (float)** — Fine for personal use; for accounting-grade precision I'd switch to integer cents.
- **Timezone** — "Today" uses the server's local date. On a hosted deploy you'd want explicit timezone handling.
- **Delete is irreversible** — No soft-delete or undo.
