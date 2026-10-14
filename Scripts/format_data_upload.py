#!/usr/bin/env python3

import argparse
from pathlib import Path
import pandas as pd
from helper_functions import excel_to_df

# See how much is doable just with excel formulas, versus what would be easier to do with code

################# Genbank #################

################# GBIF #################

# Input file needs to have
# Specimen ID column
# Site
# Trap
# Start date
# End date
# Sampling period length (days)
# Sampling protocol
# Sample size
# Habitat

# Additional info to provide
# Coordinates of locations

# Code should do:

#### Event data sheet
# Put date in various formats that we will need
# Create Event ID
# Fill in stuff that's always the same (e.g. country, parent Event ID, geodeticDatum)
# Map coordinates
#

### Occurrence data sheet
# Map occurrences to their associated events
# Fill in info from event data (e.g. date, location, coordinates, etc.)
# Fill in stuff that's always the same (identification info, reference database, primer info)
# Carry over DNA sequence
# Map taxonomy (highest ID, taxonRank, higher taxonomy - kingdom, phylum etc)


################# Morphbank #################

# Get image file names
# Map to specimen ID
# Get scientific names
# Map to Morphbank TSN
# Get date in yyyy-mm-dd format





def main():

    parser = argparse.ArgumentParser(
        description="Format data for uploading to a repository"
    )

    parser.add_argument(
        "--input_dir",
        required=True,
        help="Directory containing Excel sheets to convert to FASTA format"
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

