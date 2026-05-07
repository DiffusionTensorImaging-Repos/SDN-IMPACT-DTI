---
layout: default
title: "Step 2 -  ANTs Skull Stripping"
parent: "Preprocessing (Steps 1–14)"
nav_order: 2
---

# Step 2 -  ANTs Skull Stripping

We use **ANTs (Advanced Normalization Tools)**, an open-source software suite for image processing. ANTs is a highly reliable package for brain extraction.  
- ( ANTs’ template-based approach typically produces cleaner extractions than simpler tools (like FSL BET), especially for high-resolution T1 images.)

- **Why it’s needed for DTI:** later diffusion preprocessing (e.g., registration, distortion correction) requires the structural image to be **brain-only**. Extra tissue like skull and scalp can throw off alignment and bias field corrections, so stripping ensures cleaner, accurate DTI processing.


**Locating ANTs skull stripping**: 
- Rather than download the ANTs library, I conducted a search to check if it is already on the Linux:

Type the following into the terminal: 
```bash
find / -type f -name "antsBrainExtraction.sh" 2>/dev/null | head -n 20
```
I confirmed ANTs is available on the lab Linux system under: `data/tools/ANTs/bin`

- **Note**: If you need to download ANTs *yourself* in future implementations, the official repository is here:  https://github.com/ANTsX/ANTs

Next, we add the ANTs functions to path by pasting the following in the terminal: 
```bash
export ANTSPATH="/data/tools/ANTs/bin"
export PATH="$ANTSPATH:$PATH"
```

**Before skull stripping we will set up the template and mask for  skull stripping**:
 
- ANTs (Advanced Normalization Tools) needs a **template image** (a standardized brain) and a **mask** (which defines which parts of that template are “brain” vs. “not-brain”) to guide skull stripping. These act as a reference: your subject’s T1 is aligned to the template, and the mask tells ANTs where to cut off skull, scalp, and neck.

**Which template should I use?**  
- **NKI templates** (from the Enhanced NKI-Rockland sample) are commonly used for **adolescent and adult** data.  
- **OASIS** or **ICBM** templates are sometimes used for older adults.  
- **Custom or age-specific templates** might be needed for pediatric datasets or other special populations.  

**What to check as an RA:**  
- Confirm whether the lab already has suitable templates downloaded (saves time and ensures consistency across projects).  
- Look for a pair within the SAME TEMPLATE (eg., NKI):  
  - `T_template.nii.gz` → the actual template brain.  
  - `T_template_BrainCerebellumMask.nii.gz` → the brain + cerebellum mask.  
  - Type the following into the terminal to conduct this search to see if masks already exist on the Linux: 
```bash
 find / -type f -name "T_template.nii" 2>/dev/null | head -n 20
 find /-type f -name "T_template_BrainCerebellumMask.nii" 2>/dev/null | head -n 20
 ```

- If you don’t find both the template **and** its matching mask for the template type you’re using (e.g., NKI, OASIS, ICBM), download the correct pair from the official ANTs figshare repository:  
https://figshare.com/articles/dataset/ANTs_ANTsR_Brain_Templates/915436
Then save it and reference the brain and mask tamplates for your participants. 

**In our case:**  
- We already found the NKI templates (this template has worked very well on adult data) on the lab Linux under `/data/projects/STUDIES/LEARN/…/ANTs_Images/NKI`. 
- To keep things organized, we copy them into the IMPACT project folder:

Type the following into the terminal:
```bash
mkdir -p /data/projects/STUDIES/IMPACT/DTI/ANTsTemplate/NKI
cd /data/projects/STUDIES/IMPACT/DTI/ANTsTemplate/NKI

cp /data/projects/STUDIES/LEARN/fMRI/NM/ANTs_toolbox/NM_toolbox/ANTs_Images/NKI/T_template.nii.gz \
   /data/projects/STUDIES/IMPACT/DTI/ANTsTemplate/NKI/

cp /data/projects/STUDIES/LEARN/fMRI/NM/ANTs_toolbox/NM_toolbox/ANTs_Images/NKI/T_template_BrainCerebellumMask.nii.gz \
   /data/projects/STUDIES/IMPACT/DTI/ANTsTemplate/NKI/
```

**Now that the masks are set, we can execute the ANTs Skull Stripping.**

