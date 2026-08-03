import pandas as pd
import argparse
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

# What this script does:
# Merge Mastersheet with MOTUs/Barcodes/IDs 
# Merge by specified column
# Keep all values in both sheets
# Remove columns: CleanID, SpecimenID_file2, Blast match, final (Order, Class, order) columns
# Colour-code columns

# Columns
mastersheet_cols = [
    'Specimen ID',
    'Plate',
    'Well',
    'Provisional ID',
    'Lens',
    'Image count',
    'Person',
    'Site',
    'Trap ID',
    'Date',
    'Time',
    'Notes'
]

motu_cols = [
    'Unique Seq ID',
    'MOTU (OTU97%)',
    'MOTU (SWARM)',
    'Consensus MOTU'
]

barcodes_cols = [
    'Number of sequences demultiplexed',
    'Number used for generating barcodes',
    'stage',
    'type',
    'length',
    'barcode',
    'translation check',
    '#ambiguities',
    'passed_QC',
    'num_reads_filter'
]

bold_cols = [
    'phylum',
    'class',
    'order',
    'family',
    'genus',
    'species',
    'pct_identity',
    'status',
    'records',
    'records_ratio',
    'selected_level',
    'BIN',
    'flags'
]

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

    # Remove unneeded columns
    merged = merged.drop(
        ["CleanID",
        "Specimen ID_file2",
        "Blast Match",
        "Order",
        "Family",
        "Genus",
        "Species"],
        axis =1
    )

    # Move unknown columns to the end
    known_cols = (
        mastersheet_cols +
        motu_cols +
        barcodes_cols +
        bold_cols
    )

    other_cols = [col for col in merged.columns if col not in known_cols]

    if other_cols:
        print("Columns not matching template: ", other_cols)
        print("Moving unknown columns to the end of dataframe.")

    ordered_cols = [col for col in merged.columns if col in known_cols] + other_cols

    merged = merged[ordered_cols]

    # Colour code

    # Mastersheet = #EBF1DE
    # MOTUs = #DAEEF3
    # Barcodes = #F2DCDB
    # BOLD = #E4DFEC
    # Other = #D9D9D9 (and move to end)
    
    column_colours = {
        '#EBF1DE': mastersheet_cols,
        '#DAEEF3': motu_cols,
        '#F2DCDB': barcodes_cols,
        '#E4DFEC': bold_cols,
        '#D9D9D9': other_cols
        }

    # Save dataframe
    merged.to_excel("temp_output.xlsx", index=False)    

    # Re-open workbook
    wb = load_workbook("temp_output.xlsx")
    ws = wb.active

    # Build lookup: column name -> fill object
    fill_lookup = {}

    for colour, cols in column_colours.items():
        fill = PatternFill(
            fill_type='solid',
            fgColor=colour.replace('#', '')
        )
        for col in cols:
            fill_lookup[col] = fill

    # Colour columns
    for header_cell in ws[1]:
        if header_cell.value not in fill_lookup:
            continue

        fill = fill_lookup[header_cell.value]

        for row in range(1, ws.max_row + 1):
            ws.cell(row=row, column=header_cell.column).fill = fill

    output_path = Path(args.output)

    if output_path.suffix.lower() != ".xlsx":
        raise ValueError("Output file must have .xlsx extension")

    # Save merged file
    wb.save(output_path)
    
    print(f"Merged spreadsheet saved to: {output_path}")

if __name__ == "__main__":
    main()