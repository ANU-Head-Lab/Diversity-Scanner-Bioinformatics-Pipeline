#!/usr/bin/env python3

import argparse
from pathlib import Path
import pandas as pd
from helper_functions import excel_to_df

# Format Entomoscope sheet to match new template

# Reference column names 

reference_columns = [
    "Specimen ID",
    "Plate",
    "Well",
    "Provisional ID",
    "Lens",
    "Image count",
    "Person",
    "Site",
    "Trap ID",
    "Date",
    "Time",
    "Notes"
]

old_columns = [
    "Insect no.",
    "Image code",
    "Well no.",
    "Tag",
    "Tag",
    "provisional ID",
    "Notes",
    "Lens",
    "Image count",
    "Image quality",
    "Image notes",
    "Person",
    "Date",
    "Time",
    "Site",
    "Trap_ID"
]

### DEFINE FUNCTIONS ###

def combine_notes_columns(df, filename):

    # Convert notes columns to type string
    df["Notes"] = df["Notes"].astype("string")
    df["Imagequality"] = df["Imagequality"].astype("string")
    df["Imagenotes"] = df["Imagenotes"].astype("string")

    for idx, row in df.iterrows():

        notes = row.get("Notes")
        image_quality = row.get("Imagequality")
        image_notes = row.get("Imagenotes")

        # Collect non-empty values from Image quality and Image notes
        extras = []

        if pd.notna(image_quality) and str(image_quality).strip():
            extras.append(str(image_quality))

        if pd.notna(image_notes) and str(image_notes).strip():
            extras.append(str(image_notes))

        if not extras:
            continue

        extra_text = "; ".join(extras)

        # If notes is empty, populate it
        if pd.isna(notes) or not str(notes).strip():
            df.at[idx, "Notes"] = extra_text

        # If notes already contains something, append and warn
        else:
            print(
                f"WARNING: {filename}, row {idx + 2}: "
                f"'Notes' already contains data. Appending Image quality/Image notes."
            )

            df.at[idx, "Notes"] = f"{notes}; {extra_text}"

    # Remove Image quality and Image notes
    df = df.drop(columns={
        "Imagequality",
        "Imagenotes"
    })
    
    # Move notes to the end
    col = df.pop("Notes")
    df["Notes"] = col

    return df


def format_df(df, filename):

    print("")
    print(f"Processing file: {filename}")

    # Remove white spaces from column names
    df.columns = df.columns.str.replace(" ", "")

    # Delete columns
    df = df.drop(columns={
        "Insectno.",
        "Tag"
    })
    
    # Rename columns
    df = df.rename(columns={
        "Imagecode": "Specimen ID",
        "Wellno.": "Well",
        "provisionalID": "Provisional ID",
        "Imagecount" : "Image count",
        "Trap_ID": "Trap ID"
    })

    # Extract plate number from file name "Project Plate 1.xlsx"
    plate_num = (filename.split(".")[0]).split(" ")[2]

    # Insert Plate number column
    df.insert(1, "Plate", plate_num)

    # Combine Notes, Image quality, and Image notes
    df = combine_notes_columns(df, filename)

    # Move "Site" and "Trap ID" before "Date" and "Time"
    site = df.pop("Site")
    trap = df.pop("Trap ID")
    df.insert(7, "Site", site)
    df.insert(8, "Trap ID", trap)

    print("")
    print(f"Fixed formatting. New column names: {df.columns.tolist()}")

    return df


def main():
    parser = argparse.ArgumentParser(
        description="Format entomoscope sheets."
    )

    parser.add_argument(
        "--input_dir",
        required=True,
        help="Directory containing Entomoscope sheets to format"
    )

    parser.add_argument(
        "--output_dir",
        required=True,
        help="Directory for output files"
    )

    args = parser.parse_args()

    # Check if input directory exists, and is a directory
    input_dir = Path(args.input_dir)
    
    if not input_dir.exists():
        raise ValueError(f"{input_dir} does not exist.")
        
    if not input_dir.is_dir():
        raise ValueError(f"{input_dir} is not a directory.")

    # Create output directory if it doesn't exist
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load spreadsheet for each Entomoscope sheet in input directory

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
    
    # Format each file
    for df, filename in loaded:
        # First, check if input file has expected old template column names
        cols = df.columns.str.replace(" ", "").tolist()
        template_cols = [col.replace(" ", "") for col in old_columns]

        if (cols != template_cols):
            message = f"Unexpected column names in input dataframe. Manual reformatting may be required. \
            \nColumns in input dataframe: {df.columns.tolist()} \
            \nTemplate columns: {old_columns}"
            
            raise ValueError(message)

        formatted = format_df(df, filename)

        output_file = f"{args.output_dir}/{filename}"

        formatted.to_excel(output_file, index=False)
    
    

if __name__ == "__main__":
    main()
