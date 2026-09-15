#!/usr/bin/env python3

import argparse
from pathlib import Path
import pandas as pd
from helper_functions import excel_to_df

# STEP 1
# Combine barcode/ID files for all plates in a project 
# Add extra column "Blast Match"
# Save

# STEP 2
# Create fasta file
# Take only "Specimen ID" and "barcode" columns
# Save

# Takes arguments:
# Input directory containing files to combine
# Output file name for barcodes and IDs (e.g. ProjectName_PlateXtoX_Barcodes_IDs.xlsx)
# Output file name for FASTA file (e.g. ProjectName_PlateXtoX.fasta)

### MAIN ###

def main():
    parser = argparse.ArgumentParser(
        description="Combine barcodes/IDs for several plates into one project file."
    )

    # Arguments passed in through command line
    parser.add_argument(
        "--input_dir",
        required=True,
        help="Directory containing plate files to merge"
    )
    parser.add_argument(
        "--output_barcodes_ids",
        required=True,
        help="Name for combined barcodes/IDs file"
    )
    parser.add_argument(
        "--output_fasta",
        required=True,
        help="Name for combined FASTA file"
    )

    args = parser.parse_args()

    # Check if input directory exists, and is a directory
    input_dir = Path(args.input_dir)
    
    if not input_dir.exists():
        raise ValueError(f"{input_dir} does not exist.")
        
    if not input_dir.is_dir():
        raise ValueError(f"{input_dir} is not a directory.")

    ### STEP 1
    
    # Load spreadsheet for each plate sheet in input directory

    loaded = []

    for file in sorted(input_dir.glob("*.xlsx")):
        df = excel_to_df(file)
    
        print(f"Loaded: {file.name} ({len(df)} rows)")
        loaded.append((df, file.name))
    
    # If no input files found
    if not loaded:
        raise ValueError(
            f"No .xlsx files found in {input_dir}"
        )

    # Combine plates into project file
    combined_df = pd.concat(
        [df for df, _ in loaded],
        ignore_index=True
    )

    required_cols = {"Specimen ID", "barcode"}

    missing = required_cols - set(combined_df.columns)
    if missing:
        raise ValueError(f"Combined dataframe missing required columns: {missing}")

    
    # Save project file
    combined_df.to_excel(args.output_barcodes_ids, index=False)

    # Print results
    print(f"Combined {len(loaded)} files")
    print(f"Total rows: {len(combined_df)}")
    print(f"Concatenated project file saved to: {args.output_barcodes_ids}")

    ### STEP 2

    # Create FASTA file

    fasta_df = combined_df[["Specimen ID", "barcode"]]

    with open(args.output_fasta, "w") as fasta:
        for _, row in fasta_df.iterrows():
            fasta.write(f">{row['Specimen ID']}\n")
            fasta.write(f"{row['barcode']}\n")

    print(f"FASTA file saved to: {args.output_fasta}")

if __name__ == "__main__":
    main()
