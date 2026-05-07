---
layout: default
title: "Step 16 — Response Function Estimation (dwi2response)"
parent: "Tractography (Steps 15–26)"
nav_order: 16
---

# Step 16 — Response Function Estimation (dwi2response)

Before we can model fiber orientations, MRtrix needs to know what the diffusion signal looks like inside each tissue type — white matter, gray matter, and CSF. The **Dhollander algorithm** (`dwi2response dhollander`) automatically estimates these tissue-specific "response functions" from each subject's own data, without requiring a T1 image or atlas. It works by identifying voxels that are unambiguously single-tissue (e.g., deep WM, cortical GM, ventricles) and averaging the signal profile within each.

Each subject gets three output files:
- `wm_response.txt` — white matter response function (multi-shell: one row per b-value)
- `gm_response.txt` — gray matter response function
- `csf_response.txt` — CSF response function

In Step 17, we will average these across subjects to create **group response functions**, which then feed into the actual FOD estimation in Step 18. Using group-averaged responses (rather than per-subject) ensures that differences in FODs between subjects reflect genuine biological differences in fiber architecture — not differences in how the response function was estimated.

**Input (per subject — from Step 15):**
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/dwi.mif`
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/mask.mif`

**Expected Output (per subject):**
```
derivatives/CSD/s1000/
│
├── dwi.mif              # (from Step 15)
├── mask.mif             # (from Step 15)
├── wm_response.txt      # white matter response function
├── gm_response.txt      # gray matter response function
├── csf_response.txt     # CSF response function
```

This step is moderately CPU-intensive — we run up to 15 parallel jobs.

**Running Step 16 in tmux:**

1. SSH into the cluster and reattach (or create) the tmux session:
```bash
ssh -XY tur50045@cla19097.tu.temple.edu
tmux attach -t csd || tmux new -s csd
```

2. Create the script:
```bash
nano run_dwi2response.sh
```

3. Paste the following into nano:
```bash
#!/bin/bash
# ============================================================
# Step 16: Estimate per-subject response functions (dwi2response)
# ============================================================
# Uses the Dhollander algorithm to estimate tissue-specific
# response functions (WM, GM, CSF) from each subject's DWI data.
# These are needed for multi-shell multi-tissue CSD (Step 18).
# Input:  CSD/<subj>/dwi.mif, mask.mif
# Output: CSD/<subj>/wm_response.txt, gm_response.txt, csf_response.txt
# ============================================================

export PATH=/data/tools/mrtrix3/bin:$PATH

csd_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD"
nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"

process_subj() {
    subj=$1
    echo ">>> [$subj] Estimating response functions"
    d="$csd_base/$subj"

    if [[ ! -f "$d/dwi.mif" || ! -f "$d/mask.mif" ]]; then
        echo "!!! [$subj] Missing dwi.mif or mask.mif, skipping"
        return
    fi

    dwi2response dhollander \
        "$d/dwi.mif" \
        "$d/wm_response.txt" \
        "$d/gm_response.txt" \
        "$d/csf_response.txt" \
        -mask "$d/mask.mif" \
        -force

    echo ">>> [$subj] Done"
}

export -f process_subj
export csd_base

subjects=$(ls -1 "$nifti_base")
for subj in $subjects; do
    process_subj "$subj" &
    while [ "$(jobs -r | wc -l)" -ge 15 ]; do sleep 1; done
done
wait
echo "=== All response function estimations finished ==="
```

4. Save and exit nano:
Press Ctrl+O then Enter to save
Press Ctrl+X to close

5. Make the script runnable and execute inside tmux:
```bash
chmod +x run_dwi2response.sh
./run_dwi2response.sh 2>&1 | tee dwi2response.log
```

6. Detach from tmux while it runs (if needed):
Press Ctrl+B, then D to detach. Reconnect later with:
```bash
tmux attach -t csd
```
* Note: All coding output from this script is recorded in dwi2response.log.

**Step 16 Audit — verify dwi2response outputs for all subjects:**
```bash
#!/bin/bash
# Audit Step 16: dwi2response outputs

nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
csd_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD"

printf "Subject\twm_response\tgm_response\tcsf_response\n"

for subj in $(ls -1 "$nifti_base"); do
    d="$csd_base/$subj"
    wm=$([ -f "$d/wm_response.txt" ] && echo "✅" || echo "❌")
    gm=$([ -f "$d/gm_response.txt" ] && echo "✅" || echo "❌")
    csf=$([ -f "$d/csf_response.txt" ] && echo "✅" || echo "❌")
    printf "%s\t%s\t%s\t%s\n" "$subj" "$wm" "$gm" "$csf"
done

echo -e "\n=== dwi2response Audit Complete ==="
```

---

