# backend/chat_context.py
# Builds rich live context from the database for the chatbot system prompt

from backend.models import Event, CertificateTemplate, TeamMember, Project


# ======================================================
# EVENTS
# ======================================================
def get_upcoming_events():
    events = Event.query.order_by(Event.created_at.desc()).limit(10).all()
    if not events:
        return "No events are currently scheduled."

    lines = ["Current / Recent Events:"]
    for e in events:
        line = f"- {e.title}"
        if e.description:
            line += f": {e.description[:120]}"
        lines.append(line)
    return "\n".join(lines)


# ======================================================
# CERTIFICATE AVAILABILITY
# ======================================================
def get_certificate_events():
    certs = CertificateTemplate.query.all()
    if not certs:
        return "Certificates are not currently available for any event."
    titles = [c.event_title for c in certs]
    return "Certificates available for: " + ", ".join(titles)


# ======================================================
# FULL TEAM CONTEXT (for "who is the president" queries)
# ======================================================
def get_team_context():
    # Active office bearers
    office = (
        TeamMember.query
        .filter_by(member_type="office", is_former=False)
        .order_by(TeamMember.id.asc())
        .all()
    )
    member_count = TeamMember.query.filter_by(member_type="member", is_former=False).count()

    if not office:
        return f"InnoSphere has {member_count} active members. Office bearer details are not yet listed."

    lines = ["Current InnoSphere Office Bearers:"]
    for m in office:
        line = f"- {m.role}: {m.name}"
        if m.department:
            line += f" ({m.department}"
            if m.college:
                line += f", {m.college}"
            line += ")"
        if m.member_id:
            line += f" [ID: {m.member_id}]"
        lines.append(line)

    lines.append(f"\nTotal active members: {member_count}")
    return "\n".join(lines)


# ======================================================
# PROJECTS CONTEXT
# ======================================================
def get_projects_context():
    ongoing   = Project.query.filter_by(status="ongoing").all()
    completed = Project.query.filter_by(status="completed").all()

    lines = []

    if ongoing:
        lines.append("Ongoing Projects:")
        for p in ongoing:
            line = f"- {p.title}"
            if p.description:
                line += f": {p.description[:100]}"
            if p.lead:
                line += f" (Lead: {p.lead.name})"
            lines.append(line)
    else:
        lines.append("Ongoing Projects: None currently.")

    if completed:
        lines.append("\nCompleted Projects:")
        for p in completed:
            line = f"- {p.title}"
            if p.description:
                line += f": {p.description[:100]}"
            if p.lead:
                line += f" (Lead: {p.lead.name})"
            lines.append(line)
    else:
        lines.append("\nCompleted Projects: None yet.")

    return "\n".join(lines)


# ======================================================
# ABOUT INNOSPHERE (static context)
# ======================================================
def get_about_context():
    return """
About InnoSphere Club:
- InnoSphere is an interdisciplinary innovation club under Paavai Innovation Forum, Paavai Engineering College.
- InnoSphere Club was proposed and formed by Janarthanan P, bringing together students with national-level internship exposure at premier institutions such as IISc and other reputed research centers.
- Patron: Dr. M. Premkumar (Principal, Paavai Engineering College)
- Director: Prof. Dr. R. R. Krishnamurthy (Director, Centre for Research, Paavai Educational Institutions)
- Centre Head: Kamala Krishnamurthy (Centre Head, Paavai Innovation Forum)
- Vision: To build a sustainable innovation-centric ecosystem empowering students to transform ideas into impactful solutions.
- Mission: Encourage interdisciplinary collaboration, bridge academic knowledge with real-world applications, promote research and innovation.
- Members can join via the 'Join Us' page; applications are reviewed by the admin.
- InnoSphere conducts events, manages projects, and issues certificates to participants.
""".strip()


# ======================================================
# COMBINED FULL CONTEXT BUILDER
# ======================================================
def get_full_context(intent=None):
    """
    Returns the richest possible context for the chatbot.
    If intent is provided, prioritise the relevant section.
    """
    sections = []

    # Always include about + team for any query
    sections.append(get_about_context())
    sections.append(get_team_context())

    if intent == "EVENT" or intent is None:
        sections.append(get_upcoming_events())

    if intent == "PROJECT" or intent is None:
        sections.append(get_projects_context())

    if intent == "CERTIFICATE":
        sections.append(get_certificate_events())

    return "\n\n".join(sections)


# Legacy wrappers (kept for backward compat with chat_router)
def get_team_summary():
    return get_team_context()
