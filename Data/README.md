# Data/

Gitignored (except this file). Populate via:
```bash
conda run -n spikelab python scripts/fetch_htho_24448a_d63.py
conda run -n spikelab python scripts/curate_htho_24448a_d63.py
```

## Source

S3 endpoint: `https://s3.braingeneers.gi.ucsc.edu`, bucket `braingeneers` (public read).

- Sorted (phy/KiloSort2): `s3://braingeneers/ephys/2026-06-22-e-htho-agg_041326/derived/kilosort2/24448a_htho_d63_061626_phy.zip`
- Raw recording: `s3://braingeneers/ephys/2026-06-22-e-htho-agg_041326/original/data/24448a_htho_d63_061626.raw.h5`

## Expected local structure

```
Data/htho_agg/24448a_htho_d63_061626/
├── raw/24448a_htho_d63_061626.raw.h5
├── sorted_spikedata.pkl
└── sorted_spikedata_curated.pkl
```
