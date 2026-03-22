"""
Presentation Layer - Tier 1
Flask routes and template rendering only.
All data is fetched through the KnessetService (Business Logic Layer).
"""
from functools import wraps
import os
import uuid
from flask import Flask, render_template, g, request, redirect, url_for, session, flash# type: ignore
from dal import DatabaseConnection# type: ignore
from services import KnessetService# type: ignore

app = Flask(__name__)
app.secret_key = "knesset_admin_secret_key_2026"

def handle_upload(file_obj, subfolder, old_url=""):
    """Saves an uploaded file to static/images/{subfolder} and returns its URL path."""
    if file_obj and file_obj.filename:
        ext = os.path.splitext(file_obj.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        folder_path = os.path.join(app.root_path, "static", "images", subfolder)
        os.makedirs(folder_path, exist_ok=True)
        file_obj.save(os.path.join(folder_path, filename))
        return filename
    return old_url

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


# ── Auth helpers ────────────────────────────────────────────────────

def login_required(f):
    """Decorator: redirect to login page if user is not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.context_processor
def inject_admin_flag():
    """Make the admin flag available in every template."""
    return {"is_admin": session.get("admin", False)}


# ── Public Routes ───────────────────────────────────────────────────

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


# ── Login / Logout ──────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        service = get_service()
        if service.authenticate(username, password):
            session["admin"] = True
            session["username"] = username
            return redirect(url_for("admin_panel"))
        flash("שם משתמש או סיסמה שגויים", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ── Admin Panel (protected) ────────────────────────────────────────

@app.route("/admin")
@login_required
def admin_panel():
    service = get_service()
    data = service.get_admin_data()
    return render_template("admin.html", **data)


@app.route("/admin/member/add", methods=["POST"])
@login_required
def admin_add_member():
    service = get_service()
    photo_url = handle_upload(request.files.get("photo"), "mks")
    service.create_member(
        member_name=request.form["member_name"],
        age=int(request.form["age"]),
        job=request.form["job"],
        photo_url=photo_url,
        partyID=int(request.form["partyID"]),
        committee_ids=[int(x) for x in request.form.getlist("committee_ids") if x],
        law_ids=[int(x) for x in request.form.getlist("law_ids") if x],
    )
    flash("חבר הכנסת נוסף בהצלחה!", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/member/edit/<int:item_id>", methods=["POST"])
@login_required
def admin_edit_member(item_id):
    service = get_service()
    photo_url = handle_upload(
        request.files.get("photo"), 
        "mks", 
        request.form.get("existing_photo_url", "")
    )
    service.update_member(
        member_id=item_id,
        member_name=request.form["member_name"],
        age=int(request.form["age"]),
        job=request.form["job"],
        photo_url=photo_url,
        partyID=int(request.form["partyID"]),
        committee_ids=[int(x) for x in request.form.getlist("committee_ids") if x],
        law_ids=[int(x) for x in request.form.getlist("law_ids") if x],
    )
    flash("חבר הכנסת עודכן בהצלחה!", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/member/delete/<int:item_id>", methods=["POST"])
@login_required
def admin_delete_member(item_id):
    service = get_service()
    # Fetch photo filename before deleting the member record
    member = service.get_member_details(item_id)
    photo_url = member["member"].get("photo_url", "") if member else ""
    service.delete_member(item_id)
    # Remove the photo file from disk
    if photo_url:
        photo_path = os.path.join(app.root_path, "static", "images", "mks", photo_url)
        if os.path.isfile(photo_path):
            os.remove(photo_path)
    flash("חבר הכנסת נמחק בהצלחה!", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/party/add", methods=["POST"])
@login_required
def admin_add_party():
    service = get_service()
    photo_url = handle_upload(request.files.get("photo"), "parties")
    service.create_party(
        party_name=request.form["party_name"],
        mandates=int(request.form["mandates"]),
        photo_url=photo_url,
        member_ids=[int(x) for x in request.form.getlist("member_ids") if x],
    )
    flash("המפלגה נוספה בהצלחה!", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/party/edit/<int:item_id>", methods=["POST"])
@login_required
def admin_edit_party(item_id):
    service = get_service()
    photo_url = handle_upload(
        request.files.get("photo"), 
        "parties", 
        request.form.get("existing_photo_url", "")
    )
    service.update_party(
        party_id=item_id,
        party_name=request.form["party_name"],
        mandates=int(request.form["mandates"]),
        photo_url=photo_url,
        member_ids=[int(x) for x in request.form.getlist("member_ids") if x],
    )
    flash("המפלגה עודכנה בהצלחה!", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/party/delete/<int:item_id>", methods=["POST"])
@login_required
def admin_delete_party(item_id):
    service = get_service()
    # Fetch logo filename before deleting the party record
    party_data = service.get_party_details(item_id)
    photo_url = party_data["party"].get("photo_url", "") if party_data else ""
    service.delete_party(item_id)
    # Remove the logo file from disk
    if photo_url:
        photo_path = os.path.join(app.root_path, "static", "images", "parties", photo_url)
        if os.path.isfile(photo_path):
            os.remove(photo_path)
    flash("המפלגה נמחקה בהצלחה!", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/committee/add", methods=["POST"])
@login_required
def admin_add_committee():
    service = get_service()
    service.create_committee(
        commitie_name=request.form["commitie_name"],
        description=request.form["description"],
        LeaderID=int(request.form["LeaderID"]),
        member_ids=[int(x) for x in request.form.getlist("member_ids") if x],
    )
    flash("הוועדה נוספה בהצלחה!", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/committee/edit/<int:item_id>", methods=["POST"])
@login_required
def admin_edit_committee(item_id):
    service = get_service()
    service.update_committee(
        committee_id=item_id,
        commitie_name=request.form["commitie_name"],
        description=request.form["description"],
        LeaderID=int(request.form["LeaderID"]),
        member_ids=[int(x) for x in request.form.getlist("member_ids") if x],
    )
    flash("הוועדה עודכנה בהצלחה!", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/committee/delete/<int:item_id>", methods=["POST"])
@login_required
def admin_delete_committee(item_id):
    get_service().delete_committee(item_id)
    flash("הוועדה נמחקה בהצלחה!", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/law/add", methods=["POST"])
@login_required
def admin_add_law():
    service = get_service()
    service.create_law(
        law_name=request.form["law_name"],
        description=request.form["description"],
        member_ids=[int(x) for x in request.form.getlist("member_ids") if x],
    )
    flash("החוק נוסף בהצלחה!", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/law/edit/<int:item_id>", methods=["POST"])
@login_required
def admin_edit_law(item_id):
    service = get_service()
    service.update_law(
        law_id=item_id,
        law_name=request.form["law_name"],
        description=request.form["description"],
        member_ids=[int(x) for x in request.form.getlist("member_ids") if x],
    )
    flash("החוק עודכן בהצלחה!", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/law/delete/<int:item_id>", methods=["POST"])
@login_required
def admin_delete_law(item_id):
    get_service().delete_law(item_id)
    flash("החוק נמחק בהצלחה!", "success")
    return redirect(url_for("admin_panel"))


# ── Entry point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
