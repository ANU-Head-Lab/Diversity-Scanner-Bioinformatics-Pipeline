#!/usr/bin/env python3

import pytest
import pandas as pd
import subprocess
from pathlib import Path
import pandas.testing as pdt
import sys

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "Tests" / "merge_and_split_test"
SCRIPT = ROOT / "Scripts" / "merge_and_split.py"

# Import helper functions
sys.path.append(str(ROOT / "Scripts"))
from helper_functions import count_files_in_directory

def test():

    barcodes = TEST / "Test1_Barcodes.xlsx"
    ids = TEST / "Test1_IDs.xlsx"
    runinfo = TEST / "Test1_RunInfo.xlsx"
    input_dir = TEST / "input1"
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
         "--input_dir",
         str(input_dir),
         "--output_dir",
         str(output_dir)
        ],
        capture_output = True,
        text = True
    )

    # No errors
    assert result.returncode == 0, result.stderr

    # Number of input files = number of output files - 1
    num_input = count_files_in_directory(input_dir)
    num_output = count_files_in_directory(output_dir)
    assert (num_input == num_output - 1)

    # Number of columns in output = sum of barcodes and IDs columns - 1
    input1 = pd.read_excel(barcodes)
    input2 = pd.read_excel(ids)
    output1 = pd.read_excel(output_dir / "RPbula Plate 74 DS_Barcodes_IDs.xlsx")
    assert len(input1.columns) + len(input2.columns) - 1 == len(output1.columns)

