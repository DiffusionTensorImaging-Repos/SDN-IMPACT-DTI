---
layout: default
title: "Step 21 — ROI Warping: MNI → T1 → Diffusion Space + Visual QC"
parent: "Tractography (Steps 15–26)"
nav_order: 21
---

# Step 21 — ROI Warping: MNI → T1 → Diffusion Space + Visual QC

With the ANTs warp fields computed in Step 20, we now warp all ROIs through two transforms to land them in each subject's native diffusion space:

1. **MNI → T1**: `antsApplyTransforms` using the warp + affine from Step 20, with `NearestNeighbor` interpolation (preserves binary mask values).
2. **T1 → Diffusion**: `flirt -applyxfm` using the `str2diff_<subj>.mat` matrix computed in Step 12, with `nearestneighbour` interpolation.

Each output is also binarized (`fslmaths -thr 0.5 -bin`) as a safety step — NearestNeighbor should already produce binary values, but this guarantees it.

**Why two steps instead of one?** The MNI → T1 transform is nonlinear (ANTs) and the T1 → diffusion transform is linear (FLIRT/FSL). These are different software tools with different transform formats, so we apply them separately. For binary ROI masks with NearestNeighbor interpolation, two rounds of resampling has negligible impact.

**ROIs warped per subject (6 total):**

| ROI | Purpose |
|---|---|
| `left_VTA_diff.nii.gz` | Seed for left hemisphere tractography |
| `right_VTA_diff.nii.gz` | Seed for right hemisphere tractography |
| `left_HPC_diff.nii.gz` | Target for left hemisphere tractography |
| `right_HPC_diff.nii.gz` | Target for right hemisphere tractography |
| `left_tract_atlas_diff.nii.gz` | Tract atlas for left exclusion mask (Step 22) |
| `right_tract_atlas_diff.nii.gz` | Tract atlas for right exclusion mask (Step 22) |

**Input (per subject):**
- `/data/projects/STUDIES/IMPACT/DTI/ROIs/VTA-HPC/*.nii.gz` (MNI space ROIs)
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/reg/mni2t1_1Warp.nii.gz` (from Step 20)
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/reg/mni2t1_0GenericAffine.mat` (from Step 20)
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/TRANSFORMS/<subj>/str2diff_<subj>.mat` (from Step 12)
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/BEDPOSTX/<subj>/bedpostx_input/nodif_brain_mask.nii.gz` (diffusion reference)

**Expected Output (per subject):**
```
derivatives/CSD/s1000/rois/
│
├── left_VTA_t1.nii.gz              # intermediate (T1 space)
├── left_VTA_diff.nii.gz            # final (diffusion space) — SEED
├── right_VTA_t1.nii.gz
├── right_VTA_diff.nii.gz           # SEED
├── left_HPC_t1.nii.gz
├── left_HPC_diff.nii.gz            # TARGET
├── right_HPC_t1.nii.gz
├── right_HPC_diff.nii.gz           # TARGET
├── left_tract_atlas_t1.nii.gz
├── left_tract_atlas_diff.nii.gz    # for exclusion mask
├── right_tract_atlas_t1.nii.gz
├── right_tract_atlas_diff.nii.gz   # for exclusion mask
```

This step is lightweight — we run up to 15 parallel jobs.

**Running Step 21 in tmux:**

1. SSH into the cluster and reattach (or create) the tmux session:
```bash
ssh -XY tur50045@cla19097.tu.temple.edu
tmux attach -t csd || tmux new -s csd
```

2. Create the script:
```bash
nano run_roi_warp.sh
```

