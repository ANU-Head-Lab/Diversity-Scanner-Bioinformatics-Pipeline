import pandas as pd
import argparse
from pathlib import Path

# Make final_merge:
# Order of final columns:
# Mastersheet, MOTUs, Barcodes, IDs
# Remove columns: CleanID, SpecimenID_file2, Blast match, final (Order, Class, order) columns
# Colour code!

# What this script does:
# Merge two spreadsheets by SpecimenID column, keeping all values in both sheets

# To-do
# Specify what column to merge by
# Allow to increase number of sheets

# Load dataframe from given excel file
# Specify sheet name, if not provided, take first sheet
def excel_to_df(filename, sheet = 0):
    path = Path(filename)

    # Throw error if file not found
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filename}")

    return pd.read_excel(path, sheet_name = sheet)

# Merge list of dataframes based on a given column or list of columns
def merge_sheets(dataframes, merge_columns):

    if len(dataframes) < 2:
        raise ValueError("At least two files are required for merge")

    # Same merge column in all files
    if len(merge_columns) == 1:
        merge_columns = merge_columns * len(dataframes)

    # Different merge column per file
    elif len(merge_columns) != len(dataframes):
        raise ValueError("Number of merge columns does not equal number of files")

    # Verify columns exist in input files
    for i, (df, col) in enumerate(zip(dataframes, merge_columns)):
        if col not in df.columns:
            raise ValueError(
                f"Merge column '{col}' not found in input file {i + 1}"
            )

    # Iteratively merge dataframes
    merged = dataframes[0]

    for i in range(1, len(dataframes)):
        left_col = merge_columns[0]
        right_col = merge_columns[i]

        # Check missing rows
        left_keys = set(merged[left_col].dropna())
        right_keys = set(dataframes[i][right_col].dropna())

        only_in_left = len(left_keys - right_keys)
        only_in_right = len(right_keys - left_keys)

        print(f"Comparing file 1 to file {i+1}:")
        print(f"  Rows only in file 1: {only_in_left}")
        print(f"  Rows only in file {i+1}: {only_in_right}")

        merged = merged.merge(
            dataframes[i],
            left_on = left_col,
            right_on = right_col,
            how="outer",
            suffixes=("", f"_file{i+1}")
        )

        # Drop duplicate merge columns
        if left_col != right_col:
            merged = merged.drop(columns=[right_col])

    return merged


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