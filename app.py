"""
Presentation Layer - Tier 1
Flask routes and template rendering only.
All data is fetched through the KnessetService (Business Logic Layer).
"""
from flask import Flask, render_template, g
from dal import DatabaseConnection
from services import KnessetService

app = Flask(__name__)


# ── Per-request service setup ───────────────────────────────────────

def get_service() -> KnessetService:
    """Return a KnessetService for the current request,
    creating the underlying DB connection if needed."""
    if "service" not in g:
        db = DatabaseConnection()
        db.connect()
        g.db = db
        g.service = KnessetService(db)
    return g.service


@app.teardown_appcontext
def close_db(e=None):
    """Close the database connection at the end of each request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()
    g.pop("service", None)


# ── Routes ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    service = get_service()
    stats = service.get_dashboard_stats()
    return render_template("index.html", stats=stats)


@app.route("/members")
def members():
    service = get_service()
    all_members = service.get_all_members()
    return render_template("members.html", members=all_members)


@app.route("/member/<int:member_id>")
def member_details(member_id):
    service = get_service()
    data = service.get_member_details(member_id)
    if data is None:
        return "Member not found", 404
    return render_template(
        "member_details.html",
        member=data["member"],
        laws=data["laws"],
        committees=data["committees"],
    )


@app.route("/parties")
def parties():
    service = get_service()
    all_parties = service.get_all_parties()
    return render_template("parties.html", parties=all_parties)


@app.route("/party/<int:party_id>")
def party_details(party_id):
    service = get_service()
    data = service.get_party_details(party_id)
    if data is None:
        return "Party not found", 404
    return render_template(
        "party_details.html", party=data["party"], members=data["members"]
    )


@app.route("/committees")
def committees():
    service = get_service()
    all_committees = service.get_all_committees()
    return render_template("committees.html", committees=all_committees)


@app.route("/committee/<int:committee_id>")
def committee_details(committee_id):
    service = get_service()
    data = service.get_committee_details(committee_id)
    if data is None:
        return "Committee not found", 404
    return render_template(
        "committee_details.html",
        committee=data["committee"],
        members=data["members"],
    )


@app.route("/laws")
def laws():
    service = get_service()
    all_laws = service.get_all_laws()
    return render_template("laws.html", laws=all_laws)


@app.route("/law/<int:law_id>")
def law_details(law_id):
    service = get_service()
    data = service.get_law_details(law_id)
    if data is None:
        return "Law not found", 404
    return render_template(
        "law_details.html", law=data["law"], members=data["members"]
    )


# ── Entry point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
