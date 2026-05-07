---
layout: default
title: "Anterior VTA→HPC Tract Addendum"
parent: "Tractography (Steps 15–26)"
nav_order: 27
---

# Anterior VTA→HPC Tract Addendum

### Background

After we completed the full pipeline for the posterior VTA→HPC tract, Ranesh and Blake informed us they had identified a second VTA→HPC tract — an **anterior** projection that is "more aligned with how we think of the VTA-hipp projections" than the posterior tract we ran. Ranesh's exact words:

> "The one you have right now is what we are calling the posterior VTA-hipp tract, we found an anterior one that is more aligned with how we think of the VTA-hipp projections. I think you should still run this posterior one, since they travel the same path for the first 75-80 ish nodes, so if you see an effect in the posterior tract, it will extend to the anterior tract."

Ranesh sent us two new tract atlas files (left and right anterior VTA→HPC, both thresholded at 50% from his group mean at HCP 7T) and confirmed that **the exact same pipeline (Steps 21-26) applies**, just swapping in the anterior atlas files for the posterior ones at Step 22.

### Files Added

| File | Description |
|---|---|
| `anterior_l_vta_l_hipp_1mm_MNI_GroupMean_thr50.nii.gz` | Left anterior VTA→HPC tract atlas (MNI 1mm, thresholded at 50%) |
| `anterior_r_vta_r_hipp_1mm_MNI_GroupMean_thr50.nii.gz` | Right anterior VTA→HPC tract atlas (MNI 1mm, thresholded at 50%) |

Both uploaded to `/data/projects/STUDIES/IMPACT/DTI/ROIs/VTA-HPC/` on the cluster.

### Pipeline Execution

Ran the same Steps 21, 22, 24, and 25 pipeline using the anterior atlas files — all packaged into one consolidated script (`run_anterior_full_pipeline.sh`) since the procedure is identical:

- **Step 21a:** Warped anterior atlas MNI → T1 (ANTs) → Diffusion (FLIRT). Output: `anterior_<l/r>_tract_atlas_diff.nii.gz`
- **Step 22a:** Built anterior exclusion masks (dilated corridor + VTA + HPC, then inverted). Output: `anterior_exclusion_mask_<l/r>.nii.gz`
- **Step 24a:** Ran tckgen on all 57 subjects (seed: VTA, include: HPC, exclude: anterior mask, cutoff 0.01, select 2500, seeds 25M). Output: `tckgen/anterior_<l/r>_vta_<l/r>_hipp/anterior_<l/r>_vta_<l/r>_hipp_0.01.tck`
- **Step 25a:** Ran pyAFQ `clean_bundle` with Ranesh's parameters. Output: `..._0.01_cleaned.tck`

**Result: 114/114 pass** — every subject hit 2500 streamlines and produced a clean bundle. Seeds used ranged from ~1.5M to ~11M (slightly higher than posterior ~1.1M average, reflecting the smaller anterior projection — but all well under the 25M cap).

### Visual QC — All Three Stages

Generated 342 QC images (57 subjects × 2 hemispheres × 3 stages) mirroring the QC from the posterior pipeline.

**Step 21a QC — Anterior tract atlas in diffusion space (example: s169 left):**

![Anterior atlas QC]({{ "/images/anterior_step21a_atlas.png" | relative_url }})

The red arc shows the anterior tract atlas after being warped through the two-step MNI → T1 → Diffusion transform chain. It sits medial/anterior to where the posterior tract runs, following the expected anatomy of the anterior VTA→HPC projection. All 57 subjects × 2 hemispheres (114 images) — **0 flags.**

**Step 22a QC — Anterior exclusion zone (inclusion region shown in cyan; example: s169 left):**

![Anterior inclusion QC]({{ "/images/anterior_step22a_incl.png" | relative_url }})

The cyan region is the inclusion zone (dilated anterior tract atlas + VTA + HPC) — everything outside this zone becomes the exclusion mask. Inclusion zone size averages ~1,400 voxels per hemisphere, virtually identical to the posterior tract's ~1,500 voxels.

