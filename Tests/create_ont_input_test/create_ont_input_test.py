#!/usr/bin/env python3

import pytest
import pandas as pd
import subprocess
from pathlib import Path
import pandas.testing as pdt

# Tests for create_ont_input.py

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "Tests" / "create_ont_input_test"
SCRIPT = ROOT / "Scripts" / "create_ont_input.py"
TAGINFO_313 = ROOT / "Files" / "313bp_primers_TA.csv"
TAGINFO_658 = ROOT / "Files" / "658bp_primers_TA.csv"

# Create ONT input using entomoscope files with new template (313bp)
def test_new_template():

    input_dir = TEST / "input1"
    output = TEST / "output1.csv"
    runinfo = TEST / "runinfo1.xlsx"
    manual = TEST / "output_manual_1.csv"

    result = subprocess.run(
        [
        "python",
         str(SCRIPT),
         "--input_dir",
         str(input_dir),
         "--runinfo",
         str(runinfo),
         "--taginfo",
         str(TAGINFO_313),
         "--output",
         str(output),
         "--transposeDS"
        ],
        capture_output = True,
        text = True
    )

    try:
        # No errors output
        assert result.returncode == 0, result.stderr

        # Output file exists
        assert output.exists()

        # Compare to manually created output file
        df = pd.read_csv(output)
        manual = pd.read_csv(manual)

        pdt.assert_frame_equal(df, manual)

    finally:
        # Delete output file
        if output.exists():
            output.unlink()

# Create ONT input using entomoscope files with old template (658bp)
def test_old_template():

    input_dir = TEST / "input2"
    output = TEST / "output2.csv"
    runinfo = TEST / "runinfo2.xlsx"
    manual = TEST / "output_manual_2.csv"

    result = subprocess.run(
        [
        "python",
         str(SCRIPT),
         "--input_dir",
         str(input_dir),
         "--specimen_id_column",
         "Image code",
         "--runinfo",
         str(runinfo),
         "--taginfo",
         str(TAGINFO_658),
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

        # Compare to manually created output file
        df = pd.read_csv(output)
        manual = pd.read_csv(manual)

        pdt.assert_frame_equal(df, manual)

    finally:
        # Delete output file
        if output.exists():
            output.unlink()