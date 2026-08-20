import pandas as pd
from pathlib import Path
import sys

# Helper functions that get reused in multiple scripts

# Load dataframe from given excel file
# Specify sheet name, if not provided, take first sheet
def excel_to_df(filename, sheet = 0):
    path = Path(filename)

    # Throw error if file not found
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filename}")

    return pd.read_excel(path, sheet_name = sheet)

# Load dataframe from given csv file
def csv_to_df(filename):
    path = Path(filename)

    # Throw error if file not found
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filename}")

    df = pd.read_csv(path)
    return df

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

# Split barcodes file by plate according to specified columns
def split_by_plate(barcodes, barcodes_column, plates, plate_column):

    results = []

    for df, filename in plates:

        # Get specimen IDS
        if plate_column not in df.columns:
            raise ValueError(f"{plate_column} column not found in {filename}")

        specimen_ids = df[plate_column]

        # Split runsummary per plate
        plate_barcodes = barcodes[barcodes[barcodes_column].isin(specimen_ids)]

        # Sort by specimen ID
        plate_barcodes = plate_barcodes.sort_values(by = barcodes_column)

        results.append(plate_barcodes)

    return results


# Count number of files in a directory
def count_files_in_directory(directory_path):
    directory_path = Path(directory_path)

    # Ensure the path exists and is a directory
    if not directory_path.exists():
        raise ValueError(
            f"Error: The path '{directory_path}' does not exist."
        )

    if not directory_path.is_dir():
        raise ValueError(
            f"Error: '{directory_path}' is not a directory."
        )

    # Count only files (exclude directories)
    file_count = sum(
        1 for entry in directory_path.iterdir()
        if entry.is_file()
    )

    return file_count