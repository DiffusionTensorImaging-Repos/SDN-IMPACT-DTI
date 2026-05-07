---
layout: default
title: "Step 4 — TOPUP Susceptibility Distortion Correction"
parent: "Preprocessing (Steps 1–14)"
nav_order: 4
---

# Step 4 — TOPUP Susceptibility Distortion Correction

**TOPUP corrects for **susceptibility-induced geometric distortions** in diffusion-weighted MRI**

- By using the AP and PA b0s created in Step 6, TOPUP estimates the susceptibility field and produces corrected reference images. These corrected b0s are essential for accurate alignment and later diffusion preprocessing.



The following steps accomplished by our code..
1. Create an output directory for TOPUP results inside each subject’s `dti/` folder.  
2. Use the merged AP/PA b0 file  from the previous step(`<subj>_merged_b0s.nii.gz`) as input to TOPUP.  
3. Call in an acquisition parameters file (`acqp.txt`) that specifies phase encoding direction and readout time.  
4. TOPUP outputs corrected b0 images and a displacement field for later use.  



**! IMPORTANT: Configuration File needed:** 
![acqp]({{ "/images/acqp.png" | relative_url }})


This file tells TOPUP how the scans were collected. Each row is one scan (AP or PA) and describes:  
- **Direction of phase encoding** (whether distortion runs front-to-back or back-to-front).  
- **How long the readout took** (the time distortions can build up).  
- It can be found here: -`/data/projects/STUDIES/IMPACT/DTI/config/acqp.txt`  
- With both directions listed, TOPUP can figure out how the distortions flip and then fix them in the diffusion data.


For the TOPUP code, the following input, produced by the previous steps is needed: 

**Expected Input (per subject)**
- `NIFTI/<subj>/dti/<subj>_merged_b0s.nii.gz` (from Step 6)  
- Acquisition parameters file:  `/data/projects/STUDIES/IMPACT/DTI/config/acqp.txt`  

Topup will use the "topup" FSL function, and the topup call will use the following sturcture:
```
topup --imain="$b0_file" \
      --datain="$datain_file" \
      --config="$config_file" \
      --out="$output_prefix" \
      --iout="${output_prefix}_corrected_b0" \
      --fout="${output_prefix}_fieldmap" \
      --verbose
```

Before implimenting this code, I conducted a quick
**System RAM check**

```bash
free -h

              total        used        free      shared  buff/cache   available
Mem:          125Gi       9.7Gi        54Gi        60Mi        61Gi       114Gi
Swap:         2.0Gi          0B       2.0Gi

```
TOPUP is more demanding than earlier steps. Even though the system has plenty of RAM, I/O and CPU load can still cause failures when too many jobs run at once. To keep things stable, we cap parallel jobs at 18 (max_jobs=18).

**How to run The Bash Code in Nohup**

1. **Create the `run_topup.sh` script**
Open nano to create the script file:
```bash
nano run_topup.sh
```

2. **Paste the following into nano:**
```Bash
#!/bin/bash

# Step 4: TOPUP (susceptibility distortion correction)

nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
b0_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/b0_concat"
deriv_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/TOPUP"
datain_file="/data/projects/STUDIES/IMPACT/DTI/config/acqp.txt"
config_file="/usr/local/fsl/etc/flirtsch/b02b0_1.cnf"

process_subj() {
    subj=$1
    b0_file="$b0_base/$subj/${subj}_merged_b0s.nii.gz"
    output_dir="$deriv_base/$subj/topup_output"
    mkdir -p "$output_dir"

    output_prefix="$output_dir/${subj}_topup"

    # Skip if outputs already exist
    if [[ -f "${output_prefix}_corrected_b0.nii.gz" && -f "${output_prefix}_fieldmap.nii.gz" ]]; then
        echo "=== [$subj] Already has TOPUP outputs, skipping"
        return
    fi

    if [ ! -f "$b0_file" ]; then
        echo "!!! [$subj] Missing merged b0 input, skipping"
        return
    fi

    echo ">>> [$subj] Running TOPUP"
    topup --imain="$b0_file" --datain="$datain_file" \
          --config="$config_file" \
          --out="$output_prefix" \
          --iout="${output_prefix}_corrected_b0" \
          --fout="${output_prefix}_fieldmap" \
          --verbose
    echo ">>> [$subj] Done"
}

export -f process_subj
export nifti_base b0_base deriv_base datain_file config_file

subjects=$(basename -a "$nifti_base"/*)

echo "Found $(echo $subjects | wc -w) subjects in $nifti_base"

# Run in parallel: up to 18 jobs at once
if command -v parallel > /dev/null; then
    echo "$subjects" | tr ' ' '\n' | parallel -j 18 process_subj {}
else
    max_jobs=18
    for subj in $subjects; do
        process_subj "$subj" &
        while [ "$(jobs -r | wc -l)" -ge "$max_jobs" ]; do
            sleep 1
        done
    done
    wait
fi

echo "=== All TOPUP jobs finished ==="


```

3. **Save and exit nano:**
Press Ctrl+O then Enter to save
Press Ctrl+X to close

4. **Make the script runnable**
```bash
 chmod +x run_topup.sh 
 ```
5. **Run with nohup so it survives SSH disconnections**
```bash
 nohup ./run_topup.sh > topup.log 2>&1 & 
 ```

6. **Watch progress in real time**
We can still watch the progress even though it is running outside of the ssh!
```bash
tail -f topup.log
```
Even if you disconnect, the job keeps running. When you reconnect later, you can just run the same tail -f topup.log command to pick up the log again. **This log will also be SAVED and can be checked later if you encounter errors**

**Expected Output**:
```
derivatives/TOPUP/s100/topup_output/
│
├── s1000_topup.nii.gz
├── s1000_topup_corrected_b0.nii.gz
├── s1000_topup_fieldmap.nii.gz

derivatives/TOPUP/s1323/topup_output/
├── s1323_topup.nii.gz
├── s1323_topup_corrected_b0.nii.gz
├── s1323_topup_fieldmap.nii.gz
│
└── ...
```
Notes
* _topup.nii.gz → combined corrected image (TOPUP’s direct output, less commonly used than the corrected_b0)
* _corrected_b0.nii.gz → distortion-corrected baseline images
* _fieldmap.nii.gz → estimated field distortion map

**These outputs will be used in eddy motion corrections in following steps.**

**Here is a Topup Audit to check that conversion and file org was succesful**

```bash
#!/bin/bash
# Robust audit for TOPUP outputs (handles prefixed/unprefixed names)

nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"

printf "Subject\tCorrected_b0\tFieldmap\tTopupCore\n"

for subj in $(ls -1 "$nifti_base"); do
    out_dir="$nifti_base/$subj/dti/topup_output"

    corrected=$(find "$out_dir" -maxdepth 1 -type f -name "*corrected*b0*.nii*" 2>/dev/null | head -n1)
    fieldmap=$(find "$out_dir" -maxdepth 1 -type f \( -name "*fieldmap*.nii*" -o -name "fout*.nii*" \) 2>/dev/null | head -n1)
    topupcore=$(find "$out_dir" -maxdepth 1 -type f \( -name "*fieldcoef*.nii*" -o -name "*movpar*.txt" -o -name "*log*.txt" \) 2>/dev/null | head -n1)

    [[ -n "$corrected" ]] && cstat="✅" || cstat="❌"
    [[ -n "$fieldmap" ]] && fstat="✅" || fstat="❌"
    [[ -n "$topupcore" ]] && tstat="✅" || tstat="❌"

    printf "%s\t%s\t%s\t%s\n" "$subj" "$cstat" "$fstat" "$tstat"
done

```
---

