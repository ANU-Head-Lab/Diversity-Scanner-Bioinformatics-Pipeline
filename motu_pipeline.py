#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path
import shutil
import pandas as pd
import requests
import time
import hashlib
import json
import matplotlib.pyplot as plt
import numpy as np
import sys

# -----------------------------
# Utility Functions
# -----------------------------
def check_dependencies():
    for tool in ["vsearch", "swarm"]:
        if shutil.which(tool) is None:
            raise EnvironmentError(f"❌ Required tool '{tool}' not found in PATH. Please install it.")

def clean_fasta(input_fasta, output_fasta):
    seen = set()
    excluded = []
    with open(input_fasta, "r") as infile, open(output_fasta, "w") as outfile:
        current_seq = ""
        current_header = ""
        for line in infile:
            if line.startswith(">"):
                if current_header:
                    cleaned_seq = current_seq.replace("-", "").replace("N", "").strip()
                    key = (current_header, hashlib.md5(cleaned_seq.encode()).hexdigest())
                    if cleaned_seq and key not in seen:
                        seen.add(key)
                        outfile.write(current_header + "\n")
                        outfile.write(cleaned_seq + "\n")
                    elif not cleaned_seq:
                        excluded.append(current_header[1:].strip())
                current_header = line.strip()
                current_seq = ""
            else:
                current_seq += line.strip()
        if current_header:
            cleaned_seq = current_seq.replace("-", "").replace("N", "").strip()
            key = (current_header, hashlib.md5(cleaned_seq.encode()).hexdigest())
            if cleaned_seq and key not in seen:
                outfile.write(current_header + "\n")
                outfile.write(cleaned_seq + "\n")
            elif not cleaned_seq:
                excluded.append(current_header[1:].strip())
    return excluded

def dereplicate(input_fasta, output_fasta, output_uc):
    subprocess.run([
        "vsearch", "--derep_fulllength", input_fasta,
        "--output", output_fasta, "--sizeout", "--uc", output_uc
    ], check=True)

def cluster_with_swarm(input_fasta, output_txt, d):
    subprocess.run([
        "swarm", "-d", str(d), "-z", "-t", "4",
        "-o", output_txt, input_fasta
    ], check=True)

def cluster_with_otu97(input_fasta, otu_output_uc):
    subprocess.run([
        "vsearch", "--cluster_fast", input_fasta, "--id", "0.97",
        "--uc", otu_output_uc,
        "--centroids", str(Path(otu_output_uc).with_suffix(".fasta")),
        "--threads", "4"
    ], check=True)

def clean_seq_id(seq_id):
    return seq_id.split(";")[0]

# -----------------------------
# UC & OTU Parsers
# -----------------------------
def parse_derep_uc(uc_file):
    mapping = {}
    with open(uc_file) as f:
        for line in f:
            if line.startswith("#"): continue
            parts = line.strip().split("\t")
            if len(parts) >= 10:
                query_id = clean_seq_id(parts[8])
                target_id = clean_seq_id(parts[9])
                mapping[query_id] = target_id
    return mapping

def parse_swarm(swarm_file):
    motu_data = []
    with open(swarm_file) as f:
        for idx, line in enumerate(f, 1):
            seqs = line.strip().split()
            if seqs:
                motu_name = f"MOTU_{idx}"
                for seq in seqs:
                    seq_id = seq.split(";")[0].strip()
                    motu_data.append({'Unique Seq ID': seq_id, 'MOTU (SWARM)': motu_name})
    return pd.DataFrame(motu_data)

def parse_otu(otu_file, include_centroids=False):
    otu_data = []
    with open(otu_file) as f:
        for line in f:
            if line.startswith("#"): continue
            parts = line.strip().split("\t")
            if len(parts) >= 10:
                if not include_centroids and parts[0] == 'C': continue
                seq_id = clean_seq_id(parts[8])
                otu_data.append({'Sequence ID': seq_id, 'MOTU (OTU97%)': parts[1]})
    return pd.DataFrame(otu_data)

