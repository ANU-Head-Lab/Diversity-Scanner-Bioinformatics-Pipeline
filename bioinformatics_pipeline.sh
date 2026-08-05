#!/bin/bash

# Stop script if something goes wrong
set -euo pipefail

# ======================================================
# User settings
# ======================================================

RUNNAME="2Jul26"

# Which step to start at?
START_STEP=1

# Directories
# Modify if required
BASE="$HOME/Diversity-Scanner-Bioinformatics-Pipeline"
SCRIPTS = "$BASE/Scripts"
TESTS = "$BASE/Tests"
WORKING = "$BASE/Working"

# Input files
RUNINFO = 
RUNSUMMARY =
QC_BARCODES = 

# Other paths
# Modify if required
BOLD_DB="$HOME/BOLD_Public.10-Jul-2026.ddb"




# ======================================================
# Begin pipeline
# ======================================================

echo
echo "Starting bioinformatics pipeline..."
echo "Run name: ${RUNNAME}"
echo

# ======================================================
# Step 1: Sequencing summary
# ======================================================

if [ "$START_STEP" -le 1 ]; then

    

fi

# ======================================================
# Step 2: Filter reads using vsearch
# ======================================================

if [ "$START_STEP" -le 2 ]; then

    echo "Step 2: Filtering reads..."
    echo
    sleep 3

    cd "$BASE"

    # Modify parameters if required
    for f in "$DEMUX"/*.fastq; do
        base=$(basename "$f" .fastq)
        base="${base#sample_}"
        vsearch \
        --fastq_filter "$f" \
        --fastq_maxlen 338 \
        --fastq_minlen 288 \
        --fastq_maxee_rate 0.02 \
        --fastq_maxns 0 \
        --fastq_qmax 93 \
        --fastaout "${FILT}/${base}_filtered.fasta" \
        --fastaout_discarded "${DISC}/${base}_discarded.fasta"
    done

    # Generate filtering summary
    echo
    echo "Generating filtering summary..."
    echo

    cd "$FILT"

    echo "sample_id,filtered_reads,discarded_reads" > "${RUNNAME}_filtering_summary.csv"
    for f in *_filtered.fasta; do
        sample=$(basename "$f" _filtered.fasta)
        filtered=$(grep -c '^>' "$f" || true)

        discarded_file="${DISC}/${sample}_discarded.fasta"
        discarded=0
        [ -f "$discarded_file" ] && discarded=$(grep -c '^>' "$discarded_file" || true)

        echo "$sample,$filtered,$discarded" >> "${RUNNAME}_filtering_summary.csv"
    done

fi

# ======================================================
# Step 3: Dereplicate sequences using vsearch
# ======================================================

if [ "$START_STEP" -le 3 ]; then

    echo "Step 3: Dereplicating sequences..."
    echo
    sleep 3

    cd "$BASE"

    # Modify parameters if required
    for f in "$FILT"/*.fasta; do
        base=$(basename "$f" _filtered.fasta)
        vsearch \
        --fastx_uniques "$f" \
        --sizeout \
        --strand both \
        --fastaout "${DEREP}/${base}_derep.fasta"
    done

    # Generate dereplication summary
    echo
    echo "Generating dereplication summary..."
    echo

    cd "$DEREP"

    echo "sample_id,derep_seqs" > "${RUNNAME}_derep_summary.csv"
    for f in *_derep.fasta; do
        sample=$(basename "$f" _derep.fasta)
        seqs=$(grep -c '^>' "$f" || true)
        echo "$sample,$seqs" >> "${RUNNAME}_derep_summary.csv"
    done

fi

# ======================================================
# Step 4: Cluster sequences using vsearch
# ======================================================

if [ "$START_STEP" -le 4 ]; then

    echo "Step 4: Clustering sequences..."
    echo

    cd "$BASE"

    # If CLUST_METHOD set to 1
    if [ "$CLUST_METHOD" -le 1 ]; then

        echo "Clustering method 1: Fixed identity threshold"
        echo
        sleep 3

        # Modify parameters if required
        for f in "$DEREP"/*.fasta; do
            base=$(basename "$f" _derep.fasta)
            vsearch \
            --cluster_size "$f" \
            --id 0.97 \
            --minsize 1 \
            --sizein \
            --sizeout \
            --strand both \
            --clusterout_id \
            --clusterout_sort \
            --centroids "${CLUST}/${base}_clustered.fasta"
        done
    
    fi

    # If CLUST_METHOD set to 2
    if [ "$CLUST_METHOD" -le 2 ]; then

        echo "Clustering method 2: UNOISE algorithm"
        echo
        sleep 3

        # Modify parameters if required
        for f in "$DEREP"/*.fasta; do
            base=$(basename "$f" _derep.fasta)
            vsearch \
            --cluster_unoise "$f" \
            --minsize 1 \
            --sizein \
            --sizeout \
            --strand both \
            --clusterout_id \
            --clusterout_sort \
            --centroids "${CLUST}/${base}_clustered.fasta"
        done

    fi

    # Generate clustering summary
    echo
    echo "Generating clustering summary..."
    echo

    cd "$CLUST"

    echo "sample_id,clusters" > "${RUNNAME}_clustering_summary.csv"
    for f in *_clustered.fasta; do
        sample=$(basename "$f" _clustered.fasta)
        clusters=$(grep -c '^>' "$f" || true)
        echo "$sample,$clusters" >> "${RUNNAME}_clustering_summary.csv"
    done

fi

# ======================================================
# Step 5: Remove chimeras using vsearch
# ======================================================

if [ "$START_STEP" -le 5 ]; then

    echo "Step 5: Removing chimeras..."
    echo
    sleep 3

    cd "$BASE"

    for f in "$CLUST"/*.fasta; do
        base=$(basename "$f" _clustered.fasta)
        vsearch \
        --uchime3_denovo "$f" \
        --sizein \
        --sizeout \
        --nonchimeras "${NOCHIM}/${base}_nochim.fasta" \
        --chimeras "${CHIM}/${base}_chim.fasta"
    done

    echo

fi

# ======================================================
# Step 6: Filter and merge top clusters
# ======================================================

if [ "$START_STEP" -le 6 ]; then

    echo "Step 6: Filtering and merging top clusters..."
    sleep 2
    echo
    echo "Filtering out top clusters..."
    echo
    sleep 3

    cd "$BASE"

    # Modify parameters if required
    for f in "$NOCHIM"/*.fasta; do     
        base=$(basename "$f" _nochim.fasta);      
        vsearch \
        --fastx_filter "$f" \
        --minsize 5 \
        --fastaout "${TOPCLUST}/${base}_topclusters.fasta" 
    done

    echo
    echo "Merging clusters for all samples..."
    echo
    sleep 3

    cd "$TOPCLUST"

    for f in *_topclusters.fasta; do
        sample=$(basename "$f" _topclusters.fasta)
        awk -v sample="$sample" '
        /^>/ {
            match($0, /clusterid=[0-9]+/)
            cid=substr($0, RSTART, RLENGTH)

            match($0, /size=[0-9]+/)
            sz=substr($0, RSTART, RLENGTH)

            print ">sample=" sample ";" cid ";" sz
            next
        }
        { print }
        ' "$f"
    done > "${CONCAT}/${RUNNAME}_clustered.fasta"

fi

# ======================================================
# Step 7: Identify clusters using BOLD
# ======================================================

if [ "$START_STEP" -le 7 ]; then

    echo "Step 7: Identifying clusters..."
    echo
    sleep 2

    cd "$CONCAT"

    boldigger3 identify "${RUNNAME}_clustered.fasta" "$BOLD_DB" --db 3 --mode 3

    mv boldigger3_data "$IDENT"

    echo

fi

# ======================================================
# Step 8: Merge data
# ======================================================

if [ "$START_STEP" -le 8 ]; then

    echo "Step 8: Merging data..."
    echo
    sleep 1

    # Convert concatenated clusters FASTA file to Excel file
    # Using metabarcoding_fasta_to_excel.py

    echo "Converting clustered barcodes from FASTA to Excel..."
    echo
    sleep 1

    cd "$CONCAT"
    python "$FASTA_TO_EXCEL" \
    --input "${RUNNAME}_clustered.fasta" \
    --output "${RUNNAME}_clustered.xlsx"

    # Merge mastersheet, clustered barcodes, and identifications into one Excel file

    echo "Merging mastersheet, barcodes, and identifications..."
    echo
    sleep 1

    cd "$IDENT"
    python "$MERGE_SHEETS" \
    --mastersheet "$MASTERSHEET" \
    --barcodes "$CONCAT/${RUNNAME}_clustered.xlsx" \
    --identification "$IDENT/boldigger3_data/${RUNNAME}_clustered_identification_result.xlsx" \
    --output "$MERGED/${RUNNAME}_merged.xlsx"

    # Generate final summary

    echo
    echo "Generating final summary..."
    echo
    sleep 1

    cd "$BASE"

    echo "sample_id,demultiplexed,filtered,dereplicated,clustered,no_chimeras" \
    > "${RUNNAME}_final_summary.csv"

    for f in ${DEMUX}/*.fastq; do
        sample=$(basename "$f" .fastq | cut -d'_' -f2-)

        demux=$(($(wc -l < "$f") / 4))

        filt_file="${FILT}/${sample}_filtered.fasta"
        derep_file="${DEREP}/${sample}_derep.fasta"
        cluster_file="${CLUST}/${sample}_clustered.fasta"
        nochim_file="${NOCHIM}/${sample}_nochim.fasta"

        filtered=0
        derep=0
        clustered=0
        nochim=0

        [ -f "$filt_file" ] && filtered=$(grep -c '^>' "$filt_file" || true)
        [ -f "$derep_file" ] && derep=$(grep -c '^>' "$derep_file" || true)
        [ -f "$cluster_file" ] && clustered=$(grep -c '^>' "$cluster_file" || true)
        [ -f "$nochim_file" ] && nochim=$(grep -c '^>' "$nochim_file" || true)

        echo "${sample},${demux},${filtered},${derep},${clustered},${nochim}" \
        >> "${RUNNAME}_final_summary.csv"

    done

fi
 
echo "Metabarcoding pipeline complete!"
echo



