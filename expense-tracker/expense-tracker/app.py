"""Personal Expense Tracker - Flask + SQLite."""
import os
import sqlite3
from datetime import date, datetime
from flask import Flask, g, render_template, request, redirect, url_for, jsonify, abort

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "expenses.db")
CATEGORIES = ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Other"]

app = Flask(__name__)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute(
        """CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            note TEXT
        )"""
    )
    con.commit()
    con.close()


def parse_expense_form(form):
    title = (form.get("title") or "").strip()
    amount_raw = (form.get("amount") or "").strip()
    category = (form.get("category") or "").strip()
    date_raw = (form.get("date") or "").strip() or date.today().isoformat()
    note = (form.get("note") or "").strip()

    errors = []
    if not title or len(title) > 200:
        errors.append("Title is required (max 200 chars).")
    try:
        amount = float(amount_raw)
        if amount < 0:
            errors.append("Amount must be >= 0.")
    except ValueError:
        amount = 0.0
        errors.append("Amount must be a number.")
    if category not in CATEGORIES:
        errors.append("Invalid category.")
    try:
        datetime.strptime(date_raw, "%Y-%m-%d")
    except ValueError:
        errors.append("Invalid date (YYYY-MM-DD).")

    return {
        "title": title, "amount": amount, "category": category,
        "date": date_raw, "note": note,
    }, errors


@app.route("/")
def index():
    db = get_db()
    category = request.args.get("category", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()
    title_q = request.args.get("q", "").strip()

    sql = "SELECT * FROM expenses WHERE 1=1"
    params = []
    if category and category in CATEGORIES:
        sql += " AND category = ?"; params.append(category)
    if date_from:
        sql += " AND date >= ?"; params.append(date_from)
    if date_to:
        sql += " AND date <= ?"; params.append(date_to)
    if title_q:
        sql += " AND title LIKE ?"; params.append(f"%{title_q}%")
    sql += " ORDER BY date DESC, id DESC"
    expenses = db.execute(sql, params).fetchall()

    # Monthly summary (current month, ignores filters by design)
    today = date.today()
    month_start = today.replace(day=1).isoformat()
    rows = db.execute(
        "SELECT category, SUM(amount) AS total FROM expenses "
        "WHERE date >= ? AND date <= ? GROUP BY category",
        (month_start, today.isoformat()),
    ).fetchall()
    summary = {c: 0.0 for c in CATEGORIES}
    for r in rows:
        summary[r["category"]] = r["total"] or 0.0
    month_total = sum(summary.values())

    return render_template(
        "index.html",
        expenses=expenses,
        categories=CATEGORIES,
        summary=summary,
        month_total=month_total,
        month_label=today.strftime("%B %Y"),
        filters={"category": category, "date_from": date_from, "date_to": date_to, "q": title_q},
        today=today.isoformat(),
        edit_expense=None,
    )


@app.route("/add", methods=["POST"])
def add():
    data, errors = parse_expense_form(request.form)
    if errors:
        return ("; ".join(errors), 400)
    db = get_db()
    db.execute(
        "INSERT INTO expenses (title, amount, category, date, note) VALUES (?,?,?,?,?)",
        (data["title"], data["amount"], data["category"], data["date"], data["note"]),
    )
    db.commit()
    return redirect(url_for("index"))


@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit(expense_id):
    db = get_db()
    row = db.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    if not row:
        abort(404)
    if request.method == "POST":
        data, errors = parse_expense_form(request.form)
        if errors:
            return ("; ".join(errors), 400)
        db.execute(
            "UPDATE expenses SET title=?, amount=?, category=?, date=?, note=? WHERE id=?",
            (data["title"], data["amount"], data["category"], data["date"], data["note"], expense_id),
        )
        db.commit()
        return redirect(url_for("index"))
    # GET -> render index with edit modal preloaded
    return render_index_with_edit(row)


def render_index_with_edit(row):
    db = get_db()
    expenses = db.execute("SELECT * FROM expenses ORDER BY date DESC, id DESC").fetchall()
    today = date.today()
    month_start = today.replace(day=1).isoformat()
    rows = db.execute(
        "SELECT category, SUM(amount) AS total FROM expenses WHERE date >= ? AND date <= ? GROUP BY category",
        (month_start, today.isoformat()),
    ).fetchall()
    summary = {c: 0.0 for c in CATEGORIES}
    for r in rows:
        summary[r["category"]] = r["total"] or 0.0
    return render_template(
        "index.html",
        expenses=expenses,
        categories=CATEGORIES,
        summary=summary,
        month_total=sum(summary.values()),
        month_label=today.strftime("%B %Y"),
        filters={"category": "", "date_from": "", "date_to": "", "q": ""},
        today=today.isoformat(),
        edit_expense=row,
    )


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete(expense_id):
    db = get_db()
    db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    db.commit()
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