# -----------------------------
# Taxonomy
# -----------------------------
def gbif_taxonomy_lookup(name):
    url = "https://api.gbif.org/v1/species/match"
    try:
        resp = requests.get(url, params={"name": name}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("matchType") == "EXACT" or data.get("confidence",0)>80:
            return {
                "Order": data.get("order"),
                "Family": data.get("family"),
                "Genus": data.get("genus"),
                "Species": data.get("species"),
            }
    except Exception as e:
        print(f"⚠️ GBIF lookup error for '{name}': {e}")
    return {"Order": None, "Family": None, "Genus": None, "Species": None}

def fetch_full_taxonomy(df_taxonomy, col_name="Blast Match", cache_file="taxonomy_cache.json"):
    cache_path = Path(cache_file)
    if cache_path.exists():
        taxonomy_cache = json.loads(cache_path.read_text())
    else:
        taxonomy_cache = {}

    for name in df_taxonomy[col_name].dropna().unique():
        if name not in taxonomy_cache:
            taxonomy_cache[name] = gbif_taxonomy_lookup(name)
            time.sleep(0.3)

    cache_path.write_text(json.dumps(taxonomy_cache, indent=2))

    # Only fill missing values, do not overwrite existing
    for rank in ["Order","Family","Genus","Species"]:
        if rank not in df_taxonomy.columns:
            df_taxonomy[rank] = df_taxonomy[col_name].map(lambda x: taxonomy_cache.get(x, {}).get(rank))
        else:
            df_taxonomy[rank] = df_taxonomy.apply(
                lambda row: row[rank] if pd.notna(row[rank]) else taxonomy_cache.get(row[col_name], {}).get(rank),
                axis=1
            )
    return df_taxonomy

# -----------------------------
# Plots
# -----------------------------
def plot_rarefaction_curve(df_all, output_png):
    seqs = df_all['Sequence ID'].tolist()
    motus = df_all['Consensus MOTU'].tolist()
    seen = set()
    counts = []
    for m in motus:
        seen.add(m)
        counts.append(len(seen))
    plt.figure(figsize=(8,6))
    plt.plot(range(1,len(seqs)+1), counts, color='blue')
    plt.xlabel("Number of sequences")
    plt.ylabel("Unique MOTUs")
    plt.title("Rarefaction Curve")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_png)
    plt.close()

# 
# Safe Excel Write
# 
def safe_to_excel(df, writer, sheet_name):
    if df is None or df.empty:
        df = pd.DataFrame({"Message":["No data available"]})
    i = 0
    while True:
        try:
            if i == 0:
                df.to_excel(writer, index=False, sheet_name=sheet_name)
            else:
                df.to_excel(writer, index=False, sheet_name=f"{sheet_name}_{i}")
            break
        except ValueError:
            i += 1

