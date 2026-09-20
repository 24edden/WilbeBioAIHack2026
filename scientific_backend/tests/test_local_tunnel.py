"""Offline lifecycle checks; never start SSH or contact the demo."""
import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def tunnel(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("local_tunnel", Path(__file__).parents[1] / "scripts/local_tunnel.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "STATE_DIR", tmp_path / "private-tunnel")
    monkeypatch.setattr(module.signal, "signal", lambda *_: None)
    module.prepare_directory()
    return module


def test_disconnect_reconnect_then_stop_only_own_live_child(tunnel, monkeypatch):
    children = []

    class Child:
        def __init__(self, exited):
            self.pid = 1234 + len(children)
            self.returncode = 255 if exited else None
            self.terminated = False

        def poll(self):
            return self.returncode

        def terminate(self):
            self.terminated = True
            self.returncode = 0

        def wait(self, **_kwargs):
            return self.returncode

    def spawn(command, **_kwargs):
        assert command == tunnel.SSH_COMMAND
        child = Child(exited=not children)
        children.append(child)
        return child

    def sleep(_seconds):
        if len(children) == 2:
            tunnel.write_json("stop.json", {"generation": "new-generation"})

    # A stop request from an old supervisor must not stop a restarted supervisor.
    tunnel.write_json("stop.json", {"generation": "old-generation"})
    monkeypatch.setattr(tunnel.subprocess, "Popen", spawn)
    monkeypatch.setattr(tunnel, "port_open", lambda: False)
    monkeypatch.setattr(tunnel.time, "sleep", sleep)
    tunnel.supervisor("new-generation")
    assert len(children) == 2
    assert not children[0].terminated
    assert children[1].terminated
    assert tunnel.read_json("state.json")["phase"] == "stopped"
    assert not tunnel.running()


def test_stale_pid_does_not_authorize_stop(tunnel, monkeypatch, capsys):
    tunnel.write_json("state.json", {"generation": "old", "supervisor_pid": 1, "ssh_pid": 2})
    monkeypatch.setattr(tunnel.os, "kill", lambda *_: pytest.fail("Never signal a stored PID"))
    tunnel.stop()
    assert not (tunnel.STATE_DIR / "stop.json").exists()
    assert "No process was signalled" in capsys.readouterr().out


def test_stop_targets_current_generation_without_pid_signal(tunnel, monkeypatch):
    tunnel.write_json("state.json", {"generation": "current", "supervisor_pid": 1})
    monkeypatch.setattr(tunnel.os, "kill", lambda *_: pytest.fail("Never signal a stored PID"))
    with tunnel.open_private("supervisor.lock") as lock:
        tunnel.fcntl.flock(lock, tunnel.fcntl.LOCK_EX | tunnel.fcntl.LOCK_NB)
        assert tunnel.running()
        tunnel.stop()
        assert tunnel.read_json("stop.json") == {"generation": "current"}


def test_occupied_port_is_left_alone(tunnel, monkeypatch, capsys):
    monkeypatch.setattr(tunnel, "port_open", lambda: True)
    monkeypatch.setattr(tunnel.subprocess, "Popen", lambda *_args, **_kwargs: pytest.fail("Existing listener must remain untouched"))
    tunnel.start()
    assert "Nothing changed" in capsys.readouterr().out


def test_existing_supervisor_prevents_duplicate_child(tunnel, monkeypatch):
    monkeypatch.setattr(tunnel.subprocess, "Popen", lambda *_args, **_kwargs: pytest.fail("Duplicate supervisor must not start SSH"))
    with tunnel.open_private("supervisor.lock") as lock:
        tunnel.fcntl.flock(lock, tunnel.fcntl.LOCK_EX | tunnel.fcntl.LOCK_NB)
        tunnel.supervisor("duplicate")


def test_state_permissions_and_symlink_rejection(tunnel, tmp_path):
    tunnel.write_json("state.json", {"generation": "current"})
    assert tunnel.STATE_DIR.stat().st_mode & 0o777 == 0o700
    assert (tunnel.STATE_DIR / "state.json").stat().st_mode & 0o777 == 0o600
    target = tmp_path / "unrelated"
    target.write_text("untouched")
    (tunnel.STATE_DIR / "stop.json").symlink_to(target)
    with pytest.raises(OSError):
        tunnel.read_json("stop.json")
    assert target.read_text() == "untouched"


def test_ssh_is_private_bounded_and_noninteractive(tunnel):
    command = tunnel.SSH_COMMAND
    assert command[command.index("-L") + 1] == "127.0.0.1:8081:127.0.0.1:8080"
    for setting in ("BatchMode=yes", "ControlPath=none", "ExitOnForwardFailure=yes", "ServerAliveCountMax=3", "ConnectTimeout=10"):
        assert setting in command
    assert "-g" not in command
    assert command[-1] == "agentic-takeoff-cpu"
