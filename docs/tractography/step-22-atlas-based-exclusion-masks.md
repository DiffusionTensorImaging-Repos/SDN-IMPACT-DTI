---
layout: default
title: "Step 22 — Atlas-Based Exclusion Masks"
parent: "Tractography (Steps 15–26)"
nav_order: 22
---

# Step 22 — Atlas-Based Exclusion Masks

Ranesh's original pipeline used 13 individual exclusion ROIs (ventral pallidum, accumbens L/R, striatum, thalamus, cortex/cerebellum, brainstem, amygdala, red nucleus, fornix, optic tract, optic nerve, opposite hemisphere) to constrain tractography. Each had to be warped, tidied (overlaps subtracted), and passed as separate `-exclude` flags to tckgen.

Instead, we use the **atlas shortcut** that Ranesh recommended: his GroupMean_thr50 tract atlas (built from ~170 HCP 7T subjects using those 13 exclusion ROIs) already encodes "where VTA→HPC streamlines should plausibly go." We dilate this atlas by 2 voxels, add the VTA seed and HPC target ROIs, binarize the result into an "inclusion zone," and invert everything outside it into a single exclusion mask.

From Ranesh's meeting notes: "By dilating the atlas by like two-ish voxels, you're generating like this box where your streamlines should plausibly go through... you exclude everything outside of this box... add the VTA and the hippocampus to this atlas mask, and then you invert everything else."

**Logic (per hemisphere):**
1. Dilate tract atlas by 2 voxels (`fslmaths -dilM -dilM`)
2. Add VTA + HPC to dilated atlas, binarize → inclusion zone
3. Invert inclusion zone → exclusion mask (everything outside is excluded)

**Input (per subject, from Step 21):**
- `CSD/<subj>/rois/left_tract_atlas_diff.nii.gz` — left GroupMean_thr50 atlas in diffusion space
- `CSD/<subj>/rois/right_tract_atlas_diff.nii.gz` — right GroupMean_thr50 atlas in diffusion space
- `CSD/<subj>/rois/left_VTA_diff.nii.gz` — left VTA seed ROI in diffusion space
- `CSD/<subj>/rois/right_VTA_diff.nii.gz` — right VTA seed ROI in diffusion space
- `CSD/<subj>/rois/left_HPC_diff.nii.gz` — left hippocampus target in diffusion space
- `CSD/<subj>/rois/right_HPC_diff.nii.gz` — right hippocampus target in diffusion space

**Expected Output (per subject):**
```
derivatives/CSD/s1000/rois/
│
├── l_atlas_dilated.nii.gz      # left tract atlas dilated by 2 voxels
├── r_atlas_dilated.nii.gz      # right tract atlas dilated by 2 voxels
├── l_inclusion_zone.nii.gz     # left allowed region (atlas + VTA + HPC, binarized)
├── r_inclusion_zone.nii.gz     # right allowed region
├── exclusion_mask_l.nii.gz     # LEFT exclusion mask (inverted inclusion zone)
├── exclusion_mask_r.nii.gz     # RIGHT exclusion mask (inverted inclusion zone)
```

This step is lightweight — fslmaths operations only. We allow up to 30 parallel jobs.

**Running Step 22 in tmux:**

1. SSH into the cluster and reattach (or create) the tmux session:
```bash
ssh -XY tur50045@cla19097.tu.temple.edu
tmux attach -t csd || tmux new -s csd
```

2. Create the script:
```bash
nano run_step22_exclusion_masks.sh
```

