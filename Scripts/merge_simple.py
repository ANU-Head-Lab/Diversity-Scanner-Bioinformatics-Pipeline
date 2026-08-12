import pandas as pd
import argparse
from pathlib import Path
from helper_functions import excel_to_df, merge_sheets

# Make final_merge:
# Order of final columns:
# Mastersheet, MOTUs, Barcodes, IDs
# Remove columns: CleanID, SpecimenID_file2, Blast match, final (Order, Class, order) columns
# Colour code!

# What this script does:
# Merge multiple spreadsheets by SpecimenID column, keeping all values in both sheets

# To-do
# Specify what column to merge by
# Allow to increase number of sheets

def main():
    parser = argparse.ArgumentParser(
        description="Merge spreadsheets by specified column"
    )
    parser.add_argument(
        "--input_files",
        required=True,
        nargs= '+',
        help="List of files to merge"
    )
    parser.add_argument(
        "--merge_columns",
        required=True,
        nargs='+',
        help="Name of the column(s) to merge by. If the column names are different in the input files, list them in the order that you listed the files."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output file name"
    )

    args = parser.parse_args()

    # Load input files
    loaded = []
    for file in args.input_files:
        df = excel_to_df(file)
        print(f"Loaded input file: {file} ({len(df)} rows)")
        loaded.append(df)

    # Merge files
    merged = merge_sheets(loaded, args.merge_columns)

    output_path = Path(args.output)

    if output_path.suffix.lower() != ".xlsx":
        raise ValueError("Output file must have .xlsx extension")

    # Save merged file
    merged.to_excel(output_path, index=False)
    
    print(f"Merged spreadsheet saved to: {output_path}")

if __name__ == "__main__":
    main()
