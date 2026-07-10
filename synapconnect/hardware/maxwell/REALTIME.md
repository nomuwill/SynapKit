# Real-time / closed-loop on the Maxwell rig

Source: `~/MaxLab/Documentation/mll_api_docs/tutorial/closed_loop_tutorial.html`
(MaxLab 1.1.0 docs, "Closed-Loop API" tutorial page).

There are two distinct ways to react to spikes in real time on this rig — don't
confuse them:

## 1. MaxLab's official Closed-Loop API (C++, not Python)

The `maxlab` Python package only *prepares* things (electrode config, stimulation
sequences via `mx.Sequence(...)`) and hands them to `mxwserver`. The actual
low-latency read-a-frame / decide / stimulate loop is a separate **C++** program
that links against a static library — Python is too slow for the per-frame
decision loop MaxLab intends here.

- Library: unzip `~/MaxLab/share/libmaxlab-1.1.0_9c79a6037.zip` → `maxlab_lib/`
  (confirmed present on this machine), `make` it to get an executable.
- Two stream flavors: `DataStreamerRaw` (raw voltage per channel, you threshold
  it yourself) or `DataStreamerFiltered` (MaxLab Live's own spike detector,
  gives you `SpikeEvent`s with a channel + timestamp).
- On a hit, the C++ program calls `maxlab::sendSequence("closed_loop")` — a
  sequence you pre-registered from the Python setup script — then holds off
  ("blanking") for ~8000 frames (0.4 ms MaxOne / 0.8 ms MaxTwo) while the chip
  settles post-stimulation.
- Workflow: `mxwserver` running → compiled C++ binary running (`./example_raw
  <detection_channel>`) → then run your Python setup script, which only
  defines electrodes/sequences and never touches the per-frame loop itself.

## 2. Direct ZMQ streaming from Python (what this lab actually uses)

`mxwserver` also publishes frames over ZMQ (filtered stream on
`localhost:<MXW_BASE_PORT+5>`, e.g. `7205` — used in
`set_reference_electrode.py`'s `_measure_noise()` in this repo). This lets you
read spikes/traces straight from Python with no C++ build step, at the cost of
Python-level latency instead of the C++ loop's. This is the path
`synapsortrt`'s real-time detector/matcher is built around — see the top-level
README's "Phase 2" pipeline. Prefer this over touching MaxLab's C++ closed-loop
library unless you specifically need C++-loop latency.
