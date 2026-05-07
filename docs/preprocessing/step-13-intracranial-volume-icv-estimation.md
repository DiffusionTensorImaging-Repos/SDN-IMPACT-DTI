---
layout: default
title: "Step 13: Intracranial Volume (ICV Estimation)"
parent: "Preprocessing (Steps 1–14)"
nav_order: 13
---

# Step 13: Intracranial Volume (ICV Estimation)

ICV (total volume of CSF, gray matter, and white matter) is estimated from each participant’s skull-stripped T1 image using ANTs’ Atropos segmentation. This value is often used as a covariate in diffusion analyses to control for individual differences in head size.
ICV is estimated by segmenting T1 images into CSF, GM, and WM using ANTs’ Atropos, then summing their volumes with FSL’s fslstats.

**Inputs (per subject):**
1. Brain-extracted T1 image
- /data/projects/STUDIES/IMPACT/DTI/derivatives/ANTs/<subj>/<subj>_BrainExtractionBrain.nii.gz
2. Brain mask
- /data/projects/STUDIES/IMPACT/DTI/derivatives/ANTs/<subj>/<subj>_BrainExtractionMask.nii.gz

Expected File Output (per subject):
```
derivatives/ICV/<subj>/
├── anat/
│   ├── <subj>_BrainExtractionBrain_segmentation_labelled.nii.gz   → 3-class segmentation
│   ├── <subj>_BrainExtractionBrain_segmentation_prob01.nii.gz     → CSF probability map
│   ├── <subj>_BrainExtractionBrain_segmentation_prob02.nii.gz     → GM probability map
│   └── <subj>_BrainExtractionBrain_segmentation_prob03.nii.gz     → WM probability map
└── icv_results.csv                                                → total ICV summary (CSF+GM+WM)
```
**This task is very lightweight, and thus can be pasted directly in the SSH terminal and easily parallelized acorss all 60 participants. If you have more participants than this, you can adjust accordingly.** 

**Paste the following into the terminal:**
```bash
#!/bin/bash
# ============================================================
# 🧠 IMPACT DTI — Step 13: Intracranial Volume (ICV) Estimation
# ============================================================

source /usr/local/fsl/etc/fslconf/fsl.sh
export FSLOUTPUTTYPE=NIFTI_GZ

ANTs_bin="/data/tools/ANTs/bin"
ants_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/ANTs"
icv_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/ICV"
csv_file="$icv_base/icv_results.csv"
log_file="$HOME/icv.log"

mkdir -p "$icv_base"
: > "$log_file"
echo "participant_id,brain_file_name,ICV_mm3" > "$csv_file"

# --- Function to process one subject ---
process_subj() {
    subj="$1"
    subj_dir="$ants_base/$subj"
    brain_file="$subj_dir/${subj}_BrainExtractionBrain.nii.gz"
    mask_file="$subj_dir/${subj}_BrainExtractionMask.nii.gz"
    out_dir="$icv_base/$subj"
    mkdir -p "$out_dir"

    echo ">>> [$subj] Running Atropos segmentation..." | tee -a "$log_file"

    # Segmentation (probabilistic)
    "$ANTs_bin/Atropos" -d 3 \
        -a "$brain_file" \
        -x "$mask_file" \
        -i KMeans[3] \
        -c [5,0.001] \
        -m [0.3,1x1x1] \
        -o ["$out_dir/${subj}_seg_labelled.nii.gz","$out_dir/${subj}_seg_prob%02d.nii.gz"]

    # Ensure segmentation maps exist
    if [[ ! -f "$out_dir/${subj}_seg_prob01.nii.gz" ]]; then
        echo "!!! [$subj] Segmentation failed — missing prob maps." | tee -a "$log_file"
        return
    fi

    # Compute ICV
    csf=$(fslstats "$out_dir/${subj}_seg_prob01.nii.gz" -V | awk '{print $2}')
    gm=$(fslstats "$out_dir/${subj}_seg_prob02.nii.gz" -V | awk '{print $2}')
    wm=$(fslstats "$out_dir/${subj}_seg_prob03.nii.gz" -V | awk '{print $2}')

    icv=$(echo "$csf + $gm + $wm" | bc)
    echo "$subj,$(basename "$brain_file"),$icv" >> "$csv_file"

    echo ">>> [$subj] Done (ICV = ${icv} mm³)" | tee -a "$log_file"
}

export -f process_subj
export ANTs_bin ants_base icv_base csv_file log_file

# --- Parallel run ---
subjects=$(ls -1 "$ants_base")
max_jobs=20  # adjust based on system load

echo "Found $(echo "$subjects" | wc -l) subjects. Running up to $max_jobs in parallel..." | tee -a "$log_file"

echo "$subjects" | xargs -n 1 -P "$max_jobs" -I {} bash -c 'process_subj "$@"' _ {}

echo "=== All ICV jobs finished. Results in $csv_file ===" | tee -a "$log_file"


```
* Note - all coding from the icv step will be saved to icv.log

**Audit ICV script**

```bash
#!/bin/bash
# ============================================================
# 🧠 IMPACT DTI — Step 13 Audit: Intracranial Volume (ICV)
# ============================================================

nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
ants_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/ANTs"
icv_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/ICV"
csv_file="$icv_base/icv_results.csv"

printf "Subject\tBrain\tMask\tProb01\tProb02\tProb03\tCSV\n"

# Loop over subjects that exist in the NIFTI base (expected participants)
for subj in $(ls -1 "$nifti_base"); do
    subj_ants="$ants_base/$subj"
    subj_icv="$icv_base/$subj"

    # Expected ANTs input files
    brain="$subj_ants/${subj}_BrainExtractionBrain.nii.gz"
    mask="$subj_ants/${subj}_BrainExtractionMask.nii.gz"

    # Expected ICV output files
    prob01="$subj_icv/${subj}_seg_prob01.nii.gz"
    prob02="$subj_icv/${subj}_seg_prob02.nii.gz"
    prob03="$subj_icv/${subj}_seg_prob03.nii.gz"

    # Checks
    b_check=$([ -f "$brain" ] && echo "✅" || echo "❌")
    m_check=$([ -f "$mask" ] && echo "✅" || echo "❌")
    p1_check=$([ -f "$prob01" ] && echo "✅" || echo "❌")
    p2_check=$([ -f "$prob02" ] && echo "✅" || echo "❌")
    p3_check=$([ -f "$prob03" ] && echo "✅" || echo "❌")

    csv_check=$([ -f "$csv_file" ] && grep -q "^$subj," "$csv_file" 2>/dev/null && echo "✅" || echo "❌")

    printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
        "$subj" "$b_check" "$m_check" "$p1_check" "$p2_check" "$p3_check" "$csv_check"
done

echo -e "\n=== ICV Audit Complete ==="
```

