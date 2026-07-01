from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any


REQUIRED_EEG_JSON_FIELDS = {
    "TaskName",
    "SamplingFrequency",
    "PowerLineFrequency",
    "EEGReference",
}

RECOMMENDED_EEG_JSON_FIELDS = {
    "EEGGround",
    "EEGPlacementScheme",
    "Manufacturer",
    "ManufacturersModelName",
    "SoftwareVersions",
    "CapManufacturer",
    "CapManufacturersModelName",
}

REQUIRED_CHANNEL_COLUMNS = {"name", "type", "units"}
RECOMMENDED_CHANNEL_COLUMNS = {"status", "status_description", "sampling_frequency"}
VALID_CHANNEL_TYPES = {
    "EEG",
    "EOG",
    "ECG",
    "EMG",
    "MISC",
    "TRIG",
    "VEOG",
    "HEOG",
    "REF",
    "GSR",
    "PUPIL",
    "EYEGAZE",
}


@dataclass(frozen=True)
class Finding:
    severity: str
    location: str
    message: str


def audit_dataset(root: Path) -> tuple[list[Finding], dict[str, Any]]:
    eeg_jsons = sorted(root.rglob("*_eeg.json"))
    channels_files = sorted(root.rglob("*_channels.tsv"))
    electrodes_files = sorted(root.rglob("*_electrodes.tsv"))
    findings: list[Finding] = []

    if not eeg_jsons:
        findings.append(Finding("FAIL", ".", "No *_eeg.json sidecar files found."))
    if not channels_files:
        findings.append(Finding("WARN", ".", "No *_channels.tsv files found."))

    json_sampling: dict[str, float] = {}
    for path in eeg_jsons:
        payload = _load_json(path, findings)
        if payload is None:
            continue
        findings.extend(_audit_eeg_json(path, payload))
        sfreq = _as_float(payload.get("SamplingFrequency"))
        if sfreq is not None:
            json_sampling[_stem_key(path)] = sfreq

    for path in channels_files:
        rows = _load_tsv(path, findings)
        if rows is None:
            continue
        expected_sfreq = json_sampling.get(_stem_key(path))
        findings.extend(_audit_channels(path, rows, expected_sfreq))

    for path in electrodes_files:
        rows = _load_tsv(path, findings)
        if rows is None:
            continue
        findings.extend(_audit_electrodes(path, rows))

    summary = {
        "dataset": str(root),
        "eeg_json_files": len(eeg_jsons),
        "channels_tsv_files": len(channels_files),
        "electrodes_tsv_files": len(electrodes_files),
        "failures": sum(1 for item in findings if item.severity == "FAIL"),
        "warnings": sum(1 for item in findings if item.severity == "WARN"),
        "info": sum(1 for item in findings if item.severity == "INFO"),
    }
    return findings, summary


def _load_json(path: Path, findings: list[Finding]) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        findings.append(Finding("FAIL", str(path), f"Invalid JSON: {exc.msg}."))
        return None


def _load_tsv(path: Path, findings: list[Finding]) -> list[dict[str, str]] | None:
    try:
        with path.open("r", newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle, delimiter="\t"))
    except OSError as exc:
        findings.append(Finding("FAIL", str(path), f"Could not read TSV: {exc}."))
        return None


