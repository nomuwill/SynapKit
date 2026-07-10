"""
fetch_htho_24448a_d63.py

Download the sorted (KiloSort2 phy) output AND the raw recording for
24448a_htho_d63_061626 (chip 24448a, day 63, htho aggregate line,
batch 2026-06-22-e-htho-agg_041326) from S3 into Data/.

Requires: `spikelab` importable (conda env `spikelab` on the Sharf lab
machines: `conda run -n spikelab python scripts/fetch_htho_24448a_d63.py`),
and the `aws` CLI configured for the braingeneers S3 endpoint (no special
credentials needed -- the bucket is public/anonymous-readable via this
endpoint).

See Data/README.md for the full provenance and what's downloaded where.
"""
import os
import pickle
import shutil
import subprocess
import tempfile
import warnings
import zipfile
from pathlib import Path

from spikelab.data_loaders import load_spikedata_from_kilosort

ENDPOINT = "https://s3.braingeneers.gi.ucsc.edu"
UUID = "2026-06-22-e-htho-agg_041326"
STEM = "24448a_htho_d63_061626"
S3_PHY_ZIP = f"s3://braingeneers/ephys/{UUID}/derived/kilosort2/{STEM}_phy.zip"
S3_RAW_H5 = f"s3://braingeneers/ephys/{UUID}/original/data/{STEM}.raw.h5"
FS_HZ = 20000.0

REPO_ROOT = Path(__file__).parent.parent
OUT_DIR = REPO_ROOT / "Data" / "htho_agg" / STEM
RAW_DIR = OUT_DIR / "raw"
OUT_PKL = OUT_DIR / "sorted_spikedata.pkl"
RAW_H5_PATH = RAW_DIR / f"{STEM}.raw.h5"

OUT_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

# --- Sorted (phy) output -> sorted_spikedata.pkl ---
tmp = tempfile.mkdtemp()
try:
    zip_path = os.path.join(tmp, "phy.zip")
    print(f"Downloading {S3_PHY_ZIP} ...")
    r = subprocess.run(
        ["aws", "s3", "cp", S3_PHY_ZIP, zip_path, "--endpoint-url", ENDPOINT],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"S3 download failed: {r.stderr.strip()}")
    print(f"Downloaded {os.path.getsize(zip_path)} bytes")

    phy_dir = os.path.join(tmp, "phy")
    os.makedirs(phy_dir)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(phy_dir)

    tsv = ("cluster_group.tsv"
           if any(f.endswith("cluster_group.tsv") for f in os.listdir(phy_dir))
           else "cluster_info.tsv")

    print(f"Loading phy output (fs={FS_HZ} Hz, cluster info: {tsv}) ...")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sd = load_spikedata_from_kilosort(
            phy_dir, fs_Hz=FS_HZ, cluster_info_tsv=tsv, include_noise=False,
        )

    print(f"Loaded {sd.N} units, {sd.length / 1000.0:.1f} s recording")

    with open(OUT_PKL, "wb") as f:
        pickle.dump(sd, f)
    print(f"Saved to {OUT_PKL}")

finally:
    shutil.rmtree(tmp, ignore_errors=True)

# --- Raw recording -> raw/<stem>.raw.h5 (~5.1 GB) ---
print(f"Downloading {S3_RAW_H5} ...")
r = subprocess.run(
    ["aws", "s3", "cp", S3_RAW_H5, str(RAW_H5_PATH), "--endpoint-url", ENDPOINT],
    capture_output=True, text=True,
)
if r.returncode != 0:
    raise RuntimeError(f"S3 download failed: {r.stderr.strip()}")
print(f"Saved to {RAW_H5_PATH}")
