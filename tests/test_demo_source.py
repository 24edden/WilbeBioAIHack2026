from frontend.ui.adapters import DemoSource, ReplaySource, RunRequest, source_for
from frontend.ui.events import Event
from frontend.ui.state import RunState
import subprocess
import sys
from pathlib import Path


def run(question, config=None):
    state = RunState()
    events = list(DemoSource(mock_latency_scale=0).events(
        RunRequest(mode="Demo", question=question, sample=True, config=config or {})))
    for event in events:
        assert isinstance(event, Event)
        state.apply(event)
    return state, events


def test_demo_prompt_changes_actual_hypothesis_investigation():
    supported, first = run("Why did this patient fail?")
    unsupported, second = run("Did the patient fail because of BRCA2?")
    assert supported.complete and unsupported.complete
    assert not supported.abstained and "KRAS" in supported.verdict
    assert unsupported.abstained
    assert supported.verdict != unsupported.verdict
    assert second[0].payload["question"] == "Did the patient fail because of BRCA2?"
    assert any(event.type == "agent_message" for event in first)


def test_demo_roster_is_real_and_environment_cannot_switch_to_live(monkeypatch):
    monkeypatch.setenv("RUN_MODE", "live")
    monkeypatch.setenv("REASONING_API_KEY", "never-use-this")
    import app.providers
    monkeypatch.setattr(app.providers, "build_providers", lambda *args: (_ for _ in ()).throw(AssertionError("live factory used")))
    state, events = run("Why did this patient fail?", {"specialists": ["clinical"]})
    assert set(agent.role for agent in state.agents.values()) == {"orchestrator", "clinical", "critic"}
    assert state.abstained
    config = events[0].payload["config"]
    assert config["run_mode"] == "mock" and config["execution_source"] == "local_demo"
    assert config["specialists"] == ["clinical"]
    assert not state.errors


def test_demo_configuration_and_failures_are_honest():
    assert isinstance(source_for("Demo"), DemoSource)
    assert isinstance(source_for("Mock"), ReplaySource)
    assert DemoSource().capabilities("")["model_overrides_supported"] is False
    state, events = run("Question", {"reasoning_model": "live-model"})
    assert state.errors and state.complete
    assert [event.type for event in events] == ["error", "run_complete"]
    assert state.abstained


def test_closing_demo_stream_cleans_up_engine():
    stream = DemoSource(mock_latency_scale=0).events(RunRequest(mode="Demo", question="Why?", sample=True))
    assert next(stream).type == "run_started"
    stream.close()


def test_streamlit_script_path_does_not_shadow_backend_package():
    root = Path(__file__).resolve().parents[1]
    script = """
import sys
sys.path.insert(0, 'frontend')
from ui.adapters import DemoSource, RunRequest
events = list(DemoSource(0).events(RunRequest(mode='Demo', question='Why did this patient fail?', sample=True)))
assert events[0].type == 'run_started', events[0]
assert events[-1].type == 'run_complete'
assert not [event for event in events if event.type == 'error']
"""
    result = subprocess.run([sys.executable, "-c", script], cwd=root, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
