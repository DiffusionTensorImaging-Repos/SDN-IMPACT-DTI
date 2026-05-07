---
layout: default
title: "Step 7 — Gibbs Ringing Removal + b=250 Cleanup"
parent: "Preprocessing (Steps 1–14)"
nav_order: 7
---

# Step 7 — Gibbs Ringing Removal + b=250 Cleanup

This step does two things:  reduces oscillation artifacts in diffusion MRI caused by Fourier sampling. Additionaly, we remove volumes with b=250 from the `.bvec` and `.bval` files. These volumes can cause instability in downstream tensor modeling.  
   The Olson Lab (and others at Temple) have regularly excluded these volumes, and doing so will not interfere with analyses. (Many labs don't even ***collect*** b=250 for DTI anymore, so this is a safe bet.)

**! Required Software**:

- Note that this step requires MRtrix3 (for following commands: dwidenoise, mrdegibbs, dwiextract).

Since MRtrix3 was not originally available on the LINUX, I cloned and built it manually:
```bash
cd /data/tools
git clone https://github.com/MRtrix3/mrtrix3.git
cd mrtrix3
./configure
/data/tools/mrtrix3$ ./build ##this won't add the GUI features, which depend on specific modules (QtSvg, QtOpenGL) not in the Linux, and we won't need them. 
```
Then we added it to the PATH (so commands are globally available):
```
export PATH=/data/tools/mrtrix3/bin:$PATH
```

**Our code will use the following Inputs**:
- Gradient tables (per subject):  
  - `NIFTI/<subj>/dti/cmrr_mb3hydi_ipat2_64ch/<subj>_cmrr_mb3hydi_ipat2_64ch.bval`  
  - `NIFTI/<subj>/dti/cmrr_mb3hydi_ipat2_64ch/<subj>_cmrr_mb3hydi_ipat2_64ch.bvec`  
- NIfTI data (per subject):  
  - `NIFTI/<subj>/dti/cmrr_mb3hydi_ipat2_64ch/<subj>_cmrr_mb3hydi_ipat2_64ch.nii.gz`

**Outputs (per subject)**:
```
denoise/<subj>/
├── dwidenoise/              → noise map + denoised volume
├── mrdegibbs/               → Gibbs-corrected volume
└── mrdegibbs_no_b250/       → final cleaned volume + modified .bval / .bvec
```


**And -  it will use the following functions from MrTRIX dwidenoise, mrdegibbs, dwiextract, which will be called using the following structure:**
```
dwidenoise dwi.nii.gz dwi_denoised.nii.gz -mask brain_mask.nii.gz -noise noise_map.nii.gz

 mrdegibbs dwi_denoised.nii.gz dwi_denoised_degibbs.nii.gz

dwiextract dwi_denoised_degibbs.nii.gz dwi_no_b250.nii.gz -fslgrad dwi.bvec dwi.bval -shells 0,1000,2000,3250,5000 -export_grad_fsl dwi_no_b250.bvec dwi_no_b250.bval
```


---

**Notes**: 

- Because it will take some time to finish across ~60 subjects, it’s best to run the script with nohup (in the background) so it survives SSH disconnects.
- We run one subject at a time. Mrdegibbs is multithreaded by default and will use all available CPU cores for a single subject. If you try to run many subjects in parallel, they compete for the same cores and slow each other down. Therefore, the most efficient approach is to run jobs sequentially (1 at a time) — each finishes quickly because it uses the whole available CPU.

---

**To run The Bash Code in Nohup**
1. **Create the `run_denoise.sh` script**
Open nano to create the script file:
```bash
nano run_denoise.sh
```
2. **Paste the following into nano:**
```bash
#!/bin/bash

# Step 7: Gibbs ringing removal + b=250 cleanup (sequential version)

denoise_dir="/data/projects/STUDIES/IMPACT/DTI/derivatives/denoise"
nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
topup_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/TOPUP"

# Add MRtrix to PATH (adjust if installed elsewhere)

for subj in $(ls -1 "$nifti_base"); do
    echo ">>> [$subj] Starting denoise + mrdegibbs + b=250 cleanup"

    subj_dir="$nifti_base/$subj/dti"
    # Auto-detect .nii or .nii.gz for DWI
    dwi_file=$(ls "$subj_dir/${subj}_dwi.nii"* 2>/dev/null | head -n1)
    bval_file="$subj_dir/${subj}_dwi.bval"
    bvec_file="$subj_dir/${subj}_dwi.bvec"
    mask_file="$topup_base/$subj/topup_output/${subj}_topup_Tmean_brain_mask.nii.gz"

    # Skip subject if files are missing
    if [[ ! -f "$dwi_file" || ! -f "$bval_file" || ! -f "$bvec_file" || ! -f "$mask_file" ]]; then
        echo "!!! [$subj] Missing input files, skipping"
        continue
    fi

    out_subj="$denoise_dir/$subj"
    mkdir -p "$out_subj/dwidenoise" "$out_subj/mrdegibbs" "$out_subj/mrdegibbs_no_b250"

    # Step 1: Denoise
    dwidenoise \
        -mask "$mask_file" \
        -noise "$out_subj/dwidenoise/${subj}_noise_map.nii.gz" \
        "$dwi_file" \
        "$out_subj/dwidenoise/${subj}_denoised.nii.gz" -force

    # Step 2: Gibbs ringing removal
    mrdegibbs \
        "$out_subj/dwidenoise/${subj}_denoised.nii.gz" \
        "$out_subj/mrdegibbs/${subj}_denoised_degibbs.nii.gz" -force

    # Step 3: Remove b=250 shell from data (keep 0,1000,2000,3250,5000)
    dwiextract \
        "$out_subj/mrdegibbs/${subj}_denoised_degibbs.nii.gz" \
        -fslgrad "$bvec_file" "$bval_file" \
        -shells 0,1000,2000,3250,5000 \
        "$out_subj/mrdegibbs_no_b250/${subj}_dwi_no_b250.nii.gz" \
        -export_grad_fsl \
        "$out_subj/mrdegibbs_no_b250/${subj}_dwi_no_b250.bvec" \
        "$out_subj/mrdegibbs_no_b250/${subj}_dwi_no_b250.bval" \
        -force

    echo ">>> [$subj] Done"
done

echo "=== All subjects finished (sequential run) ==="


```
3. **Save and exit nano:**
Press Ctrl+O then Enter to save
Press Ctrl+X to close

4. **Make the script runnable**
```bash
 chmod +x run_denoise.sh 
 ```

5. **Run with nohup so it survives SSH disconnects**
```bash
 nohup ./run_denoise.sh >denoise.log 2>&1 & 
 ```
6. **Watch progress in real time**
We can still watch the progress even though it is running outside of the ssh!
```bash
tail -f denoise.log
```
Even if you disconnect, the job keeps running. When you reconnect later, you can just run the same tail -f topup.log command to pick up the log again.

**Outputs For each subject:**
```
derivatives/denoise/s1000/mrdegibbs_no_b250/
│
├── 1000_modified_bvec.bvec
├── 1000_mrdegibbs.nii.gzata
```

**Audit Script to ensure proper execution of this step:**
```bash
#!/bin/bash
# Audit Step 9: Denoise + mrdegibbs + b=250 cleanup

denoise_dir="/data/projects/STUDIES/IMPACT/DTI/derivatives/denoise"
nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"

printf "Subject\tNoiseMap\tDenoisedDegibbs\tNoB250\tBvec\tBval\n"

for subj in $(ls -1 "$nifti_base"); do
    out_subj="$denoise_dir/$subj"

    noise_map="$out_subj/dwidenoise/${subj}_noise_map.nii.gz"
    degibbs="$out_subj/mrdegibbs/${subj}_denoised_degibbs.nii.gz"
    nob250="$out_subj/mrdegibbs_no_b250/${subj}_dwi_no_b250.nii.gz"
    nob250_bvec="$out_subj/mrdegibbs_no_b250/${subj}_dwi_no_b250.bvec"
    nob250_bval="$out_subj/mrdegibbs_no_b250/${subj}_dwi_no_b250.bval"

    [[ -f "$noise_map" ]] && noise_stat="✅" || noise_stat="❌"
    [[ -f "$degibbs" ]] && degibbs_stat="✅" || degibbs_stat="❌"
    [[ -f "$nob250" ]] && nob250_stat="✅" || nob250_stat="❌"
    [[ -f "$nob250_bvec" ]] && bvec_stat="✅" || bvec_stat="❌"
    [[ -f "$nob250_bval" ]] && bval_stat="✅" || bval_stat="❌"

    printf "%s\t%s\t%s\t%s\t%s\t%s\n" "$subj" "$noise_stat" "$degibbs_stat" "$nob250_stat" "$bvec_stat" "$bval_stat"
done
```
---
