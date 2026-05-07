---
layout: default
title: "Step 14: PYAFQ - BIDS and Running AFQ"
parent: "Preprocessing (Steps 1–14)"
nav_order: 14
---

# Step 14: PYAFQ - BIDS and Running AFQ

This script organizes all preprocessed DTI outputs (from EDDY, BEDPOSTX, and ANTs) into a BIDS-compliant directory structure expected by pyAFQ.
The goal is to take your finalized diffusion and anatomical data — already denoised, motion- and distortion-corrected, and brain-extracted — and place them in a standardized format so pyAFQ can automatically find and process each subject’s data.

| Data Type                          | Source Derivative                                        | Conceptual Purpose                                                       |
| ---------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------ |
| **DWI (diffusion-weighted image)** | **EDDY** (output from motion + eddy-current correction)  | Cleaned diffusion data used for all subsequent modeling and tractography |
| **bvals / bvecs**                  | **BEDPOSTX → bedpostx_input** (copied from EDDY outputs) | Define diffusion gradient strength and direction for each volume         |
| **DWI brain mask**                 | **BEDPOSTX → bedpostx_input/nodif_brain_mask.nii.gz**    | Binary mask delimiting brain voxels for fitting diffusion models         |
| **T1 structural image**            | **NIFTI → struct/** (native T1)                          | Anatomical reference in subject space for coregistration                 |
| **Brain-extracted T1**             | **ANTs → *_BrainExtractionBrain.nii.gz**                 | Skull-stripped version of T1 for improved alignment and tissue contrast  |
| **T1 brain mask**                  | **ANTs → *_BrainExtractionMask.nii.gz**                  | Binary mask defining brain voxels in T1 space                            |

These represent the final, cleaned derivatives from your full DTI pipeline (Denoise → Gibbs → Topup → Eddy → Bedpostx → ANTs).


**What BIDS Is** 

BIDS (Brain Imaging Data Structure) is a community standard for organizing neuroimaging data.
It enforces consistent file naming and folder hierarchy, allowing automated tools like pyAFQ, FSL, or fMRIPrep to locate inputs without manual specification.

In BIDS:
1. Each participant is sub-####
2. Modalities go in dedicated folders (/dwi, /anat)
3. Filenames encode modality and processing details (e.g., _dwi_desc-brain_mask.nii.gz).

pyAFQ automatically locates DWI and T1 data based on BIDS conventions.
It expects:
```
derivatives/
└── sub-####/
    ├── dwi/
    │   ├── sub-####_dwi.nii.gz
    │   ├── sub-####_dwi.bval
    │   ├── sub-####_dwi.bvec
    │   └── sub-####_dwi_desc-brain_mask.nii.gz
    └── anat/
        ├── sub-####_T1w.nii.gz
        ├── sub-####_desc-brain_T1w.nii.gz
        └── sub-####_desc-brain_mask.nii.gz
```

* I didn't parallelize this step because it is already short. 

**Paste the following into the terminal**

```bash
#!/bin/bash
# IMPACT DTI — pyAFQ Prep Script

set -euo pipefail

nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
eddy_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/EDDY"
bedpostx_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/BEDPOSTX"
ants_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/ANTs"
pyafq_base="/data/projects/STUDIES/IMPACT/DTI/pyAFQ/derivatives"

log_file="$pyafq_base/_pyAFQ_prep.log"
mkdir -p "$(dirname "$log_file")"

for subj_dir in "$eddy_base"/*/; do
    subj=$(basename "$subj_dir")
    subj_num="${subj#s}"
    echo ">>> $subj" | tee -a "$log_file"

    dwi_src="$eddy_base/$subj/${subj}_eddy.nii.gz"
    bval_src="$bedpostx_base/$subj/bedpostx_input/bvals"
    bvec_src="$bedpostx_base/$subj/bedpostx_input/bvecs"
    dwi_mask_src="$bedpostx_base/$subj/bedpostx_input/nodif_brain_mask.nii.gz"
    t1_src="$nifti_base/$subj/struct/${subj}_struct.nii"
    ants_brain_src="$ants_base/$subj/${subj}_BrainExtractionBrain.nii.gz"
    ants_mask_src="$ants_base/$subj/${subj}_BrainExtractionMask.nii.gz"

    subj_out="$pyafq_base/sub-${subj_num}"
    dwi_out="$subj_out/dwi"
    anat_out="$subj_out/anat"
    mkdir -p "$dwi_out" "$anat_out"

    missing=false
    for f in "$dwi_src" "$bval_src" "$bvec_src" "$dwi_mask_src" "$t1_src" "$ants_brain_src" "$ants_mask_src"; do
        if [ ! -f "$f" ]; then
            echo "Missing: $f" | tee -a "$log_file"
            missing=true
        fi
    done
    if [ "$missing" = true ]; then
        echo "Skipping $subj" | tee -a "$log_file"
        continue
    fi

    cp "$dwi_src" "$dwi_out/sub-${subj_num}_dwi.nii.gz"
    cp "$bval_src" "$dwi_out/sub-${subj_num}_dwi.bval"
    cp "$bvec_src" "$dwi_out/sub-${subj_num}_dwi.bvec"
    cp "$dwi_mask_src" "$dwi_out/sub-${subj_num}_dwi_desc-brain_mask.nii.gz"
    cp "$t1_src" "$anat_out/sub-${subj_num}_T1w.nii"
    cp "$ants_brain_src" "$anat_out/sub-${subj_num}_desc-brain_T1w.nii.gz"
    cp "$ants_mask_src" "$anat_out/sub-${subj_num}_desc-brain_mask.nii.gz"

    echo "Done: $subj" | tee -a "$log_file"
done
```
* Note: All output code from this script will be saved to pyAFQ_prep.log

---

# B. TRACTOGRAPHY: MRtrix3 Constrained Spherical Deconvolution (CSD)

