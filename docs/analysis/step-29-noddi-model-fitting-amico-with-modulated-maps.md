---
layout: default
title: "Step 29 — NODDI Model Fitting (AMICO with Modulated Maps)"
parent: "Analysis (Steps 27–31)"
nav_order: 29
---

# Step 29 — NODDI Model Fitting (AMICO with Modulated Maps)

Ranesh emphasized NODDI — he found NDI revealed effects that FA missed in his HCP cohort ("NDI_modulated" specifically, nodes 25–75). We fit NODDI on all 57 subjects using the AMICO toolbox with his exact configuration.

**Why modulated maps (per Ranesh's email):** Standard NODDI output is contaminated by partial-volume effects (free-water signal mixing with tissue compartments). The `doSaveModulatedMaps=True` flag in AMICO produces `fit_NDI_modulated.nii.gz` and `fit_ODI_modulated.nii.gz`, which apply a tissue-weighted correction described in [Parker et al. 2021](https://doi.org/10.1016/j.neuroimage.2021.118749). FWF has no modulated version — the tissue-weighting *is* the partial-volume correction for NDI/ODI, so you use the regular `fit_FWF.nii.gz` if you want free-water content.

**Dependencies:**
- AMICO (`pip3 install --user dmri-amico`) — version 2.1.1 installed on cluster.

**Input (per subject — same files as Step 25):**
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/BEDPOSTX/<subj>/bedpostx_input/data.nii.gz` (eddy-corrected DWI)
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/BEDPOSTX/<subj>/bedpostx_input/bvals`
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/BEDPOSTX/<subj>/bedpostx_input/bvecs`
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/BEDPOSTX/<subj>/bedpostx_input/nodif_brain_mask.nii.gz`

**Expected Output (per subject):**
```
derivatives/NODDI/sub-s1000/
│
├── config.pickle
├── sub-s1000_scheme.scheme
├── fit_dir.nii.gz               # primary fiber direction
├── fit_NDI.nii.gz               # neurite density index
├── fit_ODI.nii.gz               # orientation dispersion index
├── fit_FWF.nii.gz               # free water fraction
├── fit_NDI_modulated.nii.gz     # NDI with tissue-weighted PVE correction (USE FOR ANALYSIS)
├── fit_ODI_modulated.nii.gz     # ODI with tissue-weighted PVE correction (USE FOR ANALYSIS)
└── fit_RMSE.nii.gz              # quality: model-fit residual
```

**Ranesh's parameters (reproduced exactly):**

| Parameter | Value | Notes |
|-----------|-------|-------|
| `amico.util.fsl2scheme` `bStep` | 200 | Rounds b-values to nearest 200 (handles jitter around 0/1000/2000/3250/5000) |
| `b0_thr` | 100 | Treat b-values < 100 as b0 |
| `doSaveModulatedMaps` | True | Partial volume correction output |
| `doComputeRMSE` | True | QC output |
| `BLAS_nthreads` | 1 | Prevents BLAS over-subscription |
| `save_dir_avg` | True | Saves full per-voxel metrics |

**Parallelization strategy:** Ranesh ran 48 threads per subject serially. Our cluster has 48 cores + 125 GB RAM, so we ran **4 subjects in parallel × 12 threads each** = all 48 cores saturated with better wall-time utilization. A single-subject fit takes ~36 seconds, so 57 subjects with 4-way parallelism completed in ~15 minutes total.

**Running Step 29 in tmux:**

1. SSH into the cluster and create a tmux session:
```bash
ssh -XY tur50045@cla19097.tu.temple.edu
tmux new -s step29
```

2. Create the single-subject Python script:
```bash
nano /data/projects/STUDIES/IMPACT/DTI/scripts/run_step29_noddi.py
```

3. Paste the Python script (adapted from Ranesh's `NODDI_fitting.py` with IMPACT paths — one-subject-per-invocation pattern).

4. Create the parallel runner `run_step29_noddi_parallel.sh` that loops through all 57 subjects launching 4 at a time with `NODDI_NTHREADS=12`.

5. Run:
```bash
chmod +x /data/projects/STUDIES/IMPACT/DTI/scripts/run_step29_noddi_parallel.sh
bash /data/projects/STUDIES/IMPACT/DTI/scripts/run_step29_noddi_parallel.sh
```

6. Detach from tmux while it runs (Ctrl+B, D). Reconnect with `tmux attach -t step29`.

**NOTE on the kernel-directory race condition:** AMICO's `generate_kernels(regenerate=True)` removes and regenerates files in a shared `NODDI/kernels/` directory. When multiple parallel jobs hit this simultaneously (early in the run), one job may delete a file another is writing, causing `FileNotFoundError`. On our run, 3 subjects (s1324, s418, s673) hit this on the first pass. They were re-run serially afterwards (each subject has its own output directory, so retries are safe) and all succeeded. If re-running from scratch, consider generating kernels once on a single subject before launching the parallel pool.

**Downloading a subject's NODDI outputs locally (for FSLeyes inspection):**
```bash
scp -r tur50045@cla19097.tu.temple.edu:/data/projects/STUDIES/IMPACT/DTI/derivatives/NODDI/sub-s1000 \
    ~/Desktop/SDN/DTI/data.check/noddi_s1000/
```

**Interactive review in FSLeyes (verify NDI looks right):**
```bash
export FSLDIR=/usr/local/fsl
source $FSLDIR/etc/fslconf/fsl.sh

fsleyes /data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/s1000/qc/mean_b0.nii.gz \
    /data/projects/STUDIES/IMPACT/DTI/derivatives/NODDI/sub-s1000/fit_NDI_modulated.nii.gz \
    -cm render3 -dr 0 1 &
```

NDI should show the classic white-matter-bright pattern (high in CC, internal capsule, corona radiata; low in cortex and CSF).

**Step 29 Audit — verify NODDI outputs exist for all subjects:**
```bash
#!/bin/bash
# Audit Step 29: NODDI fitting outputs

nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
noddi_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/NODDI"

pass=0; fail=0
printf "%-12s %-4s %-4s %-4s %-4s %-4s\n" "Subject" "NDI" "ODI" "FWF" "NDIm" "ODIm"

for subj in $(ls -1 "$nifti_base"); do
    d="$noddi_base/sub-$subj"
    ndi=$([ -f "$d/fit_NDI.nii.gz" ] && echo "✅" || echo "❌")
    odi=$([ -f "$d/fit_ODI.nii.gz" ] && echo "✅" || echo "❌")
    fwf=$([ -f "$d/fit_FWF.nii.gz" ] && echo "✅" || echo "❌")
    ndim=$([ -f "$d/fit_NDI_modulated.nii.gz" ] && echo "✅" || echo "❌")
    odim=$([ -f "$d/fit_ODI_modulated.nii.gz" ] && echo "✅" || echo "❌")
    printf "%-12s %-4s %-4s %-4s %-4s %-4s\n" "$subj" "$ndi" "$odi" "$fwf" "$ndim" "$odim"

    if [[ -f "$d/fit_NDI_modulated.nii.gz" ]]; then
        pass=$((pass + 1))
    else
        fail=$((fail + 1))
    fi
done
echo ""
echo "Pass: $pass / $((pass + fail))"
echo "Fail: $fail / $((pass + fail))"
```

### Step 29 Results

**57/57 subjects pass** — all have the complete set of NODDI outputs (NDI, ODI, FWF + modulated NDI/ODI + RMSE). No subjects excluded. Ready for Step 30 (nodewise extraction).

---

