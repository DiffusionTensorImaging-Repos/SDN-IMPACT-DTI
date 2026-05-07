---
layout: default
title: "Step 19 — FOD Normalization (mtnormalise)"
parent: "Tractography (Steps 15–26)"
nav_order: 19
---

# Step 19 — FOD Normalization (mtnormalise)

Before tractography, we normalize the FOD intensities across tissue types and subjects using `mtnormalise`. This corrects for global intensity differences between subjects (caused by scanner drift, coil sensitivity, etc.) so that the FOD amplitudes are comparable. Without this step, a subject whose scan had slightly higher overall signal intensity would appear to have "stronger" fiber orientations, biasing tractography.

The normalized WM FOD (`wm_fod_norm.mif`) is what feeds into tractography in Steps 23–24.

This step also creates **tissue-concatenated images** (`vf_fod.mif`, `vf_fod_norm.mif`) for visualization and quality checking — matching Ranesh's pipeline. These combine the first spherical harmonic component (l=0) of the WM FOD with the GM and CSF FODs into a single RGB-like image where you can see all three tissue compartments at once in mrview.

**Input (per subject — from Step 18):**
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/wm_fod.mif`
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/gm_fod.mif`
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/csf_fod.mif`
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/mask.mif`

**Expected Output (per subject):**
```
derivatives/CSD/s1000/
│
├── dwi.mif              # (from Step 15)
├── mask.mif             # (from Step 15)
├── wm_response.txt      # (from Step 16)
├── gm_response.txt      # (from Step 16)
├── csf_response.txt     # (from Step 16)
├── wm_fod.mif           # (from Step 18)
├── gm_fod.mif           # (from Step 18)
├── csf_fod.mif          # (from Step 18)
├── wm_fod_norm.mif      # normalized WM FOD → feeds tractography
├── gm_fod_norm.mif      # normalized GM FOD
├── csf_fod_norm.mif     # normalized CSF FOD
├── vf_fod.mif           # tissue concat for visualization
├── vf_fod_norm.mif      # tissue concat (normalized) for visualization
```

This step is moderately CPU-intensive — we run up to 15 parallel jobs.

**Running Step 19 in tmux:**

1. SSH into the cluster and reattach (or create) the tmux session:
```bash
ssh -XY tur50045@cla19097.tu.temple.edu
tmux attach -t csd || tmux new -s csd
```

2. Create the script:
```bash
nano run_mtnormalise.sh
```

3. Paste the following into nano:
```bash
#!/bin/bash
# ============================================================
# Step 19: Normalize FODs (mtnormalise)
# ============================================================
# Normalizes FOD intensities across tissue types and subjects
# so they are comparable. The normalized WM FOD (wm_fod_norm.mif)
# is what feeds into tractography.
# Also creates tissue-concatenated images for visualization/QC.
# Input:  CSD/<subj>/wm_fod.mif, gm_fod.mif, csf_fod.mif, mask.mif
# Output: CSD/<subj>/wm_fod_norm.mif, gm_fod_norm.mif, csf_fod_norm.mif
#         CSD/<subj>/vf_fod.mif, vf_fod_norm.mif (visualization)
# ============================================================

export PATH=/data/tools/mrtrix3/bin:$PATH

csd_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD"
nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"

process_subj() {
    subj=$1
    echo ">>> [$subj] Normalizing FODs"
    d="$csd_base/$subj"

    if [[ ! -f "$d/wm_fod.mif" || ! -f "$d/gm_fod.mif" || ! -f "$d/csf_fod.mif" || ! -f "$d/mask.mif" ]]; then
        echo "!!! [$subj] Missing FOD or mask files, skipping"
        return
    fi

    # Normalize FODs
    mtnormalise \
        "$d/wm_fod.mif"  "$d/wm_fod_norm.mif" \
        "$d/gm_fod.mif"  "$d/gm_fod_norm.mif" \
        "$d/csf_fod.mif" "$d/csf_fod_norm.mif" \
        -mask "$d/mask.mif" \
        -force

    # Tissue concatenation for visualization (matches Ranesh's pipeline)
    mrconvert -coord 3 0 "$d/wm_fod.mif" - | \
        mrcat "$d/csf_fod.mif" "$d/gm_fod.mif" - "$d/vf_fod.mif" -force

    mrconvert -coord 3 0 "$d/wm_fod_norm.mif" - | \
        mrcat "$d/csf_fod_norm.mif" "$d/gm_fod_norm.mif" - "$d/vf_fod_norm.mif" -force

    echo ">>> [$subj] Done"
}

export -f process_subj
export csd_base

subjects=$(ls -1 "$nifti_base")
for subj in $subjects; do
    process_subj "$subj" &
    while [ "$(jobs -r | wc -l)" -ge 15 ]; do sleep 1; done
done
wait
echo "=== All FOD normalizations finished ==="
```

4. Save and exit nano:
Press Ctrl+O then Enter to save
Press Ctrl+X to close

5. Make the script runnable and execute inside tmux:
```bash
chmod +x run_mtnormalise.sh
./run_mtnormalise.sh 2>&1 | tee mtnormalise.log
```

6. Detach from tmux while it runs (if needed):
Press Ctrl+B, then D to detach. Reconnect later with:
```bash
tmux attach -t csd
```
* Note: All coding output from this script is recorded in mtnormalise.log.

**Step 19 Audit — verify mtnormalise outputs for all subjects:**
```bash
#!/bin/bash
# Audit Step 19: mtnormalise outputs

nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
csd_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD"

printf "Subject\twm_norm\tgm_norm\tcsf_norm\tvf_fod\tvf_norm\n"

for subj in $(ls -1 "$nifti_base"); do
    d="$csd_base/$subj"
    wm=$([ -f "$d/wm_fod_norm.mif" ] && echo "✅" || echo "❌")
    gm=$([ -f "$d/gm_fod_norm.mif" ] && echo "✅" || echo "❌")
    csf=$([ -f "$d/csf_fod_norm.mif" ] && echo "✅" || echo "❌")
    vf=$([ -f "$d/vf_fod.mif" ] && echo "✅" || echo "❌")
    vfn=$([ -f "$d/vf_fod_norm.mif" ] && echo "✅" || echo "❌")
    printf "%s\t%s\t%s\t%s\t%s\t%s\n" "$subj" "$wm" "$gm" "$csf" "$vf" "$vfn"
done

echo -e "\n=== mtnormalise Audit Complete ==="
```

---

