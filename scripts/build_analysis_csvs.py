#!/usr/bin/env python3
"""
================================================================================
Step 28-prep: Build analysis-ready CSVs for permutation testing
================================================================================
Merges everything Ranesh's permutation R script needs:
  - Subject ID
  - 5 outcomes:
      * SOCIAL_dprime, MONETARY_dprime (memory)
      * ctqsf_adult_totalmaltreatment_pnrscoring (trauma — total)
      * ctqsf_adult_totalabuse_pnrscoring (trauma — abuse)
      * ctqsf_adult_totalneglect_pnrscoring (trauma — neglect)
  - 5 covariates:
      * mot_abs (absolute head motion, eddy quad)
      * ICV_mm3
      * <tract>_count (streamline count)
      * <tract>_mean_length
      * demo_poc_51 (maternal age)
  - 100 wide metric columns (FA_0..FA_99 OR NDI_0..NDI_99 etc.)

Output: 16 CSVs (4 tracts × 4 metrics) in
        ~/Desktop/SDN/DTI/data.check/analysis_ready/
        Each named: <tract>__<metric>__analysis.csv
"""
import pandas as pd
from pathlib import Path

base = Path("/Users/dannyzweben/Desktop/SDN/DTI")
fa_dir = base / "data.check/step27_fa"
nd_dir = base / "data.check/step30_noddi"
out_dir = base / "data.check/analysis_ready"
out_dir.mkdir(exist_ok=True, parents=True)

red = pd.read_csv(base / "Impact-Analyses/IMPACT_REDCap_clean_093024.csv")
grp = pd.read_csv(base / "Impact-Analyses/IMPACT_grouped_export.csv")
cov = pd.read_csv(base / "Impact-Analyses/imaging_covariates.csv")

# Outcomes
TRAUMA_COLS = [
    "ctqsf_adult_totalmaltreatment_pnrscoring",
    "ctqsf_adult_totalabuse_pnrscoring",
    "ctqsf_adult_totalneglect_pnrscoring",
]
MEM_COLS = ["SOCIAL_dprime", "MONETARY_dprime"]

# Memory-rate outcomes derived from raw counts
# True memory rate  = TrueMem / TotalTrials
# False memory rate = FalseMem / (TrueMem + FalseMem)
RAW_MEM_COLS = [
    "SOCIAL_TrueMem", "SOCIAL_FalseMem", "SOCIAL_TotalTrials",
    "MONETARY_TrueMem", "MONETARY_FalseMem", "MONETARY_TotalTrials",
]
DERIVED_MEM_COLS = [
    "SOCIAL_TrueMemRate", "SOCIAL_FalseMemRate",
    "MONETARY_TrueMemRate", "MONETARY_FalseMemRate",
]

# Positivity memory-bias outcomes — valence-broken-down counts
# HitRateBias  = P(hit | positive item) - P(hit | negative item)
# FABias       = P(FA  | positive item) - P(FA  | negative item)
RAW_BIAS_COLS = [
    "SOCIAL_TrueMem_positive", "SOCIAL_TrueMem_negative",
    "SOCIAL_FalseMem_positive", "SOCIAL_FalseMem_negative",
    "SOCIAL_Total_pos", "SOCIAL_Total_neg",
    "MONETARY_TrueMem_positive", "MONETARY_TrueMem_negative",
    "MONETARY_FalseMem_positive", "MONETARY_FalseMem_negative",
    "MONETARY_Total_pos", "MONETARY_Total_neg",
]
BIAS_COLS = [
    "SOCIAL_HitRateBias", "SOCIAL_FABias",
    "MONETARY_HitRateBias", "MONETARY_FABias",
]

# === Tidy IDs ===
red = red.rename(columns={"sub_id": "Subject"})
grp = grp.rename(columns={"ID": "Subject"})
cov = cov.rename(columns={"subject": "Subject"})

# REDCap may have repeated rows per subject (event); collapse on Subject taking first non-null
red_subset = red[["Subject", "demo_poc_51"] + TRAUMA_COLS].copy()
red_subset = (red_subset.dropna(subset=["Subject"])
                        .groupby("Subject")
                        .first()
                        .reset_index())

grp_subset = grp[["Subject"] + MEM_COLS + RAW_MEM_COLS + RAW_BIAS_COLS].copy()
grp_subset = (grp_subset.dropna(subset=["Subject"])
                        .groupby("Subject")
                        .first()
                        .reset_index())

