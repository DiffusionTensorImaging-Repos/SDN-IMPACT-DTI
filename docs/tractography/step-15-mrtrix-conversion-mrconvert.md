---
layout: default
title: "Step 15 — MRtrix Conversion (mrconvert)"
parent: "Tractography (Steps 15–26)"
nav_order: 15
---

# Step 15 — MRtrix Conversion (mrconvert)

This step converts the eddy-corrected DWI data and brain mask from NIfTI format into MRtrix's `.mif` format, embedding the gradient table (bvecs/bvals) directly into the image header. This is required for all downstream MRtrix commands (dwi2response, dwi2fod, tckgen, etc.).

We go back to `BEDPOSTX/<subj>/bedpostx_input/` — the same directory we prepared in Step 9 — because it contains the final, clean versions of everything MRtrix needs:
- `data.nii.gz` — eddy-corrected DWI (all shells: b=0, 1000, 2000, 3250, 5000; b=250 already removed)
- `bvecs` — eddy-rotated gradient directions
- `bvals` — corresponding b-values
- `nodif_brain_mask.nii.gz` — binary brain mask

This step uses MRtrix3's `mrconvert` command, which embeds gradient information via the `-fslgrad` flag:
```
mrconvert data.nii.gz -fslgrad bvecs bvals dwi.mif
mrconvert nodif_brain_mask.nii.gz mask.mif
```

**Inputs (per subject):**
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/BEDPOSTX/<subj>/bedpostx_input/data.nii.gz`
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/BEDPOSTX/<subj>/bedpostx_input/bvecs`
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/BEDPOSTX/<subj>/bedpostx_input/bvals`
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/BEDPOSTX/<subj>/bedpostx_input/nodif_brain_mask.nii.gz`

**Expected Output (per subject):**
```
derivatives/CSD/s1000/
│
├── dwi.mif        # DWI data in MRtrix format (gradient table embedded in header)
├── mask.mif       # brain mask in MRtrix format
```

This step is lightweight — mrconvert is essentially a file format conversion. We allow up to 30 parallel jobs.

**Running Step 15 in tmux:**

1. SSH into the cluster and start a tmux session:
```bash
ssh -XY tur50045@cla19097.tu.temple.edu
tmux new -s csd
```

2. Create the script:
```bash
nano run_mrconvert.sh
```

3. Paste the following into nano:
```bash
#!/bin/bash
# ============================================================
# Step 15: Convert DWI to MRtrix format (mrconvert)
# ============================================================
# Converts eddy-corrected DWI + gradients + brain mask from
# NIfTI to MRtrix .mif format for CSD pipeline
# Input: BEDPOSTX/bedpostx_input/ (data.nii.gz, bvecs, bvals, mask)
# Output: CSD/<subj>/dwi.mif, mask.mif
# ============================================================

export PATH=/data/tools/mrtrix3/bin:$PATH

bedpostx_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/BEDPOSTX"
csd_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD"
nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"

process_subj() {
    subj=$1
    echo ">>> [$subj] Converting to MRtrix format"
    in_dir="$bedpostx_base/$subj/bedpostx_input"
    out_dir="$csd_base/$subj"
    mkdir -p "$out_dir"

    # Skip if inputs missing
    if [[ ! -f "$in_dir/data.nii.gz" || ! -f "$in_dir/bvecs" || ! -f "$in_dir/bvals" || ! -f "$in_dir/nodif_brain_mask.nii.gz" ]]; then
        echo "!!! [$subj] Missing input files, skipping"
        return
    fi

    # Convert DWI with embedded gradient table
    mrconvert "$in_dir/data.nii.gz" \
        -fslgrad "$in_dir/bvecs" "$in_dir/bvals" \
        "$out_dir/dwi.mif" -force

    # Convert brain mask
    mrconvert "$in_dir/nodif_brain_mask.nii.gz" \
        "$out_dir/mask.mif" -force

    echo ">>> [$subj] Done"
}

export -f process_subj
export bedpostx_base csd_base

subjects=$(ls -1 "$nifti_base")
for subj in $subjects; do
    process_subj "$subj" &
    while [ "$(jobs -r | wc -l)" -ge 30 ]; do sleep 1; done
done
wait
echo "=== All MRtrix conversions finished ==="
```

4. Save and exit nano:
Press Ctrl+O then Enter to save
Press Ctrl+X to close

5. Make the script runnable and execute inside tmux:
```bash
chmod +x run_mrconvert.sh
./run_mrconvert.sh 2>&1 | tee mrconvert.log
```

6. Detach from tmux while it runs (if needed):
Press Ctrl+B, then D to detach. Reconnect later with:
```bash
tmux attach -t csd
```
* Note: All coding output from this script is recorded in mrconvert.log.

**Step 15 Audit — verify mrconvert outputs for all subjects:**
```bash
#!/bin/bash
# Audit Step 15: mrconvert outputs

nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
csd_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD"

printf "Subject\tdwi.mif\tmask.mif\n"

for subj in $(ls -1 "$nifti_base"); do
    d="$csd_base/$subj"
    dwi=$([ -f "$d/dwi.mif" ] && echo "✅" || echo "❌")
    mask=$([ -f "$d/mask.mif" ] && echo "✅" || echo "❌")
    printf "%s\t%s\t%s\n" "$subj" "$dwi" "$mask"
done

echo -e "\n=== mrconvert Audit Complete ==="
```

---

