"""Private Linux/Brev process launcher. Never changes any other service."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
RUNTIME.mkdir(exist_ok=True)
PID = RUNTIME / "service.pid"


def own_process():
    try:
        pid = int(PID.read_text())
        cmd = Path(f"/proc/{pid}/cmdline").read_bytes()
        cwd = Path(f"/proc/{pid}/cwd").resolve()
        return pid if cwd == ROOT and b"app\x00serve" in cmd else None
    except (OSError, ValueError):
        return None


def health():
    with urllib.request.urlopen("http://127.0.0.1:8080/api/health", timeout=3) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "stop", "status"])
    action = parser.parse_args().action
    pid = own_process()
    if action == "stop":
        if pid:
            os.kill(pid, signal.SIGTERM)
            for _ in range(30):
                if not own_process():
                    break
                time.sleep(.2)
            print("Stop requested for the identified demo process.")
        else:
            print("No matching demo process is running.")
    elif action == "status":
        print(json.dumps({"owned_pid": pid, "health": health() if pid else None}, indent=2))
    elif pid:
        print(f"Demo already running as process {pid}.")
    else:
        import socket
        with socket.socket() as sock:
            # A just-stopped server can leave TIME_WAIT sockets; an active
            # listener still fails this bind because SO_REUSEPORT is not set.
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", 8080))
            except OSError:
                raise SystemExit("Port 8080 is occupied. No existing service was stopped.")
        with (RUNTIME / "service.log").open("ab") as log:
            process = subprocess.Popen([str(ROOT / ".venv/bin/python"), "-m", "app", "serve", "--port", "8080"], cwd=ROOT,
                                       stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
        PID.write_text(str(process.pid))
        for _ in range(40):
            if process.poll() is not None:
                raise SystemExit("Demo exited. Inspect runtime/service.log.")
            try:
                result = health()
                if result.get("worker_alive"):
                    print(json.dumps({"pid": process.pid, "url": "http://127.0.0.1:8080", "status": result["status"]}))
                    return
            except OSError:
                pass
            time.sleep(.25)
        raise SystemExit("Process started but did not become ready in ten seconds; inspect runtime/service.log.")


if __name__ == "__main__":
    main()
