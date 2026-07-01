# EEG BIDS Sidecar Auditor

A compact Python CLI for auditing common metadata issues in BIDS-style EEG sidecar files before a dataset is shared or used for modeling.

The tool checks:

- required `_eeg.json` fields: `TaskName`, `SamplingFrequency`, `PowerLineFrequency`, and `EEGReference`
- recommended EEG acquisition fields that make reuse easier
- `_channels.tsv` required columns: `name`, `type`, and `units`
- duplicate channel names, unusual channel units, channel status values, and sampling-rate mismatches
- basic `_electrodes.tsv` coordinate column presence

The checks are intentionally lightweight and local. They complement the official BIDS Validator rather than replacing it.

## Source Basis

The rule set follows the BIDS EEG specification current on 2026-07-01, especially the EEG sidecar JSON and channels/electrodes TSV guidance in the official BIDS documentation:

- https://bids-specification.readthedocs.io/en/stable/modality-specific-files/electroencephalography.html

## Install

```bash
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

The package itself uses only the Python standard library at runtime.

## Demo

```bash
python -m eeg_bids_sidecar_auditor demo --out reports/demo
```

This creates a tiny simulated BIDS EEG sidecar dataset under `reports/demo/example_bids`, audits it, and writes:

- `reports/demo/report.md`
- `reports/demo/summary.json`

## Audit Your Dataset

```bash
python -m eeg_bids_sidecar_auditor audit path\to\bids_dataset --out reports/my_audit
```

The command exits with status code `1` if any `FAIL` findings are present, making it suitable for simple CI checks.

## Development Checks

```bash
python -m unittest discover -s tests -v
python -m compileall -q eeg_bids_sidecar_auditor tests
```
