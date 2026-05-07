---
layout: default
title: "Step 26 — Visual QC of Cleaned Tracts (All 57 Subjects)"
parent: "Tractography (Steps 15–26)"
nav_order: 26
---

# Step 26 — Visual QC of Cleaned Tracts (All 57 Subjects)

Ranesh emphasized that visual QC is mandatory after both tractography and cleaning. In this step, we generate tract density images (TDIs) for every cleaned tract across all 57 subjects and both hemispheres, overlay them on each subject's mean b0, and inspect for anatomical plausibility.

**What we're looking for:**
- The VTA→HPC arc — a curved bundle running from the ventral midbrain laterally into the medial temporal lobe
- Consistent shape across subjects (some size variation is expected)
- No stray blobs or tracts running to wrong brain regions
- No empty/missing tracts

**What would be a red flag:**
- Tract density in completely wrong location (e.g., frontal lobe, contralateral hemisphere)
- Very sparse TDI with only a few scattered voxels (< 50 voxels)
- Extremely diffuse spread with no clear core bundle (> 5000 voxels)

**Input (per subject — from Step 25):**
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/tckgen/l_vta_l_hipp/l_vta_l_hipp_0.01_cleaned.tck`
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/tckgen/r_vta_r_hipp/r_vta_r_hipp_0.01_cleaned.tck`
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/qc/mean_b0.nii.gz` (background image)

**Expected Output:**
```
derivatives/CSD/qc_step26/
│
├── s1000_l_vta_l_hipp_qc.png     # left tract QC image (axial + coronal)
├── s1000_r_vta_r_hipp_qc.png     # right tract QC image
├── ...                            # (114 images total: 57 subjects × 2 hemispheres)
├── step26_qc.log                  # log with voxel counts and flag status
```

**Running Step 26 in tmux:**

1. SSH into the cluster and create a tmux session:
```bash
ssh -XY tur50045@cla19097.tu.temple.edu
tmux new -s step26
```

2. Create the script:
```bash
nano /data/projects/STUDIES/IMPACT/DTI/scripts/run_step26_qc.py
```

3. Paste the following into nano:
```python
#!/usr/bin/env python3
# ============================================================
# Step 26: Visual QC — Cleaned Tract TDIs for All 57 Subjects
# ============================================================
# Generates tract density images (TDIs) for cleaned tracts
# and overlays them on mean b0 for visual inspection.
# Automated flags: LOW_VOXELS (<50), HIGH_VOXELS (>5000),
#                  LOW_DENSITY (max<5)
# ============================================================

import os
import nibabel as nib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

csd = Path("/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD")
nifti = Path("/data/projects/STUDIES/IMPACT/DTI/NIFTI")
out = Path("/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/qc_step26")
out.mkdir(exist_ok=True)

subjects = sorted([d.name for d in nifti.iterdir() if d.is_dir()])
hemis = [("l_vta_l_hipp", "Left VTA→HPC"),
         ("r_vta_r_hipp", "Right VTA→HPC")]
cutoff = "0.01"

os.environ["PATH"] = "/data/tools/mrtrix3/bin:" + os.environ.get("PATH", "")

log = open(out / "step26_qc.log", "w")
log.write("=== Step 26: Visual QC of Cleaned Tracts ===\n\n")

flags = []
total = len(subjects) * len(hemis)
count = 0

