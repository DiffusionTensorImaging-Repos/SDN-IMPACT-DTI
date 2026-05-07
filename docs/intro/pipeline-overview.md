---
layout: default
title: "What does the DTI pipeline ential?"
parent: "Introduction"
nav_order: 2
---

# What does the DTI pipeline ential?

- **Note** - see github repo for a a breif description of each of the steps below:https://github.com/DiffusionTensorImaging-Repos/SDN-IMPACT-DTI/blob/main/Pipelineoutline.MD

- Additionally all steps are described in detail before their implimentation below. 

A. Preprocessing
1. **DICOM to NIfTI Conversion**
2. **ANTs Skull Stripping**
3. **RB0 Concatenate**
4. **TOPUP**
5. **Mean B0 Image**
6. **Binary Brain Mask**
7. **MRDegibbes**
8. **Eddy Current Correction**
9. **DWI Extraction**
10. **DTI Fit**
11. **FLIRT and Convert**
12. **AFQ Prep - BIDS Conversion**
13. **ICV Calculation**

Index — IMPACT DTI Preprocessing Pipeline
1. [Step 1 — DICOM to NIfTI Conversion](#step-1--dicom-to-nifti-conversion)
2. [Step 2 -  ANTs Skull Stripping](#step-2---ants-skull-stripping)
3. [Step 3 — B0 Concatenation](#step-3--b0-concatenation)
4. [Step 4 — TOPUP (Susceptibility Distortion Correction)](#step-4--topup-susceptibility-distortion-correction)
5. [Step 5 — Mean B0 Image (Collapse Across Time)](#step-5--mean-b0-image-collapse-across-time)
6. [Step 6 — Brain Extraction on Mean B0](#step-6--brain-extraction-on-mean-b0)
7. [Step 7 — Gibbs Ringing Removal + b=250 Cleanup](#step-7--gibbs-ringing-removal--b250-cleanup)
8. [Step 8 — Eddy Current & Motion Correction](#step-8--eddy-current--motion-correction)
9. [Step 9: BedpostX](#step-9-bedpostx)
10. [Step 10: DWI Shell Extraction](#step-10-dwi-shell-extraction)
11. [Step 11 Tensor Fitting (DTIFIT)](#step-11-tensor-fitting-dtifit)
12. [Step 12: FLIRT and CONVERT (Spatial Alignment and Standardization)](#step-12-flirt-and-convert-spatial-alignment-and-standardization)
13. [Step 13: Intracranial Volume (ICV Estimation)](#step-13-intracranial-volume-icv-estimation)
14. [Step 14: PYAFQ - BIDS and Running AFQ](#step-14-pyafq---bids-and-running-afq)

Index — IMPACT DTI Tractography Pipeline (Section B)
15. [Step 15 — MRtrix Conversion (mrconvert)](#step-15--mrtrix-conversion-mrconvert)
16. [Step 16 — Response Function Estimation (dwi2response)](#step-16--response-function-estimation-dwi2response)
17. [Step 17 — Group-Average Response Functions (responsemean)](#step-17--group-average-response-functions-responsemean)
18. [Step 18 — Fiber Orientation Distribution (dwi2fod MSMT-CSD)](#step-18--fiber-orientation-distribution-dwi2fod-msmt-csd)
19. [Step 19 — FOD Normalization (mtnormalise)](#step-19--fod-normalization-mtnormalise)
20. [Step 20 — ANTs Registration: MNI → T1 Space](#step-20--ants-registration-mni--t1-space)
21. [Step 21 — ROI Warping: MNI → T1 → Diffusion Space + Visual QC](#step-21--roi-warping-mni--t1--diffusion-space--visual-qc)
22. Step 22 — Atlas-Based Exclusion Masks
23. Step 23 — Test Tractography (5 Subjects)
24. Step 24 — Full Tractography (All Subjects)
25. [Step 25 — Tract Cleaning (pyAFQ Mahalanobis Distance)](#step-25--tract-cleaning-pyafq-mahalanobis-distance)
26. [Step 26 — Visual QC of Cleaned Tracts](#step-26--visual-qc-of-cleaned-tracts-all-57-subjects)
    - [Anterior VTA→HPC Tract Addendum](#anterior-vtahpc-tract-addendum) — same pipeline re-run with new atlas from Ranesh
27. [Step 27 — Node-wise FA Extraction (AFQ-style Tract Profiling)](#step-27--node-wise-fa-extraction-afq-style-tract-profiling)
28. Step 28 — Statistical Analysis: Permutation Testing (awaiting Ranesh's script)
29. [Step 29 — NODDI Model Fitting (AMICO with Modulated Maps)](#step-29--noddi-model-fitting-amico-with-modulated-maps)
30. [Step 30 — Node-wise NODDI Extraction (NDI, ODI, FWF)](#step-30--node-wise-noddi-extraction-ndi-odi-fwf-along-tracts)
31. Step 31 — Statistical Analysis on NDI/ODI (permutation testing)


# DTI PREPROCESSING: 

