---
layout: default
title: "Step 27 — Node-wise FA Extraction (AFQ-style Tract Profiling)"
parent: "Analysis (Steps 27–31)"
nav_order: 27
---

# Step 27 — Node-wise FA Extraction (AFQ-style Tract Profiling)

With the cleaned tracts from Step 25 and the DTIFIT FA maps from Step 11, we extract FA along each tract at 100 equidistant nodes using AFQ-style tract profiling. This produces a subject-by-node matrix of FA values that feeds into the node-wise statistical analysis (Step 28).

**Adapted from Ranesh's `nodewise_noddi.py` script**, with identical profiling machinery (QuickBundles orientation, resampling, Gaussian-weighted AFQ profiling). The only change: instead of extracting NDI/ODI/FWF from NODDI maps, we extract FA from the DTIFIT output. This matches Ranesh's exact approach but applied to FA first; Step 30 will do the same for NODDI metrics.

**Why 100 nodes:** Matches Ranesh's pipeline exactly. Nodes near the seed (0-4) and target (95-99) are typically excluded from final analyses due to partial-volume contamination from gray matter (VTA, hippocampus). Deep white matter sits around nodes 25-75.

**Why Gaussian-weighted AFQ profiling:** At each node, instead of taking the FA value at a single centroid voxel, `dipy.stats.analysis.afq_profile` weights each streamline by its Mahalanobis distance from the bundle centroid, then computes a weighted mean of FA across streamlines at that node. This reduces the influence of outlier streamlines and produces smoother, more reliable profiles.

**Why streamline orientation matters:** Raw streamlines may run in either direction (VTA→HPC or HPC→VTA). Before profiling, we use `dipy.tracking.streamline.orient_by_streamline` with a QuickBundles centroid as reference, ensuring all 100 nodes index the same anatomical location across streamlines and subjects.

**Input (per subject, per tract):**
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/tckgen/<tract>/<tract>_0.01_cleaned.tck` (from Step 25)
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/DTIFIT_OUTPUT/<subj>/DTI_FA.nii.gz` (from Step 11)

**Expected Output (per tract):**
```
derivatives/nodewise_fa/
│
├── csvs/
│   ├── l_vta_l_hipp_fa_nodewise_all_subjects.csv         # posterior left
│   ├── r_vta_r_hipp_fa_nodewise_all_subjects.csv         # posterior right
│   ├── anterior_l_vta_l_hipp_fa_nodewise_all_subjects.csv # anterior left
│   └── anterior_r_vta_r_hipp_fa_nodewise_all_subjects.csv # anterior right
│
└── <subj>/<tract>/<tract>_FA_profile.png  # per-subject per-tract profile plot
```

Each CSV has 5,701 rows (header + 57 subjects × 100 nodes) with columns: `Subject, Tract, Node, FA`.

