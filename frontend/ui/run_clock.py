"""A local submission clock, independent of event arrival or backend duration."""
from math import isfinite
from pathlib import Path


def measured_execution_ms(state):
    if not state.complete:
        return None
    value = state.metrics.get("wall_time_ms", state.metrics.get("wall_ms"))
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
        try:
            if isfinite(value):
                return value
        except OverflowError:
            pass
    return None


def clock_data(job, state):
    # Existing sessions may hold a worker created before the clock was added.
    if not job or not getattr(job, "clock_id", None):
        return None
    return {"runKey": job.clock_id, "active": not job.finished.is_set(),
            "elapsedMs": job.elapsed_ms, "measuredMs": measured_execution_ms(state)}


def render_run_clock(data):
    if data is None:
        return
    from streamlit.components.v2 import component
    assets = Path(__file__).resolve().parents[1] / "static"
    clock = component("trace_run_clock_display",
        html=(assets / "run_clock.html").read_text(encoding="utf-8"),
        css=(assets / "run_clock.css").read_text(encoding="utf-8"),
        js=(assets / "run_clock.js").read_text(encoding="utf-8"))
    clock(key="trace_run_clock", data=data)