> **Note on the "LOW_COVERAGE" flag:** The automated QC script flags any inclusion zone that covers <1% of the brain. All 114 anterior inclusion zones triggered this flag (0.2–0.3% of brain) — this is a **false positive**. The inclusion zone is SUPPOSED to be small (it's a tight anatomical corridor, not a whole-brain mask). The posterior tract's inclusion zones are the same size and would have triggered the same flag if we had used this threshold. Visual inspection confirmed all 114 zones are anatomically correct.

**Step 26a QC — Cleaned anterior tract bundles (example: s169 left):**

![Anterior tract QC s169]({{ "/images/anterior_step26a_tract_s169.png" | relative_url }})

**Another subject (s1000 left):**

![Anterior tract QC s1000]({{ "/images/anterior_step26a_tract_s1000.png" | relative_url }})

Every cleaned anterior tract shows a focused, coherent bundle running from the VTA into the hippocampus along the anterior pathway. The tracts are tight (post-cleaning), anatomically plausible, and consistent across subjects. **0 flags across 114 cleaned tracts.**

### QC Script

All three QC stages were run in a single Python script (`anterior_qc_all.py`) using the same approach as the posterior pipeline:
- nibabel + matplotlib for TDI generation and overlay rendering
- Automated flag checks (voxel counts, density thresholds)
- Output: 342 PNGs (3 stages × 114 subject-hemisphere pairs) + comprehensive log

**Running the QC script (via tmux, same pattern as other steps):**

```bash
ssh -XY tur50045@cla19097.tu.temple.edu
tmux new -s qcant
python3 /data/projects/STUDIES/IMPACT/DTI/scripts/anterior_qc_all.py 2>&1 | tee anterior_qc_output.log
```

**Downloading QC images locally (for FSLeyes inspection or browsing):**
```bash
mkdir -p ~/Desktop/SDN/DTI/data.check/anterior_qc
scp tur50045@cla19097.tu.temple.edu:/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/qc_anterior/*.png \
    ~/Desktop/SDN/DTI/data.check/anterior_qc/
```

**Interactive review in FSLeyes (same as posterior Step 26):**
```bash
export FSLDIR=/usr/local/fsl
source $FSLDIR/etc/fslconf/fsl.sh

# Example: s1000 anterior left
fsleyes /data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/s1000/qc/mean_b0.nii.gz \
    /data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/s1000/tckgen/anterior_l_vta_l_hipp/anterior_l_vta_l_hipp_0.01_cleaned.tck \
    -cm hot -a 70 &
```

### Final Audit Summary

| Stage | Pass | Flags | Notes |
|-------|------|-------|-------|
| Step 21a (atlas warp) | 114/114 | 0 | All atlases correctly placed in diffusion space |
| Step 22a (exclusion masks) | 114/114 | 0 (*) | *114 false-positive LOW_COVERAGE flags — threshold artifact, not an issue |
| Step 24a (tractography) | 114/114 | 0 | Every subject hit 2500 streamlines |
| Step 25a (cleaning) | 114/114 | 0 | Retention ~30–45%, consistent with posterior |
| Step 26a (visual QC) | 114/114 | 0 | All cleaned bundles anatomically correct |

**Result:** The anterior VTA→HPC tract pipeline completed successfully for all 57 subjects with no subjects excluded. Both posterior and anterior tracts are now ready for downstream FA extraction (Step 27) and statistical analysis (Step 28).

### What's Next

All downstream steps (27–31) will be run on **both** the posterior and anterior tracts:
- **Step 27** (Node-wise FA extraction): 100 nodes × 2 hemispheres × 2 tracts (posterior/anterior) = 4 FA profiles per subject
- **Step 28** (Permutation testing): Same for both tracts — will enable the anterior vs posterior dissociability analysis Ranesh mentioned
- **Steps 29–31** (NODDI): NDI/ODI extraction and testing on both tract sets

Ranesh noted that the core bundles are similar for the first ~60 nodes, so effects in the posterior tract should extend to the anterior tract. Differences in the later nodes (especially nodes 60+) may reveal tract-specific functional roles — this is the kind of analysis he and Blake are actively working on.

---

