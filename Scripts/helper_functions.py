import pandas as pd
from pathlib import Path

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