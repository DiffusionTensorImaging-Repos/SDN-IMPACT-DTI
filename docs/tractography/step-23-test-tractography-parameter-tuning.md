---
layout: default
title: "Step 23 — Test Tractography (Parameter Tuning)"
parent: "Tractography (Steps 15–26)"
nav_order: 23
---

# Step 23 — Test Tractography (Parameter Tuning)

Before running tractography on all 57 subjects, we test on 5 subjects with multiple FOD cutoff values to find optimal parameters for our 3T IMPACT data. Ranesh's pipeline was optimized for 7T HCP data — the key difference is that lower magnetic field strength produces noisier FOD estimates, so the FOD amplitude cutoff (which determines when tracking stops) may need to be higher at 3T to avoid following noise.

Ranesh's exact advice: "Start at 0.1, try 0.08, maybe 0.06. At 3T, 0.08 might work." He also noted that minlength/maxlength (35-65mm at 7T) may need adjustment at 3T.

**Ranesh's 7T parameters vs. our 3T test values:**

| Parameter | Ranesh (HCP 7T) | Our test (IMPACT 3T) | Rationale |
|-----------|-----------------|---------------------|-----------|
| FOD cutoff (`-cutoff`) | 0.06 | **0.1, 0.08, 0.06** | 3T may need higher cutoff — test all three |
| Streamline target (`-select`) | 2500 | **1000** | Reduced for faster testing (will increase in Step 24) |
| Seeding attempts (`-seeds`) | 25,000,000 | **5,000,000** | Reduced for faster testing (will increase in Step 24) |
| Min track length (`-minlength`) | 35 mm | **35 mm** | Start with Ranesh's value |
| Max track length (`-maxlength`) | 65 mm | **65 mm** | Start with Ranesh's value |
| Seed direction (`-seed_unidirectional`) | yes | **yes** | Match Ranesh |
| Stop flag (`-stop`) | yes | **yes** | Stop when select count reached |
| Threads (`-nthreads`) | 24 | **8** | Shared cluster |
| Exclusion strategy | 13 individual ROIs | **1 atlas-based mask** | Ranesh's recommended shortcut (Step 22) |

