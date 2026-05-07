---
layout: default
title: "Step 25 — Tract Cleaning (pyAFQ Mahalanobis Distance)"
parent: "Tractography (Steps 15–26)"
nav_order: 25
---

# Step 25 — Tract Cleaning (pyAFQ Mahalanobis Distance)

After tractography, we clean each tract bundle using pyAFQ's `clean_bundle` function, which removes anatomically implausible streamlines using Mahalanobis distance. This is a standard post-tractography step — even with the atlas-based exclusion mask constraining tracking (Step 22), some streamlines will take unusual paths through the corridor. Mahalanobis cleaning identifies and removes these outliers by comparing each streamline's shape to the bundle's average shape across multiple iterations.

Ranesh used this exact approach on his HCP 7T data and provided the specific parameters. He noted that with the atlas mask keeping tracts clean at cutoff 0.01, the cleaning step may not need to remove many streamlines — but we run it as a safeguard to ensure the cleanest possible bundles for FA extraction.

**Dependencies (installed on cluster):**

pyAFQ and dipy are required for this step. They were installed via:
```bash
pip3 install --user pyAFQ dipy
```
Note: The cluster's system `zipp` package (1.0.0) was too old for pyAFQ — `pip3 install --user --upgrade zipp` resolved the version conflict.

**Cleaning parameters (from Ranesh):**

| Parameter | Value | Description |
|-----------|-------|-------------|
| `n_points` | 100 | Resample each streamline to 100 equidistant nodes before comparison |
| `clean_rounds` | 5 | Number of iterative cleaning passes |
| `distance_threshold` | 3 | Remove streamlines > 3 SD from bundle centroid (Mahalanobis distance) |
| `length_threshold` | 2 | Remove streamlines > 2 SD from mean tract length |
| `stat` | 'mean' | Use mean (not median) for centroid calculation |
| `return_idx` | True | Return indices of retained streamlines |

**Input (per subject — from Step 24):**
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/tckgen/l_vta_l_hipp/l_vta_l_hipp_0.01.tck` (uncleaned left tract)
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/tckgen/r_vta_r_hipp/r_vta_r_hipp_0.01.tck` (uncleaned right tract)
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/qc/mean_b0.nii.gz` (reference image for tractogram loading)

**Expected Output (per subject):**
```
derivatives/CSD/s1000/tckgen/
│
├── l_vta_l_hipp/
│   ├── l_vta_l_hipp_0.01.tck            # uncleaned (2500 streamlines)
│   └── l_vta_l_hipp_0.01_cleaned.tck    # cleaned (typically 700–1400 streamlines)
│
├── r_vta_r_hipp/
│   ├── r_vta_r_hipp_0.01.tck            # uncleaned (2500 streamlines)
│   └── r_vta_r_hipp_0.01_cleaned.tck    # cleaned (typically 700–1400 streamlines)
```

**Running Step 25 in tmux:**

1. SSH into the cluster and create a tmux session:
```bash
ssh -XY tur50045@cla19097.tu.temple.edu
tmux new -s step25
```

2. Create the script:
```bash
nano /data/projects/STUDIES/IMPACT/DTI/scripts/run_step25_cleaning.py
```

3. Paste the following into nano:
```python
#!/usr/bin/env python3
# ============================================================
# Step 25: Clean tracts using pyAFQ
# ============================================================
# Adapted from Ranesh's cleaning script
# (hcp_afq_tract_cleaning_hipp_accumbens.txt)
#
# Parameters (from Ranesh):
#   n_points = 100
#   clean_rounds = 5
#   distance_threshold = 3 (Mahalanobis SD)
#   length_threshold = 2 (SD from mean length)
#   stat = 'mean'
#   return_idx = True
#
# Input:  CSD/<subj>/tckgen/{l,r}_vta_{l,r}_hipp/{l,r}_vta_{l,r}_hipp_0.01.tck
# Output: CSD/<subj>/tckgen/{l,r}_vta_{l,r}_hipp/{l,r}_vta_{l,r}_hipp_0.01_cleaned.tck
# ============================================================

import os
import sys
from pathlib import Path

from AFQ.recognition.cleaning import clean_bundle
from dipy.io.streamline import load_tractogram, save_tractogram

# Paths
csd_base = Path("/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD")
nifti_base = Path("/data/projects/STUDIES/IMPACT/DTI/NIFTI")
log_file = Path("/data/projects/STUDIES/IMPACT/DTI/scripts/step25_cleaning.log")

