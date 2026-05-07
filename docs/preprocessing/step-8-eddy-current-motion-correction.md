---
layout: default
title: "Step 8 — Eddy Current & Motion Correction"
parent: "Preprocessing (Steps 1–14)"
nav_order: 8
---

# Step 8 — Eddy Current & Motion Correction

FSL EDDY corrects for subject head motion during diffusion scans, Eddy current–induced geometric distortions, and uses TOPUP fieldmap outputs (Step 7) to further correct susceptibility distortions.

Without this step, head motion and distortions can bias tensor fitting and tractography.

**Inputs (per subject)**
1. From denoise step:
- <subj>_dwi_no_b250.nii.gz 
- <subj>_dwi_no_b250.bvec
- <subj>_dwi_no_b250.bval
2. From TOPUP step:
- <subj>_topup_Tmean_brain_mask.nii.gz
- <subj>_topup (field coefficients, fieldmap, corrected b0s)
3. From config:
- acqp.txt (phase encoding info) - same file we used in the TOPUP step
- index_no_b250.txt (volume index file)

![acqp]({{ "/images/indexn250.png" | relative_url }})

Each 1 in index_no_b250.txt points to line 1 of acqp.txt, telling eddy to use that set of phase-encoding parameters for the corresponding volume. Because the b=250 volumes were dropped earlier, only the remaining shells are listed, all mapped to the same acquisition direction.

**Outputs (per subject)**
```
derivatives/eddyoutput/<subj>/
├── data.nii.gz                     → corrected DWI
├── bvals, bvecs                    → gradients (updated & rotated)
├── nodif_brain_mask.nii.gz         → brain mask from Step 9
├── cnr_maps.nii.gz                 → contrast-to-noise maps
└── eddy QC files/                  → .eddy_rotated_bvecs, .eddy_outlier_report, etc.

```

Our code will use the FSL ```eddy``` function, and it will use the following call
```bash
eddy --imain="$mrdegibbs_dir/${subj}_dwi_no_b250.nii.gz" \   # input 4D DWI
     --mask="$topup_dir/${subj}_topup_Tmean_brain_mask.nii.gz" \   # brain mask
     --acqp="$acq_params_file" \   # acq params (phase-encoding)
     --index="$index_file" \       # index file mapping vols → acq lines
     --bvecs="$mrdegibbs_dir/${subj}_dwi_no_b250.bvec" \   # input bvecs
     --bvals="$mrdegibbs_dir/${subj}_dwi_no_b250.bval" \   # input bvals
     --topup="$topup_dir/${subj}_topup" \   # TOPUP field estimate prefix
     --out="$out_dir/${subj}_eddy" \        # eddy output prefix
     --cnr_maps \   # write CNR maps
     --repol \      # replace outlier slices - very important!
     -v             # verbose output
```


Eddy is computationally intensive and can take a few hours, so we will again run with nohup. In practice it does not fully use all available RAM/cores, which means it is safe and  preferable to parallelize across multiple subjects.

**Before running EDDY, we will check our copmuting power**
```bash
free -h
              total        used        free      shared  buff/cache   available
Mem:          125Gi        10Gi        66Gi        60Mi        48Gi       113Gi
Swap:         2.0Gi       5.0Mi       2.0Gi

```
We cap eddy at 8 parallel jobs because each run typically uses ~6–10 GB of memory, and with ~113 GB free this keeps total usage well within safe limits. This balance avoids overloading the system while still speeding up processing by running multiple participants at once.

(We likely could have run more than 8 in parallel, but chose a conservative cap.)

**Running Eddy in Nohup**: 
1. **Creat script in Nano**
```bash
nano run_eddy.sh**
```
2. **Paste the following code into Nano**: 
```bash
#!/bin/bash

# Base directories
nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
denoise_dir="/data/projects/STUDIES/IMPACT/DTI/derivatives/denoise"
topup_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/TOPUP"
eddy_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/EDDY"

acq_params_file="/data/projects/STUDIES/IMPACT/DTI/config/acqp.txt"
index_file="/data/projects/STUDIES/IMPACT/DTI/config/index_no_b250.txt"

# Function to run EDDY for one subject
process_subj() {
    subj=$1
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

    echo ">>> [$subj] Done"
}

export -f process_subj
export denoise_dir topup_base eddy_base acq_params_file index_file

subjects=$(ls -1 "$nifti_base")

# Run up to 8 jobs in parallel
if command -v parallel > /dev/null; then
    echo "$subjects" | parallel -j 8 process_subj {}
else
    max_jobs=8
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
fi

echo "=== All EDDY jobs finished ==="

```

