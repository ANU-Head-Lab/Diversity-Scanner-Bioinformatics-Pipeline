#!/bin/bash

# Stop script if something goes wrong
set -euo pipefail

# ======================================================
# User settings
# ======================================================

# Project name and plate IDs
# E.g. BLITZ_Plate1to6
PROJECT="NED_Plate1to6"

# Which step to start at?
START_STEP=6

# Directories
# Modify if required
BASE="$HOME/Diversity-Scanner-Bioinformatics-Pipeline"
SCRIPTS="$BASE/Scripts"
TESTS="$BASE/Tests"
WORKING="$BASE/Working"
ENTO_SHEETS="$WORKING/ento_sheets"
BARCODES_IDS="$WORKING/barcodes_ids"

# ======================================================
# Begin bioinformatics pipeline
# ======================================================

echo
echo "Starting bioinformatics pipeline..."
echo "Project name: ${PROJECT}"
echo

# ======================================================
# Step 6: Concatenate project plates
# ======================================================

if [ "$START_STEP" -le 6 ]; then

    echo "Step 6: Concatenating project plates..."
    echo
    sleep 1

    cd "$WORKING"

    python "$SCRIPTS"/concat_project.py \
    --input_dir "$BARCODES_IDS" \
    --output_barcodes_ids "${PROJECT}_Barcodes_IDs.xlsx" \
    --output_fasta "${PROJECT}.fasta"

fi

# ======================================================
# Step 7: Cluster into MOTUs
# ======================================================

if [ "$START_STEP" -le 7 ]; then

    sleep 1
    echo
    echo "Step 7: Clustering into MOTUs..."
    echo
    sleep 1

    cd "$WORKING"

    python "$SCRIPTS"/motu_pipeline.py \
    --input "${PROJECT}.fasta" \
    --taxonomy "${PROJECT}_Barcodes_IDs.xlsx" \
    --threshold 3 \
    --output "${PROJECT}_MOTUs_Barcodes_IDs.xlsx" \
    --verbose

    echo

fi

# ======================================================
# Step 8: Create Mastersheet
# ======================================================

if [ "$START_STEP" -le 8 ]; then

    sleep 1
    echo "Step 8: Creating mastersheet..."
    echo
    sleep 1

    cd "$WORKING"

    python "$SCRIPTS"/create_mastersheet.py \
    --input_dir "$ENTO_SHEETS" \
    --output "${PROJECT}_Mastersheet.xlsx"

    echo
    
fi

# ======================================================
# Step 9: Final Merge
# ======================================================

if [ "$START_STEP" -le 9 ]; then

    sleep 1
    echo "Step 9: Final merge..."
    echo
    sleep 1

    cd "$WORKING"

    python "$SCRIPTS"/final_merge.py \
    --input_files "${PROJECT}_Mastersheet.xlsx" \
    "${PROJECT}/${PROJECT}_MOTUs_Barcodes_IDs.xlsx" \
    --merge_columns "Specimen ID" "Sequence ID" \
    --output "${PROJECT}_Mastersheet_MOTUs_Barcodes_IDs.xlsx"

    echo
    
fi

# Remove temp files
rm taxonomy_cache.json
rm temp_output.xlsx


echo "Project analysis is complete!"


