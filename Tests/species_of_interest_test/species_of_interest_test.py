#!/usr/bin/env python3

import pytest
import pandas as pd
import subprocess
from pathlib import Path
import pandas.testing as pdt
import sys

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "Tests" / "species_of_interest_test"
SCRIPT = ROOT / "Scripts" / "species_of_interest.py"

# Import helper functions
sys.path.append(str(ROOT / "Scripts"))
from helper_functions import count_files_in_directory

# Test directory containing input file with no species of interest
def test_no_species():

    input = TEST / "input1"
    output = TEST / "output1"

    species = ROOT / "Files" / "Species of interest.xlsx"
    
    result = subprocess.run(
        [
        "python",
         str(SCRIPT),
         "--input",
         str(input),
         "--output",
         str(output),
         "--species_of_interest",
         str(species)
        ],
        capture_output = True,
        text = True
    )

    # No errors
    assert result.returncode == 0, result.stderr

    # Number of output files = 1
    num_output = count_files_in_directory(output)
    assert num_output == 1


# Test directory containing input file with 3 threatened species and 2 pests
def test_species():

    input = TEST / "input2"
    output = TEST / "output2"

    species = ROOT / "Files" / "Species of interest.xlsx"
    
    result = subprocess.run(
        [
        "python",
         str(SCRIPT),
         "--input",
         str(input),
         "--output",
         str(output),
         "--species_of_interest",
         str(species)
        ],
        capture_output = True,
        text = True
    )

    # No errors
    assert result.returncode == 0, result.stderr

    # Num output files = 3
    num_output = count_files_in_directory(output)
    assert num_output == 3

    threatened = pd.read_excel(output / "Test_species_of_interest_threatened.xlsx")
    assert len(threatened) == 3

    pests = pd.read_excel(output / "Test_species_of_interest_pests.xlsx")
    assert len(pests) == 2

# Test single input file with 3 threatened species and 2 pests
def test_single_file():

    input = TEST / "input3.xlsx"
    output = TEST / "output3"

    species = ROOT / "Files" / "Species of interest.xlsx"
    
    result = subprocess.run(
        [
        "python",
         str(SCRIPT),
         "--input",
         str(input),
         "--output",
         str(output),
         "--species_of_interest",
         str(species)
        ],
        capture_output = True,
        text = True
    )

    # No errors
    assert result.returncode == 0, result.stderr

    # Num output files = 3
    num_output = count_files_in_directory(output)
    assert num_output == 3

    threatened = pd.read_excel(output / "input3_threatened.xlsx")
    assert len(threatened) == 3

    pests = pd.read_excel(output / "input3_pests.xlsx")
    assert len(pests) == 2