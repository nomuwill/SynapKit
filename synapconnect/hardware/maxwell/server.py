"""Start/stop/check the `mxwserver` process — the software on/off switch for the
Maxwell rig. The physical chip only responds to the `maxlab` API (see `session.py`)
once this server is running.

Sources:
- Port + reachability check: braindance/core/maxwell/maxwell_utils.get_maxwell_status()
  (BrainDance-dev), which itself reads MXW_BASE_PORT the same way maxlab.comm does.
- Start/stop commands: /home/sharf-lab/MaxLab/bin/mxwserver.sh and killall.sh.
"""

import os
import socket
import subprocess
import time

MAXLAB_BIN = "/home/sharf-lab/MaxLab/bin"
API_PORT = int(os.environ.get("MXW_BASE_PORT", 7200)) + 15


def is_running(timeout: float = 1.0) -> bool:
    """True if something is listening on the maxlab API port."""
    try:
        with socket.create_connection(("localhost", API_PORT), timeout=timeout):
            return True
    except OSError:
        return False


def start(wait_seconds: float = 10.0) -> bool:
    """Launch mxwserver in the background and wait for it to come online.

    Returns True once the API port is reachable, False if it didn't come up
    within `wait_seconds`. No-op (returns True immediately) if already running.
    """
    if is_running():
        return True

    subprocess.Popen(
        ["bash", f"{MAXLAB_BIN}/mxwserver.sh"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        if is_running():
            return True
        time.sleep(0.5)
    return False


def stop() -> None:
    """Kill mxwserver (and scope, if open) via MaxLab's own killall.sh."""
    subprocess.run(["bash", f"{MAXLAB_BIN}/killall.sh"], check=False)


def status() -> dict:
    return {"running": is_running(), "port": API_PORT, "bin": MAXLAB_BIN}
