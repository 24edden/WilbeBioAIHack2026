#!/usr/bin/env python3
"""Private, reconnecting Mac/Linux tunnel. No credentials or process-ID signals."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import uuid


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / "runtime" / "local-tunnel"
HOST = "agentic-takeoff-cpu"
PORT = 8081
SSH_COMMAND = [
    "ssh", "-N", "-T", "-o", "BatchMode=yes", "-o", "ControlMaster=no",
    "-o", "ControlPath=none", "-o", "ExitOnForwardFailure=yes",
    "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=3",
    "-o", "ConnectTimeout=10", "-L", "127.0.0.1:8081:127.0.0.1:8080", HOST,
]


def prepare_directory() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    if STATE_DIR.is_symlink() or STATE_DIR.stat().st_uid != os.getuid():
        raise RuntimeError("Tunnel state directory must belong to this user and not be a symlink.")
    STATE_DIR.chmod(0o700)


def open_private(name: str):
    fd = os.open(STATE_DIR / name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    if os.fstat(fd).st_uid != os.getuid():
        os.close(fd)
        raise RuntimeError("Tunnel state file must belong to this user.")
    os.fchmod(fd, 0o600)
    return os.fdopen(fd, "a+")


def write_json(name: str, data: dict) -> None:
    temporary = f".{name}.{uuid.uuid4().hex}"
    try:
        with open_private(temporary) as stream:
            json.dump(data, stream)
        os.replace(STATE_DIR / temporary, STATE_DIR / name)
    finally:
        (STATE_DIR / temporary).unlink(missing_ok=True)


def read_json(name: str) -> dict:
    try:
        with open_private(name) as stream:
            stream.seek(0)
            value = json.load(stream)
        return value if isinstance(value, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def running() -> bool:
    """The held kernel lock, never a saved PID, establishes supervisor ownership."""
    with open_private("supervisor.lock") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(lock, fcntl.LOCK_UN)
    return False


def port_open() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", PORT), timeout=0.3):
            return True
    except OSError:
        return False


def stop_requested(generation: str) -> bool:
    return read_json("stop.json").get("generation") == generation


def supervisor(generation: str) -> None:
    prepare_directory()
    with open_private("supervisor.lock") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return  # A concurrent start already owns the tunnel.
        state = {"generation": generation, "supervisor_pid": os.getpid(),
                 "local_url": "http://127.0.0.1:8081", "ssh_host": HOST}

        def publish(phase: str, **extra) -> None:
            write_json("state.json", {**state, "phase": phase, "updated_at": time.time(), **extra})

        interrupted = False

        def interrupt(_signum, _frame) -> None:
            nonlocal interrupted
            interrupted = True

        signal.signal(signal.SIGTERM, interrupt)
        signal.signal(signal.SIGINT, interrupt)
        child = None
        delay = 1
        publish("starting")
        try:
            while not interrupted and not stop_requested(generation):
                if port_open():
                    publish("waiting_for_port", message="Another listener owns port 8081; it was not changed.")
                    time.sleep(1)
                    continue
                publish("connecting")
                try:
                    child = subprocess.Popen(SSH_COMMAND, stdin=subprocess.DEVNULL,
                                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except OSError:
                    publish("reconnecting", message="SSH could not start; retrying.")
                else:
                    connected = False
                    while child.poll() is None and not interrupted and not stop_requested(generation):
                        if not connected and port_open():
                            connected = True
                            delay = 1
                            publish("forwarding", ssh_pid=child.pid)
                        time.sleep(1)
                    if interrupted or stop_requested(generation):
                        break
                    publish("reconnecting", ssh_exit_code=child.returncode)
                    child = None
                # Interruptible, bounded backoff; never requests an investigation or inference.
                for _ in range(delay):
                    if interrupted or stop_requested(generation):
                        break
                    time.sleep(1)
                delay = min(delay * 2, 30)
        finally:
            if child is not None and child.poll() is None:
                # This is our unreaped child, never a PID loaded from disk.
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
            publish("stopped")


def start() -> None:
    if running():
        status()
        return
    if port_open():
        print("Port 8081 already has a listener. Nothing changed; stop its existing tunnel before starting this helper.")
        return
    generation = uuid.uuid4().hex
    with open_private("supervisor.log") as log:
        subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "_supervise", generation],
                         stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True,
                         close_fds=True, cwd=ROOT)
    for _ in range(30):
        if read_json("state.json").get("generation") == generation:
            status()
            return
        time.sleep(0.1)
    print("Supervisor starting. Check status; private logs are under runtime/local-tunnel/.")


def status() -> None:
    state = read_json("state.json")
    alive = running()
    print(json.dumps({"managed_supervisor_running": alive,
                      "phase": state.get("phase", "starting") if alive else "stopped",
                      "local_listener_present": port_open(),
                      "url": "http://127.0.0.1:8081"}, indent=2))


def stop() -> None:
    if not running():
        print("No managed supervisor is running. No process was signalled.")
        return
    generation = read_json("state.json").get("generation")
    if not generation:
        print("Supervisor is initializing. Retry stop in a moment; no process was signalled.")
        return
    write_json("stop.json", {"generation": generation})
    print("Shutdown requested for this managed tunnel only.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start", "status", "stop", "_supervise"))
    parser.add_argument("generation", nargs="?")
    args = parser.parse_args()
    prepare_directory()
    if args.action == "_supervise":
        if not args.generation:
            parser.error("Supervisor requires a generation token.")
        supervisor(args.generation)
    else:
        {"start": start, "status": status, "stop": stop}[args.action]()


if __name__ == "__main__":
    main()
