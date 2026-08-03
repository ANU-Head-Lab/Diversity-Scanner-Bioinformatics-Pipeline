#!/usr/bin/env python3

import argparse
from pathlib import Path
import pandas as pd

# Create input file for ONT barcoder
# Assumes correct 96 well layout: A1, A2...B1, B2...H1, H2...H12
# Assumes no empty wells 
# Any changes from regular layout may need to be handled manually

# Inputs:
# File containing the Plate IDs for the given sequencing run and their corresponding tags
# File path to 313bp/658bp masterfile
# Output file name

# Load dataframe from given excel file
# Specify sheet name, if not provided, take first sheet
def excel_to_df(filename, sheet = 0):
    path = Path(filename)

    # Throw error if file not found
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filename}")

    df = pd.read_excel(path, sheet_name = sheet)
    return df

# Load dataframe from given csv file
def csv_to_df(filename):
    path = Path(filename)

    # Throw error if file not found
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filename}")

    df = pd.read_csv(path)
    return df

def main():
    parser = argparse.ArgumentParser(
        description="Create input file for ONT barcoder"
    )

    # Arguments passed in through command line
    parser.add_argument(
        "--runinfo",
        required=True,
        help="Excel file containing list of plates in the sequencing run and their corresponding tag names"
    )

    parser.add_argument(
        "--taginfo",
        required=True,
        help="Excel file containing tags and primers"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Name for output spreadsheet"
    )

    parser.add_argument(
        "--transposeDS",
        action="store_true",
        help="Use the 'Transposed' sheet for DS plates"
    )

    args = parser.parse_args()

    # Load run info
    runinfo = excel_to_df(args.runinfo)

    required_runinfo_cols = ['Plate', 'Tag']

    # Check if runinfo contains required columns
    for col in required_runinfo_cols:
        if col not in runinfo.columns:
            raise ValueError(
                f"Column '{col}' missing from runinfo file"
            )

    # Load tag info
    taginfo = csv_to_df(args.taginfo)

    # Check taginfo contains Forward Tag Name column
    if 'Forward Tag Name' not in taginfo.columns:
        raise ValueError("'Forward Tag Name' column missing from taginfo file")

    all_results = []

    # Go through each row in the runinfo file
    for _, row in runinfo.iterrows():

        plate = row['Plate']
        tag_name = row['Tag']

        filename = f"{plate}.xlsx"

        print(f"Loading plate: {plate}")

        # Load plate excel file
        # If tranposeDS flag used and plate name contains "DS", take "Transposed" sheet
        # Else, take first sheet
        sheet = (
            "Transposed" 
            if args.transposeDS and "DS" in str(plate).upper() 
            else 0
            )
        plate_df = excel_to_df(filename, sheet = sheet)

        # Get specimen IDS
        if 'Image code' not in plate_df.columns:
            raise ValueError(f"'Image code' column not found in {filename}")
        
        specimen_ids = plate_df['Image code']

        # Get tag sequences from taginfo file
        tag_seqs = taginfo[
        taginfo['Forward Tag Name'] == tag_name
        ]

        # Throw error if no matching tag sequences found in file
        if tag_seqs.empty:
            raise ValueError(
                f"Tag '{tag_name}' not found in tag file"
            )

        # Drop first two columns of taginfo data (tag name and well)
        tag_seqs = tag_seqs.iloc[:, 2:]

        # Check number of sequences = number of primers
        if len(specimen_ids) != len(tag_seqs):
            raise ValueError(
                f"Plate {plate} contains {len(specimen_ids)} specimens "
                f"but tag set contains {len(tag_seqs)} rows"
        )

        # Concatenate specimen IDs and tag info
        combined = pd.concat(
            [specimen_ids.reset_index(drop=True),
            tag_seqs.reset_index(drop=True)],
            axis=1
        )
        
        # Add plate to all_results
        all_results.append(combined)

    # Combine results from all plates
    final_df = pd.concat(
        all_results,
        ignore_index=True
    )

    # Save ONT input file as csv
    final_df.to_csv(args.output, index=False, header=False)


if __name__ == "__main__":
    main()

