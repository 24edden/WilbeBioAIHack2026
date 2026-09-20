from frontend.ui.events import Event
from frontend.ui.replay import Playback
from frontend.ui.state import RunState


def test_replay_pause_step_restart_and_finish_preserve_original_result():
    now = [0.0]
    events = [Event(type='run_started', ts=100, payload={'question': 'Original'}),
              Event(type='agent_spawned', ts=101, agent_id='researcher', agent_role='literature'),
              Event(type='run_complete', ts=100000, payload={'verdict': 'Saved result'})]
    original = RunState()
    for event in events:
        original.apply(event)
    playback = Playback(original.raw, clock=lambda: now[0])
    assert playback.index == 1 and not playback.state.complete
    playback.pause()
    now[0] = 20
    playback.advance()
    assert playback.index == 1
    playback.step()
    assert 'researcher' in playback.state.agents and not playback.playing
    playback.set_speed(2)
    playback.resume()
    now[0] += .5
    playback.advance()
    assert playback.finished and not playback.playing
    assert playback.state.verdict == original.verdict == 'Saved result'
    playback.state.raw[0].payload['question'] = 'Changed replay'
    assert original.raw[0].payload['question'] == 'Original'
    playback.restart()
    assert playback.index == 1 and playback.playing
    assert original.complete and len(original.raw) == 3


def test_empty_replay_is_finished_without_timer():
    playback = Playback([])
    playback.step()
    playback.resume()
    assert playback.finished and not playback.playing
