"""Recognize saved session results without opening or reinterpreting their output."""
from html import escape


def connection_label(record):
    mode = getattr(record.get("request"), "mode", None)
    return {"Demo": "Interactive demo", "Mock": "Recorded playback", "Live": "Live connection"}.get(
        mode, f"Mode: {mode}" if mode else "Mode not recorded")


def outcome_label(record):
    state = record["run"]
    if not state.complete:
        return "No final result"
    if state.status == "cancelled":
        return "Cancelled"
    if state.status == "error":
        return "Ended with an error"
    if state.status != "complete":
        return f"Status: {state.status or 'not recorded'}"
    if state.abstained:
        return "Abstained"
    if state.task_mode == "idea_review":
        return "Idea review complete"
    return "Complete (errors recorded)" if state.errors else "Complete"


def _question(record):
    recorded = record["run"].question
    return recorded or getattr(record.get("request"), "question", "") or ""


def result_labels(records):
    """Keep compact IDs distinguishable even when their first eight characters match."""
    ids = [record["id"] for record in records]
    labels = {}
    for record in records:
        result_id = record["id"]
        size = min(8, len(result_id))
        while size < len(result_id) and any(
            other != result_id and other[:size] == result_id[:size] for other in ids
        ):
            size += 1
        question = " ".join(_question(record).split())
        excerpt = question[:60] + ("…" if len(question) > 60 else "")
        # Native menus truncate a single line on narrow screens. Put the unique
        # part first so repeated questions never hide every distinguishing field.
        labels[result_id] = (f"#{result_id[:size]} · {outcome_label(record)} · {connection_label(record)} · "
                             f"{excerpt or 'Question not recorded'}")
    return labels


def selected_result_html(record):
    """Only inspect small saved metadata; never serialize findings or event history."""
    state, request = record["run"], record.get("request")
    recorded_question = state.question
    submitted_question = getattr(request, "question", "")
    question_label = "Recorded research question" if recorded_question else "Submitted research question"
    question = _question(record)
    config = state.config if isinstance(state.config, dict) else {}
    execution = config.get("run_mode")
    execution = execution if isinstance(execution, str) and execution.strip() else "Not recorded"
    mode = getattr(request, "mode", None)
    summary = f"{connection_label(record)} · {outcome_label(record)}"
    details = (
        f"<p class='argument-trace-id'>Session record ID: {escape(record['id'])}</p>"
        f"<p class='argument-trace-id'>Backend run ID: {escape(state.run_id or 'Not recorded')}</p>"
        f"<p class='argument-trace-note'>Saved connection mode: {escape(mode or 'Not recorded')}<br>"
        f"Execution mode reported in saved configuration: {escape(execution)}<br>"
        f"Recorded status: {escape(state.status or 'Not recorded')}</p>"
        "<p class='argument-trace-note'>Live connection describes the connection route, not confirmation of live providers. "
        "Session record IDs distinguish these local entries; backend IDs may be missing or reused. "
        "These records are retained only in this open session.</p>"
    )
    if submitted_question and submitted_question != recorded_question:
        details += ("<div class='argument-trace-turn'><div class='argument-trace-kicker'>Submitted research question</div>"
                    f"<div class='argument-trace-text'>{escape(submitted_question)}</div></div>")
    return (
        "<div class='argument-trace-turn'><div class='argument-trace-kicker'>Selected saved result</div>"
        f"<div class='argument-trace-agent'>{escape(summary)}</div>"
        f"<div class='argument-trace-kicker'>{question_label}</div>"
        f"<div class='argument-trace-text'>{escape(question or 'Question not recorded')}</div></div>"
        f"<details class='argument-trace'><summary>Saved result identifiers and mode</summary>{details}</details>"
    )