3. Paste the following into nano:
```bash
#!/bin/bash
# ============================================================
# Step 22: Build Atlas-Based Exclusion Masks
# ============================================================
# Uses Ranesh's GroupMean_thr50 tract atlas to create a single
# exclusion mask per hemisphere, replacing 13 individual exclusion ROIs.
#
# Logic (per Ranesh):
#   1. Dilate tract atlas by 2 voxels (fslmaths -dilM -dilM)
#   2. Add VTA seed + HPC target to dilated atlas
#   3. Binarize = inclusion zone (where streamlines are allowed)
#   4. Invert = exclusion mask (everything outside is excluded)
#
# Input:  CSD/<subj>/rois/ (atlas, VTA, HPC in diffusion space)
# Output: CSD/<subj>/rois/ (exclusion_mask_l/r.nii.gz)
# ============================================================

export FSLDIR=/usr/local/fsl
export PATH=$FSLDIR/bin:$PATH
source $FSLDIR/etc/fslconf/fsl.sh

csd_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD"
nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
log_file="/data/projects/STUDIES/IMPACT/DTI/scripts/step22.log"

echo "=== Step 22: Building exclusion masks ==="  > "$log_file"
echo "Started: $(date)" >> "$log_file"

process_subj() {
    subj=$1
    d="$csd_base/$subj/rois"

    # Check inputs exist
    missing=0
    for f in left_tract_atlas_diff.nii.gz right_tract_atlas_diff.nii.gz \
             left_VTA_diff.nii.gz right_VTA_diff.nii.gz \
             left_HPC_diff.nii.gz right_HPC_diff.nii.gz; do
        if [ ! -f "$d/$f" ]; then
            echo "!!! [$subj] Missing $f — SKIPPING" | tee -a "$log_file"
            missing=1
        fi
    done
    if [ "$missing" -eq 1 ]; then return 1; fi

    echo ">>> [$subj] Building exclusion masks" | tee -a "$log_file"

    # === LEFT HEMISPHERE ===
    # 1. Dilate tract atlas by 2 voxels
    fslmaths "$d/left_tract_atlas_diff.nii.gz" -dilM -dilM "$d/l_atlas_dilated.nii.gz"

    # 2. Add VTA + HPC to dilated atlas, binarize = inclusion zone
    fslmaths "$d/l_atlas_dilated.nii.gz" \
        -add "$d/left_VTA_diff.nii.gz" \
        -add "$d/left_HPC_diff.nii.gz" \
        -bin "$d/l_inclusion_zone.nii.gz"

    # 3. Invert = exclusion mask
    fslmaths "$d/l_inclusion_zone.nii.gz" -binv "$d/exclusion_mask_l.nii.gz"

    # === RIGHT HEMISPHERE ===
    fslmaths "$d/right_tract_atlas_diff.nii.gz" -dilM -dilM "$d/r_atlas_dilated.nii.gz"

    fslmaths "$d/r_atlas_dilated.nii.gz" \
        -add "$d/right_VTA_diff.nii.gz" \
        -add "$d/right_HPC_diff.nii.gz" \
        -bin "$d/r_inclusion_zone.nii.gz"

    fslmaths "$d/r_inclusion_zone.nii.gz" -binv "$d/exclusion_mask_r.nii.gz"

    echo ">>> [$subj] Done" | tee -a "$log_file"
}

export -f process_subj
export csd_base log_file FSLDIR PATH

# Run all subjects in parallel (lightweight fslmaths — 30 jobs fine)
for subj in $(ls -1 "$nifti_base"); do
    process_subj "$subj" &
    while [ "$(jobs -r | wc -l)" -ge 30 ]; do sleep 0.5; done
done
wait

echo "=== Step 22 Complete: $(date) ===" | tee -a "$log_file"
```

4. Save and exit nano:
Press Ctrl+O then Enter to save
Press Ctrl+X to close

5. Make the script runnable and execute inside tmux:
```bash
chmod +x run_step22_exclusion_masks.sh
./run_step22_exclusion_masks.sh 2>&1 | tee step22.log
```

6. Detach from tmux while it runs (if needed):
Press Ctrl+B, then D to detach. Reconnect later with:
```bash
tmux attach -t csd
```
* Note: All coding output from this script is recorded in step22.log.

**Step 22 Audit — verify exclusion masks for all subjects (7 checks):**

The audit verifies:
1. **File existence** — all 6 output files per subject
2. **Binary check** — exclusion masks contain only 0s and 1s
3. **Dimension match** — masks match DWI dimensions
4. **VTA not excluded** — VTA voxels have value 0 in the exclusion mask (i.e., they are NOT excluded)
5. **HPC not excluded** — HPC voxels have value 0 in the exclusion mask
6. **Exclusion coverage** — inclusion zone is <20% of total volume (most of the brain is excluded)
7. **Inclusion zone size** — reasonable voxel count (100-50000 range)

Results: **57/57 subjects pass all 7 checks. 0 failures, 0 warnings.**

Inclusion zone voxel counts range from ~1526 to ~1934 (mean ≈ 1720), consistent across subjects — this represents the narrow VTA→HPC white matter corridor.

### Step 22 Visual QC

QC images show the inclusion corridor (green), VTA (yellow), and HPC (red) overlaid on the mean b0 in three views (sagittal, coronal, axial), both whole-brain and zoomed.

**Example: s1000 — Left VTA→HPC exclusion mask:**

The green corridor traces a plausible anatomical path from VTA (midbrain) through medial forebrain bundle white matter to hippocampus (medial temporal lobe). VTA and HPC are fully contained within the inclusion zone.

| Script | Purpose |
|--------|---------|
| `run_step22_exclusion_masks.sh` | Build exclusion masks for all subjects |
| `step22_audit.sh` | 7-check automated audit |
| `step22_visual_qc.py` | Generate QC overlay images (run on cluster) |

#### QC Verdict

All 57 subjects pass all 7 automated audits and visual inspection. Exclusion masks show anatomically plausible VTA→HPC corridors. Inclusion zone sizes are consistent (1526-1934 voxels). Ready for Step 23 (test tractography).

> **Anterior VTA→HPC tract:** Anterior exclusion masks were later built using the same dilated-corridor approach with the anterior tract atlas. Inclusion zone sizes (~1,400 voxels per hemisphere) are comparable to the posterior tract. All 114 anterior masks passed QC. See [Anterior Tract Addendum](#anterior-vtahpc-tract-addendum).

**NOTE**: Ranesh recommended experimenting with 1 vs 2 voxel dilation. We start with 2 voxels. If Step 23 test tractography produces tracts that look too loose/dispersed, we can re-run with 1 voxel dilation.

---

