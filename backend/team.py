# backend/team.py

from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime

from backend.db import db
from backend.models import TeamMember, Project, DEFAULT_OFFICE_ROLES
from backend.cloudinary_helper import upload_file, delete_file

team_bp = Blueprint("team", __name__)
FOLDER  = "innosphere/team"


# ─────────────────────────────────────────
# ID generators
# ─────────────────────────────────────────
def generate_office_id():
    last = TeamMember.query.filter_by(member_type="office").order_by(TeamMember.id.desc()).first()
    if not last:
        return "PIFIS021"
    try:
        num = int(last.member_id.replace("PIFIS", ""))
    except ValueError:
        num = 20
    return f"PIFIS{num + 1:03d}"


def generate_member_id():
    last = TeamMember.query.filter_by(member_type="member").order_by(TeamMember.id.desc()).first()
    if not last:
        return "PIFINSM001"
    try:
        num = int(last.member_id.replace("PIFINSM", ""))
    except ValueError:
        num = 0
    return f"PIFINSM{num + 1:03d}"


# ─────────────────────────────────────────
# ADMIN: TEAM MANAGEMENT
# ─────────────────────────────────────────
@team_bp.route("/admin/team", methods=["GET", "POST"])
def admin_team():
    if not session.get("admin_logged_in"):
        return redirect(url_for("auth.login"))

    msg = err = None

    if request.method == "POST":
        action = request.form.get("action", "")

        # ── DELETE ──────────────────────────────────
        if action == "delete":
            m = TeamMember.query.get(request.form.get("member_id"))
            if m:
                delete_file(getattr(m, "cloudinary_public_id", None), resource_type="image")
                db.session.delete(m)
                db.session.commit()
                msg = "Member deleted."
            return redirect(url_for("team.admin_team"))

        # ── MOVE TO FORMER ───────────────────────────
        if action == "make_former":
            m = TeamMember.query.get(request.form.get("member_id"))
            if m:
                m.is_former = True
                db.session.commit()
                msg = f"{m.name} moved to Alumni."
            return redirect(url_for("team.admin_team"))

        # ── RESTORE FROM FORMER ───────────────────────
        if action == "restore":
            m = TeamMember.query.get(request.form.get("member_id"))
            if m:
                m.is_former = False
                db.session.commit()
                msg = f"{m.name} restored to Active Office Bearers."
            return redirect(url_for("team.admin_team"))

        # ── UPDATE OFFICE BEARER ─────────────────────
        if action == "update_office":
            m = TeamMember.query.get(request.form.get("member_id"))
            if m:
                m.name       = request.form.get("name",       m.name).strip()
                m.role       = request.form.get("role",       m.role).strip()
                m.department = request.form.get("department", m.department or "").strip()
                m.college    = request.form.get("college",    m.college or "").strip()
                m.batch      = request.form.get("batch",      m.batch or "").strip()
                
                image = request.files.get("image")
                if image and image.filename:
                    if m.cloudinary_public_id:
                        try:
                            delete_file(m.cloudinary_public_id, resource_type="image")
                        except Exception:
                            pass
                    result                 = upload_file(image, folder=FOLDER, resource_type="image")
                    m.image_file           = result["secure_url"]
                    m.cloudinary_public_id = result["public_id"]

                db.session.commit()
                msg = f"Office bearer {m.name} updated."
            return redirect(url_for("team.admin_team"))

        # ── ADD OFFICE BEARER ────────────────────────
        if action == "add_office":
            image = request.files.get("image")
            role  = request.form.get("role", "").strip()

            if not image or not image.filename:
                err = "Office bearer photo is required."
            elif not role:
                err = "Role is required."
            else:
                result    = upload_file(image, folder=FOLDER, resource_type="image")
                image_url = result["secure_url"]
                public_id = result["public_id"]

                m = TeamMember(
                    member_id            = generate_office_id(),
                    name                 = request.form.get("name", "").strip(),
                    role                 = role,
                    department           = request.form.get("department", "").strip(),
                    college              = request.form.get("college", "").strip(),
                    batch                = request.form.get("batch", "").strip(),
                    member_type          = "office",
                    image_file           = image_url,
                    cloudinary_public_id = public_id,
                    is_former            = False,
                    created_at           = datetime.utcnow(),
                )
                db.session.add(m)
                db.session.commit()
                msg = f"Office bearer {m.name} added."
            return redirect(url_for("team.admin_team"))

        # ── ADD MEMBER ───────────────────────────────
        if action == "add_member":
            m = TeamMember(
                member_id   = generate_member_id(),
                name        = request.form.get("name", "").strip(),
                role        = "Member",
                department  = request.form.get("department", "").strip(),
                college     = request.form.get("college", "").strip(),
                batch       = request.form.get("batch", "").strip(),
                member_type = "member",
                image_file  = None,
                cloudinary_public_id = None,
                is_former   = False,
                created_at  = datetime.utcnow(),
            )
            db.session.add(m)
            db.session.commit()
            msg = f"Member {m.name} added."
            return redirect(url_for("team.admin_team"))

    # Build role slot map
    active_office = TeamMember.query.filter_by(member_type="office", is_former=False).order_by(TeamMember.id.asc()).all()
    filled        = {m.role: m for m in active_office}
    role_slots    = [(role, filled.get(role)) for role in DEFAULT_OFFICE_ROLES]
    custom        = [m for m in active_office if m.role not in DEFAULT_OFFICE_ROLES]
    for m in custom:
        role_slots.append((m.role, m))

    former_office = TeamMember.query.filter_by(member_type="office", is_former=True).order_by(TeamMember.id.desc()).all()
    members       = TeamMember.query.filter_by(member_type="member", is_former=False).order_by(TeamMember.id.asc()).all()

    return render_template(
        "admin/team.html",
        role_slots    = role_slots,
        default_roles = DEFAULT_OFFICE_ROLES,
        former_office = former_office,
        members       = members,
        msg = msg, err = err
    )


