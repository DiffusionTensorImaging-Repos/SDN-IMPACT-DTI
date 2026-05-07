---
layout: default
title: "Step 1 — DICOM to NIfTI Conversion"
parent: "Preprocessing (Steps 1–14)"
nav_order: 1
---

# Step 1 — DICOM to NIfTI Conversion

Before we we begin conversion, lets quickly check which participants have the necessary DTI and anatomical DICOM Runs?

For a subject to be *DTI-clear*, it must include all four required scan types inside its DICOM folder:

- Note look through your DICOMS first To make sure your T1 and DTI runs follow this naming structure.
Example:

```bash
 ls /project/dicoms/subject*/
```

If they don't, update the naming throughout this step

1. Structural T1 (`anat_T1w_acq_mpgSag`)  
2. Diffusion run (`cmrr_mb3hydi_ipat2_64ch`)  
3. Fieldmap AP (`cmrr_fieldmapse_ap`)  
4. Fieldmap PA (`cmrr_fieldmapse_pa`)  


 **We will use the following bash Code to check which participants have these files:**

Paste the following into the SSH terminal: 
```bash
#!/bin/bash
# Tidy check for required DTI runs in each IMPACT subject folder

base_dir="/data/projects/STUDIES/IMPACT/fMRI/dicoms"

required_scans=(
    "anat_T1w_acq_mpgSag"
    "cmrr_mb3hydi_ipat2_64ch"
    "cmrr_fieldmapse_ap"
    "cmrr_fieldmapse_pa"
)

echo "=== DTI Scan Check: $base_dir ==="
printf "%-12s | %-25s | %-25s | %-20s | %-20s\n" \
"Subject" "T1 (anat_T1w)" "DTI (mb3hydi)" "Fieldmap AP" "Fieldmap PA"
printf -- "-------------+---------------------------+---------------------------+----------------------+----------------------\n"

for subj in "$base_dir"/*; do
    [ -d "$subj" ] || continue
    subj_id=$(basename "$subj")
    status=()
    for scan in "${required_scans[@]}"; do
        if find "$subj" -maxdepth 1 -type d -regex ".*/[0-9]+-$scan.*" | grep -q .; then
            status+=("✅")
        else
            status+=("❌")
        fi
    done
    printf "%-12s | %-25s | %-25s | %-20s | %-20s\n" \
    "$subj_id" "${status[0]}" "${status[1]}" "${status[2]}" "${status[3]}"
done
```

**What We get from the Output:**

 Most subjects are DTI-clear: they have T1, diffusion, and both fieldmaps present.
Incomplete subjects include:  
* s1253  
* s1476  
* s578  
* s820  
* s999-pilot

**Next, we will batch convert the DICOM to NIFTI conversion**

- We use **dcm2niix**, a widely adopted command-line tool that converts DICOM medical imaging files into the NIfTI format.  

- DICOMs are the raw scanner output, but NIfTI is the standard format used by neuroimaging software (FSL, AFNI, SPM, etc.).  
- `dcm2niix` automatically handles orientation, metadata, and generates `.json`, `.bval`, and `.bvec` files that are essential for preprocessing.  

As a reminder, we require the following four scan types for each subject:
1. **Structural T1** → `anat_T1w_acq_mpgSag`  
2. **DTI run** → `cmrr_mb3hydi_ipat2_64ch`  
3. **Fieldmap AP** → `cmrr_fieldmapse_ap`  
4. **Fieldmap PA** → `cmrr_fieldmapse_pa`  

- Only subjects with all 4 will be converted, and the output files will be place in the newly created DTI directory. 

This step will use the basic dc2niix function. 

**Note** — This step is lightweight and will be completed quickly, so we just paste it directly into the SSH terminal and run it for all participants at once. 

I quickly check available system RAM to decide how many participants we can process at once, by pasting this in the SSH terminal: 
```
free -h
```

Example output:
```
              total        used        free      shared  buff/cache   available
Mem:          125Gi       9.7Gi        54Gi        60Mi        61Gi       114Gi
Swap:         2.0Gi          0B       2.0Gi
```

dcm2niix is very lightweight, using only ~100–300 MB per subject. With 114 GB available, even 60 subjects in parallel is well within limits.
→ Safe to set max_jobs=60.