for subj in subjects:
    b0_f = csd / subj / "qc" / "mean_b0.nii.gz"
    if not b0_f.exists():
        log.write(f"[{subj}] SKIP: no mean_b0\n")
        continue

    bg = nib.load(str(b0_f)).get_fdata()

    for hemi_dir, hemi_label in hemis:
        count += 1
        cleaned = (csd / subj / "tckgen" / hemi_dir
                   / f"{hemi_dir}_{cutoff}_cleaned.tck")
        tdi_f = out / f"{subj}_{hemi_dir}_tdi.nii.gz"

        if not cleaned.exists():
            msg = f"[{count}/{total}] {subj} {hemi_dir} — MISSING"
            print(msg)
            log.write(msg + "\n")
            flags.append((subj, hemi_dir, "MISSING"))
            continue

        # Generate TDI via tckmap
        template = csd / subj / "rois" / "left_VTA_diff.nii.gz"
        os.system(f"tckmap {cleaned} {tdi_f} "
                  f"-template {template} -force 2>/dev/null")

        if not tdi_f.exists():
            msg = f"[{count}/{total}] {subj} {hemi_dir} — tckmap FAILED"
            print(msg)
            log.write(msg + "\n")
            flags.append((subj, hemi_dir, "TCKMAP_FAIL"))
            continue

        tdi = nib.load(str(tdi_f)).get_fdata()
        n_voxels = int(np.sum(tdi > 0))
        max_density = float(np.max(tdi))

        # Find best slices
        best_ax = int(np.argmax(tdi.sum(axis=(0, 1))))
        best_cor = int(np.argmax(tdi.sum(axis=(0, 2))))

        # Automated flag checks
        flag = None
        if n_voxels < 50:
            flag = f"LOW_VOXELS ({n_voxels})"
        elif n_voxels > 5000:
            flag = f"HIGH_VOXELS ({n_voxels})"
        elif max_density < 5:
            flag = f"LOW_DENSITY (max={max_density:.0f})"

        if flag:
            flags.append((subj, hemi_dir, flag))

        status = f"FLAG: {flag}" if flag else "OK"
        msg = (f"[{count}/{total}] {subj} {hemi_dir} — "
               f"{status} (voxels={n_voxels}, "
               f"max_density={max_density:.0f})")
        print(msg)
        log.write(msg + "\n")

        # Generate QC image
        fig, axes = plt.subplots(1, 2, figsize=(10, 5))
        fig.suptitle(f'{subj} — {hemi_label} (cleaned)',
                     fontsize=13, fontweight='bold')

        for j, (sl, title) in enumerate([
            (bg[:, :, best_ax], 'Axial'),
            (bg[:, best_cor, :], 'Coronal')
        ]):
            ax = axes[j]
            ax.imshow(np.rot90(sl), cmap='gray')
            tdi_sl = (tdi[:, :, best_ax] if j == 0
                      else tdi[:, best_cor, :])
            mask = tdi_sl > 0
            overlay = np.ma.masked_where(~mask, tdi_sl)
            ax.imshow(np.rot90(overlay), cmap='hot', alpha=0.7)
            ax.set_title(title, fontsize=11)
            ax.axis('off')

        if flag:
            fig.text(0.5, 0.01, f"FLAG: {flag}",
                     ha='center', fontsize=11,
                     color='red', fontweight='bold')

        plt.tight_layout()
        plt.savefig(str(out / f"{subj}_{hemi_dir}_qc.png"),
                    dpi=100, bbox_inches='tight')
        plt.close()

        os.remove(str(tdi_f))

log.write("\n=== FLAGGED SUBJECTS ===\n")
if flags:
    for subj, hemi, reason in flags:
        log.write(f"  {subj} {hemi}: {reason}\n")
else:
    log.write("  None — all subjects pass\n")

log.write(f"\nTotal: {count}/{total}\n")
log.write(f"Flagged: {len(flags)}\n")
log.write("STEP26_ALL_DONE\n")
log.close()

