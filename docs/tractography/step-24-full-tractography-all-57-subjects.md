---
layout: default
title: "Step 24 — Full Tractography (All 57 Subjects)"
parent: "Tractography (Steps 15–26)"
nav_order: 24
---

# Step 24 — Full Tractography (All 57 Subjects)

With the optimal FOD cutoff determined in Step 23 (0.01), we now run tractography on all 57 subjects using Ranesh's full parameters. The only change from the pilot is scaling up the streamline target and seed limit to match Ranesh's production values.

**Parameters (finalized):**

| Parameter | Value | Source |
|-----------|-------|--------|
| FOD cutoff (`-cutoff`) | 0.01 | Pilot-tested (Step 23) + Ranesh confirmation |
| Streamline target (`-select`) | 2500 | Ranesh's production value |
| Seeding attempts (`-seeds`) | 25,000,000 | Ranesh's production value |
| Min track length (`-minlength`) | 35 mm | Ranesh's value |
| Max track length (`-maxlength`) | 65 mm | Ranesh's value |
| Seed direction (`-seed_unidirectional`) | yes | Ranesh's value |
| Stop flag (`-stop`) | yes | Ranesh's value |
| Threads (`-nthreads`) | 8 | Shared cluster |
| Exclusion strategy | 1 atlas-based mask per hemisphere | Step 22 |

**Input (per subject):**
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/wm_fod_norm.mif` (normalized WM FODs from Step 19)
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/rois/left_VTA_diff.nii.gz` (seed ROI)
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/rois/left_HPC_diff.nii.gz` (target/include ROI)
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/rois/exclusion_mask_l.nii.gz` (exclusion mask from Step 22)
- (same for right hemisphere with right_ prefix and _r suffix)

**Expected Output (per subject):**
```
derivatives/CSD/s1000/tckgen/
│
├── l_vta_l_hipp/
│   └── l_vta_l_hipp_0.01.tck     # left VTA→HPC tract (2500 streamlines)
│
├── r_vta_r_hipp/
│   └── r_vta_r_hipp_0.01.tck     # right VTA→HPC tract (2500 streamlines)
```

**Running Step 24 in tmux:**

1. SSH into the cluster and create a tmux session:
```bash
ssh -XY tur50045@cla19097.tu.temple.edu
tmux new -s step24
```

2. Create the script:
```bash
nano /data/projects/STUDIES/IMPACT/DTI/scripts/run_step24_full_tractography.sh
```

3. Paste the following into nano:
```bash
#!/bin/bash
# ============================================================
# Step 24: Full Tractography — All 57 Subjects (cutoff 0.01)
# ============================================================
# Runs tckgen on all subjects with parameters determined in Step 23:
#   - cutoff 0.01 (confirmed by Ranesh + pilot testing)
#   - select 2500 streamlines (Ranesh's target)
#   - seeds 25,000,000 (Ranesh's seed limit)
#   - minlength 35mm, maxlength 65mm (Ranesh's values)
#   - Atlas-based exclusion masks from Step 22
#
# Input:  CSD/<subj>/wm_fod_norm.mif
#         CSD/<subj>/rois/{left,right}_{VTA,HPC}_diff.nii.gz
#         CSD/<subj>/rois/exclusion_mask_{l,r}.nii.gz
#
# Output: CSD/<subj>/tckgen/{l,r}_vta_{l,r}_hipp/{l,r}_vta_{l,r}_hipp_0.01.tck
# ============================================================

export PATH=/data/tools/mrtrix3/bin:$PATH

csd_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD"
nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
log_file="/data/projects/STUDIES/IMPACT/DTI/scripts/step24_full.log"

echo "=== Step 24: Full Tractography ===" > "$log_file"
echo "Started: $(date)" >> "$log_file"
echo "Parameters: cutoff=0.01, select=2500, seeds=25000000, minlength=35, maxlength=65" >> "$log_file"
echo "" >> "$log_file"

subjects=$(ls -1 "$nifti_base")
total=$(echo "$subjects" | wc -w)
count=0

for subj in $subjects; do
    count=$((count + 1))
    echo "========================================" | tee -a "$log_file"
    echo ">>> [$count/$total] $subj — $(date)" | tee -a "$log_file"
    echo "========================================" | tee -a "$log_file"

    # Verify inputs
    if [[ ! -f "$csd_base/$subj/wm_fod_norm.mif" ]]; then
        echo "!!! [$subj] MISSING wm_fod_norm.mif — skipping" | tee -a "$log_file"
        continue
    fi

    for side in l r; do
        if [ "$side" = "l" ]; then
            seed=left_VTA_diff.nii.gz
            inc=left_HPC_diff.nii.gz
            exc=exclusion_mask_l.nii.gz
            dir=l_vta_l_hipp
            label="LEFT"
        else
            seed=right_VTA_diff.nii.gz
            inc=right_HPC_diff.nii.gz
            exc=exclusion_mask_r.nii.gz
            dir=r_vta_r_hipp
            label="RIGHT"
        fi

        echo ">>> [$subj] $label VTA→HPC — $(date)" | tee -a "$log_file"
        mkdir -p "$csd_base/$subj/tckgen/$dir"

        tckgen "$csd_base/$subj/wm_fod_norm.mif" \
            "$csd_base/$subj/tckgen/$dir/${dir}_0.01.tck" \
            -seed_image "$csd_base/$subj/rois/$seed" \
            -seed_unidirectional \
            -include "$csd_base/$subj/rois/$inc" \
            -exclude "$csd_base/$subj/rois/$exc" \
            -select 2500 \
            -seeds 25000000 \
            -cutoff 0.01 \
            -minlength 35 \
            -maxlength 65 \
            -stop \
            -nthreads 8 \
            -force 2>&1 | tee -a "$log_file"

        # Log streamline count
        if [[ -f "$csd_base/$subj/tckgen/$dir/${dir}_0.01.tck" ]]; then
            count_str=$(tckinfo "$csd_base/$subj/tckgen/$dir/${dir}_0.01.tck" 2>/dev/null | grep "count:" | head -1 | awk '{print $NF}')
            seeds_used=$(tckinfo "$csd_base/$subj/tckgen/$dir/${dir}_0.01.tck" 2>/dev/null | grep "total_count:" | awk '{print $NF}')
            echo "    → $subj $label: $count_str streamlines from $seeds_used seeds" | tee -a "$log_file"
        else
            echo "    → $subj $label: tck file NOT created" | tee -a "$log_file"
        fi
    done
done

echo "" | tee -a "$log_file"
echo "========================================" | tee -a "$log_file"
echo "=== Step 24 Complete ===" | tee -a "$log_file"
echo "Finished: $(date)" | tee -a "$log_file"

# === SUMMARY ===
echo "" >> "$log_file"
echo "=== SUMMARY ===" >> "$log_file"
printf "%-8s %-15s %-12s %-12s\n" "Subject" "Hemisphere" "Streamlines" "Seeds_used" >> "$log_file"

for subj in $(ls -1 "$nifti_base"); do
    for dir in l_vta_l_hipp r_vta_r_hipp; do
        f="$csd_base/$subj/tckgen/$dir/${dir}_0.01.tck"
        if [[ -f "$f" ]]; then
            cnt=$(tckinfo "$f" 2>/dev/null | grep "count:" | head -1 | awk '{print $NF}')
            seeds=$(tckinfo "$f" 2>/dev/null | grep "total_count:" | awk '{print $NF}')
            printf "%-8s %-15s %-12s %-12s\n" "$subj" "$dir" "$cnt" "$seeds" >> "$log_file"
        else
            printf "%-8s %-15s %-12s %-12s\n" "$subj" "$dir" "MISSING" "N/A" >> "$log_file"
        fi
    done
done
echo "STEP24_ALL_DONE" >> "$log_file"
```

