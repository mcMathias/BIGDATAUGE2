"""Test af udleveret runner-infrastruktur, ikke facit til lærlingens TODO'er."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pipeline


class CheckpointRunnerTests(unittest.TestCase):
    def test_realtime_checkpoint_does_not_require_settlement_todos(self):
        expected = pd.DataFrame({"hour_utc": ["2026-01-01T00:00Z"], "price_area": ["DK1"], "rt_interval_count": [12]})
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(pipeline, "OUTPUT_DIR", Path(directory)), patch.object(pipeline, "load_records", return_value=pd.DataFrame()) as load, patch.object(pipeline, "validate_snapshot", return_value=pd.DataFrame()), patch.object(pipeline, "prepare_realtime", return_value=expected), patch.object(pipeline, "prepare_settlement", side_effect=AssertionError("Må ikke kaldes")):
                result, path = pipeline.build_realtime_period("dst")
                self.assertEqual(len(result), 1)
                self.assertTrue(path.exists())
                self.assertEqual(path.name, "realtime_hourly_dst.csv")
                self.assertEqual(len(pd.read_csv(path)), 1)
                self.assertEqual(load.call_count, 1)

    def test_unknown_period_fails_before_input(self):
        with self.assertRaisesRegex(ValueError, "Ukendt periode"):
            pipeline.build_realtime_period("unknown")


if __name__ == "__main__":
    unittest.main()
