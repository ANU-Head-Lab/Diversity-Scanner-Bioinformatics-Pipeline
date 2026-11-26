# Diversity-Scanner-Bioinformatics-Pipeline
Post-sequencing bioinformatics workflow for the CBA Diversity Scanner project. In brief, this involves demultiplexing, generating consensus barcodes, quality filtering, assigning taxonomy, and clustering into MOTUs.

## Workflow

|Step|Step name|Program/Script|Description|
|-|-|-|-|
|1|Create demultiplexing file|create_ont_input.py|Create a file with the Specimen ID and tag/primer sequences for each sample in the sequencing run|
|2|Demultiplexing & consensus barcodes|ONTbarcoder|Demultiplex & generate consensus barcodes
|3|Sequencing summary|sequencing_summary.py|Step 1: Flag which barcodes pass ONTbarcoder QC <br> Step 2: Save final barcodes file <br> Step 3: Generate summary statistics for each plate in the run <br> Step 4: Create FASTA file with Specimen ID and barcode for each sample|
|4|Assign taxonomy|BOLDigger3|Identify barcodes using BOLD database|
|5|Merge and split|merge_and_split.py|Step 1: Merge BOLD IDs with Final barcodes <br> Step 2: Split results by plate|
|6|Concatenate project plates|concat_project.py|Step 1: Merge all plate files for a given project <br> Step 2: Create FASTA file with Specimen ID and barcode for each sample|
|7|Cluster into MOTUs|motu_pipeline.py|Cluster barcodes into MOTUs at 97% identity|
|8|Create Mastersheet|create_mastersheet.py|Combine individual Entomoscope sheets for each plate into one Mastersheet|
|9|Final merge|final_merge.py|Step 1: Merge Entomoscope Mastersheet with MOTUs, Final barcodes, and BOLD IDs to create final spreadsheet <br> Step 2: Check if positive controls have been identified correctly <br> Step 3: Apply a minimum reads filter based on negative control in each plate <br> Step 4: Colour code and format final spreadsheet|
|10|Flag species of interest|species_of_interest.py|Search through project file and flag any species matching the “Species of interest” database (threatened invertebrates, pests, etc.)|

## Step 0: Set up

Open Ubuntu and navigate to your home directory (home/uXXXXXXX).

If this is your first time accessing this repository, run the following command:

    git clone https://github.com/ANU-Head-Lab/Diversity-Scanner-Bioinformatics-Pipeline.git

This will create a folder “Diversity-Scanner-Bioinformatics-Pipeline” with the contents of the repository. Use `cd Diversity-Scanner-Bioinformatics-Pipeline` to navigate inside this folder and `ls` to list the files/folders inside.

If you have used this repository before, run the following command:
    
    git pull
    
This will pull any changes that have been made to the repo since last time. This ensures your code remains up to date.

Run the following command to run the tests for this repository:
    
    pytest

Use `mkdir` to create a new folder called “Working”. This will be your working directory. Use cd to navigate inside this folder. 

The below commands are written assuming you are located in your working directory, along with all your input files. It also assumes the required python scripts are located in home/uXXXXXXX/Diversity-Scanner-Bioinformatics-Pipeline/Scripts. If your file path is different, make sure to change the commands accordingly.

At each specified Stopping Point, move the output files to their appropriate place in the ABDF shared database and (if necessary) delete them from your working directory.

### Step 1: Create demultiplexing file

To save time, this step can be done while the sequencing is running. 

#### Step 1.1 Make RunInfo file

First, create an Excel file containing the names and corresponding PCR tags of all the plates in the run. This information can be found in the Sequencing Overview file: “ABDF/Sequencing/Sequencing Overview/2026 Sequencing.xlsx”.

Along the bottom, navigate to the tab for the sequencing run you are analysing. Copy and paste the “Plate” and “Tag” columns into a new file. If necessary, edit the plate column so that it contains the project name, the word Plate, and the plate number (including DS if necessary). The file should look like this:

|Plate|Tag|
|-|-|
|RPbula Plate 70|SU111|
|RPbula Plate 71|SU112|
|RPbula Plate 72 DS|SU113|

Save this file in “ABDF/Sequencing/RunName/2.ONT barcoder/1.ONT input”. Name the file “RunName_RunInfo.xlsx”, where RunName is the name of the run you are analysing.

#### Step 1.2: Make demultiplexing file

Copy and paste the following into your Ubuntu working directory:
- RunName_RunInfo.xlsx
- The Entomoscope sheets for each individual plate in the run. Copy these over from “ABDF/PROJECT_DATA/ProjectName/1.Entomoscope Sheets” and place into their own folder called “ento_sheets”.
Note: the names of the Entomoscope sheets must be exactly the same as the plate names in the RunInfo file, including spaces and capital letters.

Run the following command:

    python ../Scripts/create_ont_input.py \
    --input_dir ento_sheets \
    --specimen_id_column "Specimen ID" \
    --runinfo RunName_RunInfo.xlsx \
    --taginfo ../Files/313bp_primers_TA.csv \
    --output RunName_DemuxSheet.csv \
    --transposeDS

Arguments:

`--input_dir`: Name of the folder containing the Entomoscope sheets for each plate in the run

`--specimen_id_column`: Name of the column in the Entomoscope sheets that specifies the specimen ID. The default is “Specimen ID”, so you only need to use this argument if your column name is different. (For example, the old template Entomoscope sheets use “Image code”).

`--taginfo`: File containing the forward/reverse tag and primer sequences for each well in a plate. Choose the relevant file depending on the amplicon size (313bp or 658bp). These are located in “Diversity-Scanner-Bioinformatics-Pipeline/Files”.

`--output`: Name for output demultiplexing sheet.

`--transposeDS`: Optional flag to specify whether to take the "Transposed" sheet from DS plate files. Use this flag if DS plates are using old layout format (A1, B1, C1...) and you have stored the correct format (A1, A2, A3...) in a "Transposed" sheet in the excel file.

Output:

The output file (RunName_DemuxSheet.csv) will have the sample ID, forward tag, reverse tag, forward primer and reverse primer for each sample in the sequencing run. This will be the input file for ONT barcoder.

#### Stopping Point

Move RunName_DemuxSheet.csv to “ABDF/Sequencing/RunName/2.ONT barcoder/1.ONT input”

If you are doing the Sequencing Summary step later, keep RunInfo and the Entomoscope sheets in your working directory, as you will need these again. Everything else can be deleted from your working directory. 

If you are not doing the Sequencing Summary step any time soon, you can delete everything in your working directory.