# ─────────────────────────────────────────
# ADMIN: MEMBER EDIT PAGE
# ─────────────────────────────────────────
@team_bp.route("/admin/members", methods=["GET", "POST"])
def admin_members():
    if not session.get("admin_logged_in"):
        return redirect(url_for("auth.login"))

    msg = None
    if request.method == "POST":
        action = request.form.get("action", "")
        if action == "update_member":
            m = TeamMember.query.get(request.form.get("member_id"))
            if m:
                m.name       = request.form.get("name",       m.name).strip()
                m.role       = request.form.get("role",       m.role or "").strip()
                m.department = request.form.get("department", m.department or "").strip()
                m.college    = request.form.get("college",    m.college or "").strip()
                m.batch      = request.form.get("batch",      m.batch or "").strip()
                new_pids     = request.form.getlist("project_ids")
                m.projects   = []
                for pid in new_pids:
                    p = Project.query.get(int(pid))
                    if p and m not in p.members:
                        p.members.append(m)
                db.session.commit()
                msg = f"Member {m.name} updated."

    members  = TeamMember.query.filter_by(member_type="member").order_by(TeamMember.id.asc()).all()
    projects = Project.query.order_by(Project.title).all()
    return render_template("admin/members.html", members=members, projects=projects, msg=msg)


# ─────────────────────────────────────────
# PUBLIC PAGES
# ─────────────────────────────────────────
@team_bp.route("/team")
def public_team():
    active_office = TeamMember.query.filter_by(member_type="office", is_former=False).order_by(TeamMember.id.asc()).all()
    filled     = {m.role: m for m in active_office}
    role_slots = [(role, filled.get(role)) for role in DEFAULT_OFFICE_ROLES]
    custom     = [m for m in active_office if m.role not in DEFAULT_OFFICE_ROLES]
    for m in custom:
        role_slots.append((m.role, m))

    members = TeamMember.query.filter_by(member_type="member", is_former=False).order_by(TeamMember.id.asc()).all()
    return render_template("team.html", role_slots=role_slots, members=members)


@team_bp.route("/alumni")
def alumni():
    former = TeamMember.query.filter_by(member_type="office", is_former=True).order_by(TeamMember.id.desc()).all()
    return render_template("alumni.html", former=former)


@team_bp.route("/members")
def public_members():
    search = request.args.get("q", "").strip()
    query  = TeamMember.query.filter_by(member_type="member", is_former=False)
    if search:
        query = query.filter(
            db.or_(
                TeamMember.member_id.ilike(f"%{search}%"),
                TeamMember.name.ilike(f"%{search}%")
            )
        )
    members = query.order_by(TeamMember.member_id.asc()).all()
    return render_template("members.html", members=members, search=search)
