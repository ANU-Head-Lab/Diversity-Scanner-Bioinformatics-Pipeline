#!/bin/bash

# Stop script if something goes wrong
set -euo pipefail

# ======================================================
# Usage example:
# ./bioinformatics_steps3to5.sh RunName 3

# First argument = name of sequencing run to analyse
# Second argument = step to start at (between 3 and 5)
# ======================================================

# Name of sequencing run
# First command line argument
RUNNAME=$1

# Which step to start at?
# Second command line argument
START_STEP=$2

# ======================================================
# User settings
# ======================================================

# Directories
# Modify if required
BASE="$HOME/Diversity-Scanner-Bioinformatics-Pipeline"
SCRIPTS="$BASE/Scripts"
TESTS="$BASE/Tests"
WORKING="$BASE/Working"
INPUT_DIR="$WORKING/input"

# Input files
RUNINFO="$WORKING/${RUNNAME}_RunInfo.xlsx"
RUNSUMMARY="$WORKING/runsummary.xlsx"
QC_BARCODES="$WORKING/QC_Compliant_barcodes_noamb_noerr.fa"

# Other paths
# Modify if required
BOLD_DB="$HOME/BOLD_Public.04-Sep-2026.ddb"


# ======================================================
# Begin bioinformatics pipeline
# ======================================================

echo
echo "Starting bioinformatics pipeline..."
echo "Run name: ${RUNNAME}"
echo

# ======================================================
# Step 3: Sequencing summary
# ======================================================

if [ "$START_STEP" -le 3 ]; then

    echo "Step 3: Sequencing summary..."
    echo
    sleep 1

    cd "$WORKING"

    python "$SCRIPTS"/sequencing_summary.py \
    --runsummary "$RUNSUMMARY" \
    --qc_barcodes "$QC_BARCODES" \
    --num_reads_filter 500 \
    --runinfo "$RUNINFO" \
    --input_dir "$INPUT_DIR" \
    --specimen_id_column "Specimen ID" \
    --output_dir output

fi

# ======================================================
# Step 4: Assign taxonomy (BOLDigger3)
# ======================================================

if [ "$START_STEP" -le 4 ]; then

    sleep 1
    echo
    echo "Step 4: Assigning taxonomy..."
    echo
    sleep 1

    cd "$WORKING"

    boldigger3 identify "output/${RUNNAME}.fasta" "$BOLD_DB" --db 3 --mode 3

    echo "BOLD ID data saved to: ${WORKING}/output/boldigger3_data"

    echo

fi

# ======================================================
# Step 5: Merge and split
# ======================================================

if [ "$START_STEP" -le 5 ]; then

    sleep 1
    echo "Step 5: Merging data and splitting into project-specific plates..."
    echo
    sleep 1

    cd "$WORKING"

    python "$SCRIPTS"/merge_and_split.py \
    --barcodes "output/${RUNNAME}_Barcodes.xlsx" \
    --ids "output/boldigger3_data/${RUNNAME}_identification_result.xlsx" \
    --runinfo "${RUNNAME}_RunInfo.xlsx" \
    --input_dir "$INPUT_DIR" \
    --specimen_id_column "Specimen ID" \
    --output_dir output

    echo "Project-specific Barcodes and IDs saved to: output/PlateID_Barcodes_IDs.xlsx"
    echo
    
fi


echo "Analysis of sequencing run is complete!"
echo "Next step: Run project-specific analysis using bioinformatics_steps6to10.sh"
echo



