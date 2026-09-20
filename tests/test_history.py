"""Saved run recognition uses local identity and only historical metadata."""
from copy import deepcopy
from html import escape

import pytest

from frontend.ui.adapters import RunRequest
from frontend.ui.history import connection_label, outcome_label, result_labels, selected_result_html
from frontend.ui.state import RunState


def record(result_id="abcdefgh-one", *, mode="Live", status="complete", abstained=False):
    question = "An identical question " * 9 + "with its full final sentence."
    state = RunState(question=question, complete=True, status=status, abstained=abstained,
                     run_id="reused-backend-id")
    return {"id": result_id, "run": state, "request": RunRequest(mode=mode, question=question)}


def test_identical_questions_and_backend_ids_have_collision_safe_local_labels():
    records = [record("abcdefgh-one"), record("abcdefgh-two"), record("abcdefgh-three")]
    labels = result_labels(records)
    assert len(set(labels.values())) == 3
    assert labels["abcdefgh-one"].startswith("#abcdefgh-o ·")
    assert labels["abcdefgh-two"].startswith("#abcdefgh-tw ·")
    assert labels["abcdefgh-three"].startswith("#abcdefgh-th ·")
    assert result_labels(list(reversed(records))) == labels
    assert all("Live connection" in label and "Complete" in label for label in labels.values())


@pytest.mark.parametrize("status,abstained,expected", [
    ("complete", False, "Complete"), ("complete", True, "Abstained"),
    ("error", True, "Ended with an error"), ("cancelled", True, "Cancelled"),
    ("unfamiliar", False, "Status: unfamiliar"), ("", False, "Status: not recorded"),
])
def test_outcome_is_the_recorded_state_not_a_success_assumption(status, abstained, expected):
    saved = record(status=status, abstained=abstained)
    assert outcome_label(saved) == expected
    saved["run"].complete = False
    assert outcome_label(saved) == "No final result"


def test_review_abstention_errors_and_recording_are_distinct():
    saved = record(mode="Mock")
    saved["run"].task_mode = "idea_review"
    assert outcome_label(saved) == "Idea review complete"
    saved["run"].abstained = True
    assert outcome_label(saved) == "Abstained"
    assert connection_label(saved) == "Recorded playback"
    assert connection_label(record(mode="Demo")) == "Interactive demo"
    saved["run"].abstained = False
    saved["run"].task_mode = "investigation"
    saved["run"].errors = ["A recovered error"]
    assert outcome_label(saved) == "Complete (errors recorded)"


def test_preview_preserves_full_questions_escapes_metadata_and_does_not_inspect_large_output():
    saved = record("<local&identifier>")
    saved["run"].question += "\n<script>not markup</script>"
    saved["run"].config = {"run_mode": "mock"}
    saved["run"].run_id = "<backend&identifier>"

    class UnreadOutput:
        def __iter__(self):
            raise AssertionError("Saved selection must not inspect output")

    saved["run"].raw = UnreadOutput()
    saved["run"].findings = UnreadOutput()
    original_question = saved["run"].question
    html = selected_result_html(saved)
    assert escape(original_question) in html and "<script>" not in html
    assert escape(saved["request"].question) in html
    assert "Session record ID: &lt;local&amp;identifier&gt;" in html
    assert "Backend run ID: &lt;backend&amp;identifier&gt;" in html
    assert "Execution mode reported in saved configuration: mock" in html
    assert "not confirmation of live providers" in html
    assert "<details" in html and "<summary>Saved result identifiers and mode</summary>" in html
    assert saved["run"].question == original_question


def test_legacy_missing_metadata_is_unknown_and_current_defaults_are_not_inferred():
    saved = record(mode="unfamiliar")
    saved["run"].run_id = ""
    saved["run"].config = {}
    original = deepcopy(saved)
    html = selected_result_html(saved)
    assert "Backend run ID: Not recorded" in html
    assert "Execution mode reported in saved configuration: Not recorded" in html
    assert "Saved connection mode: unfamiliar" in html
    assert saved == original
    saved["request"] = None
    assert connection_label(saved) == "Mode not recorded"
    assert "Saved connection mode: Not recorded" in selected_result_html(saved)
    saved["run"].question = ""
    assert "Question not recorded" in selected_result_html(saved)
