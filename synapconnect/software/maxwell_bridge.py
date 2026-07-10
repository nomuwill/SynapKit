"""Bridge a Maxwell .raw.h5 recording into either a SpikeInterface recording
or a SpikeLab SpikeData -- use whichever fits the task.

Sources (all verified against real recordings on this machine, see below):
- neo.rawio.maxwellrawio.MaxwellRawIO (Samuel Garcia, Alessio Buccino, Pierre
  Yger) -- the h5 schema this reads: wells/<well>/<rec>/{settings,groups}.
- The default `install_maxwell_plugin=True` on spikeinterface.read_maxwell
  crashes on this machine: it tries to mkdir() the raw, colon-joined
  HDF5_PLUGIN_PATH env var (which also contains a stale /home/mxwbio path
  that doesn't exist here). The decompression plugin is already installed
  at /home/sharf-lab/MaxLab/so/libcompression.so, so we just skip the
  auto-install step. Verified against /home/sharf-lab/Desktop/Anton/
  hAss_2310a1_D88.raw.h5 (983 channels, reads real trace data).
- Known quirk (hit by SpikeLab's own maxwell_io.py, not reused here per
  project convention of not depending on spikelab.spike_sorting): some
  MaxWell v25.x firmware writes duplicate channel-id rows in
  settings/mapping, which trips neo's uniqueness check --
  "signal_channels do not have unique ids for stream {i}"
  (neo/rawio/baserawio.py:714). neo's parser addresses signal rows and
  raw-array rows by the same position, so de-duplicating by first
  occurrence and indexing the raw array the same way preserves the
  channel/electrode mapping. Reasoned from neo's parser, but not
  exercised against an actual duplicate-mapping file -- none was
  available on this machine. If you hit this path, sanity check
  raw.shape[0] == len(mapping) for your file first.
- SpikeData conversion: spikelab.data_loaders.load_spikedata_from_spikeinterface_recording.
"""

from __future__ import annotations

import h5py
import numpy as np
from spikeinterface.core import NumpyRecording
from spikeinterface.extractors import read_maxwell


def load_maxwell_recording(h5_path, rec_name: str | None = None):
    """Load a Maxwell .raw.h5 file as a SpikeInterface BaseRecording."""
    try:
        return read_maxwell(h5_path, rec_name=rec_name, install_maxwell_plugin=False)
    except ValueError as e:
        if "unique ids" not in str(e):
            raise
        return _load_maxwell_dedup(h5_path, rec_name)


def _load_maxwell_dedup(h5_path, rec_name: str | None):
    """Fallback for files with duplicate settings/mapping rows (see module docstring)."""
    with h5py.File(h5_path, "r") as f:
        well_id = next(iter(f["wells"]))
        rec_id = rec_name or next(iter(f["wells"][well_id]))
        group = f["wells"][well_id][rec_id]
        settings = group["settings"]
        fs = float(settings["sampling"][0])
        gain_uV = float(settings["lsb"][0]) * 1e6

        mapping = settings["mapping"]
        channel_ids, first_seen = np.unique(mapping["channel"][:], return_index=True)
        routed = channel_ids >= 0
        channel_ids, first_seen = channel_ids[routed], first_seen[routed]

        raw = group["groups"]["routed"]["raw"][first_seen, :]

    traces = (raw.astype("float32") * gain_uV).T  # (samples, channels), uV
    recording = NumpyRecording([traces], sampling_frequency=fs)
    recording.set_channel_ids([str(c) for c in channel_ids])
    return recording


def to_spikedata(recording, **kwargs):
    """Convert a SpikeInterface recording (e.g. from load_maxwell_recording)
    into a SpikeLab SpikeData, via SpikeLab's own converter."""
    from spikelab.data_loaders import load_spikedata_from_spikeinterface_recording

    return load_spikedata_from_spikeinterface_recording(recording, **kwargs)