Brefore running this, I conduct a System RAM check to help decide how many paritcipants we can tell ANTs to skullstrip at once.

Type the following into the terminal: 

```bash
free -h
```

Example output:
```
              total        used        free      shared  buff/cache   available
Mem:          125Gi       9.7Gi        54Gi        60Mi        61Gi       114Gi
Swap:         2.0Gi          0B       2.0Gi
```

`antsBrainExtraction.sh` typically uses ~2–3 GB per subject.  
With 114 GB free, we could theoretically run ≈38 jobs in parallel (114 ÷ 3).  
To be safe but still efficient, we cap at 30 jobs (max_jobs=30).

**This script will use the antsBrainExtraction.sh function from the ANTs library:** 

**Note** — This step may take a while (1-2 hours), so we run it as a background script in Nohup to avoid it terminating in the case ssh disruptions. Here is how to run The Bash Code in Nohup:

1.  **First, create the `run_ants.sh` script**

Open nano to create the script file:
```bash
nano run_ants.sh
```
 Paste the following into nano:
```bash
#!/bin/bash
# ============================================================
# Parallelized ANTs Skull Stripping for IMPACT (DTI)
# ============================================================

# Paths
ANTs_bin="/data/tools/ants/bin/antsBrainExtraction.sh"
TEMPLATE="/data/projects/STUDIES/IMPACT/DTI/ANTsTemplate/NKI/T_template.nii.gz"
TEMPLATE_MASK="/data/projects/STUDIES/IMPACT/DTI/ANTsTemplate/NKI/T_template_BrainCerebellumMask.nii.gz"
in_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
out_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/ANTs"

# Collect all subject IDs from NIFTI directory
subjects=($(ls -1 "$in_base"))

# Function to process one subject
process_subject () {
    subj_id="$1"
    echo "=== Processing $subj_id ==="

    nii_file="$in_base/$subj_id/struct/${subj_id}_struct.nii"
    out_dir="$out_base/$subj_id"
    mkdir -p "$out_dir"

    "$ANTs_bin" -d 3 -a "$nii_file" -e "$TEMPLATE" -m "$TEMPLATE_MASK" -o "$out_dir/"

    # Rename outputs with subject prefix
    mv "$out_dir/BrainExtractionBrain.nii.gz" "$out_dir/${subj_id}_BrainExtractionBrain.nii.gz"
    mv "$out_dir/BrainExtractionMask.nii.gz" "$out_dir/${subj_id}_BrainExtractionMask.nii.gz"
    mv "$out_dir/BrainExtractionPrior0GenericAffine.mat" "$out_dir/${subj_id}_BrainExtractionPrior0GenericAffine.mat"

    echo "=== Finished $subj_id ==="
}

# ==============================
# Run jobs in parallel (max 30)
# ==============================
max_jobs=30
job_count=0

for subj in "${subjects[@]}"; do
    process_subject "$subj" &   # run in background
    ((job_count++))

    if (( job_count >= max_jobs )); then
        wait -n                 # wait for one job to finish
        ((job_count--))
    fi
done

wait  # wait for all jobs to finish

echo -e "\n=== Skull stripping finished. Results saved to: $out_base ==="
```
**Save and exit nano:**
Press Ctrl+O then Enter to save
Press Ctrl+X to close

2. **Make the script runnable**
```bash
 chmod +x run_ants.sh 
 ```

3.  Run with nohup so it survives SSH disconnections during execution: 
```bash
 nohup ./run_ants.sh >ants.log 2>&1 & 
 ```

4. We can still watch the progress even though it is running outside of the ssh - by typing: 
```bash
tail -f ants.log
```
- Even if you disconnect, the job keeps running. When you reconnect later, you can just run the same tail -f topup.log command to pick up the log again.

**Expected output structure**:
```bash
/data/projects/STUDIES/IMPACT/DTI/derivatives/ANTs/
│
├── s1000/
│   ├── s1000_BrainExtractionBrain.nii.gz
│   ├── s1000_BrainExtractionMask.nii.gz
│   ├── s1000_BrainExtractionPrior0GenericAffine.mat
│
├── s1323/
│   ├── s1323_BrainExtractionBrain.nii.gz
│   ├── s1323_BrainExtractionMask.nii.gz
│   ├── s1323_BrainExtractionPrior0GenericAffine.mat
│
└── ...
```

