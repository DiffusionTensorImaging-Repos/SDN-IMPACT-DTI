---
layout: default
title: "Step 9: BedpostX"
parent: "Preprocessing (Steps 1–14)"
nav_order: 9
---

# Step 9: BedpostX

FSL BEDPOSTX (Bayesian Estimation of Diffusion Parameters Obtained using Sampling Techniques) fits a multi-fiber diffusion model at each voxel.

- Uses Markov Chain Monte Carlo (MCMC) sampling to estimate distributions of fiber orientations.
- Provides the probabilistic fiber model that is required for probabilistic tractography (probtrackx2).
- Without this step, tractography would assume only a single tensor per voxel, missing crossing/kissing fibers and producing biased streamlines.

**Inputs (per subject)**

- * Note - make sure to use the version of eddy output with outliers replaced (see below)
From eddy step: 
- <subj>_eddy.eddy_outlier_free_data.nii.gz → eddy-corrected DWI (with repol; falls back to <subj>_eddy.nii.gz if not present)
- <subj>_eddy.eddy_rotated_bvecs → rotated b-vectors
- <subj>_dwi_no_b250.bval (from denoise step, unchanged by eddy) → b-values

From topup: 
- nodif_brain_mask.nii.gz → brain mask (collapsed b0)

The code will create a folder, derivatives/bedpostx_input, and rename the eddy files to FSL expected files names

**Outputs (per subject)**
```
derivatives/BEDPOSTX/s1000/
│
├── bedpostx_input/                      # input directory prepared for bedpostx
│   ├── data.nii.gz                      # eddy-corrected diffusion data
│   ├── bvecs                            # eddy-rotated gradient directions
│   ├── bvals                            # corresponding b-values
│   └── nodif_brain_mask.nii.gz          # binary brain mask (from TOPUP mean b0)
│
└── bedpostx_input.bedpostX/             # main output directory created by bedpostx
    ├── dyads1.nii.gz                    # principal fiber orientation (direction)
    ├── mean_f1samples.nii.gz            # mean fiber fraction (fiber 1)
    ├── mean_th1samples.nii.gz           # mean theta (fiber 1)
    ├── mean_ph1samples.nii.gz           # mean phi (fiber 1)
    ├── merged_f1samples.nii.gz          # merged MCMC samples for fiber 1
    ├── merged_th1samples.nii.gz         # merged MCMC samples for theta (fiber 1)
    ├── merged_ph1samples.nii.gz         # merged MCMC samples for phi (fiber 1)
    ├── merged_f2samples.nii.gz          # merged MCMC samples for fiber 2
    ├── merged_th2samples.nii.gz         # merged MCMC samples for theta (fiber 2)
    ├── merged_ph2samples.nii.gz         # merged MCMC samples for phi (fiber 2)
    ├── merged_f3samples.nii.gz          # merged MCMC samples for fiber 3
    ├── merged_th3samples.nii.gz         # merged MCMC samples for theta (fiber 3)
    └── merged_ph3samples.nii.gz         # merged MCMC samples for phi (fiber 3)

 ```

- **Note:** Unlike TOPUP/EDDY, which is moderately parallel and safe to run many subjects at once, BEDPOSTX is far more CPU-intensive, using MCMC sampling voxel-by-voxel. We cap threads per job (e.g., 4) and then parallelize across subjects dynamically, so the node stays busy without oversubscribing cores.

Because this is going to run for a long time, we will run the script in nohup, so it survives SSH disruptions. 

1. Create the run_topup.sh script Open nano to create the script file:
```bash
nano run_bedpostx.sh
```
Paste the following into nano: 

