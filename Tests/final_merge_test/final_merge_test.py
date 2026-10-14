#!/usr/bin/env python3

import pytest
import pandas as pd
import subprocess
from pathlib import Path
import pandas.testing as pdt

# Tests for final_merge.py

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "Tests" / "final_merge_test"
SCRIPT = ROOT / "Scripts" / "final_merge.py"

# Create final merged file using files with new template
def test_new_template():

    input1 = TEST / "mastersheet1.xlsx"
    input2 = TEST / "motus_barcodes_ids1.xlsx"
    output = TEST / "output1.xlsx"
    
    #manual = TEST / "output_manual_1.csv"

    result = subprocess.run(
        [
        "python",
         str(SCRIPT),
         "--input_files",
         str(input1),
         str(input2),
         "--merge_columns",
         "Specimen ID",
         "Sequence ID",
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

        # Check number of rows and columns
        df = pd.read_excel(output)
        ms = pd.read_excel(input1)
        assert(len(df.columns) == 40)
        assert(len(df) == len(ms))

    finally:
        # Delete output file
        if output.exists():
            print("done")
            #output.unlink()

def test_old_template():
    input1 = TEST / "mastersheet2.xlsx"
    input2 = TEST / "motus_barcodes_ids2.xlsx"
    output = TEST / "output2.xlsx"

    result = subprocess.run(
        [
        "python",
         str(SCRIPT),
         "--input_files",
         str(input1),
         str(input2),
         "--merge_columns",
         "Image code",
         "Sequence ID",
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

        # Check number of rows and columns
        df = pd.read_excel(output)
        ms = pd.read_excel(input1)
        assert(len(df.columns) == 41)
        assert(len(df) == len(ms))

        # manual = pd.read_csv(manual)

        # pdt.assert_frame_equal(df, manual)

    finally:
        # Delete output file
        if output.exists():
            print("done")
            #output.unlink()