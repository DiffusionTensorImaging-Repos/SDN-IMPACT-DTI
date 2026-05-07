---
layout: default
title: "Step 12: FLIRT and CONVERT (Spatial Alignment and Standardization)"
parent: "Preprocessing (Steps 1–14)"
nav_order: 12
---

# Step 12: FLIRT and CONVERT (Spatial Alignment and Standardization)

After tensor fitting, each participant’s diffusion-derived maps (FA, MD, RD, AD) remain in their native diffusion space. For many group-level or visualization analyses, however, these images must be aligned to a common reference space so that every voxel corresponds to the same anatomical location across participants.
This alignment step—performed using FSL’s FLIRT (FMRIB Linear Image Registration Tool)—creates spatially standardized versions of the scalar maps.

* Note: While pyAFQ handles its own registration and doesn’t require pre-aligned FA maps, running FLIRT is still useful for quality control, future voxelwise or atlas-based analyses, and maintaining standardized, shareable outputs for visualization or cross-study compatibility.

**Inputs (per subject)**

1. FA map (moving image)
- /data/projects/STUDIES/IMPACT/DTI/derivatives/DTIFIT_OUTPUT/<subj>/DTI_FA.nii.gz
2. Template / reference image (fixed)
- /data/projects/STUDIES/IMPACT/DTI/ANTsTemplate/FA_template.nii.gz
3. Output directory
/data/projects/STUDIES/IMPACT/DTI/derivatives/FLIRT/<subj>/

**Expected File Output (Per Subject):**
```
derivatives/FLIRT/s1000/
│
├── DTI_FA_flirted.nii.gz          # FA map aligned to the study or MNI template
├── DTI_FA_to_template.mat         # affine transform matrix (FA → template)
├── DTI_MD_flirted.nii.gz          # MD map transformed using same matrix
├── DTI_RD_flirted.nii.gz          # RD map transformed using same matrix
├── DTI_AD_flirted.nii.gz          # AD (L1) map transformed using same matrix
└── flirt_command.txt              # record of the full FLIRT command used
```

**This task is very lightweight, and thus can be pasted directly in the SSH terminal and easily parallelized acorss all 60 participants. If you have more participants than this, you can adjust accordingly.** 

**Past the following into the SSH terminal:**
```bash
#!/bin/bash
# ============================================================
# 🧠 IMPACT DTI — Step 12: FLIRT + CONVERT (Spatial Alignment)
# ============================================================

source /usr/local/fsl/etc/fslconf/fsl.sh
export FSLOUTPUTTYPE=NIFTI_GZ

# --- Logging ---
log_file="$HOME/flirtconvert.log"
: > "$log_file"
echo "=== Starting FLIRT + CONVERT ===" | tee -a "$log_file"

# --- Directories ---
ants_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/ANTs"
topup_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/TOPUP"
transform_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/TRANSFORMS"
template_ref="/usr/local/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz"

mkdir -p "$transform_base"

# --- Function: Run FLIRT + CONVERT for one subject ---
process_subj() {
    subj="$1"
    subj_ants="$ants_base/$subj"
    subj_topup="$topup_base/$subj/topup_output"
    subj_out="$transform_base/$subj"
    mkdir -p "$subj_out"

    t1_brain="$subj_ants/${subj}_BrainExtractionBrain.nii.gz"
    b0_brain="$subj_topup/${subj}_topup_Tmean_brain.nii.gz"

    # Skip if missing input
    if [[ ! -f "$t1_brain" || ! -f "$b0_brain" ]]; then
        echo "!!! [$subj] Missing input(s), skipping" | tee -a "$log_file"
        return
    fi

    echo ">>> [$subj] Running FLIRT + CONVERT" | tee -a "$log_file"

    flirt -in "$b0_brain" -ref "$t1_brain" \
        -omat "$subj_out/diff2str_${subj}.mat" \
        -searchrx -90 90 -searchry -90 90 -searchrz -90 90 \
        -dof 6 -cost corratio

    convert_xfm -omat "$subj_out/str2diff_${subj}.mat" \
        -inverse "$subj_out/diff2str_${subj}.mat"

    flirt -in "$t1_brain" -ref "$template_ref" \
        -omat "$subj_out/str2standard_${subj}.mat" \
        -searchrx -90 90 -searchry -90 90 -searchrz -90 90 \
        -dof 12 -cost corratio

    convert_xfm -omat "$subj_out/standard2str_${subj}.mat" \
        -inverse "$subj_out/str2standard_${subj}.mat"

    convert_xfm -omat "$subj_out/diff2standard_${subj}.mat" \
        -concat "$subj_out/str2standard_${subj}.mat" "$subj_out/diff2str_${subj}.mat"

    convert_xfm -omat "$subj_out/standard2diff_${subj}.mat" \
        -inverse "$subj_out/diff2standard_${subj}.mat"

    echo ">>> [$subj] Done" | tee -a "$log_file"
}

export -f process_subj
export ants_base topup_base transform_base template_ref log_file

# --- Parallel Run ---
subjects=$(ls -1 "$ants_base")
echo "Found $(echo "$subjects" | wc -l) subjects. Running up to 60 in parallel..." | tee -a "$log_file"

echo "$subjects" | xargs -n 1 -P 60 -I {} bash -c 'process_subj "$@"' _ {}

echo "=== All FLIRT + CONVERT jobs finished ===" | tee -a "$log_file"
```

Note: All coding output from this script is recorded in flirtconvert.log

**Flirt and Convert Audit Script**
```bash
#!/bin/bash
# ============================================================
# 🧠 IMPACT DTI — Step 12 Audit: FLIRT + CONVERT Outputs
# ============================================================

ants_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/ANTs"
transform_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/TRANSFORMS"

printf "Subject\tdiff2str\tstr2diff\tstr2standard\tstandard2str\tdiff2standard\tstandard2diff\n"

for subj in $(ls -1 "$ants_base"); do
    subj_dir="$transform_base/$subj"

    d2s=$([ -f "$subj_dir/diff2str_${subj}.mat" ] && echo "✅" || echo "❌")
    s2d=$([ -f "$subj_dir/str2diff_${subj}.mat" ] && echo "✅" || echo "❌")
    s2s=$([ -f "$subj_dir/str2standard_${subj}.mat" ] && echo "✅" || echo "❌")
    st2s=$([ -f "$subj_dir/standard2str_${subj}.mat" ] && echo "✅" || echo "❌")
    d2st=$([ -f "$subj_dir/diff2standard_${subj}.mat" ] && echo "✅" || echo "❌")
    st2d=$([ -f "$subj_dir/standard2diff_${subj}.mat" ] && echo "✅" || echo "❌")

    printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
      "$subj" "$d2s" "$s2d" "$s2s" "$st2s" "$d2st" "$st2d"
done

echo -e "\n=== FLIRT + CONVERT Audit Complete ==="
```

