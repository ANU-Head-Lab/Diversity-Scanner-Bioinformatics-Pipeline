import pandas as pd
import argparse
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from helper_functions import merge_sheets, excel_to_df
import numpy as np

# What this script does:
# Merge Mastersheet with MOTUs/Barcodes/IDs 
# Merge by specified column
# Keep all values in both sheets
# Remove columns: CleanID, SpecimenID_file2, Blast match, final (Order, Class, order) columns
# Check that Positive controls came back as 'Apis mellifera'
# Check number of reads of negative controls, set minimum reads filter
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

mastersheet_cols_old_template = [
    'Insect no.',
    'Image code',
    'Well no.',
    'provisional ID',
    'Notes',
    'Lens',
    'Image count',
    'Image quality',
    'Image notes',
    'Person',
    'Date',
    'Time',
    'Site',
    'TrapID'
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
    'neg_control_reads',
    'reads_filter'
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

    old_template = False

    # Determine which mastersheet template is present
    if all(col in merged.columns for col in mastersheet_cols):
        mastersheet_template = mastersheet_cols

    elif all(col in merged.columns for col in mastersheet_cols_old_template):
        old_template = True
        mastersheet_template = mastersheet_cols_old_template

    else:
        missing_new = [
            col for col in mastersheet_cols
            if col not in merged.columns
        ]
        missing_old = [
            col for col in mastersheet_cols_old_template
            if col not in merged.columns
        ]
        raise ValueError(
            f"Columns do not match either mastersheet template.\n"
            f"Columns present: {merged.columns}\n"
            f"Missing from new template: {missing_new}\n"
            f"Missing from old template: {missing_old}"
        )

    # Remove unneeded columns
    merged = merged.drop(
        ["Insect no.",
        "CleanID",
        "Specimen ID_file2",
        "Blast Match",
        "Order",
        "Family",
        "Genus",
        "Species"],
        axis =1,
        errors="ignore"
    )

    # Move unknown columns to the end
    known_cols = (
        mastersheet_template +
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

    # Check positive and negative controls
    # Only do this if new template is used, for simplicity's sake

    if not old_template:

        print("\nChecking positive and negative controls...")

        # Check positive bee controls came back as 'Apis mellifera'
        bee_control_ids = ['control bee', 'bee leg', 'honey bee', 'apis mellifera', 'bee', 'positive', 'positive control', 'pos control', 'bee control']
        bee_controls = merged.loc[
            merged['Provisional ID'].str.strip().str.lower().isin(bee_control_ids)
            ]

        print(f"\n{len(bee_controls)} positive bee control samples found in file")

        incorrect = bee_controls.loc[bee_controls['species'] != 'Apis mellifera']

        if len(incorrect) > 0:
            print("Warning: Some bee controls were not identified as Apis mellifera")
            print(incorrect[['Specimen ID', 'Provisional ID', 'species']])
        elif len(bee_controls) > 0:
            print("All bee controls were identified as Apis mellifera")

        # Check positive beetle controls came back as 'Callosobruchus maculatus'
        beetle_controls_ids = ['control beetle', 'beetle', 'beetle control', 'callosobruchus maculatus', 'sea beetle']
        beetle_controls = merged.loc[
            merged['Provisional ID'].str.strip().str.lower().isin(beetle_controls_ids)
            ]

        print(f"\n{len(beetle_controls)} positive beetle control samples found in file")

        incorrect = beetle_controls.loc[beetle_controls['species'] != 'Callosobruchus maculatus']

        if len(incorrect) > 0:
            print("Warning: Some positive beetle controls were not identified as Callosobruchus maculatus")
            print(incorrect[['Specimen ID', 'Provisional ID', 'species']])
        elif len(beetle_controls) > 0:
            print("All positive beetle controls were identified as Callosobruchus maculatus")

        # Check number of reads of negative control samples
        neg_controls_ids = ['control blank', 'empty', 'blank', 'negative', 'negative control', 'neg control', 'blank control', 'empty control']
        neg_controls = merged.loc[
            merged['Provisional ID'].str.strip().str.lower().isin(neg_controls_ids)
            ]

        print(f"\n{len(neg_controls)} negative control samples found in file")
        print("Number of reads in negative control samples:")
        print(neg_controls[['Plate', 'Specimen ID', 'Provisional ID', 'Number of sequences demultiplexed']])

        # Convert reads to numeric
        reads = pd.to_numeric(
            merged["Number of sequences demultiplexed"],
            errors="coerce"
        )

        # Maximum negative-control reads per plate
        plate_neg_thresholds = (
            neg_controls
            .assign(
                reads=pd.to_numeric(
                    neg_controls["Number of sequences demultiplexed"],
                    errors="coerce"
                )
            )
            .groupby("Plate")["reads"]
            .max()
        )

        # Add neg control reads column after passed_QC column
        print("\nSetting per-plate minimum reads threshold as the maximum number of reads in a neg-control sample\n")

        idx = merged.columns.get_loc("passed_QC") + 1
        merged.insert(idx, "neg_control_reads", pd.NA)
        merged["neg_control_reads"] = merged["Plate"].map(plate_neg_thresholds)

        # Add reads_filter after neg_control_reads column
        # Leave blank if reads is blank, otherwise apply filter
        merged.insert(idx + 1, "reads_filter", pd.NA)
        merged["reads_filter"] = (
            (reads > merged["neg_control_reads"])
            .mask(reads.isna())
        )

    # Colour code 
    column_colours = {
        '#EBF1DE': mastersheet_template,
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
