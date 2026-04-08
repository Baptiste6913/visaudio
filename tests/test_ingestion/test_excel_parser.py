from pathlib import Path

import pandas as pd
import pytest

from src.ingestion.excel_parser import EXPECTED_COLUMNS, read_visaudio_excel


SAMPLE_PATH = Path("data/samples/sample_500.xlsx")


def test_reads_sample_500_rows():
    df = read_visaudio_excel(SAMPLE_PATH)
    assert len(df) == 500


def test_columns_are_renamed():
    df = read_visaudio_excel(SAMPLE_PATH)
    assert list(df.columns) == list(EXPECTED_COLUMNS)


def test_raises_if_file_missing():
    with pytest.raises(FileNotFoundError):
        read_visaudio_excel(Path("does/not/exist.xlsx"))


def test_raises_if_column_count_unexpected(tmp_path: Path):
    fake = tmp_path / "bad.xlsx"
    # Write an Excel file with only 3 columns
    pd.DataFrame({"a": [1], "b": [2], "c": [3]}).to_excel(fake, index=False)
    with pytest.raises(ValueError, match="Expected 19 columns"):
        read_visaudio_excel(fake)
