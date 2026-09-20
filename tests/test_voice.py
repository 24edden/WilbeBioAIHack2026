"""Voice actions preserve typed-input guards and never dispatch arbitrary commands."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from frontend.ui.voice import stage_announcement, validate_action


@pytest.mark.parametrize("value", [
    None, [], {}, {"id": "x", "type": "submit"},
    {"id": "x", "type": "navigate", "target": "cancel"},
    {"id": "x", "type": "navigate", "target": ["results"]},
    {"id": "x", "type": "dictation", "text": " "},
    {"id": "x", "type": "dictation", "text": "x" * 8001},
    {"id": 1, "type": "dictation", "text": "question"},
])
def test_voice_rejects_invalid_actions(value):
    assert validate_action(value) is None


def test_voice_validates_actions_without_scientific_or_code_interpretation():
    assert validate_action({"id": "abc", "type": "dictation", "text": "  show results  ", "submit": True}) == {
        "id": "abc", "type": "dictation", "text": "show results",
    }
    assert validate_action({"id": "nav", "type": "navigate", "target": "results"}) == {
        "id": "nav", "type": "navigate", "target": "results",
    }


def test_announcements_use_known_workflow_copy_only():
    assert "stopped" in stage_announcement("results", "cancelled", "critic")
    assert "critic" in stage_announcement("investigation", "running", "critic")
    assert "patient has an infection" not in stage_announcement("unknown", "running", "patient has an infection")
    assert "complete" not in stage_announcement("investigation", "running", "clinical")


@pytest.mark.parametrize("filename", ["voice_browser_test.mjs", "theme_browser_test.mjs", "help_browser_test.mjs"])
def test_voice_browser_lifecycle_and_explicit_actions(filename):
    """Run dependency-free JS mocks; no microphone, synthesis service or network."""
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for the optional browser API lifecycle test")
    script = Path(__file__).with_name(filename)
    result = subprocess.run([node, str(script)], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["passed"] is True
