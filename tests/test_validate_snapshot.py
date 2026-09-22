from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from contracts import REALTIME_REQUIRED_COLUMNS  # noqa: E402
from pipeline import RAW_DIR, load_records, validate_snapshot  # noqa: E402


class ValidateSnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = load_records(
            RAW_DIR / "realtime_dst_2026-03-28_31.json",
            "ElectricityProdex5MinRealtime",
        )

    def validate(self, frame: pd.DataFrame) -> pd.DataFrame:
        return validate_snapshot(
            frame, REALTIME_REQUIRED_COLUMNS, "Minutes5UTC", "realtime"
        )

    def test_clean_file_passes_and_keeps_all_rows(self) -> None:
        result = self.validate(self.raw)
        self.assertEqual(len(result), len(self.raw))
        self.assertEqual(str(result["Minutes5UTC"].dt.tz), "UTC")

    def test_input_frame_is_not_modified(self) -> None:
        before = self.raw["Minutes5UTC"].copy()
        self.validate(self.raw)
        pd.testing.assert_series_equal(self.raw["Minutes5UTC"], before)

    def test_missing_column_fails(self) -> None:
        column = list(REALTIME_REQUIRED_COLUMNS)[-1]
        with self.assertRaisesRegex(ValueError, "mangler"):
            self.validate(self.raw.drop(columns=[column]))

    def test_invalid_timestamp_fails(self) -> None:
        broken = self.raw.copy()
        broken.loc[0, "Minutes5UTC"] = "ikke-en-tid"
        with self.assertRaisesRegex(ValueError, "ugyldige"):
            self.validate(broken)

    def test_unknown_price_area_fails(self) -> None:
        broken = self.raw.copy()
        broken.loc[0, "PriceArea"] = "DK3"
        with self.assertRaisesRegex(ValueError, "prisområder"):
            self.validate(broken)

    def test_duplicate_key_fails(self) -> None:
        broken = pd.concat([self.raw, self.raw.iloc[[0]]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "deler nøgle"):
            self.validate(broken)


if __name__ == "__main__":
    unittest.main()