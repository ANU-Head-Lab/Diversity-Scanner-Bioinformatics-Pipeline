#!/usr/bin/env python3

import pytest
import pandas as pd
import subprocess
from pathlib import Path
import pandas.testing as pdt

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "Tests" / "merge_and_split_test"
SCRIPT = ROOT / "Scripts" / "merge_and_split.py"

# Create final merged file using files with new template
def test():

    barcodes = TEST / "Test1_Barcodes.xlsx"
    ids = TEST / "Test1_IDs.xlsx"
    runinfo = TEST / "Test1_RunInfo.xlsx"
    ento_sheets = TEST / "ento_sheets1"
    output_dir = TEST / "output1"
    
    result = subprocess.run(
        [
        "python",
         str(SCRIPT),
         "--barcodes",
         str(barcodes),
         "--ids",
         str(ids),
         "--runinfo",
         str(runinfo),
         "--ento_sheets",
         str(ento_sheets),
         "--output_dir",
         str(output_dir)
        ],
        capture_output = True,
        text = True
    )

    # No errors
    assert result.returncode == 0, result.stderr
