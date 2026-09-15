#!/usr/bin/env python3

import argparse
from pathlib import Path
import pandas as pd
from helper_functions import excel_to_df

# Combine individual entomoscope sheets into mastersheet 
# Confirm columns are the same in all individual sheets

# Takes arguments:
# Input directory containing files to combine
# Output file name (e.g. Mastersheet.xlsx)

# Reference column names (according to new Entomoscope datasheet template)

reference_columns = [
    "Specimen ID",
    "Plate",
    "Well",
    "Provisional ID",
    "Lens",
    "Image count",
    "Person",
    "Site",
    "Trap ID",
    "Date",
    "Time",
    "Notes"
]

### DEFINE FUNCTIONS ###

# Check column names in all plate spreadsheets match template
def validate_columns_template(dataframes_and_names):
    for df, filename in dataframes_and_names:
        
        if list(df.columns) != reference_columns:
            missing = set(reference_columns) - set(df.columns)
            extra = set(df.columns) - set(reference_columns)
        
            message = [f"Column mismatch in {filename}"]
        
            if missing:
                message.append(f"Missing columns: {sorted(missing)}")
        
            if extra:
                message.append(f"Extra columns: {sorted(extra)}")

            # Same columns but wrong order
            if not missing and not extra:
                message.append("Columns are present but not in the expected order")
        
            raise ValueError("\n".join(message))

# Check that column names are the same in all plate spreadsheets
def validate_columns(dataframes_and_names):        

    # Take columns of first sheet as a reference
    reference_df, reference_name = dataframes_and_names[0]
    reference_columns = list(reference_df.columns)

    # Check that the same columns exist in all subsequent files
    for df, filename in dataframes_and_names[1:]:

        if list(df.columns) != reference_columns:
            missing = set(reference_columns) - set(df.columns)
            extra = set(df.columns) - set(reference_columns)

            message = [
                f"Column mismatch in {filename}",
                f"Reference file: {reference_name}",
            ]

            if missing:
                message.append(f"Missing columns: {sorted(missing)}")

            if extra:
                message.append(f"Extra columns: {sorted(extra)}")

            raise ValueError("\n".join(message))

### MAIN ###

def main():
    parser = argparse.ArgumentParser(
        description="Combine specified plate spreadsheets."
    )

    # Arguments passed in through command line
    parser.add_argument(
        "--input_dir",
        required=True,
        help="Directory containing Entomoscope sheets to merge"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Name for Mastersheet output file"
    )
    parser.add_argument(
        "--old_template",
        action="store_true",
        help="Entomoscope sheets use old template"
    )

    args = parser.parse_args()

    # Check if input directory exists, and is a directory
    input_dir = Path(args.input_dir)
    
    if not input_dir.exists():
        raise ValueError(f"{input_dir} does not exist.")
        
    if not input_dir.is_dir():
        raise ValueError(f"{input_dir} is not a directory.")
    
    # Load spreadsheet for each Entomoscope sheet in input directory

    loaded = []

    for file in sorted(input_dir.glob("*.xlsx")):
        df = excel_to_df(file)

        # Rename 'Image count ' to 'Image count'
        if ("Image count ") in (df.columns):
            df = df.rename(columns={
                "Image count ": "Image count",
            })
    
        print(f"Loaded: {file.name} ({len(df)} rows)")
        loaded.append((df, file.name))
    
    # If no input files found
    if not loaded:
        raise ValueError(
            f"No .xlsx files found in {input_dir}"
        )

    # If Ento sheets are using the old template, check if columns are the same in all sheets
    if (args.old_template):
        validate_columns(loaded)

    # Otherwise, check column names against template names
    else:
        validate_columns_template(loaded)
    
    # Combine sheets into Mastersheet
    combined_df = pd.concat(
        [df for df, _ in loaded],
        ignore_index=True
    )
    
    # Save Mastersheet file
    combined_df.to_excel(args.output, index=False)

    # Print results
    print(f"Combined {len(loaded)} files")
    print(f"Total rows: {len(combined_df)}")
    print(f"Mastersheet file saved to: {args.output}")


if __name__ == "__main__":
    main()