3. Paste the following into nano:
```bash
#!/bin/bash
# ============================================================
# Step 21: Warp ROIs from MNI → T1 → Diffusion Space
# ============================================================
# Uses ANTs warp (Step 20) to bring ROIs from MNI to T1 space,
# then FLIRT str2diff matrix (Step 12) to bring them to diffusion.
# Both steps use NearestNeighbor interpolation for binary masks.
# Outputs are binarized as a safety step.
#
# ROIs warped (per hemisphere):
#   - VTA (Pauli atlas, 25% threshold)
#   - HPC (Harvard-Oxford, 50% threshold)
#   - Tract atlas (GroupMean_thr50)
#
# Input:  ROIs/VTA-HPC/*.nii.gz (MNI space)
#         CSD/<subj>/reg/mni2t1_* (ANTs warp from Step 20)
#         TRANSFORMS/<subj>/str2diff_<subj>.mat (FLIRT from Step 12)
# Output: CSD/<subj>/rois/*_diff.nii.gz (diffusion space)
# ============================================================

export PATH=/data/tools/ANTs/bin:/usr/local/fsl/bin:$PATH

roi_base="/data/projects/STUDIES/IMPACT/DTI/ROIs/VTA-HPC"
csd_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD"
ants_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/ANTs"
transforms_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/TRANSFORMS"
bedpostx_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/BEDPOSTX"
nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"

# ROI files (MNI space) and their output names
declare -a ROI_FILES=(
    "left_VTA_0.25_bin.nii.gz:left_VTA"
    "right_VTA_0.25_bin.nii.gz:right_VTA"
    "HPC_L_0.5_bin.nii.gz:left_HPC"
    "HPC_R_0.5_bin.nii.gz:right_HPC"
    "l_vta_l_hipp_1mm_MNI_GroupMean_thr50.nii.gz:left_tract_atlas"
    "r_vta_r_hipp_1mm_MNI_GroupMean_thr50.nii.gz:right_tract_atlas"
)

process_subj() {
    subj=$1
    echo ">>> [$subj] Warping ROIs to diffusion space"

    reg_dir="$csd_base/$subj/reg"
    roi_dir="$csd_base/$subj/rois"
    mkdir -p "$roi_dir"

    t1_brain="$ants_base/$subj/${subj}_BrainExtractionBrain.nii.gz"
    warp="$reg_dir/mni2t1_1Warp.nii.gz"
    affine="$reg_dir/mni2t1_0GenericAffine.mat"
    flirt_mat="$transforms_base/$subj/str2diff_${subj}.mat"
    diff_ref="$bedpostx_base/$subj/bedpostx_input/nodif_brain_mask.nii.gz"

    # Check all required files exist
    if [[ ! -f "$warp" || ! -f "$affine" ]]; then
        echo "!!! [$subj] Missing ANTs warp files, skipping"
        return
    fi
    if [[ ! -f "$flirt_mat" ]]; then
        echo "!!! [$subj] Missing FLIRT str2diff matrix, skipping"
        return
    fi
    if [[ ! -f "$diff_ref" ]]; then
        echo "!!! [$subj] Missing diffusion reference image, skipping"
        return
    fi

    for entry in "${ROI_FILES[@]}"; do
        roi_file="${entry%%:*}"
        roi_name="${entry##*:}"

        roi_mni="$roi_base/$roi_file"
        roi_t1="$roi_dir/${roi_name}_t1.nii.gz"
        roi_diff="$roi_dir/${roi_name}_diff.nii.gz"

        if [[ ! -f "$roi_mni" ]]; then
            echo "!!! [$subj] Missing ROI: $roi_file, skipping"
            continue
        fi

        # Step A: ANTs warp MNI → T1 (NearestNeighbor)
        antsApplyTransforms -d 3 \
            -i "$roi_mni" \
            -r "$t1_brain" \
            -o "$roi_t1" \
            -t "$warp" \
            -t "$affine" \
            -n NearestNeighbor

        # Step B: FLIRT T1 → Diffusion (nearestneighbour)
        flirt -in "$roi_t1" \
            -ref "$diff_ref" \
            -applyxfm -init "$flirt_mat" \
            -out "$roi_diff" \
            -interp nearestneighbour

        # Safety: binarize output
        fslmaths "$roi_diff" -thr 0.5 -bin "$roi_diff"
    done

    echo ">>> [$subj] Done"
}

export -f process_subj
export roi_base csd_base ants_base transforms_base bedpostx_base ROI_FILES

subjects=$(ls -1 "$nifti_base")
for subj in $subjects; do
    process_subj "$subj" &
    while [ "$(jobs -r | wc -l)" -ge 15 ]; do sleep 1; done
done
wait
echo "=== All ROI warps finished ==="
```

