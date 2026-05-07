---
layout: default
title: "Step 17 — Group-Average Response Functions (responsemean)"
parent: "Tractography (Steps 15–26)"
nav_order: 17
---

# Step 17 — Group-Average Response Functions (responsemean)

Now that every subject has their own tissue-specific response functions (from Step 16), we average them across all subjects to produce a single set of **group response functions**. This is a key recommendation from MRtrix3: using group-averaged responses for FOD estimation ensures that differences in the FOD maps between subjects reflect genuine differences in fiber architecture — not noise from how the response function was estimated for that individual.

This step produces three files that live in the parent `CSD/` directory (not inside any subject folder), since they are shared across all subjects:
- `group_wm_response.txt` — group-average white matter response
- `group_gm_response.txt` — group-average gray matter response
- `group_csf_response.txt` — group-average CSF response

These group responses feed into Step 18 (dwi2fod) for every subject.

**Input (per subject — from Step 16):**
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/wm_response.txt`
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/gm_response.txt`
- `/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD/<subj>/csf_response.txt`

**Expected Output (shared across subjects):**
```
derivatives/CSD/
│
├── group_wm_response.txt     # group-average WM response
├── group_gm_response.txt     # group-average GM response
├── group_csf_response.txt    # group-average CSF response
├── s1000/                    # (per-subject dirs from Steps 15-16)
├── s1001/
├── ...
```

This step is fast — three single commands, no parallelism needed.

**Running Step 17 in tmux:**

1. SSH into the cluster and reattach (or create) the tmux session:
```bash
ssh -XY tur50045@cla19097.tu.temple.edu
tmux attach -t csd || tmux new -s csd
```

2. Create the script:
```bash
nano run_responsemean.sh
```

3. Paste the following into nano:
```bash
#!/bin/bash
# ============================================================
# Step 17: Group-average response functions (responsemean)
# ============================================================
# Averages per-subject response functions across all subjects
# to create group-level WM, GM, CSF response functions.
# MRtrix recommends group-averaged responses for FOD estimation.
# Input:  CSD/<subj>/wm_response.txt, gm_response.txt, csf_response.txt
# Output: CSD/group_wm_response.txt, group_gm_response.txt, group_csf_response.txt
# ============================================================

export PATH=/data/tools/mrtrix3/bin:$PATH

csd_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD"

cd "$csd_base"

echo ">>> Computing group-average WM response"
responsemean */wm_response.txt group_wm_response.txt -info -force

echo ">>> Computing group-average GM response"
responsemean */gm_response.txt group_gm_response.txt -info -force

echo ">>> Computing group-average CSF response"
responsemean */csf_response.txt group_csf_response.txt -info -force

echo "=== Group-average response functions finished ==="
```

4. Save and exit nano:
Press Ctrl+O then Enter to save
Press Ctrl+X to close

5. Make the script runnable and execute inside tmux:
```bash
chmod +x run_responsemean.sh
./run_responsemean.sh 2>&1 | tee responsemean.log
```

6. Detach from tmux while it runs (if needed):
Press Ctrl+B, then D to detach. Reconnect later with:
```bash
tmux attach -t csd
```
* Note: All coding output from this script is recorded in responsemean.log.

**Step 17 Audit — verify group response functions exist:**
```bash
#!/bin/bash
# Audit Step 17: group-average response functions

csd_base="/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD"

echo "=== Group Response Function Audit ==="
for tissue in wm gm csf; do
    f="$csd_base/group_${tissue}_response.txt"
    if [ -f "$f" ]; then
        echo "✅ group_${tissue}_response.txt exists ($(wc -l < "$f") lines)"
    else
        echo "❌ group_${tissue}_response.txt MISSING"
    fi
done

echo -e "\n=== responsemean Audit Complete ==="
```

---

