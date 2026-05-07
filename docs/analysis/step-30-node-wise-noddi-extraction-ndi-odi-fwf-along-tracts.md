---
layout: default
title: "Step 30 — Node-wise NODDI Extraction (NDI, ODI, FWF along tracts)"
parent: "Analysis (Steps 27–31)"
nav_order: 30
---

# Step 30 — Node-wise NODDI Extraction (NDI, ODI, FWF along tracts)

With the NODDI maps from Step 29 and the cleaned tracts from Step 25, we extract NDI, ODI, and FWF along each tract at 100 equidistant nodes. This is a direct port of Ranesh's `nodewise_noddi.py` script to our IMPACT paths — identical profiling approach (QuickBundles orientation + AFQ Gaussian-weighted profiling), just using our cleaned tract files instead of Ranesh's HCP tracts.

**Extraction follows Ranesh's exact approach (modulated NDI + ODI, regular FWF):**
- **NDI** from `fit_NDI_modulated.nii.gz` (partial-volume corrected)
- **ODI** from `fit_ODI_modulated.nii.gz` (partial-volume corrected)
- **FWF** from `fit_FWF.nii.gz` (no modulated version needed — tissue weighting is the PVE correction)

**Input (per subject, per tract):**
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/tckgen/<tract>/<tract>_0.01_cleaned.tck` (from Step 25)
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/NODDI/sub-<subj>/fit_NDI_modulated.nii.gz`
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/NODDI/sub-<subj>/fit_ODI_modulated.nii.gz`
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/NODDI/sub-<subj>/fit_FWF.nii.gz`

**Expected Output (per tract):**
```
derivatives/nodewise_noddi/
│
├── csvs/
│   ├── l_vta_l_hipp_noddi_nodewise_all_subjects.csv
│   ├── r_vta_r_hipp_noddi_nodewise_all_subjects.csv
│   ├── anterior_l_vta_l_hipp_noddi_nodewise_all_subjects.csv
│   └── anterior_r_vta_r_hipp_noddi_nodewise_all_subjects.csv
│
└── <subj>/<tract>/
    ├── <tract>_NDI_profile.png
    ├── <tract>_ODI_profile.png
    └── <tract>_FWF_profile.png
```

Each CSV has 5,701 rows (header + 57 × 100) with columns: `Subject, Tract, Node, NDI, ODI, FWF`.

**Running Step 30 in tmux:**

1. SSH into the cluster and create a tmux session:
```bash
ssh -XY tur50045@cla19097.tu.temple.edu
tmux new -s step30
```

2. Create the script `run_step30_noddi_extraction.py` — it's a direct port of Ranesh's `nodewise_noddi.py` with identical helpers (`orient_to_centroid`, `profile_metric`) and identical output schema (Subject, Tract, Node, NDI, ODI, FWF). The only differences from Ranesh's script: subject list is derived from the NIFTI directory, tract list is ours (posterior + anterior VTA-HPC), and paths point to our IMPACT directories.

3. Run the script inside tmux:
```bash
python3 /data/projects/STUDIES/IMPACT/DTI/scripts/run_step30_noddi_extraction.py 2>&1 | tee step30_output.log
```

4. Detach from tmux while it runs:
Press Ctrl+B, then D to detach. Reconnect later with:
```bash
tmux attach -t step30
```

**Estimated runtime:** ~30-40 min for all 57 subjects × 4 tracts (slightly slower than Step 27 because we're profiling 3 metrics per tract instead of 1).

**Downloading CSVs and profile PNGs locally:**
```bash
mkdir -p ~/Desktop/SDN/DTI/data.check/step30_noddi
scp tur50045@cla19097.tu.temple.edu:/data/projects/STUDIES/IMPACT/DTI/derivatives/nodewise_noddi/csvs/*.csv \
    ~/Desktop/SDN/DTI/data.check/step30_noddi/

scp -r tur50045@cla19097.tu.temple.edu:/data/projects/STUDIES/IMPACT/DTI/derivatives/nodewise_noddi/s1000 \
    ~/Desktop/SDN/DTI/data.check/step30_noddi/
```

**Step 30 Audit — verify CSV row counts and subjects processed:**
```bash
#!/bin/bash
# Audit Step 30: NODDI extraction CSVs

csv_dir="/data/projects/STUDIES/IMPACT/DTI/derivatives/nodewise_noddi/csvs"
expected_rows=5701  # header + (57 subjects × 100 nodes)

echo "=== Step 30 Audit ==="
for f in "$csv_dir"/*.csv; do
    tract=$(basename "$f" _noddi_nodewise_all_subjects.csv)
    rows=$(wc -l < "$f")
    if [[ "$rows" -eq "$expected_rows" ]]; then
        echo "✅ $tract: $rows rows (57 subjects × 100 nodes, 3 metrics)"
    else
        subjects=$(awk -F, 'NR>1 {print $1}' "$f" | sort -u | wc -l)
        echo "⚠️  $tract: $rows rows, $subjects unique subjects"
    fi
done
```

### Step 30 Results

All 57 subjects processed successfully — **4 tracts × 57 subjects × 3 metrics = 684 profiles generated**, zero skips.

| Tract | CSV Rows | Subjects |
|-------|----------|----------|
| l_vta_l_hipp | 5,701 | 57 ✅ |
| r_vta_r_hipp | 5,701 | 57 ✅ |
| anterior_l_vta_l_hipp | 5,701 | 57 ✅ |
| anterior_r_vta_r_hipp | 5,701 | 57 ✅ |

Each row contains `NDI` (modulated), `ODI` (modulated), and `FWF` at one of 100 nodes along the tract.

**Example NODDI profiles — s1000, posterior left VTA→HPC:**

NDI (neurite density) — high near VTA (~0.78), dips in middle white matter, recovers toward HPC:

![NDI profile]({{ "/images/step30_NDI_profile_s1000_posterior_l.png" | relative_url }})

ODI (orientation dispersion) — higher near endpoints (fibers fanning out), low in deep WM (organized fibers):

![ODI profile]({{ "/images/step30_ODI_profile_s1000_posterior_l.png" | relative_url }})

FWF (free water fraction) — low in deep WM, climbs sharply near HPC endpoint (CSF/ventricle proximity):

![FWF profile]({{ "/images/step30_FWF_profile_s1000_posterior_l.png" | relative_url }})

**Anterior tract NDI (same subject) for comparison** — similar early trajectory but distinct late-tract shape:

![Anterior NDI profile]({{ "/images/step30_NDI_profile_s1000_anterior_l.png" | relative_url }})

**Step 30 Audit Result:** 4/4 CSVs at expected 5,701 rows each. 0 failures. **Ready for Step 31 (permutation testing on NODDI metrics) once the behavioral outcome variable is selected.**

---