3. **Save and exit nano:**
Press Ctrl+O then Enter to save
Press Ctrl+X to close

4. **Make the script runnable**
```bash
 chmod +x run_eddy.sh
 ```
5. **Run with nohup so it survives SSH disconnects**
```bash
 nohup ./run_eddy.sh >eddy.log 2>&1 & 
 ```
6. **Watch progress in real time**
We can still watch the progress even though it is running outside of the ssh!
```bash
tail -f eddy.log
```
- Even if you disconnect, the job keeps running. When you reconnect later, you can just run the same tail -f eddy.log command to pick up the log again.

**Expected File Output (Per Subject):**
```
derivatives/EDDY/s1000/
│
├── s1000_eddy.nii.gz          # corrected diffusion data
├── s1000_eddy.eddy_parameters # motion + eddy current params
├── s1000_eddy.eddy_cnr_maps.nii.gz  # contrast-to-noise ratio maps (from --cnr_maps)
├── s1000_eddy.eddy_outlier_map  # outlier replacement info (from --repol)
├── s1000_eddy.eddy_outlier_n_stdev_map  # stdev map of outlier replacement
├── s1000_eddy.eddy_outlier_report  # text report of outlier volumes
├── s1000_eddy.eddy_post_eddy_shell_alignment_parameters  # shell alignment
├── s1000_eddy.eddy_post_eddy_shell_PE_translation_parameters
├── s1000_eddy.eddy_movement_rms  # motion summary (RMS displacement)
├── s1000_eddy.eddy_restricted_movement_rms
└── s1000_eddy.eddy_command_txt   # record of the full eddy command used
```
**Audit script to make sure eddy was run succesfuly**:
```bash
#!/bin/bash
# Audit Step: EDDY outputs

nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
eddy_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/EDDY"

printf "Subject\tNII\tParams\tCNR\tOutlierMap\n"

for subj in $(ls -1 "$nifti_base"); do
    out_dir="$eddy_base/$subj"

    nii="$out_dir/${subj}_eddy.nii.gz"
    params="$out_dir/${subj}_eddy.eddy_parameters"
    cnr="$out_dir/${subj}_eddy.eddy_cnr_maps.nii.gz"
    outmap="$out_dir/${subj}_eddy.eddy_outlier_map"

    [[ -f "$nii" ]] && niistat="✅" || niistat="❌"
    [[ -f "$params" ]] && pstat="✅" || pstat="❌"
    [[ -f "$cnr" ]] && cnrstat="✅" || cnrstat="❌"
    [[ -f "$outmap" ]] && omapstat="✅" || omapstat="❌"

    printf "%s\t%s\t%s\t%s\t%s\n" "$subj" "$niistat" "$pstat" "$cnrstat" "$omapstat"
done

echo -e "\n=== EDDY audit finished ==="
```
**NOTE:** If EDDY fails to complete for one or more participants, see the guide linked here: Pipeline_Failure_Recovery.md. It provides code for auditing the issue and instructions for re-running earlier steps for that participant if necessary.


### Post EDDY Outlier Checks 

**For eddy, it is crucial to conduct quality assurance and outlier removal.**

- **Note**: An outlier is defined as a slice whose average intensity is at least four standard deviations lower than the expected intensity, where the expectation is given by the Gaussian Process prediction.

**We will handle outliers in 3 ways:**

1. The --repol flag, used in the EDDY code above, instructs EDDY to remove any slices deemed as movement outliers and replace them with predictions made by the Gaussian process 

2. We will use the EDDY-quad/squad quality control tool to calculate avg. absolute motion per participant - so we can exclude anybody with >2mm of absolute motion.
    - **Note**- for reporting purposes -  for this step we will also calculate Mean, SD of absolute motion, and of absolute outlier slices. 

3. Using FSLeyes, we will visually inspect all volumes for each participant, and any participant with more than five volumes with excessive intensity artifacts were excluded.

To run these scripts: 

1. The repol flag step is handled in the eddy script, so let's start with eddy Quad (step 2)

2. Eddy QUAD/SQUAD: 

**The script will use the following FSL functions:**

