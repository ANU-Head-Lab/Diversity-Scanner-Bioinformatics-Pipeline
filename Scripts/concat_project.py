#!/usr/bin/env python3

import argparse
from pathlib import Path
import pandas as pd
from helper_functions import excel_to_df

# Combine barcode/ID files for all plates in a project 

# Takes arguments:
# Input directory containing files to combine
# Output file name (e.g. ProjectName_PlateXtoX_Barcodes_IDs.xlsx)

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
        "--output",
        required=True,
        help="Name for combined project file"
    )

    args = parser.parse_args()

    # Check if input directory exists, and is a directory
    input_dir = Path(args.input_dir)
    
    if not input_dir.exists():
        raise ValueError(f"{input_dir} does not exist.")
        
    if not input_dir.is_dir():
        raise ValueError(f"{input_dir} is not a directory.")
    
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
    
    # Save project file
    combined_df.to_excel(args.output, index=False)

    # Print results
    print(f"Combined {len(loaded)} files")
    print(f"Output: {args.output}")
    print(f"Total rows: {len(combined_df)}")

if __name__ == "__main__":
    main()