**Here is the script to conduct an audit to make sure this was properly run for all subjects:**
```bash
#!/bin/bash
# Robust audit for ANTs skull stripping outputs

in_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
out_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/ANTs"

printf "Subject\tBrain\tMask\tAffine\n"

for subj in $(ls -1 "$in_base"); do
    out_dir="$out_base/$subj"

    brain=$(find "$out_dir" -maxdepth 1 -type f -name "${subj}_BrainExtractionBrain.nii.gz" 2>/dev/null | head -n1)
    mask=$(find "$out_dir" -maxdepth 1 -type f -name "${subj}_BrainExtractionMask.nii.gz" 2>/dev/null | head -n1)
    affine=$(find "$out_dir" -maxdepth 1 -type f -name "${subj}_BrainExtractionPrior0GenericAffine.mat" 2>/dev/null | head -n1)

    [[ -n "$brain"  ]] && bstat="✅" || bstat="❌"
    [[ -n "$mask"   ]] && mstat="✅" || mstat="❌"
    [[ -n "$affine" ]] && astat="✅" || astat="❌"

    printf "%s\t%s\t%s\t%s\n" "$subj" "$bstat" "$mstat" "$astat"
done

echo -e "\n=== ANTs Skull Stripping Audit Finished ==="
```

**The next step in ANTs is to use the FSL - fsleyes- interface to check each participant to make sure that the skull strip was successful.**

- You may want to use another device other than the linux to operate fsleyes. Here is how to move the files from ANTs (or any other file) onto a local computer:
```bash
# === Copy ANTs-stripped brain + T1 from Linux to local ===
# Replace subject IDs in the brace list {s1287,s1323,s1324}

# first for brain extraction: 
rsync -av \
  "tur50045@cla19097:/data/projects/STUDIES/IMPACT/DTI/derivatives/ANTs/{s1228-pilot,s4418,s4419,s4423,s4427,s4429,s4436,s4440,s4446,s4447,s4449,s4450,s4459,s4475,s4482,s4531,s4631,s4643,s4650,s523,s601,s606,s673,s692,s701,s745,s807,s926}/*BrainExtractionBrain.nii.gz" \
  /Users/dannyzweben/Desktop/SDN/DTI/data.check/

#then the full T1

rsync -av \
  "tur50045@cla19097.tu.temple.edu:/data/projects/STUDIES/IMPACT/DTI/NIFTI/{s1228-pilot,s4418,s4419,s4423,s4427,s4429,s4436,s4440,s4446,s4447,s4449,s4450,s4459,s4475,s4482,s4531,s4631,s4643,s4650,s523,s601,s606,s673,s692,s701,s745,s807,s926}/struct/*_struct.nii" \
  /Users/dannyzweben/Desktop/SDN/DTI/data.check/
```

**Next, we will check the quality of  ANTs Skull Stripping with FSLeyes, and we will make sure to check every single participant.**

 **Open FSLeyes**
From terminal, launch:
```bash
fsleyes
```

When FSL opens, it will first pull up:

![Base FSL]({{ "/images/fsl_base.png" | relative_url }})

Next, we wil overlaying Structural and ANTS Images

For each participant:  
1. Load the participant’s NIFTI structural scan.  
2. Hit the **plus (+)** to add the ANTS-stripped version.  
3. Move the stripped brain above the struct.  
![overlay]({{ "/images/struct.ants.overlay.png" | relative_url }})     

4. Change the stripped brain’s color so the extraction edges are visible:  
![antscheck]({{ "/images/Antscheck.color.png" | relative_url }})

5. We want to make sure that for each participant, the stripped brain fully covers the T1 brain and doesn't capture non brain structures.  

6. Example of a Good Extraction -- For confidentiality this is generic example not from our data base.
![Good Skull Strip Example]({{ "/images/skullcheck.png" | relative_url }})

7. Here it is good to begin keeping a csv to track your progress. 
I track each participant's progress after skullstripping. 
![Good Skull Strip Example]({{ "/images/datatracker.png" | relative_url }})

**Note:** If extraction cuts off brain or pulls in excesive spine/scalp/neck, exclude and note. This should be a rare issue (~all participants should be stripped propely if you used a good mask/template), if you run into several issues,switch template (NKI worked perfectly with IMPACT).

If you have found good mask and made sure it worked for ~all participants, we can move to the next step: 

---