- eddy_quad — runs QC on a single subject’s EDDY outputs.
- eddy_squad — aggregates QUAD outputs across all subjects to create group-level reports

**Required input (output from EDDY step):**
- Eddy output prefix:
/data/projects/STUDIES/IMPACT/DTI/derivatives/EDDY/<subj>/<subj>_eddy
- Brain mask:
/data/projects/STUDIES/IMPACT/DTI/derivatives/TOPUP/<subj>/topup_output/<subj>_topup_Tmean_brain_mask.nii.gz
- B-values (with b=250 removed):
/data/projects/STUDIES/IMPACT/DTI/derivatives/denoise/<subj>/mrdegibbs_no_b250/<subj>_dwi_no_b250.bval
- B-vectors (with b=250 removed):
/data/projects/STUDIES/IMPACT/DTI/derivatives/denoise/<subj>/mrdegibbs_no_b250/<subj>_dwi_no_b250.bvec
- Acquisition parameters file:
/data/projects/STUDIES/IMPACT/DTI/config/acqp.txt
- Index file (after dropping b=250 vols):
/data/projects/STUDIES/IMPACT/DTI/config/index_no_b250.txt

Additionally - SQUAD expects a text file listing QUAD subject dirs containing qc.json - this script creates the creation file. 
```
quad_list="$quad_base/quad_list.txt"
: > "$quad_list"
```

Quad and Squad jobs are low-intensity (mainly file I/O and small FSL utilities), so it’s safe to parallelize them. We cap at 60 concurrent runs which covered all participants in impact. If you have a larger sample consider checking availabe computing power first, but you should be good to go.
 
  This will compile the participant movement metrics with the total absolute motion and outlier %'s from SQUAD into a text file. The group-level SQUAD and summary steps run only after all per-subject jobs complete. 

* **Note**: If the outputs aren’t combining succesfuly into a single qc_summary.txt file, you can run QUAD and SQUAD manually and check each participant’s output. However, the combined QC file is much more convenient, so try to run it this way first and troubleshoot as needed 

Lastly - the script below is ***long*** because it combines quad, squad, and a script to combine them into one txt output. Feel free to only extract the quad and squad functions you need, or to run these 3 functions one at a time. 