def _audit_eeg_json(path: Path, payload: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    keys = set(payload)
    missing = sorted(REQUIRED_EEG_JSON_FIELDS - keys)
    for field in missing:
        findings.append(Finding("FAIL", str(path), f"Missing required EEG sidecar field: {field}."))

    for field in sorted(RECOMMENDED_EEG_JSON_FIELDS - keys):
        findings.append(Finding("INFO", str(path), f"Recommended EEG metadata field is absent: {field}."))

    sfreq = _as_float(payload.get("SamplingFrequency"))
    if sfreq is not None and sfreq <= 0:
        findings.append(Finding("FAIL", str(path), "SamplingFrequency must be positive."))

    power = payload.get("PowerLineFrequency")
    if power not in (50, 60, "50", "60", "n/a"):
        findings.append(
            Finding("WARN", str(path), "PowerLineFrequency is usually 50, 60, or n/a; verify this value.")
        )

    return findings


def _audit_channels(path: Path, rows: list[dict[str, str]], expected_sfreq: float | None) -> list[Finding]:
    findings: list[Finding] = []
    columns = set(rows[0].keys()) if rows else set()
    for field in sorted(REQUIRED_CHANNEL_COLUMNS - columns):
        findings.append(Finding("FAIL", str(path), f"Missing required channels.tsv column: {field}."))
    for field in sorted(RECOMMENDED_CHANNEL_COLUMNS - columns):
        findings.append(Finding("INFO", str(path), f"Recommended channels.tsv column is absent: {field}."))

    if not rows:
        findings.append(Finding("FAIL", str(path), "channels.tsv has no channel rows."))
        return findings

    names = [row.get("name", "").strip() for row in rows]
    duplicates = sorted({name for name in names if name and names.count(name) > 1})
    if duplicates:
        findings.append(Finding("FAIL", str(path), f"Duplicate channel names: {', '.join(duplicates)}."))

    eeg_count = 0
    sfreq_values: list[float] = []
    for idx, row in enumerate(rows, start=2):
        name = row.get("name", "").strip() or f"row {idx}"
        channel_type = row.get("type", "").strip().upper()
        units = row.get("units", "").strip()
        status = row.get("status", "").strip().lower()

        if not name or name == f"row {idx}":
            findings.append(Finding("FAIL", f"{path}:{idx}", "Channel name is blank."))
        if channel_type and channel_type not in VALID_CHANNEL_TYPES:
            findings.append(Finding("WARN", f"{path}:{idx}", f"Uncommon channel type '{channel_type}' for {name}."))
        if channel_type == "EEG":
            eeg_count += 1
            if units not in {"V", "uV", "µV"}:
                findings.append(Finding("WARN", f"{path}:{idx}", f"EEG channel {name} uses unusual units '{units}'."))
        if status and status not in {"good", "bad", "n/a"}:
            findings.append(Finding("WARN", f"{path}:{idx}", f"Unexpected status '{status}' for {name}."))
        sfreq = _as_float(row.get("sampling_frequency"))
        if sfreq is not None:
            sfreq_values.append(sfreq)
            if sfreq <= 0:
                findings.append(Finding("FAIL", f"{path}:{idx}", f"Non-positive sampling_frequency for {name}."))

    if eeg_count == 0:
        findings.append(Finding("WARN", str(path), "No EEG channels were labeled with type EEG."))
    if expected_sfreq is not None and sfreq_values:
        avg_sfreq = mean(sfreq_values)
        if abs(avg_sfreq - expected_sfreq) > 1e-6:
            findings.append(
                Finding(
                    "WARN",
                    str(path),
                    f"Mean channel sampling_frequency {avg_sfreq:g} differs from EEG JSON {expected_sfreq:g}.",
                )
            )

    return findings


def _audit_electrodes(path: Path, rows: list[dict[str, str]]) -> list[Finding]:
    findings: list[Finding] = []
    columns = set(rows[0].keys()) if rows else set()
    required = {"name", "x", "y", "z"}
    for field in sorted(required - columns):
        findings.append(Finding("WARN", str(path), f"electrodes.tsv is missing coordinate column: {field}."))
    if not rows:
        findings.append(Finding("WARN", str(path), "electrodes.tsv has no electrode rows."))
    return findings


def _as_float(value: Any) -> float | None:
    if value in (None, "", "n/a"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _stem_key(path: Path) -> str:
    name = path.name
    for suffix in ("_eeg.json", "_channels.tsv", "_electrodes.tsv"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem
