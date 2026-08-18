#!/usr/bin/env python3

import pytest
import pandas as pd
import subprocess
from pathlib import Path
import pandas.testing as pdt

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "Tests" / "sequencing_summary_test"
SCRIPT = ROOT / "Scripts" / "sequencing_summary.py"

# Create final merged file using files with new template
def test():

    runsummary = TEST /"Test1_runsummary.xlsx"
    qc_barcodes = TEST / "Test1_qc_barcodes.fa"
    num_reads_filter = 500
    runinfo = TEST / "Test1_runinfo.xlsx"
    ento_sheets = TEST / "ento_sheets1"
    specimen_id_column = "Specimen ID"
    output_dir = TEST / "output1"
    
    result = subprocess.run(
        [
        "python",
         str(SCRIPT),
         "--runsummary",
         str(runsummary),
         "--qc_barcodes",
         str(qc_barcodes),
         "--num_reads_filter",
         str(num_reads_filter),
         "--runinfo",
         str(runinfo),
         "--ento_sheets",
         str(ento_sheets),
         "--specimen_id_column",
         str(specimen_id_column),
         "--output_dir",
         str(output_dir)
        ],
        capture_output = True,
        text = True
    )

    # No errors
    assert result.returncode == 0, result.stderr
