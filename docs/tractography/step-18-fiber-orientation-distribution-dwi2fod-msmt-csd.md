---
layout: default
title: "Step 18 — Fiber Orientation Distribution (dwi2fod MSMT-CSD)"
parent: "Tractography (Steps 15–26)"
nav_order: 18
---

# Step 18 — Fiber Orientation Distribution (dwi2fod MSMT-CSD)

This is the core modeling step — the MRtrix equivalent of what BedpostX did back in Step 9, but better. **Multi-Shell Multi-Tissue Constrained Spherical Deconvolution (MSMT-CSD)** takes each subject's DWI data and decomposes the diffusion signal at every voxel into contributions from white matter, gray matter, and CSF. The result is a **fiber orientation distribution (FOD)** at each voxel — a 3D shape that shows which directions fibers are pointing and how strongly.

The key details:
- We use `dwi2fod msmt_csd` — the multi-shell multi-tissue variant, which takes advantage of all our b-value shells (b=0, 1000, 2000, 3250, 5000) to better separate tissue types.
- We use the **group-averaged response functions** from Step 17 (not per-subject), matching Ranesh's pipeline and MRtrix recommendations.
- Each subject gets three FOD images: `wm_fod.mif` (white matter — this is the one that matters for tractography), `gm_fod.mif`, and `csf_fod.mif`.

**Input (per subject):**
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/dwi.mif` (from Step 15)
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/mask.mif` (from Step 15)
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/group_wm_response.txt` (from Step 17)
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/group_gm_response.txt` (from Step 17)
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/group_csf_response.txt` (from Step 17)

**Expected Output (per subject):**
```
derivatives/CSD/s1000/
│
├── dwi.mif              # (from Step 15)
├── mask.mif             # (from Step 15)
├── wm_response.txt      # (from Step 16)
├── gm_response.txt      # (from Step 16)
├── csf_response.txt     # (from Step 16)
├── wm_fod.mif           # white matter FOD (feeds tractography)
├── gm_fod.mif           # gray matter FOD
├── csf_fod.mif          # CSF FOD
```

This step is CPU-intensive — we run up to 10 parallel jobs.

**Running Step 18 in tmux:**

1. SSH into the cluster and reattach (or create) the tmux session:
```bash
ssh -XY tur50045@cla19097.tu.temple.edu
tmux attach -t csd || tmux new -s csd
```

2. Create the script:
```bash
nano run_dwi2fod.sh
```

3. Paste the following into nano:
```bash
#!/bin/bash
# ============================================================
# Step 18: Generate FODs — Multi-Shell Multi-Tissue CSD (dwi2fod)
# ============================================================
# Uses group-averaged response functions to estimate fiber
# orientation distributions (FODs) for each tissue type.
# This is the MRtrix equivalent of BedpostX fiber modeling.
# Input:  CSD/<subj>/dwi.mif, mask.mif + CSD/group_*_response.txt
# Output: CSD/<subj>/wm_fod.mif, gm_fod.mif, csf_fod.mif
# ============================================================

export PATH=/data/tools/mrtrix3/bin:$PATH

csd_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD"
nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"

process_subj() {
    subj=$1
    echo ">>> [$subj] Generating FODs (MSMT-CSD)"
    d="$csd_base/$subj"

    if [[ ! -f "$d/dwi.mif" || ! -f "$d/mask.mif" ]]; then
        echo "!!! [$subj] Missing dwi.mif or mask.mif, skipping"
        return
    fi

    if [[ ! -f "$csd_base/group_wm_response.txt" || ! -f "$csd_base/group_gm_response.txt" || ! -f "$csd_base/group_csf_response.txt" ]]; then
        echo "!!! [$subj] Missing group response functions, skipping"
        return
    fi

    dwi2fod -mask "$d/mask.mif" \
        msmt_csd \
        "$d/dwi.mif" \
        "$csd_base/group_wm_response.txt" "$d/wm_fod.mif" \
        "$csd_base/group_gm_response.txt" "$d/gm_fod.mif" \
        "$csd_base/group_csf_response.txt" "$d/csf_fod.mif" \
        -force

    echo ">>> [$subj] Done"
}

export -f process_subj
export csd_base

subjects=$(ls -1 "$nifti_base")
for subj in $subjects; do
    process_subj "$subj" &
    while [ "$(jobs -r | wc -l)" -ge 10 ]; do sleep 1; done
done
wait
echo "=== All FOD estimations finished ==="
```

4. Save and exit nano:
Press Ctrl+O then Enter to save
Press Ctrl+X to close

5. Make the script runnable and execute inside tmux:
```bash
chmod +x run_dwi2fod.sh
./run_dwi2fod.sh 2>&1 | tee dwi2fod.log
```

6. Detach from tmux while it runs (if needed):
Press Ctrl+B, then D to detach. Reconnect later with:
```bash
tmux attach -t csd
```
* Note: All coding output from this script is recorded in dwi2fod.log.

**Step 18 Audit — verify dwi2fod outputs for all subjects:**
```bash
#!/bin/bash
# Audit Step 18: dwi2fod outputs

nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
csd_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD"

printf "Subject\twm_fod\tgm_fod\tcsf_fod\n"

for subj in $(ls -1 "$nifti_base"); do
    d="$csd_base/$subj"
    wm=$([ -f "$d/wm_fod.mif" ] && echo "✅" || echo "❌")
    gm=$([ -f "$d/gm_fod.mif" ] && echo "✅" || echo "❌")
    csf=$([ -f "$d/csf_fod.mif" ] && echo "✅" || echo "❌")
    printf "%s\t%s\t%s\t%s\n" "$subj" "$wm" "$gm" "$csf"
done

echo -e "\n=== dwi2fod Audit Complete ==="
```

---

