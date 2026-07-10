"""Connector for the MaxOne/MaxTwo (Maxwell Biosystems) rig.

`server` controls the `mxwserver` process (the on/off switch for the API).
`session` wraps the `maxlab` Python API itself (chip init, well activation).
See REALTIME.md for real-time/closed-loop options on this rig.
"""

from .server import is_running, start, stop, status
from .session import initialize, activate

__all__ = ["is_running", "start", "stop", "status", "initialize", "activate"]
