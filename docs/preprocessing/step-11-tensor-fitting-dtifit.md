---
layout: default
title: "Step 11 Tensor Fitting (DTIFIT)"
parent: "Preprocessing (Steps 1–14)"
nav_order: 11
---

# Step 11 Tensor Fitting (DTIFIT)

After extracting the desired diffusion shells (b=0, 1000), the next step is to fit a diffusion tensor model to each participant’s DWI data. This is done using FSL’s dtifit, which estimates voxelwise diffusion tensor parameters including fractional anisotropy (FA), mean diffusivity (MD), axial diffusivity (AD/L1), and radial diffusivity (RD, derived as the mean of L2 and L3).

* Note: This model assumes diffusion is Gaussian within each voxel, which holds true at lower b-values (≤1000 s/mm²).Including higher shells (e.g., b=2000) can bias tensor estimates, so for DTIFIT, we restrict input to b=0 and b=1000 volumes.

The DTIFIT tool requires four key inputs per subject:
1. The diffusion-weighted image (data_1000.nii.gz)
2. Corresponding gradient direction files (bvecs_1000, bvals_1000)
3. A binary brain mask to constrain tensor fitting to brain voxels
4. An output prefix to specify where to save resulting tensor maps

**Expected Input structure:**
1. DWI data (b=0 and 1000 only):
- /data/projects/STUDIES/IMPACT/DTI/derivatives/mrtrix3_1000/<subj>/data_1000.nii.gz
2. Gradient tables:
- /data/projects/STUDIES/IMPACT/DTI/derivatives/mrtrix3_1000/<subj>/bvecs_1000
- /data/projects/STUDIES/IMPACT/DTI/derivatives/mrtrix3_1000/<subj>/bvals_1000
3. Brain mask:
/data/projects/STUDIES/IMPACT/DTI/derivatives/TOPUP/<subj>/topup_output/<subj>_topup_Tmean_brain_mask.nii.gz

**Outputs (per subject):**
```
derivatives/DTIFIT_OUTPUT/s1000/
│
├── DTI_FA.nii.gz      # fractional anisotropy map (0–1, white-matter integrity)
├── DTI_MD.nii.gz      # mean diffusivity map (overall diffusion magnitude)
├── DTI_L1.nii.gz      # axial diffusivity (principal eigenvalue)
├── DTI_L2.nii.gz      # secondary eigenvalue
├── DTI_L3.nii.gz      # tertiary eigenvalue
└── DTI_RD.nii.gz      # radial diffusivity, computed as (L2 + L3) / 2
```


**This task is very lightweight, and thus can be pasted directly in the SSH terminal and easily parallelized acorss all 60 participants. If you have more participants than this, you can adjust accordingly.** 

**Paste the following into the terminal**: 

```bash
#!/bin/bash
# ============================================================
# 🧠 IMPACT DTI — Step 11: Tensor Fitting (DTIFIT)
# ============================================================

source /usr/local/fsl/etc/fslconf/fsl.sh
export FSLOUTPUTTYPE=NIFTI_GZ

# --- Safe logging (no exec redirection, no SSH close) ---
log_file="$HOME/dtifit.log"
: > "$log_file"
echo "=== Starting DTIFIT ===" | tee -a "$log_file"

# --- Base directories ---
mrtrix3_1000_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/mrtrix3_1000"
topup_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/TOPUP"
dtifit_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/DTIFIT_OUTPUT"
mkdir -p "$dtifit_base"

# --- Function ---
process_subj() {
    subj="$1"
    subj_mrtrix="$mrtrix3_1000_base/$subj"
    subj_topup="$topup_base/$subj/topup_output"
    subj_out="$dtifit_base/$subj"
    mkdir -p "$subj_out"

    data="$subj_mrtrix/data_1000.nii.gz"
    bvec="$subj_mrtrix/bvecs_1000"
    bval="$subj_mrtrix/bvals_1000"
    mask="$subj_topup/${subj}_topup_Tmean_brain_mask.nii.gz"

    if [[ ! -f "$data" || ! -f "$bvec" || ! -f "$bval" || ! -f "$mask" ]]; then
        echo "!!! [$subj] Missing input(s). Skipping." | tee -a "$log_file"
        return
    fi

    echo ">>> [$subj] Running DTIFIT" | tee -a "$log_file"
    {
        dtifit -k "$data" -o "$subj_out/DTI" -m "$mask" -r "$bvec" -b "$bval"

        if [[ -f "$subj_out/DTI_L2.nii.gz" && -f "$subj_out/DTI_L3.nii.gz" ]]; then
            echo ">>> [$subj] Calculating RD = (L2+L3)/2"
            fslmaths "$subj_out/DTI_L2.nii.gz" -add "$subj_out/DTI_L3.nii.gz" \
                     -div 2 "$subj_out/DTI_RD.nii.gz"
        else
            echo "!!! [$subj] Missing L2/L3 for RD computation"
        fi

        echo ">>> [$subj] Done"
    } 2>&1 | tee -a "$log_file"
}

export -f process_subj
export mrtrix3_1000_base topup_base dtifit_base log_file

# --- Parallel run ---
subjects=$(ls -1 "$mrtrix3_1000_base")
count=$(echo "$subjects" | wc -l)
echo "Found $count subjects. Running up to 60 in parallel..." | tee -a "$log_file"

echo "$subjects" | xargs -n 1 -P 60 -I {} bash -c 'process_subj "$@"' _ {} | tee -a "$log_file"

echo "=== All $count DTIFIT jobs finished successfully ===" | tee -a "$log_file"
```
Note: All coding output from this script is recorded in dtifit.log

**Audit script to ensure DTIFIT ran for everyone**

```bash
#!/bin/bash
###############################################################################
# 🧠 IMPACT DTI — DTIFIT Audit (compare against NIFTI base)
###############################################################################

nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
dtifit_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/DTIFIT_OUTPUT"

printf "Subject\tFA\tMD\tL1\tL2\tL3\tRD\n"

for subj in $(ls -1 "$nifti_base"); do
    out_dir="$dtifit_base/$subj"

    fa="$out_dir/DTI_FA.nii.gz"
    md="$out_dir/DTI_MD.nii.gz"
    l1="$out_dir/DTI_L1.nii.gz"
    l2="$out_dir/DTI_L2.nii.gz"
    l3="$out_dir/DTI_L3.nii.gz"
    rd="$out_dir/DTI_RD.nii.gz"

    fa_chk=$([ -f "$fa" ] && echo "✅" || echo "❌")
    md_chk=$([ -f "$md" ] && echo "✅" || echo "❌")
    l1_chk=$([ -f "$l1" ] && echo "✅" || echo "❌")
    l2_chk=$([ -f "$l2" ] && echo "✅" || echo "❌")
    l3_chk=$([ -f "$l3" ] && echo "✅" || echo "❌")
    rd_chk=$([ -f "$rd" ] && echo "✅" || echo "❌")

    printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
      "$subj" "$fa_chk" "$md_chk" "$l1_chk" "$l2_chk" "$l3_chk" "$rd_chk"
done

echo -e "\n=== DTIFIT Audit Complete ==="
```

