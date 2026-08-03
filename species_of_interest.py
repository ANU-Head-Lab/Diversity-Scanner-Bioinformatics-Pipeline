#!/usr/bin/env python3

import argparse
from pathlib import Path
import pandas as pd
import numpy as np

# Load dataframe from given excel file
# Specify sheet name, if not provided, take first sheet
def excel_to_df(filename, sheet = 0):
    path = Path(filename)

    # Throw error if file not found
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filename}")

    df = pd.read_excel(path, sheet_name = sheet)
    return df


def search_project(project, threatened_species, pest_species):

    # Normalise spacing and capitalisation in project columns
    project.columns = project.columns.str.strip().str.lower()

    # Check if project file contains 'species' column
    if 'species' not in project.columns:
        raise ValueError("'species' column missing from project file")
    
    # Normalise spacing and capitalisation in species lists
    project['species_norm'] = (
        project['species']
        .astype(str)
        .str.strip()
        .str.lower()
    )
    threatened_species = set(
        threatened_species
        .astype(str)
        .str.strip()
        .str.lower()
    )
    pest_species = set(
        pest_species
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # Add column to flag threatened or pest species
    project['threatened_flag'] = np.where(
        project['species_norm'].isin(threatened_species),
        'Threatened',
        ''
    )
    project['pest_flag'] = np.where(
        project['species_norm'].isin(pest_species),
        'Pest',
        ''
    )

    project.drop(columns = ['species_norm'], inplace = True)

    return project
    


def main():
    parser = argparse.ArgumentParser(
        description="Search through project data file and identify species of interest"
    )

    # Arguments passed in through command line

    parser.add_argument(
        "--input_dir",
        required=True,
        help="Directory containing project data files to search"
    )

    parser.add_argument(
        "--output_dir",
        required=True,
        help="Directory to save output files"
    )
    
    parser.add_argument(
        "--species_of_interest",
        required=True,
        help="Threatened species database"
    )

    args = parser.parse_args()

    threatened = excel_to_df(args.species_of_interest, sheet = "Threatened invertebrate species")
    threatened_species = threatened['Scientific name']

    pests = excel_to_df(args.species_of_interest, sheet = "National priority pest species")
    pest_species = pests['Scientific name']

    # Check if input directory exists, and is a directory
    input_dir = Path(args.input_dir)
        
    if not input_dir.exists():
        raise ValueError(f"{input_dir} does not exist.")
            
    if not input_dir.is_dir():
        raise ValueError(f"{input_dir} is not a directory.")

    # Verify output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents = True, exist_ok = True)
        
    # Load spreadsheet for each project file in input directory
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

    # Search project files for threatened and pest species
    for project, filename in loaded:
        searched = search_project(project, threatened_species, pest_species)

        project_threatened = searched[
            searched['threatened_flag'] == 'Threatened'
        ]

        print(f"Number of threatened species found: {len(project_threatened)}")

        # Save threatened species 
        if (len(project_threatened) > 0):
            output = output_dir / f"{Path(filename).stem}_threatened.xlsx"
            project_threatened.to_excel(output, index = False)
            print(f"Saving threatened species to: {output}")

        project_pests = searched[
            searched['pest_flag'] == 'Pest'
        ]
        print(f"Number of pest species found: {len(project_pests)}")

        # Save pest species
        if(len(project_pests) > 0):
            output = output_dir / f"{Path(filename).stem}_pests.xlsx"
            project_pests.to_excel(output, index = False)
            print(f"Saving pest species to: {output}")

        # Save flagged output file
        output = output_dir / f"{Path(filename).stem}_flagged.xlsx"
        searched.to_excel(
            output,
            index = False
        )
        print(f"Saving flagged project file to: {output}")


if __name__ == "__main__":
    main()


