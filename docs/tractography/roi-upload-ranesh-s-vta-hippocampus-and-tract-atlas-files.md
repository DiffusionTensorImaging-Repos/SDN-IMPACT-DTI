---
layout: default
title: "ROI Upload — Ranesh's VTA, Hippocampus, and Tract Atlas Files"
parent: "Tractography (Steps 15–26)"
nav_order: 19.5
---

# ROI Upload — Ranesh's VTA, Hippocampus, and Tract Atlas Files

Before we can run tractography, we need the seed, target, and exclusion ROIs in each subject's diffusion space. Ranesh Mopuru (Olson Lab) provided the following ROI files, all in **MNI 1mm standard space**:

| File | Description |
|---|---|
| `left_VTA_0.25_bin.nii.gz` | Left VTA — Pauli atlas, thresholded at 25% (seed ROI) |
| `right_VTA_0.25_bin.nii.gz` | Right VTA — Pauli atlas, thresholded at 25% (seed ROI) |
| `HPC_L_0.5_bin.nii.gz` | Left hippocampus — Harvard-Oxford atlas, 50% threshold (target ROI) |
| `HPC_R_0.5_bin.nii.gz` | Right hippocampus — Harvard-Oxford atlas, 50% threshold (target ROI) |
| `l_vta_l_hipp_1mm_MNI_GroupMean_thr50.nii.gz` | Left VTA→HPC tract atlas — Ranesh's group mean, 50% threshold (for exclusion mask) |
| `r_vta_r_hipp_1mm_MNI_GroupMean_thr50.nii.gz` | Right VTA→HPC tract atlas — Ranesh's group mean, 50% threshold (for exclusion mask) |
| `l_vta_l_hipp_1mm_MNI_GroupMean_OverlapProp.nii.gz` | Left tract — raw probabilistic overlap map (reference only) |
| `r_vta_r_hipp_1mm_MNI_GroupMean_OverlapProp.nii.gz` | Right tract — raw probabilistic overlap map (reference only) |

These files were stored locally in `Connectivity-Next-Steps/ROIS/VTA-HPC ROIs/` and uploaded to the cluster:

```bash
# Upload ROIs to cluster
scp /Users/dannyzweben/Desktop/SDN/DTI/Connectivity-Next-Steps/ROIS/VTA-HPC\ ROIs/*.nii.gz \
    tur50045@cla19097.tu.temple.edu:/data/projects/STUDIES/IMPACT/DTI/ROIs/VTA-HPC/
```

**Cluster location:** `/data/projects/STUDIES/IMPACT/DTI/ROIs/VTA-HPC/`

---

