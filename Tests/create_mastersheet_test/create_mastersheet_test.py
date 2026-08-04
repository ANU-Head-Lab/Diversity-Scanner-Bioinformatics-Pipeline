#!/usr/bin/env python3

import pytest
import pandas as pd
import subprocess
from pathlib import Path

# Tests for create_mastersheet.py

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "Tests" / "create_mastersheet_test"
SCRIPT = ROOT / "Scripts" / "create_mastersheet.py"

# Combine files with new template
def test_new_template():

    input_dir = TEST / "create_mastersheet_input_1"
    output = TEST / "create_mastersheet_output_1.xlsx"

    result = subprocess.run(
        [
        "python",
         str(SCRIPT),
         "--input_dir",
         str(input_dir),
         "--output",
         str(output)
        ],
        capture_output = True,
        text = True
    )

    try:
        # No errors output
        assert result.returncode == 0, result.stderr

        # Output file exists
        assert output.exists()

        input_df = pd.read_excel(input_dir / "test_df_1.xlsx")
        merged = pd.read_excel(output)

        # Number of columns equal in input and output
        assert len(merged.columns) == len(input_df.columns)

        # Number of output rows = sum of input rows
        assert len(merged) == 192

    finally:
        # Delete output file
        if output.exists():
            output.unlink()

# Combine files with old template
def test_old_template():

    input_dir = TEST / "create_mastersheet_input_2"
    output = TEST / "create_mastersheet_output_2.xlsx"

    result = subprocess.run(
        [
        "python",
         str(SCRIPT),
         "--input_dir",
         str(input_dir),
         "--output",
         str(output),
         "--old_template"
        ],
        capture_output = True,
        text = True
    )

    try:
        # No errors output
        assert result.returncode == 0, result.stderr

        # Output file exists
        assert output.exists()

        input_df = pd.read_excel(input_dir / "test_df_1.xlsx")
        merged = pd.read_excel(output)

        # Number of columns equal in input and output
        assert len(merged.columns) == len(input_df.columns)

        # Number of output rows = sum of input rows
        assert len(merged) == 192

    finally:
        # Delete output file
        if output.exists():
            output.unlink()

# Test two files whose columns don't match
def test_unmatching_files():

    input_dir = TEST / "create_mastersheet_input_3"
    output = TEST / "create_mastersheet_output_3.xlsx"

    result = subprocess.run(
        [
        "python",
         str(SCRIPT),
         "--input_dir",
         str(input_dir),
         "--output",
         str(output)
        ],
        capture_output = True,
        text = True
    )

    assert result.returncode != 0
    assert "Column mismatch" in result.stderr
