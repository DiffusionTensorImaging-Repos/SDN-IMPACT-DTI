---
layout: default
title: "Step 10: DWI Shell Extraction"
parent: "Preprocessing (Steps 1–14)"
nav_order: 10
---

# Step 10: DWI Shell Extraction

Following EDDY and BEDPOSTX preprocessing, we next extract diffusion-weighted imaging (DWI) volumes corresponding to specific b-value shells for downstream modeling and visualization.
This step uses MRtrix3’s dwiextract command, which isolates all volumes matching specified b-values (e.g., 0, 1000, 2000 s/mm²) and exports the corresponding gradient tables.

* **Note: As with BEDPOSTX, this step is performed primarily to prepare data for probabilistic tractography (e.g., MRtrix or FSL probtrackx2). It is not required for pyAFQ or other microstructure analyses, though it is advisable to run it regardless so the data remain ready for future tractography or modeling decisions.**

In our case, we extract two datasets per participant:

1. b=0 and b=1000 volumes
2. b=0, b=1000, and b=2000 volumes

Each extraction produces a 4D image containing only the selected shells, along with new .bvec and .bval files corresponding to those shells.

**Our code will use the following Inputs (output from the BEDPOSTX preparation step):** 
1. Eddy-corrected DWI data (per subject):
- /data/projects/STUDIES/IMPACT/DTI/derivatives/BEDPOSTX/<subj>/bedpostx_input/data.nii.gz
2. Gradient tables (per subject):
- /data/projects/STUDIES/IMPACT/DTI/derivatives/BEDPOSTX/<subj>/bedpostx_input/bvecs
- /data/projects/STUDIES/IMPACT/DTI/derivatives/BEDPOSTX/<subj>/bedpostx_input/bvals

**Outputs (per subject):** 
```
derivatives/mrtrix3_1000/s1000/
│
├── data_1000.nii.gz         # DWI volumes including only b=0 and b=1000 shells
├── bvecs_1000               # gradient directions for b=0,1000 data
└── bvals_1000               # corresponding b-values

derivatives/mrtrix3_2000/s1000/
│
├── data_1000_2000.nii.gz    # DWI volumes including b=0, b=1000, and b=2000 shells
├── bvecs_1000_2000          # gradient directions for b=0,1000,2000 data
└── bvals_1000_2000          # corresponding b-values
```

**This task is very lightweight, and thus can be pasted directly in the SSH terminal and easily parallelized acorss all 60 participants. If you have more participants than this, you can adjust accordingly.** 

**Paste the following into the terminal**: 

```bash
#!/bin/bash
###############################################################################
# 🧠 IMPACT DTI — Parallel DWIEXTRACT (live + logged output, stable + safe)
###############################################################################

# --- consistent logging (no SSH close) ---
log_file="$HOME/dwiextract.log"
: > "$log_file"   # clear previous run
echo "=== Starting DWIEXTRACT ===" | tee -a "$log_file"

# --- base directories ---
base_dir="/data/projects/STUDIES/IMPACT/DTI/derivatives/BEDPOSTX"
mrtrix3_1000_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/mrtrix3_1000"
mrtrix3_2000_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/mrtrix3_2000"

mkdir -p "$mrtrix3_1000_base" "$mrtrix3_2000_base"

# --- function: process one subject ---
process_subj() {
    subj="$1"
    subj_dir="$base_dir/$subj/bedpostx_input"

    echo ">>> [$subj] START" | tee -a "$log_file"

    mkdir -p "$mrtrix3_1000_base/$subj" "$mrtrix3_2000_base/$subj"

    echo ">>> [$subj] Running dwiextract (b=0,1000)" | tee -a "$log_file"
    dwiextract \
        -fslgrad "$subj_dir/bvecs" "$subj_dir/bvals" \
        -shells 0,1000 \
        "$subj_dir/data.nii.gz" \
        "$mrtrix3_1000_base/$subj/data_1000.nii.gz" \
        -export_grad_fsl \
        "$mrtrix3_1000_base/$subj/bvecs_1000" \
        "$mrtrix3_1000_base/$subj/bvals_1000" \
        -force 2>&1 | tee -a "$log_file"

    echo ">>> [$subj] Running dwiextract (b=0,1000,2000)" | tee -a "$log_file"
    dwiextract \
        -fslgrad "$subj_dir/bvecs" "$subj_dir/bvals" \
        -shells 0,1000,2000 \
        "$subj_dir/data.nii.gz" \
        "$mrtrix3_2000_base/$subj/data_1000_2000.nii.gz" \
        -export_grad_fsl \
        "$mrtrix3_2000_base/$subj/bvecs_1000_2000" \
        "$mrtrix3_2000_base/$subj/bvals_1000_2000" \
        -force 2>&1 | tee -a "$log_file"

    echo ">>> [$subj] DONE" | tee -a "$log_file"
}

export -f process_subj
export base_dir mrtrix3_1000_base mrtrix3_2000_base log_file

# --- find and run subjects in parallel (no hang, no wait) ---
subjects=$(find "$base_dir" -mindepth 1 -maxdepth 1 -type d -exec basename {} \;)
count=$(echo "$subjects" | wc -l)
echo "Found $count subjects. Running up to 60 in parallel..." | tee -a "$log_file"

echo "$subjects" | xargs -n 1 -P 60 -I {} bash -c 'process_subj "$@"' _ {} | tee -a "$log_file"

echo "=== All DWIEXTRACT jobs finished successfully ===" | tee -a "$log_file"

```
Note: All coding output from this script is recorded in dwiextract.log


**AUDIT script to make sure dwi extract worked properly for all participants**

```bash

#!/bin/bash
# ============================================================
# DWI Extract Audit — IMPACT DTI
# ============================================================
# Cross-checks that every subject in NIFTI base has
# corresponding dwiextract outputs in mrtrix3_1000 and mrtrix3_2000
# ============================================================

nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
mrtrix3_1000_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/mrtrix3_1000"
mrtrix3_2000_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/mrtrix3_2000"

printf "Subject\tdata_1000\tbvecs_1000\tbvals_1000\tdata_1000_2000\tbvecs_1000_2000\tbvals_1000_2000\n"

for subj in $(ls -1 "$nifti_base"); do
    # paths for b=1000 outputs
    data1000="$mrtrix3_1000_base/$subj/data_1000.nii.gz"
    bvec1000="$mrtrix3_1000_base/$subj/bvecs_1000"
    bval1000="$mrtrix3_1000_base/$subj/bvals_1000"

    # paths for b=2000 outputs
    data2000="$mrtrix3_2000_base/$subj/data_1000_2000.nii.gz"
    bvec2000="$mrtrix3_2000_base/$subj/bvecs_1000_2000"
    bval2000="$mrtrix3_2000_base/$subj/bvals_1000_2000"

    # ✅/❌ checks
    d1000=$([ -f "$data1000" ] && echo "✅" || echo "❌")
    bv1000=$([ -f "$bvec1000" ] && echo "✅" || echo "❌")
    bl1000=$([ -f "$bval1000" ] && echo "✅" || echo "❌")

    d2000=$([ -f "$data2000" ] && echo "✅" || echo "❌")
    bv2000=$([ -f "$bvec2000" ] && echo "✅" || echo "❌")
    bl2000=$([ -f "$bval2000" ] && echo "✅" || echo "❌")

    printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
      "$subj" "$d1000" "$bv1000" "$bl1000" "$d2000" "$bv2000" "$bl2000"
done

echo -e "\n=== DWI Extract Audit Complete ==="
```
---
