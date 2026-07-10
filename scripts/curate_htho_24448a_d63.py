"""
curate_htho_24448a_d63.py

Curate 24448a_htho_d63_061626 (spike-time-only criteria) and attach raw
voltage traces for per-unit waveform extraction. Run after
fetch_htho_24448a_d63.py (needs Data/htho_agg/24448a_htho_d63_061626/
sorted_spikedata.pkl and raw/24448a_htho_d63_061626.raw.h5 to exist).

Requires: `spikelab` importable (conda env `spikelab` on the Sharf lab
machines: `conda run -n spikelab python scripts/curate_htho_24448a_d63.py`).

RAM strategy: the raw recording is 1019 channels x 15,800,600 samples
(uint16), ~32 GB dense. We never materialize the full array. The h5py
Dataset object is used directly as `raw_data` — h5py supports the same
`[channel_indices, start:end]` slicing SpikeData's waveform extraction
uses, so each read pulls only a tiny (n_channels, ms_before+ms_after)
window per spike straight off disk.

SNR / normalized-STD curation are intentionally NOT run here: SpikeLab
band-pass filters the *entire* raw_data array up front for those two
metrics (spikelab.spikedata.curation.compute_waveform_metrics), which
would force a full ~32-60 GB in-memory filter pass. Only spike-time-based
criteria (firing rate, ISI violations, min spike count) are applied,
matching the SpikeLab pipeline defaults (spikelab.spike_sorting.config
.CurationConfig) for those three thresholds.

Verified channel alignment: neuron_attributes[i]['electrode'] (as set by
load_spikedata_from_kilosort) equals the h5 file's `channel` field
(data_store/data0000/settings/mapping), which is also the row index into
`groups/routed/raw` directly (routed channel array is 0..1018, identity
order) -- so `electrode` can be used as-is as the raw_data row index.
"""
import pickle
from pathlib import Path

import h5py
import numpy as np

STEM = "24448a_htho_d63_061626"
REPO_ROOT = Path(__file__).parent.parent
REC_DIR = REPO_ROOT / "Data" / "htho_agg" / STEM
RAW_H5 = REC_DIR / "raw" / f"{STEM}.raw.h5"
RAW_PKL = REC_DIR / "sorted_spikedata.pkl"
CURATED_PKL = REC_DIR / "sorted_spikedata_curated.pkl"

# SpikeLab CurationConfig defaults (spike-time-based subset only)
MIN_RATE_HZ = 0.05
ISI_MAX = 0.01
ISI_THRESHOLD_MS = 1.5
ISI_METHOD = "percent"
MIN_SPIKES = 50  # final (curate_second) threshold in the default pipeline

WAVEFORM_MS_BEFORE = 1.0
WAVEFORM_MS_AFTER = 2.0

with open(RAW_PKL, "rb") as f:
    sd = pickle.load(f)
print(f"Loaded raw: {sd.N} units")

# --- Spike-time-only curation (no raw data needed) ---
sd_curated, results = sd.curate(
    min_rate_hz=MIN_RATE_HZ,
    isi_max=ISI_MAX,
    isi_threshold_ms=ISI_THRESHOLD_MS,
    isi_method=ISI_METHOD,
    min_spikes=MIN_SPIKES,
)
print(f"Curated (firing rate >= {MIN_RATE_HZ} Hz, ISI viol <= {ISI_MAX}, "
      f"spikes >= {MIN_SPIKES}): {sd_curated.N} / {sd.N} units")

# --- Attach raw data lazily (h5py Dataset, never fully materialized) ---
h5f = h5py.File(str(RAW_H5), "r")
raw_ds = h5f["data_store/data0000/groups/routed/raw"]  # (1019, 15_800_600) uint16
lsb_volts = float(h5f["data_store/data0000/settings/lsb"][()][0])
fs_Hz = float(h5f["data_store/data0000/settings/sampling"][()][0])
scale_uv = lsb_volts * 1e6  # MaxWell convention: microvolts = raw_count * lsb * 1e6

# 'electrode' as set by load_spikedata_from_kilosort is the direct raw_data
# row index (verified against the h5 mapping table) -- duplicate it under
# 'channel' so SpikeData.neuron_to_channel_map() auto-detects it. Without
# this, get_waveform_traces falls back to ALL 1019 channels per unit.
for na in sd_curated.neuron_attributes:
    na["channel"] = na["electrode"]

sd_curated.raw_data = raw_ds  # bypass constructor's np.asarray(); stays lazy
sd_curated.raw_time = np.array(fs_Hz / 1000.0)  # kHz, 0-d array

print(f"Pulling per-unit waveforms ({WAVEFORM_MS_BEFORE}ms before / "
      f"{WAVEFORM_MS_AFTER}ms after spike, unit's assigned KS2 channel only)...")
sd_curated.get_waveform_traces(
    unit=None,
    ms_before=WAVEFORM_MS_BEFORE,
    ms_after=WAVEFORM_MS_AFTER,
    store=True,
    return_avg_waveform=True,
)

# Waveforms/avg_waveform came back in raw ADC counts (h5py Dataset dtype
# uint16 was preserved through slicing) -- scale to microvolts now, on the
# already-small per-unit arrays.
for na in sd_curated.neuron_attributes:
    if na.get("waveforms") is not None:
        na["waveforms"] = na["waveforms"].astype(np.float32) * scale_uv
    if na.get("avg_waveform") is not None:
        na["avg_waveform"] = na["avg_waveform"].astype(np.float32) * scale_uv
    na["waveform_units"] = "uV"

h5f.close()

# Detach raw_data before pickling -- keep the pickle small; raw traces stay
# on disk in RAW_H5 for future on-demand waveform pulls (see Data/README.md).
sd_curated.raw_data = np.zeros((0, 0))
sd_curated.raw_time = np.zeros(0)

with open(CURATED_PKL, "wb") as f:
    pickle.dump(sd_curated, f)
print(f"Saved {sd_curated.N} curated units (with waveforms) to {CURATED_PKL}")