# pyAFQ cleaning parameters (from Ranesh)
n_points = 100
clean_rounds = 5
distance_threshold = 3      # 3 SD Mahalanobis distance
length_threshold = 2         # 2 SD from mean length
cutoff = "0.01"

# Get subject list
subjects = sorted([d.name for d in nifti_base.iterdir() if d.is_dir()])
hemis = ["l_vta_l_hipp", "r_vta_r_hipp"]

with open(log_file, 'w') as log:
    log.write("=== Step 25: pyAFQ Tract Cleaning ===\n")
    log.write(f"Parameters: n_points={n_points}, clean_rounds={clean_rounds}, "
              f"distance_threshold={distance_threshold}, length_threshold={length_threshold}\n")
    log.write(f"Cutoff: {cutoff}\n")
    log.write(f"Subjects: {len(subjects)}\n\n")

    total = len(subjects) * len(hemis)
    count = 0
    results = []

    for subj in subjects:
        for hemi in hemis:
            count += 1
            in_tck = csd_base / subj / "tckgen" / hemi / f"{hemi}_{cutoff}.tck"
            out_tck = csd_base / subj / "tckgen" / hemi / f"{hemi}_{cutoff}_cleaned.tck"

            # Reference image for tractogram loading
            ref_img = csd_base / subj / "qc" / "mean_b0.nii.gz"
            if not ref_img.exists():
                ref_img = Path(f"/data/projects/STUDIES/IMPACT/DTI/derivatives/"
                               f"BEDPOSTX/{subj}/bedpostx_input/data.nii.gz")

            msg = f"[{count}/{total}] {subj} {hemi}"

            if not in_tck.exists():
                msg += " — SKIP: missing input tck"
                print(msg)
                log.write(msg + "\n")
                results.append((subj, hemi, "MISSING", "N/A", "N/A"))
                continue

            if not ref_img.exists():
                msg += " — SKIP: missing reference image"
                print(msg)
                log.write(msg + "\n")
                results.append((subj, hemi, "NO_REF", "N/A", "N/A"))
                continue

            try:
                sft = load_tractogram(str(in_tck), str(ref_img),
                                      bbox_valid_check=False)
                n_before = len(sft.streamlines)

                if n_before == 0:
                    msg += " — SKIP: 0 streamlines"
                    print(msg)
                    log.write(msg + "\n")
                    results.append((subj, hemi, 0, 0, "0%"))
                    continue

                cleaned_sft, idx = clean_bundle(
                    sft,
                    n_points=n_points,
                    clean_rounds=clean_rounds,
                    distance_threshold=distance_threshold,
                    length_threshold=length_threshold,
                    stat='mean',
                    return_idx=True
                )

                n_after = len(cleaned_sft.streamlines)
                pct = f"{n_after/n_before*100:.1f}%"
                msg += f" — {n_before} → {n_after} ({pct} retained)"
                print(msg)
                log.write(msg + "\n")
                results.append((subj, hemi, n_before, n_after, pct))

                save_tractogram(cleaned_sft, str(out_tck),
                                bbox_valid_check=False)

            except Exception as e:
                msg += f" — ERROR: {str(e)}"
                print(msg)
                log.write(msg + "\n")
                results.append((subj, hemi, "ERROR", str(e), "N/A"))

    # Summary
    log.write("\n=== SUMMARY ===\n")
    log.write(f"{'Subject':<12} {'Hemisphere':<16} {'Before':<10} "
              f"{'After':<10} {'Retained':<10}\n")
    log.write("-" * 58 + "\n")
    for subj, hemi, before, after, pct in results:
        log.write(f"{subj:<12} {hemi:<16} {str(before):<10} "
                  f"{str(after):<10} {str(pct):<10}\n")

    log.write("\nSTEP25_ALL_DONE\n")

print("\n=== Step 25 Complete ===")
```

4. Save and exit nano:
Press Ctrl+O then Enter to save
Press Ctrl+X to close

5. Run the script inside tmux:
```bash
python3 /data/projects/STUDIES/IMPACT/DTI/scripts/run_step25_cleaning.py 2>&1 | tee step25_output.log
```

6. Detach from tmux while it runs:
Press Ctrl+B, then D to detach. Reconnect later with:
```bash
tmux attach -t step25
```
* Note: All output from this script is recorded in step25_cleaning.log.

**Step 25 Audit — verify cleaned tract outputs:**
```bash
#!/bin/bash
# Audit Step 25: Cleaned tract outputs

csd_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD"
nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
export PATH=/data/tools/mrtrix3/bin:$PATH

