---
layout: default
title: Tractography (Steps 15–26)
nav_order: 4
has_children: true
permalink: /tractography/
---

# Tractography — Steps 15–26

CSD model fitting → ROI registration → atlas-based exclusion-mask tractography → pyAFQ Mahalanobis cleaning → visual QC. The Anterior VTA→HPC Tract Addendum is also in this section.

| # | Step | One-liner |
|---|------|-----------|
| — | Why MRtrix? | Rationale for streamline-based pipeline |
| 15 | mrconvert | Convert DWI to MRtrix `.mif` |
| 16 | dwi2response | Per-subject response functions |
| 17 | responsemean | Group-average response functions |
| 18 | dwi2fod (MSMT-CSD) | Multi-shell multi-tissue CSD |
| 19 | mtnormalise | FOD intensity normalization |
| — | ROI Upload | Ranesh's VTA / HPC / atlas files |
| 20 | ANTs registration | MNI → T1 nonlinear warp |
| 21 | ROI warping | MNI → T1 → diffusion + visual QC |
| 22 | Atlas-based exclusion masks | Dilated-corridor masks |
| 23 | Test tractography | Parameter tuning (5 subjects) |
| 24 | Full tractography | All 57 subjects |
| 25 | pyAFQ cleaning | Mahalanobis distance cleanup |
| 26 | Visual QC | All 57 cleaned tracts |
| — | Anterior Tract Addendum | Same pipeline re-run with Ranesh's anterior atlas |
