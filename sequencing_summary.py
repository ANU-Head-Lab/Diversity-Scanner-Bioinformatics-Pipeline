#!/usr/bin/env python3

import argparse
from pathlib import Path
import pandas as pd

# Load dataframe from given excel file
# Specify sheet name. If not provided, take first sheet
def excel_to_df(filename, sheet = 0):
    path = Path(filename)

    # Throw error if file not found
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filename}")

    df = pd.read_excel(path, sheet_name = sheet)
    return df

def main():
    parser = argparse.ArgumentParser(
        description="Generate summary statistics for sequencing run"
    )

    # Arguments passed in through command line

    parser.add_argument(
        "--runsummary",
        required=True,
        help="Summary file containing barcodes for an entire sequencing run"
    )
    parser.add_argument(
        "--runsummary_sheet",
        default=0,
        help="Sheet in runsummary file that contains barcodes. Default = 0"
    )
    parser.add_argument(
        "--runinfo",
        required=True,
        help="Excel file containing list of plates in the sequencing run and their corresponding tag names"
    )
    parser.add_argument(
        "--specimen_id_column",
        default="Specimen ID",
        help="Column name in Plate Excel file that specifies the specimen ID. Default = Specimen ID"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Name for output spreadsheet"
    )

    args = parser.parse_args()

    # Load run summary
    runsummary = excel_to_df(args.runsummary, sheet=args.runsummary_sheet)

    # Load run info
    runinfo = excel_to_df(args.runinfo)

    required_runinfo_cols = ['Plate', 'Tag']

    # Check if runinfo contains required columns
    for col in required_runinfo_cols:
        if col not in runinfo.columns:
            raise ValueError(
                f"Column '{col}' missing from runinfo file"
            )
    
    summary_stats = []

    # Go through each plate in the runinfo file
    for plate in runinfo['Plate']:

        filename = f"{plate}.xlsx"
        print(f"Loading plate: {plate}")

        # Load plate excel file
        plate_df = excel_to_df(filename)

        # Get specimen IDS
        id = args.specimen_id_column
        if id not in plate_df.columns:
            raise ValueError(f"{id} column not found in {filename}")
        specimen_ids = plate_df[id]
        print(specimen_ids)

        # Split runsummary per plate
        if 'SpecimenID' not in runsummary.columns:
            raise ValueError(
                "'SpecimenID' column not found in runsummary"
                )
        plate_barcodes = runsummary[runsummary['SpecimenID'].isin(specimen_ids)]

        # Sort by specimen ID
        plate_barcodes = plate_barcodes.sort_values(by="SpecimenID")

        # Save plate barcodes
        output_filename = f"{plate} barcodes.xlsx"
        plate_barcodes.to_excel(
            output_filename,
            index=False
        )

        print(f"Saved: {output_filename}")

        # Summary statistics
        num_input = len(specimen_ids)
        num_output = len(plate_barcodes)

        reads = plate_barcodes['Number of sequences demultiplexed']
        min_reads = reads.min()
        max_reads = reads.max()
        median_reads = reads.median()
        sd_reads = reads.std()

        # If barcodes contains passed_QC column
        if ('passed_QC' in plate_barcodes.columns):
            filtered_barcodes = plate_barcodes[
                (plate_barcodes['passed_QC'] == "TRUE" )
                ]

        # Otherwise, calculate QC-compliant barcodes manually
        # No ambiguities, no errors, translation check = 1
        else:
            filtered_barcodes = plate_barcodes[
                (plate_barcodes['type'] == "correct" | plate_barcodes['type'] == "removed 0 indels") & 
                (plate_barcodes['#ambiguities'].astype(int) == 0) &
                (plate_barcodes['#translation check'].astype(int) == 1)
                ]

        num_filt = len(filtered_barcodes)

        # Write to summary statistics
        summary_stats.append(
            {
                "Plate": plate,
                "Num specimens": num_input,
                "Num barcodes obtained": num_output,
                "Num QC-compliant barcodes": num_filt,
                "Min reads": min_reads,
                "Max reads": max_reads,
                "Median reads": median_reads,
                "SD reads": sd_reads
            }
        )
    
    # Save summary statistics
    summary_df = pd.DataFrame(summary_stats)
    summary_df.to_excel(
        args.output,
        index=False
        )
        
if __name__ == "__main__":
    main()


