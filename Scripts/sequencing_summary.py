#!/usr/bin/env python3

import argparse
from pathlib import Path
import pandas as pd
from helper_functions import excel_to_df, split_by_plate

# Create final barcodes file and FASTA file for sequencing run

# Step 1: QC filter 
# Step 2: Format final barcodes file
# Step 3: Summary statistics for each plate
# Step 4: Make FASTA

# Inputs:
# runsummary.xlsx
# RunInfo.xlsx
# Entomoscope sheets for each plate

# Load dataframe from given FASTA file
# Expects headers to look like this: >SAMPLENAME_all.fa;658;25;ambs=0;estgaps=0
def fasta_to_df(filename):
    sequences = []
    with open(filename, 'r') as file:
        sequence_data = {}
        for line in file:
            if line.startswith(">"):
                if sequence_data:
                    sequences.append(sequence_data)
                # Remove leading '>'            
                header = line.strip().lstrip(">")
                # Split header by semicolons
                parts = header.split(";")
                if len(parts) < 4:
                    raise ValueError(
                    f"Unexpected FASTA header format: {header}"
                )
                sequence_data = {
                    "SpecimenID": parts[0].replace("_all.fa", ""),
                    "Number used for generating barcodes": int(parts[2]),
                    "length": int(parts[1]),
                    "barcode": "",
                    "#ambiguities": int(parts[3].replace("ambs=", ""))
                    }
            else:
                sequence_data["barcode"] += line.strip()
        if sequence_data:
            sequences.append(sequence_data)
    
    # Return dataframe
    df = pd.DataFrame(sequences)
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Process barcodes for sequencing run"
    )

    parser.add_argument(
        "--runsummary",
        required=True,
        help="Excel file containing barcodes for all specimens"
    )
    
    parser.add_argument(
        "--qc_barcodes",
        required=True,
        help="FASTA file containing only QC-compliant barcodes"
    )

    parser.add_argument(
        "--num_reads_filter",
        type=int,
        required=True,
        help="Filter for minimum number of reads"
    )

    parser.add_argument(
        "--runinfo",
        required=True,
        help="Excel file containing list of plates in the sequencing run and their corresponding tag names"
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

    # Parse Run Name from RunInfo file
    # Use this to format output file names
    runname = args.runinfo.split("_")[0]

    ### STEP 1: QC filter

    runsummary = excel_to_df(args.runsummary, sheet = "3.Final barcodes")
    qcbarcodes = fasta_to_df(args.qc_barcodes)

    # Get IDs of QC-compliant specimens
    qc_ids = set(qcbarcodes["SpecimenID"].astype(str))

    # Check if each barcode passed QC
    runsummary["passed_QC"] = runsummary["SpecimenID"].astype(str).isin(qc_ids)

    # Check if barcode passes minimum number of demultiplexed reads
    runsummary["num_reads_filter"] = (runsummary["Number of sequences demultiplexed"].astype(int) >= args.num_reads_filter)

    ### STEP 2: Format barcodes file

    # Rename SpecimenID to Specimen ID
    runsummary.rename(
        columns={"SpecimenID": "Specimen ID"}, 
        inplace=True
        )
    
    # Add empty "Blast Match" column at index 1 (between column A and B)
    runsummary.insert(1, "Blast Match", "")

    # Save barcodes file
    output_barcodes = f"{runname}_Barcodes.xlsx"

    runsummary.to_excel(output_barcodes, index = False)

    print("Saved barcodes file.")
    print(f"Output: {output_barcodes}")

    ### STEP 3: Summary statistics for each plate

    # Load run info
    runinfo = excel_to_df(args.runinfo)

    required_runinfo_cols = ['Plate', 'Tag']

    # Check if runinfo contains required columns
    for col in required_runinfo_cols:
        if col not in runinfo.columns:
            raise ValueError(
                f"Column '{col}' missing from runinfo file"
            )

    loaded = []

    # Load ento sheet for each plate in runinfo file
    for plate in runinfo['Plate']:

        filename = f"{plate}.xlsx"
        print(f"Loading plate: {plate}")

        # Load plate excel file
        plate_df = excel_to_df(f"{args.ento_sheets}/{filename}")

        loaded.append((plate_df, filename))

    # Split runsummary by plate
    plate_barcodes = split_by_plate(runsummary, "Specimen ID", loaded, args.specimen_id_column)

    # Summary statistics for each plate
    summary_stats = []

    for i in range(len(loaded)):

        plate_df, plate_name = loaded[i]
        plate_barcodes_df = plate_barcodes[i]

        # Summary statistics
        num_input = len(plate_df)
        num_output = len(plate_barcodes_df)

        reads = plate_barcodes_df['Number of sequences demultiplexed']
        min_reads = reads.min()
        max_reads = reads.max()
        median_reads = reads.median()
        sd_reads = reads.std()

        filtered_barcodes = plate_barcodes_df[(plate_barcodes_df['passed_QC'])]
        num_filt = len(filtered_barcodes)

        # Write to summary statistics
        summary_stats.append(
            {
                "Plate": plate_name.replace(".xlsx", ""),
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

    output_summary = f"{runname}_SequencingSummary.xlsx"

    summary_df.to_excel(
        output_summary,
        index=False
        )

    print("Saved summary statistics for sequencing run.")
    print(f"Output: {output_summary}")

    ### STEP 4: Create FASTA file

    fasta_df = runsummary[["Specimen ID", "barcode"]]

    output_fasta = f"{runname}.fasta"

    with open(output_fasta, "w") as fasta:
        for _, row in fasta_df.iterrows():
            fasta.write(f">{row['Specimen ID']}\n")
            fasta.write(f"{row['barcode']}\n")

    print("Saved FASTA file.")
    print(f"Output: {output_fasta}")



if __name__ == "__main__":
    main()

