#!/usr/bin/env python3

import argparse
from pathlib import Path
import pandas as pd

# STEP 1
# Merge barcodes from individual runs to create FinalBarcodes file for a project
# Rename "SpecimenID" to "Specimen ID"
# Add extra column "Blast Match"
# Save as "RunName_PlateXtoX_FinalBarcodes.xlsx"

# STEP 2
# Create fasta file
# Take only "Specimen ID" and "barcode" columns
# Save as "RunName_PlateXtoX.fasta"

# Load dataframe from given excel file
def excel_to_df(filename):
    path = Path(filename)

    # Throw error if file not found
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filename}")

    df = pd.read_excel(path)
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Create combined FinalBarcodes file and FASTA file given a directory of Project Plate barcode files"
    )
    
    parser.add_argument(
        "--input_dir",
        required=True,
        help="Directory containing project plate barcode files to merge"
    )

    parser.add_argument(
        "--output_final_barcodes",
        required=True,
        help="Name for output FinalBarcodes spreadsheet"
    )

    parser.add_argument(
        "--output_fasta",
        required=True,
        help="Name for output FASTA file"
    )

    args = parser.parse_args()

    loaded = []

    ### STEP 1

    # Check if input directory exists, and is a directory
    input_dir = Path(args.input_dir)

    if not input_dir.exists():
        raise ValueError(f"{input_dir} does not exist.")
    
    if not input_dir.is_dir():
        raise ValueError(f"{input_dir} is not a directory.")

    # Load spreadsheet for each plate barcode file in input directory
    for file in input_dir.glob("*.xlsx"):
        df = excel_to_df(file)

        print(f"Loaded: {file.name} ({len(df)} rows)")
        loaded.append(df)

    # If no input files found
    if not loaded:
        raise ValueError(
            f"No .xlsx files found in {input_dir}"
        )

    # Combine sheets into FinalBarcodes file
    combined_df = pd.concat(
        loaded,
        ignore_index=True
        )

    required_cols = {"SpecimenID", "barcode"}

    missing = required_cols - set(combined_df.columns)
    if missing:
        raise ValueError(f"Combined dataframe missing required columns: {missing}")
    
    # Rename SpecimenID to Specimen ID
    combined_df.rename(
        columns={"SpecimenID": "Specimen ID"}, 
        inplace=True
        )
    
    # Add empty "Blast Match" column at index 1 (between column A and B)
    combined_df.insert(1, "Blast Match", "")

    # Save final barcodes file
    combined_df.to_excel(args.output_final_barcodes, index=False)

    # Print results
    print(f"Combined {len(loaded)} barcode files")
    print(f"Output: {args.output_final_barcodes}")
    print(f"Total rows: {len(combined_df)}")

    ### STEP 2

    # Create FASTA file

    fasta_df = combined_df[["Specimen ID", "barcode"]]

    with open(args.output_fasta, "w") as fasta:
        for _, row in fasta_df.iterrows():
            fasta.write(f">{row['Specimen ID']}\n")
            fasta.write(f"{row['barcode']}\n")

    print("Wrote FASTA file.")
    print(f"Output: {args.output_fasta}")



if __name__ == "__main__":
    main()

