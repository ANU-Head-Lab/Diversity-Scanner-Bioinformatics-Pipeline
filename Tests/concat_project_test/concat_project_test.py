#!/usr/bin/env python3

import pytest
import pandas as pd
import subprocess
from pathlib import Path
import pandas.testing as pdt

# Tests for concat_project.py

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "Tests" / "concat_project_test"
SCRIPT = ROOT / "Scripts" / "concat_project.py"

def test():

    input_dir = TEST / "input1"
    output_barcodes_ids = TEST / "barcodes_ids1.xlsx"
    output_fasta = TEST / "fasta1.fasta"
    
    result = subprocess.run(
        [
        "python",
         str(SCRIPT),
         "--input_dir",
         str(input_dir),
         "--output_barcodes_ids",
         str(output_barcodes_ids),
         "--output_fasta",
         str(output_fasta)
        ],
        capture_output = True,
        text = True
    )

    # No errors output
    assert result.returncode == 0, result.stderr

    # Output files exist
    assert output_barcodes_ids.exists()
    assert output_fasta.exists()

    # Check number of rows and columns
    input = pd.read_excel(input_dir / "RPbula Plate 89_Barcodes_IDs.xlsx")
    output = pd.read_excel(output_barcodes_ids)

    # Number of columns equal in input and output
    assert len(output.columns) == len(input.columns)

    # Number of output rows = sum of input rows (96 + 95 + 95)
    assert len(output) == 286