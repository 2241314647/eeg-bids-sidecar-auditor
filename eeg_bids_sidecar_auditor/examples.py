from __future__ import annotations

import json
from pathlib import Path


def write_example_dataset(root: Path) -> None:
    eeg_dir = root / "sub-01" / "ses-01" / "eeg"
    eeg_dir.mkdir(parents=True, exist_ok=True)
    prefix = eeg_dir / "sub-01_ses-01_task-checker"

    (prefix.with_name(prefix.name + "_eeg.json")).write_text(
        json.dumps(
            {
                "TaskName": "checker",
                "SamplingFrequency": 256,
                "PowerLineFrequency": 50,
                "EEGReference": "Cz",
                "Manufacturer": "Simulated",
                "EEGPlacementScheme": "10-20",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (prefix.with_name(prefix.name + "_channels.tsv")).write_text(
        "\n".join(
            [
                "name\ttype\tunits\tstatus\tstatus_description\tsampling_frequency",
                "Fp1\tEEG\tuV\tgood\tn/a\t256",
                "Fp2\tEEG\tuV\tgood\tn/a\t256",
                "Cz\tEEG\tuV\tgood\tn/a\t256",
                "HEOG\tEOG\tuV\tbad\tlarge drift\t256",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (prefix.with_name(prefix.name + "_electrodes.tsv")).write_text(
        "\n".join(
            [
                "name\tx\ty\tz",
                "Fp1\t-0.03\t0.08\t0.04",
                "Fp2\t0.03\t0.08\t0.04",
                "Cz\t0.00\t0.00\t0.09",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