```bash
#!/bin/bash
# ============================================================
# IMPACT DTI QC Pipeline (QUAD -> quad_list.txt -> SQUAD -> summary)
# Notes:
# - SQUAD expects a text file listing QUAD subject dirs containing qc.json - this script creates that file. 
# - Do NOT pre-create $squad_base (eddy_squad will create it)
# - "Outlier slice" = slice whose mean intensity is ≥ 4 SD below expected
# ============================================================

set -u -o pipefail
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1

# --- Paths ---
nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
denoise_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/denoise"
eddy_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/EDDY"
topup_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/TOPUP"
quad_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/QUAD"
squad_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/SQUAD"

acq_params="/data/projects/STUDIES/IMPACT/DTI/config/acqp.txt"
index_file="/data/projects/STUDIES/IMPACT/DTI/config/index_no_b250.txt"

out_txt="/data/projects/STUDIES/IMPACT/DTI/derivatives/qc_summary.txt"

quad_list="$quad_base/quad_list.txt"
: > "$quad_list"

# -------------------- Step 1: QUAD -------------------------
echo ">>> Step 1: running QUAD in parallel (max 60)..."

ls -1 "$nifti_base" | xargs -n 1 -P 60 -I{} bash -c '
  subj="{}"
  mask_file="'"$topup_base"'/$subj/topup_output/${subj}_topup_Tmean_brain_mask.nii.gz"
  bval_file="'"$denoise_base"'/$subj/mrdegibbs_no_b250/${subj}_dwi_no_b250.bval"
  bvec_file="'"$denoise_base"'/$subj/mrdegibbs_no_b250/${subj}_dwi_no_b250.bvec"
  eddy_prefix="'"$eddy_base"'/$subj/${subj}_eddy"
  out_dir="'"$quad_base"'/$subj"

  if [[ -f "$mask_file" && -f "$bval_file" && -f "$bvec_file" && -f "${eddy_prefix}.nii.gz" ]]; then
    echo ">>> QUAD: $subj"
    rm -rf "$out_dir"
    eddy_quad "$eddy_prefix" \
      -idx "'"$index_file"'" \
      -par "'"$acq_params"'" \
      -m "$mask_file" \
      -b "$bval_file" \
      -g "$bvec_file" \
      -o "$out_dir"
  else
    echo "!! Skipping $subj (missing inputs)"
  fi
'

# -------------------- Step 2: SQUAD ------------------------
echo ">>> Step 2: rebuilding quad_list (only QUADs with qc.json) and running SQUAD..."

find "$quad_base" -mindepth 1 -maxdepth 1 -type d \
  -exec test -f "{}/qc.json" \; -print | sort > "$quad_list"

nsubj=$(wc -l < "$quad_list" | tr -d " ")
echo "Found $nsubj subjects for SQUAD."
if [[ "$nsubj" -eq 0 ]]; then
  echo "!! quad_list.txt is empty; skipping SQUAD"
else
  # Optional: ensure a clean SQUAD run
  # rm -rf "$squad_base"

  echo "Running eddy_squad..."
  eddy_squad "$quad_list" -o "$squad_base" || echo "!! eddy_squad failed; continuing to summary with available data"
fi

# -------------------- Step 3: Summary ----------------------
echo ">>> Step 3: collating per-subject (QUAD) + group metrics (SQUAD)..."
{
  echo "QC Summary — IMPACT DTI"
  echo "Exclusion threshold: >2 mm average absolute motion"
  echo
  echo "Per-subject results:"
} > "$out_txt"

per_subj_tmp=$(mktemp)
excl_tmp=$(mktemp)

while IFS= read -r subj_dir; do
  subj=$(basename "$subj_dir")
  qc_file="$subj_dir/qc.json"
  [[ -f "$qc_file" ]] || continue

  abs_motion=$(python3 - <<PY "$qc_file"
import json,sys
d=json.load(open(sys.argv[1]))
print(d.get('qc_mot_abs') or d.get('avg_abs_motion') or "NA")
PY
)
  rel_motion=$(python3 - <<PY "$qc_file"
import json,sys
d=json.load(open(sys.argv[1]))
print(d.get('qc_mot_rel') or "NA")
PY
)
  out_prop=$(python3 - <<PY "$qc_file"
import json,sys
d=json.load(open(sys.argv[1]))
v=d.get('qc_outliers_tot') or d.get('outlier_prop')
print("" if v is None else v)
PY
)

  if [[ -n "$out_prop" ]]; then
    # qc_outliers_tot is already expressed as percent of slices
    out_pct=$(awk -v v="$out_prop" 'BEGIN{printf("%.2f",v)}')
  else
    out_pct="NA"
  fi

  printf "%s\tavg_abs_motion=%smm\trel_motion=%smm\toutlier_slices=%s%%\n" \
    "$subj" "$abs_motion" "$rel_motion" "$out_pct" >> "$per_subj_tmp"

  awk -v m="${abs_motion:-0}" -v s="$subj" 'BEGIN{ if (m+0>2.0) print s }' >> "$excl_tmp"
done < "$quad_list"

sort "$per_subj_tmp" >> "$out_txt"
echo >> "$out_txt"
echo "Exclusions (>2 mm):" >> "$out_txt"
if [[ -s "$excl_tmp" ]]; then
  sort "$excl_tmp" >> "$out_txt"
else
  echo "None" >> "$out_txt"
fi

# --- group stats from SQUAD group_db.json ---
group_db="$squad_base/group_db.json"
if [[ -f "$group_db" ]]; then
  echo >> "$out_txt"
  echo "Group-level metrics (from SQUAD group_db.json):" >> "$out_txt"

  python3 - "$group_db" >> "$out_txt" <<'PY'
import json, sys, numpy as np
path = sys.argv[1]
with open(path) as f:
    d = json.load(f)

motions = np.array(d.get("qc_motion", []), dtype=float)
outliers = np.array(d.get("qc_outliers", []), dtype=float)

if motions.size > 0:
    print(f"Mean (SD) average absolute motion across participants = {motions.mean():.2f} ({motions.std(ddof=1):.2f}) mm")
else:
    print("Mean (SD) average absolute motion across participants = NA (NA) mm")

if outliers.size > 0:
    print(f"Mean (SD) frequency of outlier slices = {outliers.mean():.2f}% ({outliers.std(ddof=1):.2f}%)")
else:
    print("Mean (SD) frequency of outlier slices = NA (NA)%")
PY
else
  echo >> "$out_txt"
  echo "!! No group_db.json found — group metrics unavailable" >> "$out_txt"
fi

rm -f "$per_subj_tmp" "$excl_tmp"

echo "=== Done. Summary written to: $out_txt ==="
tail -n 20 "$out_txt"



```