```bash
#!/bin/bash
# ============================================================
# Step 9: BEDPOSTX (IMPACT DTI)
# ============================================================
# Prepares inputs and runs bedpostx for each subject
# Dynamically parallelizes across available cores
# Outputs go to: derivatives/BEDPOSTX/<subj>.bedpostX/
# ============================================================

set -u -o pipefail

# --- Paths ---
nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
eddy_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/EDDY"
denoise_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/denoise"
topup_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/TOPUP"
bedpostx_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/BEDPOSTX"

mkdir -p "$bedpostx_base"

# --- Dynamic resource detection ---
ncores=$(nproc)              # total CPU cores
threads_per_job=4            # cores used *inside* each bedpostx
max_jobs=$(( ncores / threads_per_job ))

echo "Detected $ncores cores → running up to $max_jobs jobs in parallel"
export OMP_NUM_THREADS=$threads_per_job
export MKL_NUM_THREADS=$threads_per_job
export OPENBLAS_NUM_THREADS=$threads_per_job
export NUMEXPR_NUM_THREADS=$threads_per_job

# --- Subject processing function ---
process_subj() {
    subj=$1
    echo ">>> [$subj] Preparing and running bedpostx"

    out_dir="$bedpostx_base/$subj"
    mkdir -p "$out_dir/bedpostx_input"

    # Copy and rename into FSL’s expected filenames
    cp "$eddy_base/$subj/${subj}_eddy.nii.gz"                  "$out_dir/bedpostx_input/data.nii.gz"
    cp "$eddy_base/$subj/${subj}_eddy.eddy_rotated_bvecs"      "$out_dir/bedpostx_input/bvecs"
    cp "$denoise_base/$subj/mrdegibbs_no_b250/${subj}_modified_bval.bval" \
       "$out_dir/bedpostx_input/bvals"
    cp "$topup_base/$subj/topup_output/${subj}_topup_Tmean_brain_mask.nii.gz" \
       "$out_dir/bedpostx_input/nodif_brain_mask.nii.gz"

    # Run bedpostx
    bedpostx "$out_dir/bedpostx_input"
}

export -f process_subj
export eddy_base denoise_base topup_base bedpostx_base

# --- Loop through subjects with job control ---
subjects=$(ls -1 "$nifti_base")

job_count=0
for subj in $subjects; do
    process_subj "$subj" &
    ((job_count++))
    if (( job_count >= max_jobs )); then
        wait -n
        ((job_count--))
    fi
done

wait
echo "=== All BEDPOSTX jobs finished ==="

```
3. Save and exit nano: Press Ctrl+O then Enter to save Press Ctrl+X to close

4. Make the script runnable
```bash
 chmod +x run_bedpostx.sh 
```
5. Run with nohup so it survives SSH disconnections
```bash
 nohup ./run_bedpostx.sh > bedpostx.log 2>&1 & 
```
6. Watch progress in real time We can still watch the progress even though it is running outside of the ssh!
```bash
tail -f bedpostx.log
```
Even if you disconnect, the job keeps running. When you reconnect later, you can just run the same tail -f topup.log command to pick up the log again. This log will also be SAVED and can be checked later if you encounter errors

**Audit script to make sure that bedpostx was run properly for each participant**
```bash
#!/bin/bash
# ============================================================
# Simple BEDPOSTX Audit (IMPACT DTI)
# ============================================================
# Checks only the main expected outputs:
# dyads1, mean_f1/th1/ph1, merged f/th/ph (fibers 1–3)
# ============================================================

nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
bedpostx_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/BEDPOSTX"

printf "Subject\tdyads1\tmean_f1\tmean_th1\tmean_ph1\tf1\tth1\tph1\tf2\tth2\tph2\tf3\tth3\tph3\n"

for subj in $(ls -1 "$nifti_base"); do
    subj_dir="$bedpostx_base/$subj/bedpostx_input.bedpostX"

    dyads=$([ -f "$subj_dir/dyads1.nii.gz" ] && echo "✅" || echo "❌")
    meanf1=$([ -f "$subj_dir/mean_f1samples.nii.gz" ] && echo "✅" || echo "❌")
    meanth1=$([ -f "$subj_dir/mean_th1samples.nii.gz" ] && echo "✅" || echo "❌")
    meanph1=$([ -f "$subj_dir/mean_ph1samples.nii.gz" ] && echo "✅" || echo "❌")

    f1=$([ -f "$subj_dir/merged_f1samples.nii.gz" ] && echo "✅" || echo "❌")
    th1=$([ -f "$subj_dir/merged_th1samples.nii.gz" ] && echo "✅" || echo "❌")
    ph1=$([ -f "$subj_dir/merged_ph1samples.nii.gz" ] && echo "✅" || echo "❌")

    f2=$([ -f "$subj_dir/merged_f2samples.nii.gz" ] && echo "✅" || echo "❌")
    th2=$([ -f "$subj_dir/merged_th2samples.nii.gz" ] && echo "✅" || echo "❌")
    ph2=$([ -f "$subj_dir/merged_ph2samples.nii.gz" ] && echo "✅" || echo "❌")

    f3=$([ -f "$subj_dir/merged_f3samples.nii.gz" ] && echo "✅" || echo "❌")
    th3=$([ -f "$subj_dir/merged_th3samples.nii.gz" ] && echo "✅" || echo "❌")
    ph3=$([ -f "$subj_dir/merged_ph3samples.nii.gz" ] && echo "✅" || echo "❌")

    printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
      "$subj" "$dyads" "$meanf1" "$meanth1" "$meanph1" \
      "$f1" "$th1" "$ph1" "$f2" "$th2" "$ph2" "$f3" "$th3" "$ph3"
done

echo -e "\n=== BEDPOSTX Audit Finished ==="
```
---
