from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audit import Finding, audit_dataset
from .examples import write_example_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit lightweight BIDS EEG sidecar metadata.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo_parser = subparsers.add_parser("demo", help="Create and audit a simulated mini BIDS EEG dataset.")
    demo_parser.add_argument("--out", type=Path, default=Path("reports/demo"), help="Output directory.")

    audit_parser = subparsers.add_parser("audit", help="Audit an existing BIDS EEG dataset folder.")
    audit_parser.add_argument("dataset", type=Path, help="Dataset root to scan.")
    audit_parser.add_argument("--out", type=Path, default=Path("reports/audit"), help="Report directory.")

    args = parser.parse_args()
    if args.command == "demo":
        dataset = args.out / "example_bids"
        write_example_dataset(dataset)
        report_dir = args.out
    else:
        dataset = args.dataset
        report_dir = args.out

    findings, summary = audit_dataset(dataset)
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (report_dir / "report.md").write_text(_markdown_report(findings, summary), encoding="utf-8")

    print(f"Audited {summary['eeg_json_files']} EEG JSON and {summary['channels_tsv_files']} channel TSV files.")
    print(f"Findings: {summary['failures']} FAIL, {summary['warnings']} WARN, {summary['info']} INFO")
    print(f"Report: {report_dir / 'report.md'}")
    return 1 if summary["failures"] else 0


def _markdown_report(findings: list[Finding], summary: dict[str, object]) -> str:
    lines = [
        "# EEG BIDS Sidecar Audit Report",
        "",
        "## Summary",
        "",
        f"- Dataset: `{summary['dataset']}`",
        f"- EEG JSON files: {summary['eeg_json_files']}",
        f"- Channels TSV files: {summary['channels_tsv_files']}",
        f"- Electrodes TSV files: {summary['electrodes_tsv_files']}",
        f"- Failures: {summary['failures']}",
        f"- Warnings: {summary['warnings']}",
        f"- Info notes: {summary['info']}",
        "",
        "## Findings",
        "",
    ]
    if not findings:
        lines.append("No findings.")
    else:
        lines.extend(
            f"- **{item.severity}** `{item.location}`: {item.message}"
            for item in sorted(findings, key=lambda item: (item.severity != "FAIL", item.severity, item.location))
        )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