This will compile the participant movement metrics with the total absolute motion and outlier %'s from SQUAD into a text file. 

The following forum confirms that we have correctly interpreted our quad/output when converting it to  a summary txt file: https://www.jiscmail.ac.uk/cgi-bin/wa-jisc.exe?A2=FSL%3B8570b55c.1904&utm: 

```
qc_mot_abs → abs_motion
qc_mot_rel → rel_motion
qc_outliers_tot (or outlier_prop) → out_prop → out_pct
From group_db.json:
"qc_motion" → motions
"qc_outliers" → outliers
```
I moved this summary file and the SQUAD output onto a local computer in order to check output.
```bash
scp -Cp tur50045@cla19097.tu.temple.edu:/data/projects/STUDIES/IMPACT/DTI/derivatives/qc_summary.txt \
       tur50045@cla19097.tu.temple.edu:/data/projects/STUDIES/IMPACT/DTI/derivatives/SQUAD \
       /Users/dannyzweben/Desktop/SDN/DTI/eddyqc/
```            
Here is what our combine qc summary looks like:

![qcsum]({{ "/images/qc_summary.png" | relative_url }})

**Interpretation:** We found that head motion was low across participants, with mean average absolute motion of 0.27 mm (SD = 0.13), and no subjects exceeded the 2 mm exclusion threshold. Mean frequency of outlier slices was 1.42% (SD = 2.23%). 


**Fsl squad** will also produce a pdf with this output: 

![squadsum]({{ "/images/squad_summary.png" | relative_url }})


3. **Lastly, for step 3, we will visually inspect the eddy output for each participant to exlcude those with >5 volumes with visible eddy motion artifacts.** 

Data will be visually inspected for motion-related and signal-intensity artifacts in the EDDY-corrected diffusion volumes, and participants with more than five volumes showing excessive signal dropout or distortion were excluded from further analysis.

Volumes with visible horizontal banding or clean slice lines indicating within-volume motion or signal corruption were marked as outliers: 

* Below is an example of a volume that would be indicated as having excessive/outlier motion: 

![eddymotionoutlier]({{ "/images/eddyoutlierlines.png" | relative_url }})



This step will use FSL. Because I prefer to run fsleyes externally to the Linux I copied these files locally: 
```bash
rsync -avz \
tur50045@cla19097:/data/projects/STUDIES/IMPACT/DTI/derivatives/EDDY/ \
/Users/dannyzweben/Desktop/SDN/DTI/eddyqc/manualcheck/ \
--include="*/" \
--include="*eddy_outlier_free_data.nii.gz" \
--exclude="*"
```



Next, we'll open fsleyes, to begin manually inspecting each participant. 


1.  **Open FSLeyes**

From terminal, launch:
```bash
fsleyes
```

2. Open participant level eddy data 

When FSL opens, hit the plus button in the bottom left, to add an image. Add the eddy output data for a given subject. Make sure it is the output that utlized eddy repol (####_eddy.eddy_outlier_free_data)

![eddy base]({{ "/images/eddymanopen.png" | relative_url }})


3. Adjust brightness/contrast, and begin inspecting each volume. 

Next, for each participant, adjust the brightness and contrast until you find a level for which each volume will be visible, and begin inspecting each volume for execssive motion, which would like like the example given above.

 Make sure you inspect every volume. This can be done relatively quickly for each volume
(note: the example below depicts volumes where no outliers are detected)


![overlay]({{ "/images/eddyvid.gif" | relative_url }})     

**Note:** Very minor motion may appear as ***slight*** blurring or ghosting across slices and is acceptable.

Example: 

![minormotion]({{ "/images/minormotion.png" | relative_url }})


 In contrast, outlier volumes - depicted earlier - show distinct horizontal bands or sharp slice discontinuities that indicate severe motion or signal dropout. 

In a data tracker, for each participant, list which volumes are outliers. **If it is more than 5** exlcude that participant. 


![eddy tracker]({{ "/images/eddytracker.png" | relative_url }})


Repeat this step for all participants. 

---
