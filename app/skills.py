"""Product agent skills: fixed executable capabilities, not installed plugins."""
import re

SKILLS = [
    {"id": key, "label": label, "icon": key} for key, label in (
        ("planning", "Task planning"), ("variant_analysis", "Variant analysis"),
        ("clinical_context", "Clinical context"), ("research", "Evidence review"),
        ("proposal", "Develop proposals"), ("challenge", "Challenge assumptions"),
        ("critique", "Critical synthesis"))]
ROLE_SKILLS = {
    "orchestrator": ["planning"], "genomics": ["variant_analysis"],
    "clinical": ["clinical_context"], "literature": ["research"],
    "research": ["research"], "supporter": ["proposal"],
    "challenger": ["challenge"], "critic": ["critique"],
}


def role_metadata(role):
    return {"skills": ROLE_SKILLS.get(role, []), "icon": role,
            "alignment": {"supporter": "supporting", "challenger": "challenging"}.get(role, "neutral")}


def workflow_capabilities():
    return {"skills": SKILLS,
            "task_modes": [{"id": key, "label": label} for key, label in (
                ("auto", "Choose from my question"), ("investigation", "Evidence investigation"),
                ("idea_review", "Review an idea"))],
            "review_roles": [{"id": role, "label": role.title(), **role_metadata(role)}
                             for role in ("research", "supporter", "challenger")],
            "review_roster_fixed": True}


def resolve_task_mode(requested, question, bundle):
    if requested != "auto":
        return requested, "Task mode explicitly selected or legacy investigation default."
    if re.search(r"\b(review|evaluate|critique|stress[- ]test|assess|debate)\b.{0,45}\b(idea|proposal|design)\b|\bbrainstorm(?:ing)?\b", question, re.I):
        return "idea_review", "Question explicitly requests idea/proposal review; supplied files are inventoried, not validated."
    if not bundle.files and re.search(r"\b(idea|proposal|feasibility)\b", question, re.I):
        return "idea_review", "Question explicitly requests proposal/design review without uploaded evidence."
    return "investigation", "Uploaded evidence or an evidence question uses the investigation workflow."
