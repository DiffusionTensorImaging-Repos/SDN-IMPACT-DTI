---
layout: default
title: "Step 6 — Brain Extraction on Mean B0"
parent: "Preprocessing (Steps 1–14)"
nav_order: 6
---

# Step 6 — Brain Extraction on Mean B0

After creating the mean B0 image in Step 8, we need to generate a **brain mask**. This mask is critical for later MRtrix preprocessing steps (e.g., `dwidenoise`, `mrdegibbs`) because it ensures operations are limited to brain tissue, avoiding noise from skull and neck regions.  

This step will provide a **clean mask** for denoising and Gibbs ringing removal, prevent non-brain voxels from skewing noise estimation, and it ensures consistency across subjects during diffusion preprocessing.  

We use **FSL BET (Brain Extraction Tool)** on the mean B0 (`*_Tmean.nii.gz`) to create a skull-stripped volume and a binary brain mask.  

- **Input**: `<subj>_topup_Tmean.nii.gz` (mean b0)  
- **Output**:  
  - `<subj>_topup_Tmean_brain.nii.gz` → skull-stripped b0  
  - `<subj>_topup_Tmean_brain_mask.nii.gz` → binary mask  



This step is computationally light — averaging is fast and memory-safe.
We allow up to 60 parallel jobs at once (all participants simultaniously)

Thiss step is safe to run fully parallel without worrying about SSH disconnects. So we'll just paste this right in the terminal. This step will be completed instantly.


**The Bash Code**
```bash
# Step 6: Brain extraction on mean b0 (parallelized, Bash-only, safe logging)

deriv_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/TOPUP"

# One shared log file (always overwrite bet.log)
logfile="bet.log"
: > "$logfile"   # create/clear

# Simple logger: prints to screen AND appends to logfile
log() { echo "$*" | tee -a "$logfile" ; }

# Source FSL environment once
source /usr/local/fsl/etc/fslconf/fsl.sh
export FSLOUTPUTTYPE=NIFTI_GZ

process_subj() {
    local subj="$1"
    local input="${deriv_base}/${subj}/topup_output/${subj}_topup_Tmean.nii.gz"
    local output="${deriv_base}/${subj}/topup_output/${subj}_topup_Tmean_brain.nii.gz"

    if [[ -f "$input" ]]; then
        log ">>> [$subj] Running BET on mean b0"
        {
            echo "----- [$subj] BET start"
            echo "cmd: bet \"$input\" \"$output\" -m -f 0.2 -g 0.1 -R -v"
            bet "$input" "$output" -m -f 0.2 -g 0.1 -R -v
            echo "----- [$subj] BET end"
            echo
        } >>"$logfile" 2>&1
        log ">>> [$subj] Brain mask created"
    else
        log "!!! [$subj] Missing input: $input"
    fi
}

subjects=$(ls -1 "$deriv_base")
max_jobs=60
job_count=0

for subj in $subjects; do
    process_subj "$subj" &
    ((job_count++))
    if (( job_count >= max_jobs )); then
        wait -n   # wait for one to finish, then continue launching
        ((job_count--))
    fi
done

wait  # ensure all background jobs are finished
log "=== Brain extraction finished for all subjects ==="
```

Note: All coding output from this script is recorded in bet.log.


**Expected Output (per subject)**
```
derivatives/TOPUP/<subj>/topup_output/
│
├── <subj>_topup_Tmean.nii.gz            # mean b0 (input)
├── <subj>_topup_Tmean_brain.nii.gz      # skull-stripped mean b0
├── <subj>_topup_Tmean_brain_mask.nii.gz # binary brain mask

```
**Here is the Audit to make sure all steps have been completed:**
```bash

#!/bin/bash
# Audit Step 8b: Brain extraction outputs (compare against NIFTI subject list)

nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
deriv_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/TOPUP"

printf "Subject\tBrain\tMask\n"

for subj in $(ls -1 "$nifti_base"); do
    out_dir="$deriv_base/$subj/topup_output"
    brain="${out_dir}/${subj}_topup_Tmean_brain.nii.gz"
    mask="${out_dir}/${subj}_topup_Tmean_brain_mask.nii.gz"

    [[ -f "$brain" ]] && bstat="✅" || bstat="❌"
    [[ -f "$mask"  ]] && mstat="✅" || mstat="❌"

    printf "%s\t%s\t%s\n" "$subj" "$bstat" "$mstat"
done

echo -e "\n=== BET audit finished ==="
```
---