**Flags NOT used** (Ranesh didn't use these either): ACT, backtrack, crop_at_gmwmif, angle, step_size (MRtrix defaults).

**NOT using `-fslgrad`** because gradients are already embedded in dwi.mif from Step 15 (mrconvert with `-fslgrad`).

**Test subjects** (from Ranesh's suggestion): s169, s4222, s4418, s606, s1000

**Total runs:** 5 subjects × 3 cutoffs × 2 hemispheres = **30 tckgen runs**

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
│   ├── l_vta_l_hipp_0.1.tck     # left tract at cutoff 0.1
│   ├── l_vta_l_hipp_0.08.tck    # left tract at cutoff 0.08
│   └── l_vta_l_hipp_0.06.tck    # left tract at cutoff 0.06
│
├── r_vta_r_hipp/
│   ├── r_vta_r_hipp_0.1.tck     # right tract at cutoff 0.1
│   ├── r_vta_r_hipp_0.08.tck    # right tract at cutoff 0.08
│   └── r_vta_r_hipp_0.06.tck    # right tract at cutoff 0.06
```

**Running Step 23 in tmux:**

1. SSH into the cluster and create a tmux session:
```bash
ssh -XY tur50045@cla19097.tu.temple.edu
tmux new -s tckgen_test
```

2. Create the script:
```bash
nano /data/projects/STUDIES/IMPACT/DTI/scripts/run_step23_test_tractography.sh
```

3. Paste the following into nano:
```bash
#!/bin/bash
# ============================================================
# Step 23: Test Tractography on 5 Subjects (Parameter Tuning)
# ============================================================
# Tests tckgen with 3 FOD cutoff values (0.1, 0.08, 0.06) on
# 5 subjects to find optimal parameters for 3T IMPACT data.
# Ranesh used cutoff=0.06 at 7T; predicted 0.08 for 3T.
#
# Input:  CSD/<subj>/wm_fod_norm.mif (normalized WM FODs)
#         CSD/<subj>/rois/left_VTA_diff.nii.gz (seed)
#         CSD/<subj>/rois/left_HPC_diff.nii.gz (target/include)
#         CSD/<subj>/rois/exclusion_mask_l.nii.gz (exclusion)
#         (same for right hemisphere)
#
# Output: CSD/<subj>/tckgen/l_vta_l_hipp/l_vta_l_hipp_<cutoff>.tck
#         CSD/<subj>/tckgen/r_vta_r_hipp/r_vta_r_hipp_<cutoff>.tck
#
# Parameters matching Ranesh's pipeline (adjusted for 3T):
#   -seed_unidirectional (same as Ranesh)
#   -select 1000 (Ranesh: 2500, reduced for test)
#   -seeds 5000000 (Ranesh: 25M, reduced for test)
#   -minlength 35 (Ranesh: 35mm at 7T)
#   -maxlength 65 (Ranesh: 65mm at 7T)
#   -stop (same as Ranesh)
#   -cutoff varies: 0.1, 0.08, 0.06 (Ranesh: fixed 0.06 at 7T)
#   -nthreads 8 (Ranesh: 24, reduced for shared cluster)
#
# NOT using -fslgrad (gradients already embedded in dwi.mif from Step 15)
# NOT using ACT, backtrack, angle, step_size (Ranesh didn't use these)
# ============================================================

export PATH=/data/tools/mrtrix3/bin:$PATH

csd_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD"
log_file="/data/projects/STUDIES/IMPACT/DTI/scripts/step23_test.log"

# 5 test subjects (from Ranesh's suggestion)
test_subjects="s169 s4222 s4418 s606 s1000"

echo "=== Step 23: Test Tractography ===" > "$log_file"
echo "Started: $(date)" >> "$log_file"
echo "Test subjects: $test_subjects" >> "$log_file"
echo "Cutoffs: 0.1, 0.08, 0.06" >> "$log_file"
echo "Parameters: -select 1000 -seeds 5000000 -minlength 35 -maxlength 65" >> "$log_file"
echo "" >> "$log_file"

for subj in $test_subjects; do
    echo "========================================" | tee -a "$log_file"
    echo ">>> [$subj] Starting test tractography" | tee -a "$log_file"
    echo "========================================" | tee -a "$log_file"

    # Verify inputs exist
    if [[ ! -f "$csd_base/$subj/wm_fod_norm.mif" ]]; then
        echo "!!! [$subj] MISSING wm_fod_norm.mif — skipping" | tee -a "$log_file"
        continue
    fi
    if [[ ! -f "$csd_base/$subj/rois/exclusion_mask_l.nii.gz" ]]; then
        echo "!!! [$subj] MISSING exclusion_mask_l.nii.gz — skipping" | tee -a "$log_file"
        continue
    fi

    for cutoff in 0.1 0.08 0.06; do
        # === LEFT HEMISPHERE ===
        echo ">>> [$subj] LEFT VTA→HPC at cutoff $cutoff — $(date)" | tee -a "$log_file"
        mkdir -p "$csd_base/$subj/tckgen/l_vta_l_hipp"

        tckgen "$csd_base/$subj/wm_fod_norm.mif" \
            "$csd_base/$subj/tckgen/l_vta_l_hipp/l_vta_l_hipp_${cutoff}.tck" \
            -seed_image "$csd_base/$subj/rois/left_VTA_diff.nii.gz" \
            -seed_unidirectional \
            -include "$csd_base/$subj/rois/left_HPC_diff.nii.gz" \
            -exclude "$csd_base/$subj/rois/exclusion_mask_l.nii.gz" \
            -select 1000 \
            -seeds 5000000 \
            -cutoff $cutoff \
            -minlength 35 \
            -maxlength 65 \
            -stop \
            -nthreads 8 \
            -force 2>&1 | tee -a "$log_file"

        # Log streamline count
        if [[ -f "$csd_base/$subj/tckgen/l_vta_l_hipp/l_vta_l_hipp_${cutoff}.tck" ]]; then
            count=$(tckinfo "$csd_base/$subj/tckgen/l_vta_l_hipp/l_vta_l_hipp_${cutoff}.tck" 2>/dev/null | grep "actual count" | awk '{print $NF}')
            echo "    → Left streamlines at cutoff $cutoff: $count" | tee -a "$log_file"
        else
            echo "    → Left tck file NOT created at cutoff $cutoff" | tee -a "$log_file"
        fi

        # === RIGHT HEMISPHERE ===
        echo ">>> [$subj] RIGHT VTA→HPC at cutoff $cutoff — $(date)" | tee -a "$log_file"
        mkdir -p "$csd_base/$subj/tckgen/r_vta_r_hipp"

        tckgen "$csd_base/$subj/wm_fod_norm.mif" \
            "$csd_base/$subj/tckgen/r_vta_r_hipp/r_vta_r_hipp_${cutoff}.tck" \
            -seed_image "$csd_base/$subj/rois/right_VTA_diff.nii.gz" \
            -seed_unidirectional \
            -include "$csd_base/$subj/rois/right_HPC_diff.nii.gz" \
            -exclude "$csd_base/$subj/rois/exclusion_mask_r.nii.gz" \
            -select 1000 \
            -seeds 5000000 \
            -cutoff $cutoff \
            -minlength 35 \
            -maxlength 65 \
            -stop \
            -nthreads 8 \
            -force 2>&1 | tee -a "$log_file"

        # Log streamline count
        if [[ -f "$csd_base/$subj/tckgen/r_vta_r_hipp/r_vta_r_hipp_${cutoff}.tck" ]]; then
            count=$(tckinfo "$csd_base/$subj/tckgen/r_vta_r_hipp/r_vta_r_hipp_${cutoff}.tck" 2>/dev/null | grep "actual count" | awk '{print $NF}')
            echo "    → Right streamlines at cutoff $cutoff: $count" | tee -a "$log_file"
        else
            echo "    → Right tck file NOT created at cutoff $cutoff" | tee -a "$log_file"
        fi
    done

    echo ">>> [$subj] All cutoffs complete — $(date)" | tee -a "$log_file"
    echo "" | tee -a "$log_file"
done

echo "========================================" | tee -a "$log_file"
echo "=== Step 23 Test Tractography Complete ===" | tee -a "$log_file"
echo "Finished: $(date)" | tee -a "$log_file"

# === SUMMARY TABLE ===
echo "" | tee -a "$log_file"
echo "=== SUMMARY TABLE ===" | tee -a "$log_file"
printf "%-8s %-15s %-8s %-12s\n" "Subject" "Hemisphere" "Cutoff" "Streamlines" | tee -a "$log_file"
printf "%-8s %-15s %-8s %-12s\n" "-------" "---------" "------" "-----------" | tee -a "$log_file"

for subj in $test_subjects; do
    for hemi_dir in l_vta_l_hipp r_vta_r_hipp; do
        if [[ "$hemi_dir" == "l_vta_l_hipp" ]]; then
            hemi_label="left"
        else
            hemi_label="right"
        fi
        for cutoff in 0.1 0.08 0.06; do
            tck="$csd_base/$subj/tckgen/$hemi_dir/${hemi_dir}_${cutoff}.tck"
            if [[ -f "$tck" ]]; then
                count=$(tckinfo "$tck" 2>/dev/null | grep "actual count" | awk '{print $NF}')
            else
                count="MISSING"
            fi
            printf "%-8s %-15s %-8s %-12s\n" "$subj" "$hemi_label" "$cutoff" "$count" | tee -a "$log_file"
        done
    done
done

echo "" | tee -a "$log_file"
echo "=== LENGTH STATISTICS ===" | tee -a "$log_file"
printf "%-8s %-15s %-8s %-12s %-12s %-12s\n" "Subject" "Hemisphere" "Cutoff" "Mean(mm)" "Median(mm)" "Std(mm)" | tee -a "$log_file"

for subj in $test_subjects; do
    for hemi_dir in l_vta_l_hipp r_vta_r_hipp; do
        if [[ "$hemi_dir" == "l_vta_l_hipp" ]]; then
            hemi_label="left"
        else
            hemi_label="right"
        fi
        for cutoff in 0.1 0.08 0.06; do
            tck="$csd_base/$subj/tckgen/$hemi_dir/${hemi_dir}_${cutoff}.tck"
            if [[ -f "$tck" ]]; then
                stats=$(tckstats "$tck" 2>/dev/null)
                mean_len=$(echo "$stats" | grep -i mean | head -1 | awk '{print $2}')
                median_len=$(echo "$stats" | grep -i median | head -1 | awk '{print $2}')
                std_len=$(echo "$stats" | grep -i std | head -1 | awk '{print $2}')
                printf "%-8s %-15s %-8s %-12s %-12s %-12s\n" "$subj" "$hemi_label" "$cutoff" "$mean_len" "$median_len" "$std_len" | tee -a "$log_file"
            fi
        done
    done
done
```

4. Save and exit nano:
Press Ctrl+O then Enter to save
Press Ctrl+X to close

5. Make the script runnable and execute inside tmux:
```bash
chmod +x run_step23_test_tractography.sh
./run_step23_test_tractography.sh 2>&1 | tee step23_test_full.log
```

6. Detach from tmux while it runs:
Press Ctrl+B, then D to detach. Reconnect later with:
```bash
tmux attach -t tckgen_test
```

**NOTE**: This step takes **2-5 hours** depending on cluster load. Each of the 30 tckgen runs takes ~5-10 minutes. The script logs streamline counts after each run and prints a summary table at the end.

**Step 23 Audit — verify test tractography outputs:**
```bash
#!/bin/bash
# Audit Step 23: Test tractography outputs

csd_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD"
export PATH=/data/tools/mrtrix3/bin:$PATH

printf "%-8s %-15s %-8s %-12s %-12s\n" "Subject" "Hemisphere" "Cutoff" "Streamlines" "MeanLen(mm)"
printf "%-8s %-15s %-8s %-12s %-12s\n" "-------" "---------" "------" "-----------" "-----------"

for subj in s169 s4222 s4418 s606 s1000; do
    for hemi_dir in l_vta_l_hipp r_vta_r_hipp; do
        hemi=$([[ "$hemi_dir" == "l_vta_l_hipp" ]] && echo "left" || echo "right")
        for cutoff in 0.1 0.08 0.06; do
            tck="$csd_base/$subj/tckgen/$hemi_dir/${hemi_dir}_${cutoff}.tck"
            if [[ -f "$tck" ]]; then
                count=$(tckinfo "$tck" 2>/dev/null | grep "actual count" | awk '{print $NF}')
                mean=$(tckstats "$tck" 2>/dev/null | grep -i mean | head -1 | awk '{print $2}')
                printf "%-8s %-15s %-8s %-12s %-12s\n" "$subj" "$hemi" "$cutoff" "$count" "$mean"
            else
                printf "%-8s %-15s %-8s %-12s %-12s\n" "$subj" "$hemi" "$cutoff" "MISSING" "N/A"
            fi
        done
    done
done
```

### Step 23 Results — Pilot Findings

We tested four FOD amplitude cutoffs (0.1, 0.08, 0.06, 0.01) on 5 subjects across both hemispheres to determine the optimal tracking threshold for our 3T data.

**Streamline counts (target: 1000, seed limit: 5,000,000):**

| Subject | Hemi | 0.1 | 0.08 | 0.06 | 0.01 |
|---------|------|-----|------|------|------|
| s169 | L | 118 | 556 | 1000 | 1000 |
| s169 | R | 30 | 434 | 1000 | 1000 |
| s4222 | L | 274 | 1000 | 1000 | 1000 |
| s4222 | R | 165 | 906 | 1000 | 1000 |
| s4418 | L | 1000 | 1000 | 1000 | 1000 |
| s4418 | R | 1000 | 1000 | 1000 | 1000 |
| s606 | L | 88 | 309 | 1000 | 1000 |
| s606 | R | 731 | 1000 | 1000 | 1000 |
| s1000 | L | — | — | 1000 | 1000 |
| s1000 | R | — | — | 1000 | 1000 |

**Key findings:**
- **0.1**: Too strict for 3T — most subjects failed to reach 1000 streamlines within the seed limit
- **0.08**: Inconsistent — some subjects hit target, others fell well short (e.g., s606 left = 309)
- **0.06**: Reliable — all 10/10 runs hit 1000 streamlines
- **0.01**: Equally reliable — all 10/10 runs hit 1000 streamlines, but ~5× more seed-efficient (avg ~415K seeds vs ~2.1M+ at 0.06)

**Visual and statistical comparison of 0.01 vs 0.06:**

We generated tract density images (TDIs) for both cutoffs and compared them:
- Tract paths are virtually identical — same VTA→HPC arc in both axial and coronal views
- 0.01 produces slightly thicker TDIs (broader spatial spread through the tract corridor)
- Spatial overlap (Dice coefficient) averaged 0.66 across all subjects/hemispheres
- Mean streamline lengths were nearly identical (~44mm at 0.01 vs ~47mm at 0.06)
- Standard deviation of lengths was marginally higher at 0.01 (~7mm vs ~6mm)

**Example TDI comparison — s169, left VTA→HPC (0.06 left, 0.01 right):**

![Cutoff comparison]({{ "/images/cutoff_compare_s169_l.png" | relative_url }})

**Statistical comparison across all 5 test subjects:**

![Cutoff stats]({{ "/images/cutoff_stats_comparison.png" | relative_url }})

Note the slightly thicker TDI at 0.01 — this reflects the broader spatial spread from the more permissive cutoff. The cleaning step (Step 25) addresses this by removing outlier streamlines, producing bundles that are even tighter than the conservative 0.06 threshold.

**Decision: Use cutoff 0.01 for full tractography (Step 24).**

Ranesh confirmed this choice — he reported that with the atlas-based exclusion mask, dropping the FOD cutoff as low as 0.01 produces robust and clean streamlines. The mask constrains tracking to the anatomically plausible corridor, preventing the spurious streamlines that would normally result from a permissive cutoff. He also noted that the tracts may not even require pyAFQ cleaning afterward, though we will still run the cleaning step (Step 25) as a safeguard.

---

