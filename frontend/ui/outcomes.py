"""Quiet, outcome-specific notices that do not navigate or submit by themselves."""
from dataclasses import dataclass
from html import escape

import streamlit as st

STREAM_ENDED = "The event stream ended before a result was available."


@dataclass(frozen=True)
class OutcomeNotice:
    kind: str
    title: str
    detail: str
    action_label: str
    target: str


def outcome_notice(state, *, active: bool, recording: bool = False, replaying: bool = False):
    if active or replaying:
        return None
    if state.complete:
        if state.status == "cancelled":
            notice = OutcomeNotice("cancelled", "Investigation stopped", "The run was cancelled. Any findings shown are partial.", "View outcome", "results")
        elif state.status == "error":
            notice = OutcomeNotice("error", "Investigation ended with an error", "Review the recorded error and available output before deciding what to do next.", "View outcome", "results")
        elif state.status != "complete":
            notice = OutcomeNotice("unknown", "Run ended", f"The recorded status is {state.status or 'unspecified'}. Review the available outcome.", "View outcome", "results")
        elif state.abstained:
            notice = OutcomeNotice("abstained", "Finished without a supported conclusion", "The run abstained. Review its limitations and suggested next evidence.", "View result", "results")
        else:
            detail = ("A result is available. The run also recorded errors; review them with the findings."
                      if state.errors else "Your result is available when you are ready. Your current draft is unchanged.")
            notice = OutcomeNotice("complete", "Result ready", detail, "View result", "results")
    elif any(error != STREAM_ENDED for error in state.errors):
        notice = OutcomeNotice("error", "Investigation ended with an error", "An error was recorded and no final result arrived. Review the activity before starting another run.", "View activity", "investigation")
    else:
        notice = OutcomeNotice("incomplete", "No final result received", "The event stream ended without a final result. Available activity is retained; nothing will retry automatically.", "View activity", "investigation")
    if recording:
        return OutcomeNotice(notice.kind, "Recorded outcome: " + notice.title,
                             "This is a saved recording, not new analysis. " + notice.detail,
                             "View recording" if state.complete else "View activity", notice.target)
    return notice


def render_outcome_notice(notice: OutcomeNotice, *, key: str) -> bool:
    st.markdown("<div class='run-outcome-notice' role='status' aria-live='polite' aria-atomic='true'>"
                f"<div class='run-outcome-title'>{escape(notice.title)}</div>"
                f"<div class='run-outcome-detail'>{escape(notice.detail)}</div></div>", unsafe_allow_html=True)
    return st.button(notice.action_label, key=key)
