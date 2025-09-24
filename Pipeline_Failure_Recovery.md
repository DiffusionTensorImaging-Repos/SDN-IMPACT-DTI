# 🔄 How to Backtrack for Failed Participants  

This is an example of how to **backtrack for one or more participants** who did not successfully complete a step of the pipeline and for whom you may need to audit or re-run previous steps.  

Here, the example comes from a case where **EDDY worked for most but failed for one participant**. But the same logic applies to **any step** in the preprocessing chain where the correct output cannot be created for a subset of participants.  



## 1. Inspect the Logs  

Whenever a participant fails, the first step is to **check the logs**. You can search for that subject’s ID in the log file:  

```bash
grep -A20 "s4440" eddy.log
```
This command finds the subject ID in the log and prints 20 lines after it. You can use this same approach for any log file in the pipeline (ANTs, TOPUP, denoise, etc.).

**In our case:**
The log showed the error:

```
Error : short read, file may be truncated
EDDY::: Eddy failed with message ... Exception thrown
```
This means the .nii.gz file existed but was corrupted / incomplete.

## 2. Check for Input Files

We then checked whether the inputs existed. Even though you would have check this when they were output from previous steps, it's good to make sure. 

Here we use the ls -lh function to check for the existence of the input files for a specific participan: 

``` bash
ls -lh /data/projects/STUDIES/IMPACT/DTI/derivatives/denoise/s4440/mrdegibbs_no_b250/s4440_dwi_no_b250.nii.gz

ls -lh /data/projects/STUDIES/IMPACT/DTI/derivatives/TOPUP/s4440/topup_output/s4440_topup_Tmean_brain_mask.nii.gz
```
Both files were present, but because eddy couldn’t read them, we knew the problem was corruption from a previous step, not a missing file.

## 3. Re-run All Steps for That Subject

To fix this, we wrote a rescue script that backtracks and re-runs the necessary steps for the failed subject.

For eddy failures, this means: 
1.  Re-running denoise + mrdegibbs + b=250 cleanup to rebuild a clean dwi_no_b250.nii.gz.

2. Re-running EDDY with the corrected input.

3. Auditing outputs to confirm success.

***But this principle applies to any step — if TOPUP failed, you would re-run from B0 concat → TOPUP → audit, etc.***

## 4. Rescue Script (rerunning all steps for a participant)

Follow these steps to create the rescue script:

* Note - we're going to want to run this in nohup becuase it may take a little while. 

1. Open nano
```bash
nano rescue.sh
```
2. Enter the following script into nano: 
(Note this script isolates the functions from each of the previous steps and stacks them to run them sequentially)
```bash
#!/bin/bash
# ============================================================
# rescue.sh — Re-run preprocessing + EDDY for a single subject
# ============================================================

subj="s4440"   # Replace with participant ID to backtrack

# --- Base directories ---
nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
denoise_dir="/data/projects/STUDIES/IMPACT/DTI/derivatives/denoise"
topup_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/TOPUP"
eddy_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/EDDY"

acq_params_file="/data/projects/STUDIES/IMPACT/DTI/config/acqp.txt"
index_file="/data/projects/STUDIES/IMPACT/DTI/config/index_no_b250.txt"

# --- MRtrix setup ---
# Edit this path if mrtrix3 is installed somewhere else on your cluster
export PATH=/data/tools/mrtrix3/bin:$PATH

# Check for MRtrix commands
for cmd in dwidenoise mrdegibbs dwiextract; do
    if ! command -v $cmd &>/dev/null; then
        echo "❌ ERROR: $cmd not found in PATH. Load MRtrix3 before running."
        exit 1
    fi
done

# --- Step 1: Re-run denoise + mrdegibbs + b=250 cleanup ---
echo ">>> [$subj] Re-running denoise + mrdegibbs + b=250 cleanup"

subj_dir="$nifti_base/$subj/dti"
dwi_file=$(ls "$subj_dir/${subj}_dwi.nii"* 2>/dev/null | head -n1)
bval_file="$subj_dir/${subj}_dwi.bval"
bvec_file="$subj_dir/${subj}_dwi.bvec"
mask_file="$topup_base/$subj/topup_output/${subj}_topup_Tmean_brain_mask.nii.gz"

out_subj="$denoise_dir/$subj"
mkdir -p "$out_subj/dwidenoise" "$out_subj/mrdegibbs" "$out_subj/mrdegibbs_no_b250"

# Denoise
dwidenoise \
    -mask "$mask_file" \
    -noise "$out_subj/dwidenoise/${subj}_noise_map.nii.gz" \
    "$dwi_file" \
    "$out_subj/dwidenoise/${subj}_denoised.nii.gz" -force

# Gibbs ringing removal
mrdegibbs \
    "$out_subj/dwidenoise/${subj}_denoised.nii.gz" \
    "$out_subj/mrdegibbs/${subj}_denoised_degibbs.nii.gz" -force

# Remove b=250 shell
dwiextract \
    "$out_subj/mrdegibbs/${subj}_denoised_degibbs.nii.gz" \
    -fslgrad "$bvec_file" "$bval_file" \
    -shells 0,1000,2000,3250,5000 \
    "$out_subj/mrdegibbs_no_b250/${subj}_dwi_no_b250.nii.gz" \
    -export_grad_fsl \
    "$out_subj/mrdegibbs_no_b250/${subj}_dwi_no_b250.bvec" \
    "$out_subj/mrdegibbs_no_b250/${subj}_dwi_no_b250.bval" \
    -force

echo ">>> [$subj] Denoise + mrdegibbs complete"

# --- Step 2: Re-run EDDY ---
echo ">>> [$subj] Running EDDY"

mrdegibbs_dir="$denoise_dir/$subj/mrdegibbs_no_b250"
topup_dir="$topup_base/$subj/topup_output"
out_dir="$eddy_base/$subj"
mkdir -p "$out_dir"

eddy \
    --imain="$mrdegibbs_dir/${subj}_dwi_no_b250.nii.gz" \
    --mask="$topup_dir/${subj}_topup_Tmean_brain_mask.nii.gz" \
    --acqp="$acq_params_file" \
    --index="$index_file" \
    --bvecs="$mrdegibbs_dir/${subj}_dwi_no_b250.bvec" \
    --bvals="$mrdegibbs_dir/${subj}_dwi_no_b250.bval" \
    --topup="$topup_dir/${subj}_topup" \
    --out="$out_dir/${subj}_eddy" \
    --cnr_maps \
    --repol \
    -v

echo ">>> [$subj] Rescue run complete"

```

3. Save and exit nano

- Press Ctrl+O + Enter to save

- Press Ctrl+X to close

4. Make it executable
```bash
chmod +x rescue.sh
```
5. Run with nohup so it survives SSH disconnections:
```bash
nohup ./rescue.sh > rescue.log 2>&1 &
```
6. Check progress:
``` bash
tail -f rescue.log
```

- Even if you disconnect, the job keeps running. When you reconnect later, you can just run the same tail -f rescue.log command to pick up the log again.

## 5. Auditing

Once the re-run is complete, use the same audit scripts provided in the full pipeline guide (for denoise, eddy, topup, etc.) to confirm. 