#
# Core Mapping Function
#
def map_motus_and_taxonomy(swarm_file, derep_uc_file, otu_file, taxonomy_file, writer, excluded_samples, output_dir):
    df_otu = parse_otu(otu_file, include_centroids=True)
    derep_map = parse_derep_uc(derep_uc_file)
    df_map = pd.DataFrame(list(derep_map.items()), columns=['Sequence ID','Unique Seq ID'])
    df_all = df_map.merge(df_otu, on='Sequence ID', how='left')
    df_all['MOTU (OTU97%)'] = df_all['MOTU (OTU97%)'].fillna("MOTU_unassigned")

    if swarm_file and Path(swarm_file).exists():
        df_swarm = parse_swarm(swarm_file)
        df_all = df_all.merge(df_swarm, on='Unique Seq ID', how='left')

    for col in ['MOTU (OTU97%)','MOTU (SWARM)']:
        if col in df_all.columns:
            df_all[col] = df_all[col].astype(str).str.strip().replace("nan","MOTU_unassigned")
        else:
            df_all[col] = "MOTU_unassigned"

    df_all.loc[df_all['Unique Seq ID']=="*",'Unique Seq ID'] = df_all.loc[df_all['Unique Seq ID']=="*",'Sequence ID']

    df_all = df_all.drop_duplicates(subset=['Sequence ID', 'Unique Seq ID'])

    #
    # Consensus MOTU
    #
    def consensus(row):
        otu = row['MOTU (OTU97%)']
        swarm = row['MOTU (SWARM)']
        return otu if otu!="MOTU_unassigned" else swarm if swarm!="MOTU_unassigned" else "MOTU_unassigned"

    centroid_df = df_all[df_all['Sequence ID']==df_all['Unique Seq ID']].copy()
    centroid_df['Consensus MOTU'] = centroid_df.apply(consensus, axis=1)
    motu_map = dict(zip(centroid_df['Unique Seq ID'], centroid_df['Consensus MOTU']))
    df_all['Consensus MOTU'] = df_all['Unique Seq ID'].map(motu_map)
    df_all['Consensus MOTU'] = df_all['Consensus MOTU'].fillna("MOTU_unassigned")

    #
    # MOTU Summary
    # 
    if 'Image Count' in df_all.columns:
        summary = df_all.groupby('Consensus MOTU').agg(
            Sequence_Count=('Sequence ID','count'),
            Images=('Image Count','sum')
        ).reset_index()
    else:
        summary = df_all.groupby('Consensus MOTU').agg(
            Sequence_Count=('Sequence ID','count'),
        ).reset_index()
        summary['Images'] = 0

    # 
    # Merge Taxonomy
    #
    df_merged = None
    if taxonomy_file and Path(taxonomy_file).exists():
        df_tax = pd.read_excel(taxonomy_file)
        df_tax.columns = df_tax.columns.str.strip()

        if "Specimen ID" not in df_tax.columns:
            raise ValueError("Taxonomy file must contain 'Specimen ID' column")

        df_tax["Specimen ID"] = df_tax["Specimen ID"].astype(str).str.strip().str.upper()
        df_tax["CleanID"] = df_tax["Specimen ID"].str.replace("_", "", regex=False)

        if "Blast Match" not in df_tax.columns:
            raise ValueError("Taxonomy file must contain 'Blast Match'")
        df_tax = fetch_full_taxonomy(df_tax, col_name="Blast Match")

        df_all["CleanID"] = df_all["Sequence ID"].astype(str).str.strip().str.upper()
        df_all["CleanID"] = df_all["CleanID"].str.replace("_", "", regex=False)

        df_tax = df_tax.drop_duplicates(subset=["CleanID"])
        df_merged = df_all.merge(df_tax, on="CleanID", how="left", suffixes=("", "_tax"))

        # Fill main taxonomy columns
        for col in ["Order", "Family", "Genus", "Species", "Blast Match"]:
            if f"{col}_tax" in df_merged.columns:
                df_merged[col] = df_merged[col].fillna(df_merged[f"{col}_tax"])
                df_merged = df_merged.drop(columns=[f"{col}_tax"])

        #
        # Write all MOTU+taxonomy table
        #
        safe_to_excel(df_merged, writer, "MOTU with Taxonomy")

        # 
        # Taxonomy summary (multiple sheets)
        # 
        frames = []
        for rank in ["Order","Family","Genus","Species"]:
            if rank in df_merged.columns:
                if 'Image Count' in df_merged.columns:
                    df_rank = (
                        df_merged.groupby([rank, "Consensus MOTU"])
                        .agg(Sequence_Count=("Sequence ID","count"), Images=("Image count","sum"))
                        .reset_index()
                    )
                else:
                    df_rank = (
                        df_merged.groupby([rank, "Consensus MOTU"])
                        .agg(Sequence_Count=("Sequence ID","count"))
                        .reset_index()
                    )
                    df_rank['Images'] = 0

                df_rank["Taxonomic Rank"] = rank
                df_rank.rename(columns={rank: "Taxon Name"}, inplace=True)
                frames.append(df_rank[["Taxonomic Rank","Taxon Name","Consensus MOTU","Sequence_Count","Images"]])

                # Summary sheets by rank
                if 'Image Count' in df_merged.columns:
                    summary_by_rank = (
                        df_merged.groupby(rank)
                        .agg(Sequences=("Sequence ID","count"), MOTU_Richness=("Consensus MOTU","nunique"),
                             Images=("Image count","sum"))
                        .sort_values("MOTU_Richness", ascending=False)
                        .reset_index()
                    )
                else:
                    summary_by_rank = (
                        df_merged.groupby(rank)
                        .agg(Sequences=("Sequence ID","count"), MOTU_Richness=("Consensus MOTU","nunique"))
                        .sort_values("MOTU_Richness", ascending=False)
                        .reset_index()
                    )
                    summary_by_rank['Images'] = 0

                safe_to_excel(summary_by_rank, writer, f"{rank} Summary")

        if frames:
            safe_to_excel(pd.concat(frames, ignore_index=True), writer, "Taxonomy Summary")

        # 
        # Plots
        # 
        family_col = next((c for c in df_merged.columns if c.lower() == "family"), None)
        images_col = next((c for c in df_merged.columns if "Image Count" in c.lower()), None)

        if family_col:
            counts = df_merged.groupby(family_col)['Consensus MOTU'].nunique().sort_values(ascending=False).head(20)
            plt.figure(figsize=(10,6))
            colors = plt.cm.rainbow(np.linspace(0,1,len(counts)))
            counts.plot(kind='bar', color=colors)
            plt.ylabel("MOTU richness")
            plt.title("MOTU richness per Family (top 20)")
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(output_dir / "family_richness.png")
            plt.close()

        if family_col and images_col:
            df_merged[images_col] = pd.to_numeric(df_merged[images_col], errors='coerce').fillna(0)
            counts = df_merged.groupby(family_col)[images_col].sum().sort_values(ascending=False).head(20)
            plt.figure(figsize=(10,6))
            colors = plt.cm.Blues(np.linspace(0.3,1,len(counts)))
            counts.plot(kind='bar', color=colors)
            plt.ylabel("Number of specimens")
            plt.title("Images per Family (top 20)")
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(output_dir / "family_images.png")
            plt.close()

    # -----------------------------
    # Handle excluded samples
    # -----------------------------
    if excluded_samples:
        excluded_row = {'Consensus MOTU':"Excluded (blank)", 'Sequence Count':len(excluded_samples), 'Images':0}
        summary = pd.concat([summary,pd.DataFrame([excluded_row])], ignore_index=True)
        safe_to_excel(pd.DataFrame({"Excluded Samples":excluded_samples}), writer, "Excluded Samples")

    # -----------------------------
    # Output MOTU assignments and summary
    # -----------------------------
    df_all_out = df_all.rename(columns={'Sequence ID':'Sequence ID','Unique Seq ID':'Unique Sequence ID'})
    safe_to_excel(df_all_out, writer, "MOTU Assignments")
    safe_to_excel(summary, writer, "MOTU Summary")

    return df_all

