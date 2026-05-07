---
layout: default
title: "Step 5 — Mean B0 Image (Collapse Across Time)"
parent: "Preprocessing (Steps 1–14)"
nav_order: 5
---

# Step 5 — Mean B0 Image (Collapse Across Time)

Each subject has multiple b0 volumes (AP and PA) across time. Averaging them creates a single, **mean b0 image** that is more robust, less noisy, and better aligned than using any one volume. This mean image will serve as the reference for later registration and eddy correction.

---
**The following steps will be accopmlished by our code**: 
-  For each subject, locate the merged b0 file produced in Step 7:  
-  Collapse the 4D b0 into a 3D mean volume.  
- ave output in the same `topup_output/` folder, suffixed with `_Tcollapsed.nii.gz`.  

Our code will utilitze the fslmaths fsl function, and the call will use this structure: 
```
fslmaths "$input_file" -Tmean "$output_file"
```

* This step is computationally light — averaging is fast and memory-safe.
We allow up to 60 parallel jobs at once because it’s just I/O + averaging. We'll just paste this right in the terminal. This step will be completed instantly!

**Here is the Bash Code for this step**

```bash
#!/bin/bash
# Step 5: Mean B0 Image (collapse across time, with logging)

deriv_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/TOPUP"
logfile="mean_b0.log"

# Initialize/clear log
: > "$logfile"

# Logger function
log() { printf '%s %s\n' "$(date '+%F %T')" "$*" | tee -a "$logfile" ; }

# Source FSL environment once
source /usr/local/fsl/etc/fslconf/fsl.sh
export FSLOUTPUTTYPE=NIFTI_GZ

process_subj() {
    subj=$1
    input_file="${deriv_base}/${subj}/topup_output/${subj}_topup_corrected_b0.nii.gz"
    output_file="${deriv_base}/${subj}/topup_output/${subj}_topup_Tmean.nii.gz"

    if [[ -f "$input_file" ]]; then
        log ">>> [$subj] Averaging B0 across time"
        {
            echo "----- [$subj] fslmaths start"
            echo "cmd: fslmaths \"$input_file\" -Tmean \"$output_file\""
            fslmaths "$input_file" -Tmean "$output_file"
            echo "----- [$subj] fslmaths end"
            echo
        } >>"$logfile" 2>&1
        log ">>> [$subj] Done"
    else
        log "!!! [$subj] Missing input: $input_file"
    fi
}

# Max parallel jobs
max_jobs=60
job_count=0

for subj in $(ls -1 "$deriv_base"); do
    process_subj "$subj" &
    ((job_count++))

    if (( job_count >= max_jobs )); then
        wait -n
        ((job_count--))
    fi
done

wait
log "=== Mean B0 collapse finished for all subjects ==="
```
Note: All coding output from this script is recorded in mean_b0.log.


Expected file Output (per subject)
```bash
derivatives/TOPUP/<subj>/topup_output/
│
├── <subj>_topup.nii.gz              # input (4D b0 stack from TOPUP)
├── <subj>_topup_Tmean.nii.gz        # NEW mean B0 image
```

**Audit Step 8: Mean B0 Image (_Tmean.nii.gz). Checking that all the files were run propely.**

```bash
#!/bin/bash
# Audit Step 8: Mean B0 Image (_Tmean.nii.gz)
# Compare against NIFTI subject list

nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
deriv_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/TOPUP"

printf "Subject\tMeanB0_Tcollapsed\n"

for subj in $(ls -1 "$nifti_base"); do
    mean_b0="${deriv_base}/${subj}/topup_output/${subj}_topup_Tmean.nii.gz"

    if [[ -f "$mean_b0" ]]; then
        stat="✅"
    else
        stat="❌"
    fi

    printf "%s\t%s\n" "$subj" "$stat"
done
```