To run the code, 
**Paste the following directly into the SSH terminal**
```bash
#!/bin/bash
# ============================================================
# DICOM → NIfTI conversion for IMPACT (DTI pipeline)
# With subject-prefixed filenames + logging
# ============================================================

base_dir="/data/projects/STUDIES/IMPACT/fMRI/dicoms"
out_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
dcm2niix_bin="/usr/bin/dcm2niix"   # confirmed path on cluster

# Required scan patterns (pattern:output_dir:label)
scan_types=(
    "anat_T1w_acq_mpgSag:struct:struct"
    "cmrr_mb3hydi_ipat2_64ch:dti:dwi"
    "cmrr_fieldmapse_ap:dti:fmapAP"
    "cmrr_fieldmapse_pa:dti:fmapPA"
)

# Log file (always overwrite dcm2niix.log)
logfile="dcm2niix.log"
: > "$logfile"

# Simple logger: prints to screen AND appends to logfile
log() { echo "$*" | tee -a "$logfile" ; }

log "=== Starting DICOM → NIfTI conversion ==="

for subj in "$base_dir"/*; do
    [ -d "$subj" ] || continue
    subj_id=$(basename "$subj")
    log "--- Checking subject: $subj_id ---"

    # Check completeness
    complete=true
    for scan in "${scan_types[@]}"; do
        pattern="${scan%%:*}"
        if ! find "$subj" -maxdepth 1 -type d -regex ".*/[0-9]+-$pattern.*" | grep -q .; then
            log "  ❌ Missing required scan: $pattern"
            complete=false
        fi
    done
    if [ "$complete" = false ]; then
        log "  ⚠️ Skipping $subj_id (not DTI-clear)"
        continue
    fi

    # Output directories
    subj_out="$out_base/$subj_id"
    mkdir -p "$subj_out/struct" "$subj_out/dti"

    # Convert each scan type
    for scan in "${scan_types[@]}"; do
        IFS=":" read -r pattern target label <<< "$scan"
        scan_dir=$(find "$subj" -maxdepth 1 -type d -regex ".*/[0-9]+-$pattern.*" | head -n 1)
        log "  ✅ Converting $pattern → $target/"

        {
            echo "----- [$subj_id $label] dcm2niix start"
            $dcm2niix_bin -o "$subj_out/$target" -f "${subj_id}_${label}" "$scan_dir"
            echo "----- [$subj_id $label] dcm2niix end"
            echo
        } >>"$logfile" 2>&1
    done
done

log "=== Conversion finished. Output saved to: $out_base ==="


```
Note: All coding output from this script is recorded in dcm2niix.log.

The output data will look like this: 
```bash
/data/projects/STUDIES/IMPACT/DTI/NIFTI/
│
├── s1000/
│   ├── struct/
│   │   ├── s1000_struct.nii
│   │   ├── s1000_struct.json
│   └── dti/
│       ├── s1000_dwi.nii
│       ├── s1000_dwi.bval
│       ├── s1000_dwi.bvec
│       ├── s1000_dwi.json
│       ├── s1000_fmapAP.nii
│       ├── s1000_fmapAP.json
│       ├── s1000_fmapPA.nii
│       ├── s1000_fmapPA.json
│
├── s1323/
│   ├── struct/
│   │   ├── s1323_struct.nii
│   └── dti/
│       ├── s1323_dwi.nii
│       ├── s1323_fmapAP.nii
│       ├── s1323_fmapPA.nii
│
└── ...
```
Next, we'll run a NIFTI AUDIT to check that conversion and file org was succesful.
- **Note**: in following pre-processing steps I will  present the audit code without this detailed explanation. In each step, it will do the same thing: checking for the presence of all the files showed in the output data of the code. 

- This script audits the **NIFTI output directory** (`/Volumes/DTI/DTI/Wave1/NIFTI`) to check which subjects have proper output from this step. 

For each subject, it confirms the presence of:  
- `struct/` folder with T1 outputs (`.nii`, `.json`)  
- `dti/cmrr_mb3hydi_ipat2_64ch/` with diffusion outputs (`.nii`, `.json`, `.bval`, `.bvec`)  
- `dti/cmrr_fieldmapse_ap/` with fieldmap AP outputs (`.nii`, `.json`)  
- `dti/cmrr_fieldmapse_pa/` with fieldmap PA outputs (`.nii`, `.json`)  

The script prints a table of subjects with a ✅/**NIFTI-clear** flag if all required files exist, or ❌ if anything is missing. It also provides a final summary count of complete vs. incomplete subjects.

**Paste the following directly into the SSH terminal:**

```bash
#!/bin/bash

# Base directory with subject-level NIFTI outputs
nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"

# Counters
complete=0
incomplete=0

echo "=== NIFTI Output Check: $nifti_base ==="
printf "%-12s | %-8s\n" "Subject" "NIFTI-clear"
printf -- "-------------+----------\n"

for subj in "$nifti_base"/*; do
    [ -d "$subj" ] || continue
    subj_id=$(basename "$subj")

    # Required files for this layout
    struct_ok=$(ls "$subj"/struct/${subj_id}_struct.{nii,json} 2>/dev/null | wc -l)
    dwi_ok=$(ls "$subj"/dti/${subj_id}_dwi.{nii,json,bval,bvec} 2>/dev/null | wc -l)
    fmap_ap_ok=$(ls "$subj"/dti/${subj_id}_fmapAP.{nii,json} 2>/dev/null | wc -l)
    fmap_pa_ok=$(ls "$subj"/dti/${subj_id}_fmapPA.{nii,json} 2>/dev/null | wc -l)

    if [ $struct_ok -eq 2 ] && [ $dwi_ok -eq 4 ] && [ $fmap_ap_ok -eq 2 ] && [ $fmap_pa_ok -eq 2 ]; then
        echo "$subj_id    | ✅"
        ((complete++))
    else
        echo "$subj_id    | ❌"
        ((incomplete++))
    fi
done

echo
echo "Summary: $complete subjects complete, $incomplete subjects incomplete"
```

 OUTPUT: Summary: 57 subjects complete, 0 subjects incomplete (We're good to go)

---

