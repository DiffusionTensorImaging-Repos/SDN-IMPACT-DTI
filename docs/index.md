---
layout: default
title: Overview
nav_order: 1
description: "End-to-end documentation for the SDN Lab's IMPACT DTI pipeline."
permalink: /
---

# 🧠 SDN Lab — Project IMPACT DTI Pipeline
{: .fs-9 }

End-to-end documentation for the diffusion tractography pipeline built for the IMPACT project (Temple SDN Lab × Olson Lab collaboration).
{: .fs-6 .fw-300 }

[Browse on GitHub](https://github.com/DiffusionTensorImaging-Repos/SDN-IMPACT-DTI){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[Jump to first step](preprocessing/step-01-dicom){: .btn .fs-5 .mb-4 .mb-md-0 }

---

## What this site is

This site walks through every step of the IMPACT DTI pipeline — from raw DICOMs to AFQ-style FA / NDI / ODI tract profiles ready for statistical testing. Each step has its own page on the left sidebar. Every page documents the inputs, outputs, the exact script(s) we ran, an audit script, and the QC results.

## Sample

- **N = 57** mothers (30s–40s), socially anxious children
- 3T MRI, multi-shell diffusion (b = 0, 1000, 2000, 3250, 5000)
- b = 250 was acquired but excluded due to FOV issues

## Two tracts of interest

We extracted **bilateral VTA→hippocampus tracts in two pathway variants** (posterior and anterior — both provided by Ranesh's group atlas) and pulled both **FA** (DTIFIT) and **NODDI** metrics (NDI / ODI / FWF, modulated maps) along 100 nodes per tract.

| Tract | Status |
|-------|--------|
| Posterior VTA → HPC (L + R) | ✅ Complete |
| Anterior VTA → HPC (L + R) | ✅ Complete |
| VTA → striatum / NAcc (control) | Pending — atlas request to Ranesh |

## Pipeline at a glance

| Stage | Steps | What it produces |
|-------|-------|------------------|
| **Preprocessing** | 1–14 | Eddy-/distortion-corrected DWI, FA maps, anatomical alignment |
| **Tractography** | 15–26 | CSD model + cleaned VTA→HPC streamlines |
| **Analysis** | 27, 29, 30 | Node-wise FA / NODDI CSVs ready for permutation testing |

## Key collaborators

- **Danny Zweben** — Clinical Psych PhD student, Temple SDN Lab (project lead)
- **Johanna Jarcho** — PhD advisor, SDN Lab Director
- **Ingrid Olson** — PI, Olson Lab (collaborating)
- **Ranesh Mopuru** — Postdoc, Olson Lab (provided VTA-HPC group atlas, NODDI / cleaning / permutation testing scripts)
- **Blake Elliott** — Olson Lab (collaborating on anterior vs. posterior pathway analyses)

---

## How this site is organized

The left sidebar is grouped by pipeline phase:

- **Introduction** — environment setup, why MRtrix
- **Preprocessing (Steps 1–14)** — raw DICOM all the way through pyAFQ BIDS prep
- **Tractography (Steps 15–26)** — CSD model fitting, ROI registration, exclusion-mask tractography, cleaning, QC
- **Analysis (Steps 27, 29, 30)** — node-wise FA + NODDI extraction (Steps 28 / 31 statistical testing scripts ready, awaiting outcome variable)

Each page includes the **exact** scripts that were run on the cluster, plus per-step audits and visual QC verdicts so the pipeline is end-to-end reproducible.
