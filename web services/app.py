"""
Web Service – Deot (Opinions) REST API
========================================
This is the Web Service project.
It provides a REST API for managing opinions/comments (דעות) about
Knesset members. The main Knesset website consumes this service
via HTTP requests.

Equivalent to an ASMX Web Service in ASP.NET.

Runs on port 5000.
"""
from flask import Flask, jsonify, request  # type: ignore
from dal import DeotDatabase  # type: ignore
from datetime import datetime

app = Flask(__name__)


# ── Per-request database setup ─────────────────────────────────────

from flask import g  # type: ignore


def get_db() -> DeotDatabase:
    """Return a DeotDatabase for the current request."""
    if "db" not in g:
        g.db = DeotDatabase()
        g.db.connect()
    return g.db


@app.teardown_appcontext
def close_db(e=None):
    """Close the database connection at the end of each request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ══════════════════════════════════════════════════════════════════════
#  READ ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

@app.route("/api/deot")
def get_deot():
    """Return all opinions, newest first."""
    db = get_db()
    deot = db.get_all_deot()
    # Format dates for JSON serialization
    for d in deot:
        if d.get("dateOfDea") and hasattr(d["dateOfDea"], "strftime"):
            d["dateOfDea"] = d["dateOfDea"].strftime("%Y-%m-%d %H:%M")
    return jsonify(deot)


@app.route("/api/deot/<int:dea_id>")
def get_dea(dea_id):
    """Return a single opinion by ID."""
    db = get_db()
    dea = db.get_dea_by_id(dea_id)
    if dea is None:
        return jsonify({"error": "Opinion not found"}), 404
    if dea.get("dateOfDea") and hasattr(dea["dateOfDea"], "strftime"):
        dea["dateOfDea"] = dea["dateOfDea"].strftime("%Y-%m-%d %H:%M")
    return jsonify(dea)


@app.route("/api/deot/count")
def get_count():
    """Return the total number of opinions."""
    db = get_db()
    return jsonify({"count": db.get_deot_count()})


# ══════════════════════════════════════════════════════════════════════
#  WRITE ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

@app.route("/api/deot", methods=["POST"])
def add_dea():
    """Create a new opinion. Expects JSON body with:
    name, title, content, dateOfDea (optional — defaults to now)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    required = ["name", "title", "content"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    dea_id = get_db().add_dea(
        name=data["name"],
        title=data["title"],
        content=data["content"],
        dateOfDea=data.get("dateOfDea", datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    return jsonify({"success": True, "DeaId": dea_id}), 201


@app.route("/api/deot/<int:dea_id>", methods=["DELETE"])
def delete_dea(dea_id):
    """Delete an opinion by ID."""
    db = get_db()
    dea = db.get_dea_by_id(dea_id)
    if dea is None:
        return jsonify({"error": "Opinion not found"}), 404
    db.delete_dea(dea_id)
    return jsonify({"success": True})


# ── Entry point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  Deot Web Service (REST API)")
    print("  Running on http://localhost:5000")
    print("  Endpoints:")
    print("    GET    /api/deot          — All opinions")
    print("    GET    /api/deot/<id>     — Single opinion")
    print("    GET    /api/deot/count    — Total count")
    print("    POST   /api/deot          — Add new opinion")
    print("    DELETE /api/deot/<id>     — Delete opinion")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
