import pandas as pd
import argparse
from pathlib import Path

def fasta_to_excel(fasta_file, excel_file):
    sequences = []
    with open(fasta_file, 'r') as file:
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
    
    # Convert to DataFrame
    df = pd.DataFrame(sequences)

    # Write to Excel
    df.to_excel(excel_file, index=False)

# Format name for output file based on input file name
def make_output_name(fasta_file):
    name = Path(fasta_file).stem

    if name.endswith("_Allbarcodes"):
        name = name.replace("_Allbarcodes", "_AllBarcodes")

    elif name.endswith("_Filtered_barcodes_1percamb_upto5err"):
        name = name.replace(
            "_Filtered_barcodes_1percamb_upto5err",
            "_FilteredBarcodes"
        )

    elif name.endswith("_QC_Compliant_barcodes_noamb_noerr"):
        name = name.replace(
            "_QC_Compliant_barcodes_noamb_noerr",
            "_QCBarcodes"
        )
    
    return name + ".xlsx"

# Convert all files in a directory
def process_directory(input_dir, output_dir):
    
    input_dir = Path(input_dir)
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for fasta_file in input_dir.glob("*.fa"):
        excel_file = make_output_name(fasta_file)

        fasta_to_excel(
            fasta_file=str(fasta_file),
            excel_file=str(output_dir / excel_file)
        )

        print(f"Processed: {fasta_file.name} -> {excel_file}")

# MAIN
def main():
    parser = argparse.ArgumentParser(
        description="Convert fasta file to excel"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input fasta file to convert. Or, if --directory flag is set, input directory to process"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Name for output Excel spreadsheet. Or, if --directory flag is set, output directory name"
    )
    parser.add_argument(
        "--directory",
        action="store_true",
        help="Process all fasta files in a directory"
    )

    args = parser.parse_args()

    if args.directory:
        process_directory(args.input, args.output)
    else:
        fasta_to_excel(args.input, args.output)

if __name__ == "__main__":
    main()