**Parameters (match Ranesh's NODDI script exactly):**

| Parameter | Value | Description |
|-----------|-------|-------------|
| `num_nodes` | 100 | Nodes per streamline after resampling |
| `min_streamlines` | 5 | Minimum streamlines required to process a subject |
| `bbox_valid_check` | False | Allow streamlines outside image bounding box (matches Ranesh) |

**Running Step 27 in tmux:**

1. SSH into the cluster and create a tmux session:
```bash
ssh -XY tur50045@cla19097.tu.temple.edu
tmux new -s step27
```

2. Create the script:
```bash
nano /data/projects/STUDIES/IMPACT/DTI/scripts/run_step27_fa_extraction.py
```

3. Paste the following into nano:
```python
#!/usr/bin/env python3
# ============================================================
# Step 27: Node-wise FA Extraction (AFQ-style tract profiling)
# ============================================================
# Adapted from Ranesh's nodewise_noddi.py — exact same profiling
# machinery (QuickBundles orientation + AFQ Gaussian-weighted
# profile), just applied to FA maps from DTIFIT instead of
# NODDI metrics. Processes both posterior and anterior tracts.
# ============================================================

from pathlib import Path
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import dipy.stats.analysis as dsa
import dipy.tracking.streamline as dts
from dipy.io.streamline import load_tractogram
from dipy.io.image import load_nifti
from dipy.segment.clustering import QuickBundles
from dipy.segment.metricspeed import AveragePointwiseEuclideanMetric
from dipy.segment.featurespeed import ResampleFeature

# Tracts: both posterior and anterior VTA-HPC (both hemispheres)
tracts = [
    "l_vta_l_hipp",
    "r_vta_r_hipp",
    "anterior_l_vta_l_hipp",
    "anterior_r_vta_r_hipp",
]

# Paths
csd_root = Path("/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD")
dtifit_root = Path("/data/projects/STUDIES/IMPACT/DTI/derivatives/DTIFIT_OUTPUT")
nifti_root = Path("/data/projects/STUDIES/IMPACT/DTI/NIFTI")

nodewise = Path("/data/projects/STUDIES/IMPACT/DTI/derivatives/nodewise_fa")
nodewise.mkdir(parents=True, exist_ok=True)
csv_dir = nodewise / "csvs"
csv_dir.mkdir(parents=True, exist_ok=True)

# Profile parameters (match Ranesh's NODDI script)
num_nodes = 100
min_streamlines = 5

subjects = sorted([d.name for d in nifti_root.iterdir() if d.is_dir()])


# =========================
# HELPERS (verbatim from Ranesh)
# =========================

def orient_to_centroid(streamlines, nb_points=num_nodes):
    """Orient all streamlines to match the bundle centroid direction."""
    feat = ResampleFeature(nb_points=nb_points)
    metric = AveragePointwiseEuclideanMetric(feat)
    qb = QuickBundles(threshold=np.inf, metric=metric)
    centroid = qb.cluster(streamlines).centroids[0]
    oriented = dts.orient_by_streamline(streamlines, centroid)
    return dts.Streamlines(oriented)


def profile_metric(img_path, streamlines, nb_points=num_nodes):
    """AFQ-style Gaussian-weighted profile at nb_points nodes."""
    data, aff = load_nifti(str(img_path))
    weights = dsa.gaussian_weights(streamlines)
    prof = dsa.afq_profile(data, streamlines, aff, nb_points=nb_points, weights=weights)
    return np.asarray(prof, dtype=float)


# =========================
# MAIN
# =========================

print(f"=== Step 27: Node-wise FA Extraction ===")
print(f"Subjects: {len(subjects)}")
print(f"Tracts: {len(tracts)}")

for tract in tracts:
    print(f"\n{'='*80}\nProcessing tract: {tract}\n{'='*80}")

    csv_path = csv_dir / f"{tract}_fa_nodewise_all_subjects.csv"

    with open(csv_path, "w", newline="") as fcsv:
        w = csv.writer(fcsv)
        w.writerow(["Subject", "Tract", "Node", "FA"])

        for s in subjects:
            try:
                in_tck = csd_root / s / "tckgen" / tract / f"{tract}_0.01_cleaned.tck"
                f_fa = dtifit_root / s / "DTI_FA.nii.gz"

                if not in_tck.exists():
                    print(f"[{s}] [{tract}] SKIP: missing cleaned tract")
                    continue
                if not f_fa.exists():
                    print(f"[{s}] [{tract}] SKIP: missing FA map")
                    continue

                out_png_dir = nodewise / s / tract
                out_png_dir.mkdir(parents=True, exist_ok=True)

                tg = load_tractogram(str(in_tck), str(f_fa), bbox_valid_check=False)
                sl = tg.streamlines

                if len(sl) < min_streamlines:
                    print(f"[{s}] [{tract}] SKIP: only {len(sl)} streamlines")
                    continue

                sl_oriented = orient_to_centroid(sl, nb_points=num_nodes)
                fa = profile_metric(f_fa, sl_oriented, nb_points=num_nodes)

                for node in range(num_nodes):
                    w.writerow([s, tract, node, float(fa[node])])

                plt.figure()
                plt.plot(fa)
                plt.ylabel("FA")
                plt.xlabel(f"Node along {tract}")
                plt.title(f"{s} • {tract} • FA")
                plt.tight_layout()
                plt.savefig(out_png_dir / f"{tract}_FA_profile.png", dpi=150)
                plt.close()

                print(f"[{s}] [{tract}] wrote 100 rows to CSV and PNG")

            except Exception as e:
                print(f"[{s}] [{tract}] SKIP due to error: {e}")

print(f"\nALL DONE.\nCSV directory: {csv_dir}")
print("STEP27_ALL_DONE")
```

4. Save and exit nano:
Press Ctrl+O then Enter to save
Press Ctrl+X to close

5. Run the script inside tmux:
```bash
python3 /data/projects/STUDIES/IMPACT/DTI/scripts/run_step27_fa_extraction.py 2>&1 | tee step27_output.log
```

6. Detach from tmux while it runs:
Press Ctrl+B, then D to detach. Reconnect later with:
```bash
tmux attach -t step27
```

**Estimated runtime:** ~20-25 min for all 57 subjects × 4 tracts (the QuickBundles orientation step on 800–1,400 streamlines per tract is the main cost).

**Downloading CSVs and profile PNGs locally:**
```bash
mkdir -p ~/Desktop/SDN/DTI/data.check/step27_fa
scp tur50045@cla19097.tu.temple.edu:/data/projects/STUDIES/IMPACT/DTI/derivatives/nodewise_fa/csvs/*.csv \
    ~/Desktop/SDN/DTI/data.check/step27_fa/

# Download all subject-tract profile PNGs for a subject
scp -r tur50045@cla19097.tu.temple.edu:/data/projects/STUDIES/IMPACT/DTI/derivatives/nodewise_fa/s1000 \
    ~/Desktop/SDN/DTI/data.check/step27_fa/
```

**Step 27 Audit — verify CSV row counts and subjects processed:**
```bash
#!/bin/bash
# Audit Step 27: FA extraction CSVs

csv_dir="/data/projects/STUDIES/IMPACT/DTI/derivatives/nodewise_fa/csvs"
expected_rows=5701  # header + (57 subjects × 100 nodes)

echo "=== Step 27 Audit ==="
for f in "$csv_dir"/*.csv; do
    tract=$(basename "$f" _fa_nodewise_all_subjects.csv)
    rows=$(wc -l < "$f")
    if [[ "$rows" -eq "$expected_rows" ]]; then
        echo "✅ $tract: $rows rows (57 subjects × 100 nodes)"
    else
        subjects=$(awk -F, 'NR>1 {print $1}' "$f" | sort -u | wc -l)
        echo "⚠️  $tract: $rows rows, $subjects unique subjects"
    fi
done
```

### Step 27 Results

All 57 subjects processed successfully — **4/4 tracts × 57 subjects = 228 FA profiles generated**, zero skips.

| Tract | CSV Rows | Subjects |
|-------|----------|----------|
| l_vta_l_hipp | 5,701 | 57 ✅ |
| r_vta_r_hipp | 5,701 | 57 ✅ |
| anterior_l_vta_l_hipp | 5,701 | 57 ✅ |
| anterior_r_vta_r_hipp | 5,701 | 57 ✅ |

**FA profiles show anatomically sensible patterns:**

Posterior VTA→HPC, left hemisphere (s1000) — peaks in deep white matter (~0.53), drops toward HPC endpoint (0.29 at node 99):

![FA profile posterior L s1000]({{ "/images/step27_fa_profile_s1000_posterior_l.png" | relative_url }})

Anterior VTA→HPC, left hemisphere (s1000) — similar early trajectory, different late-tract shape (gradual decline toward HPC instead of a secondary peak):

![FA profile anterior L s1000]({{ "/images/step27_fa_profile_s1000_anterior_l.png" | relative_url }})

Posterior VTA→HPC, left hemisphere (s169) — different subject, similar overall shape with individual variation:

![FA profile posterior L s169]({{ "/images/step27_fa_profile_s169_posterior_l.png" | relative_url }})

**Step 27 Audit Result:** 4/4 CSVs at expected 5,701 rows each. 0 failures. **Ready for Step 28 (permutation testing) once the behavioral outcome variable is selected.**

---