# -----------------------------
# Main
# -----------------------------
def main():
    try:
        check_dependencies()
        parser = argparse.ArgumentParser(description="Full MOTU pipeline")
        parser.add_argument("--input", required=True, help="Input FASTA file")
        parser.add_argument("--threshold", type=int, default=3, help="SWARM d-value")
        parser.add_argument("--taxonomy", required=True, help="Taxonomy Excel file")
        parser.add_argument("--output", default="motu_full_output.xlsx", help="Output Excel file")
        parser.add_argument("--verbose", action="store_true", help="Verbose output")
        args = parser.parse_args()

        input_fasta = Path(args.input).resolve()
        taxonomy_file = Path(args.taxonomy).resolve()
        output_dir = input_fasta.with_suffix("")
        output_dir.mkdir(exist_ok=True)
        output_excel = output_dir / args.output

        cleaned_fasta = output_dir / "cleaned.fasta"
        derep_fasta = output_dir / "dereplicated.fasta"
        derep_uc = output_dir / "dereplicated.uc"
        swarm_out = output_dir / "swarm_output.txt"
        otu_uc = output_dir / "otu97_clusters.uc"

        if args.verbose: print("Cleaning FASTA...")
        excluded = clean_fasta(str(input_fasta), str(cleaned_fasta))
        if args.verbose: print("Dereplicating...")
        dereplicate(str(cleaned_fasta), str(derep_fasta), str(derep_uc))
        if args.verbose: print("OTU97 clustering...")
        cluster_with_otu97(str(derep_fasta), str(otu_uc))
        if args.verbose: print(f"SWARM clustering (d={args.threshold})...")
        cluster_with_swarm(str(derep_fasta), str(swarm_out), args.threshold)

        if args.verbose: print("Mapping MOTUs and merging taxonomy...")
        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
            df_all = map_motus_and_taxonomy(swarm_out, derep_uc, otu_uc, taxonomy_file, writer, excluded, output_dir)

        rarefaction_png = output_dir / "rarefaction_curve.png"
        plot_rarefaction_curve(df_all, rarefaction_png)
        if args.verbose:
           print(f"\n✅ Pipeline complete! Excel and plots saved in {output_dir}")

    except Exception as e:
        print(f"❌ Fatal error in main: {e}")
        sys.exit(1)

if __name__=="__main__":
    main()