4. Save and exit nano:
Press Ctrl+O then Enter to save
Press Ctrl+X to close

5. Make the script runnable and execute inside tmux:
```bash
chmod +x run_step24_full_tractography.sh
./run_step24_full_tractography.sh 2>&1 | tee step24_full_output.log
```

6. Detach from tmux while it runs:
Press Ctrl+B, then D to detach. Reconnect later with:
```bash
tmux attach -t step24
```

**NOTE**: This step takes approximately **4 hours** (57 subjects × 2 hemispheres × ~2 min each). The script logs streamline counts after each run and prints a full summary table at the end.

**Step 24 Audit — verify full tractography outputs:**
```bash
#!/bin/bash
# Audit Step 24: Full tractography outputs

csd_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD"
nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
export PATH=/data/tools/mrtrix3/bin:$PATH

pass=0
fail=0

printf "%-8s %-15s %-12s %-12s\n" "Subject" "Hemisphere" "Streamlines" "Seeds_used"
printf "%-8s %-15s %-12s %-12s\n" "-------" "---------" "-----------" "----------"

for subj in $(ls -1 "$nifti_base"); do
    for dir in l_vta_l_hipp r_vta_r_hipp; do
        f="$csd_base/$subj/tckgen/$dir/${dir}_0.01.tck"
        if [[ -f "$f" ]]; then
            cnt=$(tckinfo "$f" 2>/dev/null | grep "count:" | head -1 | awk '{print $NF}')
            seeds=$(tckinfo "$f" 2>/dev/null | grep "total_count:" | awk '{print $NF}')
            printf "%-8s %-15s %-12s %-12s\n" "$subj" "$dir" "$cnt" "$seeds"
            if [[ "$cnt" -ge 2500 ]]; then
                pass=$((pass + 1))
            else
                fail=$((fail + 1))
            fi
        else
            printf "%-8s %-15s %-12s %-12s\n" "$subj" "$dir" "MISSING" "N/A"
            fail=$((fail + 1))
        fi
    done
done

echo ""
echo "=== AUDIT RESULT ==="
echo "Pass (≥2500 streamlines): $pass / $((pass + fail))"
echo "Fail: $fail / $((pass + fail))"
```

### Step 24 Results

All 57 subjects completed successfully — **114/114 runs hit 2500 streamlines**, no subjects excluded.

- **Seed usage range:** 511K (s4650 left) to 2.03M (s35 right) — all well under the 25M seed cap
- **Average seeds used:** ~1.1M (~4.4% of the 25M limit)
- **Total tck files:** 114 (57 subjects × 2 hemispheres)

The cutoff 0.01 + atlas-based exclusion mask combination proved highly efficient at 3T, consistent with Ranesh's experience at 7T. No subject came close to exhausting the seed budget.

**Step 24 Audit Result:** 114/114 pass (all ≥ 2500 streamlines). 0 failures.

> **Anterior VTA→HPC tract:** The same tractography was later repeated for the anterior VTA→HPC atlas that Ranesh provided after we completed the posterior pipeline. Same parameters, same script (adapted for anterior atlas files), all 114 runs hit 2500 streamlines. See [Anterior Tract Addendum](#anterior-vtahpc-tract-addendum) for full details.

---

