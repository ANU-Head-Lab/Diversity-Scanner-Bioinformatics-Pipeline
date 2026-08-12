#!/usr/bin/env python3

import pytest
import pandas as pd
import subprocess
from pathlib import Path

# Tests for create_mastersheet.py

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "Tests" / "format_ento_sheet_test"
SCRIPT = ROOT / "Scripts" / "format_ento_sheet.py"

# Change old template ento sheet to new template
def test_correct_formatting():

    input_dir = TEST / "input1"
    output_dir = TEST / "output1"

    result = subprocess.run(
        [
        "python",
         str(SCRIPT),
         "--input_dir",
         str(input_dir),
         "--output_dir",
         str(output_dir)
        ],
        capture_output = True,
        text = True
    )

    # No errors output
    assert result.returncode == 0, result.stderr

    input1 = pd.read_excel(input_dir / "Test Plate 1.xlsx")
    output1 = pd.read_excel(output_dir / "Test Plate 1.xlsx")

    # Number of rows equal
    assert len(input1) == len(output1)

    # Number of columns in output file = 12
    assert(len(output1.columns) == 12)

def test_incorrect_formatting():

    input_dir = TEST / "input2"
    output_dir = TEST / "output2"

    result = subprocess.run(
        [
        "python",
         str(SCRIPT),
         "--input_dir",
         str(input_dir),
         "--output_dir",
         str(output_dir)
        ],
        capture_output = True,
        text = True
    )

    # No errors output
    assert result.returncode != 0
    assert "Unexpected column names in input dataframe" in result.stderr
