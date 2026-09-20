"""Human-readable selection notes beside the exact bounded follow-up payload."""
from html import escape
import json

import streamlit as st

from .details import render_details


def _count(pair):
    included, available = pair
    return f"{included} of {available}" if available is not None else str(included)


def preview_label(inspection):
    counts = inspection.counts()
    return (f"Prior generated context: {_count(counts['findings'])} findings, "
            f"{_count(counts['weak_points'])} weak points, {_count(counts['discussion'])} discussion turns")


def preview_html(inspection, *, include_disclosure=True):
    counts = inspection.counts()
    rules = {"findings": "First 8 findings in recorded order", "weak_points": "First 6 weak points in recorded order",
             "discussion": "Last 4 discussion turns in recorded order"}
    rows = []
    for field, noun in (("findings", "findings"), ("weak_points", "weak points"), ("discussion", "discussion turns")):
        included, available = counts[field]
        text = f"Included: {_count(counts[field])} {noun}."
        if available is not None:
            text += f" {rules[field]}. {available - included} not included in this prior-context payload."
        rows.append(f"<p class='argument-trace-note'>{escape(text)}</p>")
    reference_count = _count(counts['references'])
    reference_note = f"Included: {reference_count} source references attached to the included findings."
    if inspection.state is not None:
        reference_note += (" Up to the first 3 references per included finding. "
                           f"{counts['references_in_omitted_findings']} further source references belong to omitted findings.")
    rows.append(f"<p class='argument-trace-note'>{escape(reference_note)}</p>")
    shortened = inspection.shortened()
    if shortened is None:
        rows.append("<p class='argument-trace-note'>Only the saved context is shown here. Selection order, omissions and shortening cannot be determined from this payload alone.</p>")
    elif shortened:
        items = "".join(f"<li>{escape(label)}: {kept} of {available} characters retained.</li>" for label, kept, available in shortened)
        rows.append("<details class='argument-trace'><summary>Shortened fields: " + str(len(shortened)) +
                    "</summary><ul class='argument-trace-note'>" + items + "</ul></details>")
    else:
        rows.append("<p class='argument-trace-note'>No retained text fields were shortened by the context limits.</p>")
    payload = escape(json.dumps(inspection.payload, ensure_ascii=False, default=str, indent=2))
    selection_note = (" Selection follows record order, not an importance ranking. Limits count characters, not tokens."
                      if inspection.state is not None else "")
    body = ("<p class='argument-trace-note'>Previous generated claims are context to check, not new measurements. "
            "This is the prior-context block, separate from your new question, reused files and provider instructions."
            + selection_note + "</p>"
            + "".join(rows) + "<details class='argument-trace'><summary>Exact prior-context payload</summary>"
            "<p class='argument-trace-note'>Source-reference strings are shown exactly as sent, including any shortening. They are not full source files.</p>"
            f"<div class='argument-trace-text'>{payload}</div></details>")
    if include_disclosure:
        return f"<details class='argument-trace'><summary>{escape(preview_label(inspection))}</summary>{body}</details>"
    return body


def render_context_preview(inspection, *, key):
    if inspection.deferred:
        render_details(preview_label(inspection),
                       lambda: st.markdown(preview_html(inspection, include_disclosure=False), unsafe_allow_html=True),
                       key=key, lazy=True)
    else:
        st.markdown(preview_html(inspection), unsafe_allow_html=True)
