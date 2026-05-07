---
layout: default
title: "Step 3 — B0 Concatenation"
parent: "Preprocessing (Steps 1–14)"
nav_order: 3
---

# Step 3 — B0 Concatenation

- This is a step that is neccesary to prep our data before we run  **topup** for susceptibility distortion correction! This step will build a combined baseline (b0) image. 

This step extracts the first volume (the b0) from each subject’s AP and PA fieldmaps and merges them into a single 4D file. This merged file is the required input for topup.

This step will accomplish the following: 
1. Extract the first volume (b0) from the AP fieldmap (`*_fmapAP.nii`) → `<subj>_a2p_b0.nii.gz`  
2. Extract the first volume (b0) from the PA fieldmap (`*_fmapPA.nii`) → `<subj>_p2a_b0.nii.gz`  
3. Concatenate the AP and PA b0s into one file (`<subj>_merged_b0s.nii.gz`)  

This step will use the following input (per subject)
- `NIFTI/<subj>/dti/<subj>_fmapAP.nii`  
- `NIFTI/<subj>/dti/<subj>_fmapPA.nii`  

The code will use the fslroi + fslmerge FSL functions to grab the first b0 from each direction and merge them into the required *_merged_b0s.nii.gz

- This is a lightweight step and it will be pasted directly into the SSH terminal:

```bash
#!/bin/bash

# Step 3: B0 Concatenation (parallel + verbose)

nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
deriv_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/b0_concat"

mkdir -p "$deriv_base"

# Function to process a single subject
process_subj() {
    subj=$1
    subj_dir="$nifti_base/$subj/dti"
    out_dir="$deriv_base/$subj"
    mkdir -p "$out_dir"

    echo ">>> [$subj] Starting B0 extraction and concatenation"

    # Check inputs exist
    if [ ! -f "$subj_dir/${subj}_fmapAP.nii" ] || [ ! -f "$subj_dir/${subj}_fmapPA.nii" ]; then
        echo "!!! [$subj] Missing AP or PA fieldmap. Skipping."
        return
    fi

    # Extract b0 from AP
    echo ">>> [$subj] Extracting AP b0"
    fslroi "$subj_dir/${subj}_fmapAP.nii" \
           "$out_dir/${subj}_a2p_b0.nii.gz" 0 1

    # Extract b0 from PA
    echo ">>> [$subj] Extracting PA b0"
    fslroi "$subj_dir/${subj}_fmapPA.nii" \
           "$out_dir/${subj}_p2a_b0.nii.gz" 0 1

    # Merge AP + PA
    echo ">>> [$subj] Merging AP+PA b0s"
    fslmerge -t "$out_dir/${subj}_merged_b0s.nii.gz" \
             "$out_dir/${subj}_a2p_b0.nii.gz" \
             "$out_dir/${subj}_p2a_b0.nii.gz"

    echo ">>> [$subj] Done!"
}

export -f process_subj
export nifti_base deriv_base

# === Run in parallel ===
# Safe to use 30 jobs: B0 extraction/merge is light compared to ANT for which 30 parellel was no problem
#30 subjects in parallel.

subjects=$(basename -a "$nifti_base"/*)

echo "Found $(echo $subjects | wc -w) subjects in $nifti_base"
echo "Running with up to 30 in parallel..."

if command -v parallel > /dev/null; then
    echo "$subjects" | tr ' ' '\n' | parallel -j 30 process_subj {}
else
    max_jobs=30
    for subj in $subjects; do
        process_subj "$subj" &
        while [ "$(jobs -r | wc -l)" -ge "$max_jobs" ]; do
            sleep 1
        done
    done
    wait
fi

echo "=== All B0 concatenation jobs finished ==="

```

* Note -  All coding output from this script is recorded in b0_concat.log

**Expected File Output (Per participant):**
```
/data/projects/STUDIES/IMPACT/DTI/derivatives/b0_concat/
│
├── s1000/
│ ├── s1000_a2p_b0.nii.gz
│ ├── s1000_p2a_b0.nii.gz
│ ├── s1000_merged_b0s.nii.gz
│
├── s1323/
│ ├── s1323_a2p_b0.nii.gz
│ ├── s1323_p2a_b0.nii.gz
│ ├── s1323_merged_b0s.nii.gz
│
└── ...
```

**B0 Audit to check that conversion and file org was succesful.**:
```bash
#!/bin/bash

nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
deriv_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/b0_concat"

echo -e "Subject\tAP_b0\tPA_b0\tMerged"

for subj in $(ls "$nifti_base"); do
    out_dir="$deriv_base/$subj"
    ap="$out_dir/${subj}_a2p_b0.nii.gz"
    pa="$out_dir/${subj}_p2a_b0.nii.gz"
    merged="$out_dir/${subj}_merged_b0s.nii.gz"

    ap_status=$([ -f "$ap" ] && echo "✅" || echo "❌")
    pa_status=$([ -f "$pa" ] && echo "✅" || echo "❌")
    merged_status=$([ -f "$merged" ] && echo "✅" || echo "❌")

    echo -e "$subj\t$ap_status\t$pa_status\t$merged_status"
done

```
---