4. Save and exit nano:
Press Ctrl+O then Enter to save
Press Ctrl+X to close

5. Make the script runnable and execute inside tmux:
```bash
chmod +x run_roi_warp.sh
./run_roi_warp.sh 2>&1 | tee roi_warp.log
```

6. Detach from tmux while it runs (if needed):
Press Ctrl+B, then D to detach. Reconnect later with:
```bash
tmux attach -t csd
```
* Note: All coding output from this script is recorded in roi_warp.log.

### Step 21 Comprehensive Audit (9 Checks)

Following Ranesh Mopuru's QC approach — where he excluded 3 subjects for problematic registration — we run a 9-part automated audit covering every aspect of the ROI warp. The full audit script is at `/data/projects/STUDIES/IMPACT/DTI/scripts/step20_21_full_audit.sh`.

**Audit results (57/57 subjects):**

| # | Audit | Result |
|---|-------|--------|
| 1 | Step 20 ANTs transform files (affine, warp, invwarp, warped) | 57/57 PASS |
| 2 | Step 21 ROI file completeness (6 diff + 6 T1 intermediates) | 57/57 PASS |
| 3 | Voxel counts + outlier detection (>2 SD from mean) | 0 empty ROIs |
| 4 | ROI dimensions match diffusion reference | 57/57 PASS |
| 5 | VTA-HPC overlap (must be zero, per Ranesh) | 0 subjects with overlap |
| 6 | Binariness (all values 0 or 1) | 57/57 PASS |
| 7 | ROI laterality (left ROIs on left hemisphere) | 57/57 PASS |
| 8 | T1 intermediate files present (verify 2-stage warp) | 57/57 PASS |
| 9 | Registration quality (cross-correlation, flag <2 SD) | 2 borderline (CC=0.59, threshold=0.60) |

**Voxel count summary (non-zero voxels per ROI):**

| ROI | Min | Mean | Max | SD |
|-----|-----|------|-----|-----|
| L VTA | 32 | 44.4 | 56 | 5.5 |
| R VTA | 34 | 43.9 | 56 | 5.2 |
| L HPC | 308 | 394.8 | 497 | 33.0 |
| R HPC | 332 | 406.5 | 493 | 34.3 |
| L Atlas | 107 | 126.0 | 146 | 9.9 |
| R Atlas | 99 | 123.1 | 149 | 10.6 |

**Registration quality flagged subjects (s1694, s4531):** Both were visually inspected and confirmed to have correct ROI placement — the borderline CC score (0.59 vs threshold 0.60) reflects normal anatomical variation, not registration failure.

### Visual QC: Verifying ROI Placement in Diffusion Space

After warping, we visually confirm that ROIs landed in the correct anatomical locations. Following Ranesh's approach, visual QC was performed on **all 57 subjects** using three complementary methods.

**What to look for:**
- **VTA**: Should sit in the ventral midbrain, just anterior to the red nucleus, near the midline. It's tiny — only a few voxels. If it lands in the cerebral peduncle, pons, or outside the brainstem, the registration failed for that subject.
- **Hippocampus**: Should trace the medial temporal lobe, curving along the floor of the lateral ventricle. If it overlaps with the ventricle itself or sits in white matter, something went wrong.
- **Tract atlas**: Should form a thin corridor running from VTA up through the midbrain to the hippocampus. If it's scattered or covers half the brain, the threshold or registration is off.

**Red flags (re-check registration for that subject):**
- ROI sitting in ventricle, white matter, or cortex instead of the expected gray matter structure
- ROI completely absent (zero voxels after warping)
- ROI shifted laterally (e.g., left VTA appearing on the right side)