print(f"\n=== Step 26 Complete ===")
print(f"Flagged: {len(flags)}")
print("STEP26_ALL_DONE")
```

4. Save and exit nano:
Press Ctrl+O then Enter to save
Press Ctrl+X to close

5. Run the script inside tmux:
```bash
python3 /data/projects/STUDIES/IMPACT/DTI/scripts/run_step26_qc.py 2>&1 | tee step26_output.log
```

6. Detach from tmux while it runs:
Press Ctrl+B, then D to detach. Reconnect later with:
```bash
tmux attach -t step26
```

**Downloading QC images to local machine for review:**
```bash
# Download all 114 QC images
mkdir -p ~/Desktop/SDN/DTI/data.check/step26_qc
scp tur50045@cla19097.tu.temple.edu:/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/qc_step26/*_qc.png \
    ~/Desktop/SDN/DTI/data.check/step26_qc/
```

**Interactive review in FSLeyes (recommended for any flagged subjects):**

The TDI overlay PNGs provide a quick batch overview, but for detailed inspection you should load the cleaned tracts directly in FSLeyes. On the cluster via Citrix (or any machine with FSLeyes installed):

```bash
# Load a subject's cleaned tract overlaid on their mean b0
# Replace s1000 with any subject ID and l/r for hemisphere

export FSLDIR=/usr/local/fsl
source $FSLDIR/etc/fslconf/fsl.sh

fsleyes /data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/s1000/qc/mean_b0.nii.gz \
    /data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/s1000/tckgen/l_vta_l_hipp/l_vta_l_hipp_0.01_cleaned.tck \
    -cm hot -a 70 &
```

If FSLeyes is not available, you can use MRtrix's mrview:
```bash
export PATH=/data/tools/mrtrix3/bin:$PATH

mrview /data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/s1000/qc/mean_b0.nii.gz \
    -tractography.load /data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/s1000/tckgen/l_vta_l_hipp/l_vta_l_hipp_0.01_cleaned.tck &
```

In FSLeyes/mrview you can scroll through slices, zoom in, toggle the overlay on/off, and adjust opacity — things the static PNGs can't do.

**Step 26 Audit — verify QC images generated for all subjects:**
```bash
#!/bin/bash
# Audit Step 26: QC image outputs

qc_dir="/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/qc_step26"
nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"

pass=0
fail=0

for subj in $(ls -1 "$nifti_base"); do
    for dir in l_vta_l_hipp r_vta_r_hipp; do
        f="$qc_dir/${subj}_${dir}_qc.png"
        if [[ -f "$f" ]]; then
            pass=$((pass + 1))
        else
            echo "MISSING: $subj $dir"
            fail=$((fail + 1))
        fi
    done
done

echo ""
echo "=== AUDIT RESULT ==="
echo "Pass: $pass / $((pass + fail))"
echo "Fail: $fail / $((pass + fail))"

# Check for any flags
echo ""
echo "=== FLAGGED SUBJECTS ==="
grep "FLAG" "$qc_dir/step26_qc.log" 2>/dev/null || echo "None"
```

### Step 26 Results

All 57 subjects completed — **114/114 QC images generated, 0 flagged.**

Every cleaned tract shows the expected VTA→HPC arc from the ventral midbrain into the medial temporal lobe. No stray blobs, no missing tracts, no sparse bundles.

**Example QC — s169, left VTA→HPC (cleaned):**

![Step 26 QC s169]({{ "/images/step26_qc_s169_left.png" | relative_url }})

**Example QC — s0105-pilot, left VTA→HPC (lowest cleaning retention at 26.4%):**

![Step 26 QC s0105]({{ "/images/step26_qc_s0105_left.png" | relative_url }})

Even the subject with the most aggressive cleaning (s0105-pilot, 659 streamlines retained from 2500) still shows a clear, well-defined tract.

**Subjects of note:**
- **s1694, s4531** (flagged as borderline registration in Step 21): Both pass — tracts are anatomically correct
- **s0105-pilot** (lowest retention at 26.4%): Clean tract, just smaller
- **s35** (highest retention at 57.5%): Broader but still well-defined

**Step 26 Audit Result:** 114/114 pass (all QC images generated, 0 flags). 0 failures.

> **Anterior VTA→HPC tract:** Full visual QC was also run on the 114 cleaned anterior tracts (same TDI overlay approach). All 114 passed. See [Anterior Tract Addendum](#anterior-vtahpc-tract-addendum) for example images and details.

---

