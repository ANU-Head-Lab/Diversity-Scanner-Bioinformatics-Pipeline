import pandas as pd
import argparse
from pathlib import Path
from helper_functions import excel_to_df, merge_sheets, split_by_plate

# Step 1: Merge barcodes and Bold IDS for sequencing run
# Step 2: Split merged file by plate and save indiviual plate files

def main():
    parser = argparse.ArgumentParser(
        description="Merge barcodes and BOLD IDS, then split by each plate in the sequencing run"
    )
    parser.add_argument(
        "--barcodes",
        required=True,
        help="Barcodes file"
    )
    parser.add_argument(
        "--ids",
        required=True,
        help="BOLD IDs file"
    )
    parser.add_argument(
        "--runinfo",
        required=True,
        help="Output file name"
    )
    parser.add_argument(
        "--ento_sheets",
        required=True,
        help="Directory containing Entomoscope sheets for each plate in the sequencing run"
    )
    parser.add_argument(
        "--specimen_id_column",
        default="Specimen ID",
        help="Column name in ento sheets that specifies the specimen ID. Default = Specimen ID"
    )

    args = parser.parse_args()

    # Parse Run Name
    # Use this to format output file names
    runname = args.barcodes.split("_")[0]

    # Load barcodes and IDS
    barcodes = excel_to_df(args.barcodes)
    ids = excel_to_df(args.ids)

    # Merge barcodes and IDs
    merge_files = (barcodes, ids)
    merge_columns = ("Specimen ID", "id")
    
    merged = merge_sheets(merge_files, merge_columns)

    # Save merged file
    output_merged = f"{runname}_Barcodes_IDs.xlsx"
    merged.to_excel(output_merged, index=False)
    
    print(f"Merged spreadsheet saved to: {output_merged}")

    # Load runinfo 
    # Load run info
    runinfo = excel_to_df(args.runinfo)

    required_runinfo_cols = ['Plate', 'Tag']

    # Check if runinfo contains required columns
    for col in required_runinfo_cols:
        if col not in runinfo.columns:
            raise ValueError(
                f"Column '{col}' missing from runinfo file"
            )

    # Load each plate file in ento_sheets directory
    loaded = []

    for plate in runinfo['Plate']:

        filename = f"{plate}.xlsx"
        print(f"Loading plate: {plate}")

        # Load plate excel file
        plate_df = excel_to_df(f"{args.ento_sheets}/{filename}")

        loaded.append((plate_df, filename))

    # Split barcodes/IDs by plate
    plate_barcodes_ids = split_by_plate(merged, "Specimen ID", loaded, args.specimen_id_column)

    # Save plate barcode/ID files
    for i in range(len(plate_barcodes_ids)):
        plate_df, plate_name = loaded[i]

        barcodes_ids = plate_barcodes_ids[i]

        output = plate_name.replace(".xlsx", "_Barcodes_IDs.xlsx")

        barcodes_ids.to_excel(output, index = False)


if __name__ == "__main__":
    main()