#### QC Method 1: Whole-Brain Context (Python/nibabel)

3-panel images (sagittal, coronal, axial) showing each ROI overlaid in yellow on the mean b0. Generated on the cluster using `roi_qc_python.py` for all 57 subjects (342 images total). Useful for confirming ROIs are in the right general brain region.

**Example — s1694 Left VTA (whole-brain view):**
![roi_qc_wholebrain_left_VTA]({{ "/images/roi_qc_wholebrain_left_VTA.png" | relative_url }})

**Example — s1694 Left Hippocampus (whole-brain view):**
![roi_qc_wholebrain_left_HPC]({{ "/images/roi_qc_wholebrain_left_HPC.png" | relative_url }})

#### QC Method 2: Zoomed ROI View (Python/nibabel)

Tightly cropped around each ROI with 5x scaling so you can see individual voxels and surrounding anatomy. Generated using `roi_qc_zoomed.py` for all 57 subjects (342 images total). Best for verifying precise anatomical placement.

**Example — s1694 Left VTA (zoomed):**
![roi_qc_zoomed_left_VTA]({{ "/images/roi_qc_zoomed_left_VTA.png" | relative_url }})

**Example — s1694 Left Hippocampus (zoomed):**
![roi_qc_zoomed_left_HPC]({{ "/images/roi_qc_zoomed_left_HPC.png" | relative_url }})

**Example — s1694 Left VTA-HPC Tract Atlas (zoomed):**
![roi_qc_zoomed_left_tract_atlas]({{ "/images/roi_qc_zoomed_left_tract_atlas.png" | relative_url }})

#### QC Method 3: FSLeyes Render (Publication Quality)

Full ortho views rendered locally via `fsleyes render` with color-coded overlays: VTA in yellow, hippocampus in red, tract atlas in green. Generated for all 57 subjects (114 images total). Includes orientation labels (P/A, L/R, S/I).

**Example — s1694 Left hemisphere (FSLeyes ortho):**
![roi_qc_fsleyes_ortho_left]({{ "/images/roi_qc_fsleyes_ortho_left.png" | relative_url }})

**Example — s1694 Right hemisphere (FSLeyes ortho):**
![roi_qc_fsleyes_ortho_right]({{ "/images/roi_qc_fsleyes_ortho_right.png" | relative_url }})

#### QC Image Locations

| QC Method | Images Per Subject | Total | Location |
|-----------|-------------------|-------|----------|
| Whole-brain (Python) | 6 | 342 | `CSD/<subj>/qc/roi_qc_*.png` |
| Zoomed (Python) | 6 | 342 | `CSD/<subj>/qc/roi_qc_*_zoomed.png` |
| FSLeyes render | 2 | 114 | `~/Desktop/SDN/DTI/data.check/roi_qc_fsleyes/<subj>/` |

#### QC Scripts

All QC scripts are stored at `/data/projects/STUDIES/IMPACT/DTI/scripts/`:

| Script | What it does |
|--------|-------------|
| `step20_21_full_audit.sh` | 9-part automated audit (run on cluster) |
| `roi_qc_python.py` | Whole-brain 3-panel overlays for all subjects (run on cluster) |
| `roi_qc_zoomed.py` | Zoomed ROI overlays for all subjects (run on cluster) |
| `fsleyes_qc_render.sh` | FSLeyes ortho renders (run locally with mounted server) |

#### QC Verdict

All 57 subjects pass all 9 automated audits and visual inspection. No subjects excluded. ROIs consistently land in the correct anatomical locations across all subjects. Ready for Step 22.

> **Anterior VTA→HPC tract:** The same MNI→T1→Diffusion warping procedure was later repeated for Ranesh's anterior tract atlas files. The VTA and HPC ROIs (seed/target) are shared — only the tract atlas file changes between the posterior and anterior pipelines. All 114 anterior atlas warps passed QC. See [Anterior Tract Addendum](#anterior-vtahpc-tract-addendum).

---

