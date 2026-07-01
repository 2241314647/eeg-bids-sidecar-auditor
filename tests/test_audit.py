import shutil
import unittest
from pathlib import Path

from eeg_bids_sidecar_auditor.audit import audit_dataset
from eeg_bids_sidecar_auditor.examples import write_example_dataset


class AuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch_root = Path("reports") / "test_workspace"
        if self.scratch_root.exists():
            shutil.rmtree(self.scratch_root)
        self.scratch_root.mkdir(parents=True, exist_ok=True)

    def test_example_dataset_has_no_failures(self) -> None:
        dataset = self.scratch_root / "example" / "bids"
        write_example_dataset(dataset)
        findings, summary = audit_dataset(dataset)
        self.assertEqual(summary["failures"], 0)
        self.assertEqual(summary["eeg_json_files"], 1)
        self.assertFalse([item for item in findings if item.severity == "FAIL"])

    def test_missing_required_json_field_fails(self) -> None:
        dataset = self.scratch_root / "missing" / "bids"
        eeg_dir = dataset / "sub-01" / "eeg"
        eeg_dir.mkdir(parents=True)
        (eeg_dir / "sub-01_task-rest_eeg.json").write_text('{"TaskName":"rest"}', encoding="utf-8")
        findings, summary = audit_dataset(dataset)
        self.assertGreaterEqual(summary["failures"], 1)
        self.assertTrue(any("SamplingFrequency" in item.message for item in findings))


if __name__ == "__main__":
    unittest.main()