# Derive memory rates per subject
for cond in ["SOCIAL", "MONETARY"]:
    true_mem = pd.to_numeric(grp_subset[f"{cond}_TrueMem"], errors="coerce")
    false_mem = pd.to_numeric(grp_subset[f"{cond}_FalseMem"], errors="coerce")
    total = pd.to_numeric(grp_subset[f"{cond}_TotalTrials"], errors="coerce")
    grp_subset[f"{cond}_TrueMemRate"] = true_mem / total
    grp_subset[f"{cond}_FalseMemRate"] = false_mem / (true_mem + false_mem)

    # Positivity memory biases
    tm_pos = pd.to_numeric(grp_subset[f"{cond}_TrueMem_positive"], errors="coerce")
    tm_neg = pd.to_numeric(grp_subset[f"{cond}_TrueMem_negative"], errors="coerce")
    fm_pos = pd.to_numeric(grp_subset[f"{cond}_FalseMem_positive"], errors="coerce")
    fm_neg = pd.to_numeric(grp_subset[f"{cond}_FalseMem_negative"], errors="coerce")
    n_pos = pd.to_numeric(grp_subset[f"{cond}_Total_pos"], errors="coerce")
    n_neg = pd.to_numeric(grp_subset[f"{cond}_Total_neg"], errors="coerce")
    grp_subset[f"{cond}_HitRateBias"] = (tm_pos / n_pos) - (tm_neg / n_neg)
    grp_subset[f"{cond}_FABias"]      = (fm_pos / n_pos) - (fm_neg / n_neg)

# === Merge demographics + outcomes + imaging covariates ===
base_df = cov.merge(red_subset, on="Subject", how="left") \
             .merge(grp_subset, on="Subject", how="left") \
             .rename(columns={"demo_poc_51": "maternal_age",
                              "mot_abs": "absolute_motion",
                              "ICV_mm3": "ICV"})

print(f"Base merged: {len(base_df)} subjects")
print(f"Outcome non-null counts:")
for c in TRAUMA_COLS + MEM_COLS:
    print(f"  {c}: {base_df[c].notna().sum()}")
print(f"Covariates non-null:")
for c in ["absolute_motion", "ICV", "maternal_age"]:
    print(f"  {c}: {base_df[c].notna().sum()}")

TRACTS = ["l_vta_l_hipp", "r_vta_r_hipp",
          "anterior_l_vta_l_hipp", "anterior_r_vta_r_hipp"]
METRICS = ["FA", "NDI", "ODI", "FWF"]

# Per (tract, metric), pivot the node-wise CSV to wide and merge
for tract in TRACTS:
    # Per-tract covariates (count + mean length apply to THIS tract)
    tract_df = base_df.copy()
    tract_df["Mean_tckstats"] = tract_df[f"{tract}_mean_length"]
    tract_df["Count_tckstats"] = tract_df[f"{tract}_count"]
    tract_df = tract_df[[
        "Subject", "absolute_motion", "ICV", "maternal_age",
        "Mean_tckstats", "Count_tckstats",
        *TRAUMA_COLS, *MEM_COLS, *DERIVED_MEM_COLS, *BIAS_COLS
    ]]

    for metric in METRICS:
        if metric == "FA":
            long = pd.read_csv(fa_dir / f"{tract}_fa_nodewise_all_subjects.csv")
        else:
            long = pd.read_csv(nd_dir / f"{tract}_noddi_nodewise_all_subjects.csv")
            long = long.rename(columns={metric: "value"})[["Subject", "Tract", "Node", "value"]]
            long = long.rename(columns={"value": metric})

        # Pivot: rows=Subject, cols=<metric>_<node>
        wide = (long.pivot(index="Subject", columns="Node", values=metric)
                    .reset_index())
        wide.columns = ["Subject"] + [f"{metric}_{c}" for c in wide.columns[1:]]

        # Merge with covariates + outcomes
        out = tract_df.merge(wide, on="Subject", how="inner")
        out_path = out_dir / f"{tract}__{metric}__analysis.csv"
        out.to_csv(out_path, index=False)
        print(f"  wrote {out_path.name}  shape={out.shape}")

print("\nAll 16 analysis-ready CSVs written.")