pass=0
fail=0

printf "%-12s %-15s %-12s %-12s %-10s\n" "Subject" "Hemisphere" "Uncleaned" "Cleaned" "Retained"
printf "%-12s %-15s %-12s %-12s %-10s\n" "-------" "---------" "---------" "-------" "--------"

for subj in $(ls -1 "$nifti_base"); do
    for dir in l_vta_l_hipp r_vta_r_hipp; do
        raw="$csd_base/$subj/tckgen/$dir/${dir}_0.01.tck"
        cleaned="$csd_base/$subj/tckgen/$dir/${dir}_0.01_cleaned.tck"
        if [[ -f "$cleaned" ]]; then
            cnt_raw=$(tckinfo "$raw" 2>/dev/null | grep "count:" | head -1 | awk '{print $NF}')
            cnt_clean=$(tckinfo "$cleaned" 2>/dev/null | grep "count:" | head -1 | awk '{print $NF}')
            if [[ "$cnt_clean" -gt 0 ]]; then
                pct=$(echo "scale=1; $cnt_clean * 100 / $cnt_raw" | bc)
                printf "%-12s %-15s %-12s %-12s %-10s\n" "$subj" "$dir" "$cnt_raw" "$cnt_clean" "${pct}%"
                pass=$((pass + 1))
            else
                printf "%-12s %-15s %-12s %-12s %-10s\n" "$subj" "$dir" "$cnt_raw" "0" "FAIL"
                fail=$((fail + 1))
            fi
        else
            printf "%-12s %-15s %-12s %-12s %-10s\n" "$subj" "$dir" "N/A" "MISSING" "N/A"
            fail=$((fail + 1))
        fi
    done
done

echo ""
echo "=== AUDIT RESULT ==="
echo "Pass (cleaned file exists, >0 streamlines): $pass / $((pass + fail))"
echo "Fail: $fail / $((pass + fail))"
```

### Step 25 Results

All 57 subjects completed successfully — **114/114 tracts cleaned**, no subjects excluded.

- **Retention range:** 26.4% (s0105-pilot right, 659 streamlines) to 57.5% (s35 right, 1437 streamlines)
- **Average retention:** ~39%
- **Lowest cleaned streamline count:** 659 (s0105-pilot right) — still ample for FA extraction
- **No tracts with 0 streamlines** — every bundle survived cleaning

The ~39% retention rate is typical for Mahalanobis-distance cleaning with these parameters (3 SD distance, 2 SD length, 5 rounds). The atlas-based exclusion mask (Step 22) kept the raw tracts clean enough that even after aggressive cleaning, every subject retains hundreds of streamlines.

**Step 25 Audit Result:** 114/114 pass (all cleaned files exist, all > 0 streamlines). 0 failures.

> **Anterior VTA→HPC tract:** pyAFQ cleaning was also run on the 114 anterior tracts with identical parameters. All 114 cleaned successfully. See [Anterior Tract Addendum](#anterior-vtahpc-tract-addendum).

### Visual QC — Did Cleaning Fix the 0.01 "Messiness"?

In Step 23, we noted that the 0.01 cutoff produced slightly thicker tract density images compared to the conservative 0.06 cutoff. After pyAFQ Mahalanobis cleaning, we compared all three versions side by side to verify that cleaning tightened the bundles:

**Example 3-way comparison — s169, left VTA→HPC:**

![3-way comparison]({{ "/images/cleaned_compare_s169_l.png" | relative_url }})

Left: 0.06 conservative (1000 streamlines). Middle: 0.01 uncleaned (2500 streamlines). Right: 0.01 cleaned (~824 streamlines). The cleaned 0.01 tract is visibly more focused than both the uncleaned 0.01 and even the conservative 0.06.

**Tract length variability (std dev) across all 5 test subjects:**

![Cleaned stats comparison]({{ "/images/cleaned_stats_comparison.png" | relative_url }})

The green bars (0.01 cleaned) are consistently the lowest — meaning the tightest, most consistent bundles. The cleaning removed outlier streamlines that were making 0.01 appear messier, producing bundles with ~3.5-4.5mm std dev compared to ~5-7mm for both uncleaned options.

**Summary:** The 0.01 cutoff + pyAFQ cleaning produces tracts that are more efficient to generate AND tighter than the conservative 0.06 cutoff alone. This validates Ranesh's recommendation to use a permissive cutoff with the atlas-based exclusion mask and rely on Mahalanobis cleaning to refine the bundles.

---

