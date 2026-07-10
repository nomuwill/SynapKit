"""Thin wrapper around the `maxlab` Python API (chip-level init/activation).

`maxlab` isn't pip-installed anywhere on this machine — it ships inside the MaxLab
Live install and has to be added to sys.path at import time. This sys.path-injection
pattern, and the `system_initialize`/`system_set_activated_wells` calls it wraps, are
taken from:
- BrainDance-dev's set_reference_electrode.py (the _MAXLAB_SITE injection pattern)
- /home/sharf-lab/MaxLab/python/lib/python3.10/site-packages/maxlab/util.py
  (initialize() and activate() docstrings)

Requires the mxwserver process to already be running — see server.py.
"""

import sys

_MAXLAB_SITE = "/home/sharf-lab/MaxLab/python/lib/python3.10/site-packages"

if _MAXLAB_SITE not in sys.path:
    sys.path.insert(0, _MAXLAB_SITE)
import maxlab  # noqa: E402


def initialize(wells: list[int] | None = None) -> None:
    """Reset the given wells (or all activated wells) to a known state."""
    maxlab.initialize(wells)


def activate(wells: list[int]) -> None:
    """Select which wells are active, same as picking wells in Scope."""
    maxlab.activate(wells)
