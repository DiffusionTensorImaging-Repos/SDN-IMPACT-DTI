---
layout: default
title: Preprocessing (Steps 1–14)
nav_order: 3
has_children: true
permalink: /preprocessing/
---

# Preprocessing — Steps 1–14

Raw DICOM through pyAFQ BIDS prep. Each step has its own page in the left sidebar with the exact scripts, audit, and outputs.

| # | Step | One-liner |
|---|------|-----------|
| 1 | DICOM → NIfTI | Convert raw DICOMs to NIfTI |
| 2 | Skull stripping | ANTs brain extraction on T1 |
| 3 | B0 concatenation | Stack the AP / PA b=0 volumes |
| 4 | TOPUP | Susceptibility distortion correction |
| 5 | Mean B0 | Collapse the b=0s across time |
| 6 | Brain extraction | Mask the mean B0 |
| 7 | Gibbs ringing + b=250 cleanup | MRtrix mrdegibbs |
| 8 | Eddy + motion correction | FSL eddy_cuda |
| 9 | BedpostX | Crossing-fiber model fitting |
| 10 | Shell extraction | Per-shell DWI subsets |
| 11 | DTIFIT | Tensor fitting → FA / MD / etc. |
| 12 | FLIRT + CONVERT | T1↔diffusion↔MNI alignment |
| 13 | ICV | Intracranial volume estimate |
| 14 | pyAFQ BIDS prep | Get data ready for AFQ |
