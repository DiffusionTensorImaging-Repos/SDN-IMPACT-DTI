---
layout: default
title: "Step 20 — ANTs Registration: MNI → T1 Space"
parent: "Tractography (Steps 15–26)"
nav_order: 20
---

# Step 20 — ANTs Registration: MNI → T1 Space

The ROIs from Ranesh are in MNI standard space (1mm). Tractography runs in each subject's native diffusion space. To get ROIs from MNI → diffusion, we need two transforms applied in sequence:

1. **MNI → T1** (ANTs nonlinear warp — this step)
2. **T1 → Diffusion** (FLIRT linear transform — Step 21, using existing matrices from Step 12)

We need the **nonlinear** ANTs warp for the MNI → T1 step because every brain is shaped differently from the MNI template. A linear (affine) transform can handle rotation, scaling, and shearing, but it cannot account for the fact that one person's hippocampus is a little wider, or their VTA sits a few mm lower, than the template. ANTs SyN registration deforms the MNI template to match each subject's specific brain shape, so the ROIs land precisely where they should.

Ranesh used `antsRegistrationSyNQuick.sh` for this same purpose. We use the same tool with the same approach. The only difference is that Ranesh's HCP data was already T1-aligned to diffusion (no Step 21 needed), whereas our IMPACT data requires the additional FLIRT step.

**Input (per subject):**
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/ANTs/<subj>/<subj>_BrainExtractionBrain.nii.gz` (skull-stripped T1 from Step 2)
- `/usr/local/fsl/data/standard/MNI152_T1_1mm_brain.nii.gz` (MNI template — fixed across subjects)

**Expected Output (per subject):**
```
derivatives/CSD/s1000/reg/
│
├── mni2t1_0GenericAffine.mat      # affine component of the registration
├── mni2t1_1Warp.nii.gz            # nonlinear warp field (MNI → T1)
├── mni2t1_1InverseWarp.nii.gz     # inverse warp (T1 → MNI, not used here)
├── mni2t1_Warped.nii.gz           # MNI template warped into subject T1 space (for QC)
```

This step is CPU/memory intensive — we run up to 5 parallel jobs.

**Running Step 20 in tmux:**

1. SSH into the cluster and reattach (or create) the tmux session:
```bash
ssh -XY tur50045@cla19097.tu.temple.edu
tmux attach -t csd || tmux new -s csd
```

2. Create the script:
```bash
nano run_ants_reg.sh
```

3. Paste the following into nano:
```bash
#!/bin/bash
# ============================================================
# Step 20: ANTs Registration — MNI → Subject T1 Space
# ============================================================
# Registers the MNI152 template to each subject's skull-stripped
# T1, producing warp fields that can move any MNI-space image
# (ROIs, atlases) into subject-native T1 space.
# Input:  ANTs/<subj>/<subj>_BrainExtractionBrain.nii.gz (skull-stripped T1)
#         FSL MNI152_T1_1mm_brain.nii.gz (standard template)
# Output: CSD/<subj>/reg/mni2t1_0GenericAffine.mat
#         CSD/<subj>/reg/mni2t1_1Warp.nii.gz
#         CSD/<subj>/reg/mni2t1_1InverseWarp.nii.gz
#         CSD/<subj>/reg/mni2t1_Warped.nii.gz
# ============================================================

export ANTSPATH=/data/tools/ANTs/bin/
export PATH=${ANTSPATH}:$PATH

ants_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/ANTs"
csd_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD"
nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
mni_template="/usr/local/fsl/data/standard/MNI152_T1_1mm_brain.nii.gz"

process_subj() {
    subj=$1
    echo ">>> [$subj] Running ANTs registration: MNI → T1"

    t1_brain="$ants_base/$subj/${subj}_BrainExtractionBrain.nii.gz"
    reg_dir="$csd_base/$subj/reg"
    mkdir -p "$reg_dir"

    if [[ ! -f "$t1_brain" ]]; then
        echo "!!! [$subj] Missing skull-stripped T1, skipping"
        return
    fi

    # Register MNI (moving) to subject T1 (fixed)
    antsRegistrationSyNQuick.sh \
        -d 3 \
        -f "$t1_brain" \
        -m "$mni_template" \
        -o "$reg_dir/mni2t1_" \
        -n 4

    echo ">>> [$subj] Done"
}

export -f process_subj
export ants_base csd_base mni_template ANTSPATH

subjects=$(ls -1 "$nifti_base")
for subj in $subjects; do
    process_subj "$subj" &
    while [ "$(jobs -r | wc -l)" -ge 5 ]; do sleep 1; done
done
wait
echo "=== All ANTs registrations finished ==="
```

4. Save and exit nano:
Press Ctrl+O then Enter to save
Press Ctrl+X to close

5. Make the script runnable and execute inside tmux:
```bash
chmod +x run_ants_reg.sh
./run_ants_reg.sh 2>&1 | tee ants_reg.log
```

6. Detach from tmux while it runs (if needed):
Press Ctrl+B, then D to detach. Reconnect later with:
```bash
tmux attach -t csd
```
* Note: All coding output from this script is recorded in ants_reg.log.

**Step 20 Audit — verify ANTs registration outputs for all subjects:**
```bash
#!/bin/bash
# Audit Step 20: ANTs registration outputs

nifti_base="/data/projects/STUDIES/IMPACT/DTI/NIFTI"
csd_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD"

printf "Subject\tAffine\tWarp\tInvWarp\tWarped\n"

for subj in $(ls -1 "$nifti_base"); do
    d="$csd_base/$subj/reg"
    aff=$([ -f "$d/mni2t1_0GenericAffine.mat" ] && echo "✅" || echo "❌")
    wrp=$([ -f "$d/mni2t1_1Warp.nii.gz" ] && echo "✅" || echo "❌")
    inv=$([ -f "$d/mni2t1_1InverseWarp.nii.gz" ] && echo "✅" || echo "❌")
    wrd=$([ -f "$d/mni2t1_Warped.nii.gz" ] && echo "✅" || echo "❌")
    printf "%s\t%s\t%s\t%s\t%s\n" "$subj" "$aff" "$wrp" "$inv" "$wrd"
done

echo -e "\n=== ANTs Registration Audit Complete ==="
```

---

