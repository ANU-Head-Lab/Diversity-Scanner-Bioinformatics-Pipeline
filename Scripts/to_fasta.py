#!/usr/bin/env python3

import argparse
from pathlib import Path
import pandas as pd
from helper_functions import excel_to_df

# Convert excel files to FASTA files
# Excel files should contain Specimen ID and barcode columns

def main():

    parser = argparse.ArgumentParser(
        description="Convert Excel files to FASTA."
    )

    parser.add_argument(
        "--input_dir",
        required=True,
        help="Directory containing Excel sheets to convert to FASTA format"
    )

    parser.add_argument(
        "--specimen_id_column",
        default="Specimen ID",
        help="Column name in ento sheets that specifies the specimen ID. Default = Specimen ID"
    )

    parser.add_argument(
        "--output_dir",
        required = True,
        help="Output directory name"
    )

    args = parser.parse_args()

    input_dir = Path(args.input_dir)

    if not input_dir.exists():
        raise ValueError(f"{input_dir} does not exist.")
        
    if not input_dir.is_dir():
        raise ValueError(f"{input_dir} is not a directory.")
    

    # Make output directory if it doesn't exist
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # Load files in input directory

    loaded = []

    for file in sorted(input_dir.glob("*.xlsx")):
        df = excel_to_df(file)
    
        print(f"Loaded: {file.name} ({len(df)} rows)")
        loaded.append((df, file.name))
    
    # If no input files found
    if not loaded:
        raise ValueError(
            f"No .xlsx files found in {input_dir}"
        )

    # Create FASTA file

    for df, filename in loaded:

        fasta_df = df[[args.specimen_id_column, "barcode"]]
        output_fasta = f"{args.output_dir}/{Path(filename).stem}.fasta"

        with open(output_fasta, "w") as fasta:
            for _, row in fasta_df.iterrows():
                fasta.write(f">{row[args.specimen_id_column]}\n")
                fasta.write(f"{row['barcode']}\n")

        print("Saved FASTA file.")
        print(f"Output: {output_fasta}")

if __name__ == "__main__":
    main()

