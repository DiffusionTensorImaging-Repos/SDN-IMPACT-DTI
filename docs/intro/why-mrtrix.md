---
layout: default
title: "Why MRtrix? (And why we're going back to BedpostX)"
parent: "Introduction"
nav_order: 3
---

# Why MRtrix? (And why we're going back to BedpostX)

In Step 9, we ran FSL's **BedpostX** — a Bayesian model that estimates fiber orientations at each voxel using a ball-and-stick approach. BedpostX is designed to feed FSL's **probtrackx2**, which produces **voxel-wise** probabilistic tract maps. The problem with voxel-wise maps is that you can only extract a single number — average FA across the entire tract. You cannot split the tract into segments, you cannot run permutation-based cluster correction along the tract, and you cannot use Mahalanobis-distance tract cleaning.

For the IMPACT analysis — testing whether white matter microstructure *along specific segments* of the VTA→hippocampus tract predicts motivated memory — we need **streamline-based tractography**. Streamlines let us:
- Split the tract into **100 evenly-spaced nodes**
- Extract FA (and later NDI/ODI from NODDI) at **each node** per subject
- Run **node-wise permutation testing** to identify which segments of the tract carry the effect
- Apply **Mahalanobis-distance cleaning** (pyAFQ) to remove anatomically implausible streamlines

MRtrix3's **dwi2fod** (Constrained Spherical Deconvolution) → **tckgen** pipeline produces these streamlines. This is the recommended approach for tract-specific microstructure analysis, as confirmed by Ranesh Mopuru (Olson Lab), Blake Elliott, and Linda Hoffman.

**The good news:** BedpostX wasn't wasted. When we ran BedpostX in Step 9, we organized the eddy-corrected DWI data, rotated gradient tables, b-values, and brain mask into a clean `bedpostx_input/` directory — and that is exactly what MRtrix needs as input. So we go back to `BEDPOSTX/<subj>/bedpostx_input/` and feed those same files (`data.nii.gz`, `bvecs`, `bvals`, `nodif_brain_mask.nii.gz`) into the MRtrix CSD pipeline.

**Pipeline adapted from**: Ranesh Mopuru's complete MRtrix tractography pipeline (originally developed for HCP 7T data in the Olson Lab at Temple). His scripts were adapted for our IMPACT 3T multi-shell data with the following key differences:

| | Ranesh (HCP 7T) | IMPACT (3T) |
|---|---|---|
| Skull stripping | mri_synthstrip | ANTs (already done, Step 2) |
| Registration to diffusion space | Not needed (HCP data already T1-aligned) | FLIRT transforms from Step 12 |
| Exclusion ROIs for tractography | 20+ individual hand-drawn exclusion masks | Ranesh's tract atlas (GroupMean_thr50) as single exclusion mask |
| tckgen streamline count | 2500 | 1000 |
| tckgen seeding attempts | 25 million | 5 million |
| FOD cutoff | 0.06 | Start at 0.1, experiment with 0.08 and 0.06 |

**Note on running scripts**: Starting from this section, we use **tmux** instead of nohup. tmux creates a persistent terminal session that survives SSH disconnects and lets you reattach to monitor progress. This is more reliable and flexible than nohup for long-running jobs.

**Quick tmux reference:**
```bash
tmux new -s csd          # create a new session named "csd"
# run your script inside tmux, then:
Ctrl+B, then D           # detach (script keeps running)
tmux attach -t csd       # reattach later
tmux ls                  # list active sessions
tmux kill-session -t csd # kill a session when done
```

---

