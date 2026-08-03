#!/usr/bin/env python3

# What this script does:
# Takes runsummary.xlsx and QC_compliant_barcodes_noamb_noerr.fa
# Adds two columns to runsummary.xlsx specifying whether each barcode passed QC, and whether
# it meets the minimum number of reads threshold

# QC compliant if:
# No ambiguities
# No indels
# Is translatable
# Has expected barcode length

import argparse
from pathlib import Path
import pandas as pd

# Load dataframe from given excel file
# Specify sheet name, if not provided, take first sheet
def excel_to_df(filename, sheet = 0):
    path = Path(filename)

    # Throw error if file not found
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filename}")

    df = pd.read_excel(path, sheet_name = sheet)
    return df

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
        description="Check which barcodes in runsummary.xlsx pass ONTbarcoder QC"
    )

    # Arguments passed in through command line
    parser.add_argument(
        "--all_barcodes",
        required=True,
        help="Excel file containing barcodes for all specimens"
    )

    parser.add_argument(
        "--qc_barcodes",
        required=True,
        help="FASTA file containing only QC-compliant barcodes"
    )

    # parser.add_argument(
    #     "--barcode_length",
    #     type=int,
    #     required=True,
    #     help="Expected length of amplicons"
    # )

    parser.add_argument(
        "--num_reads_filter",
        type=int,
        required=True,
        help="Filter for minimum number of reads"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Name for output excel file"
    )

    args = parser.parse_args()

    allbarcodes = excel_to_df(args.all_barcodes, sheet = "3.Final barcodes")
    qcbarcodes = fasta_to_df(args.qc_barcodes)

    # Get IDs of QC-compliant specimens
    qc_ids = set(qcbarcodes["SpecimenID"].astype(str))

    # Check if each barcode passed QC
    allbarcodes["passed_QC"] = allbarcodes["SpecimenID"].astype(str).isin(qc_ids)

    # Can we just manually check the same conditions without needing the QC barcodes file?
    # allbarcodes["passed_QC_test"] = (
    #     ((allbarcodes["type"] == "correct") | (allbarcodes["type"] == "removed 0 indels")) &
    #     (allbarcodes["length"].astype(int) == args.barcode_length) &
    #     (allbarcodes["translation check"].astype(int) == 1) &
    #     (allbarcodes["#ambiguities"].astype(int) == 0)
    # )

    # Check if barcode passes minimum number of demultiplexed reads
    allbarcodes["num_reads_filter"] = (allbarcodes["Number of sequences demultiplexed"].astype(int) >= args.num_reads_filter)

    # Save output file
    allbarcodes.to_excel(args.output, index = False)


if __name__ == "__main__":
    main()

