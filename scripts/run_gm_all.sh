#!/bin/bash
# Refit NODDI in the hippocampus with the GM parallel diffusivity (dPar=1.1e-3)
cd /data/projects/STUDIES/IMPACT/DTI/scripts
nifti=/data/projects/STUDIES/IMPACT/DTI/NIFTI
log=/data/projects/STUDIES/IMPACT/DTI/scripts/noddi_gm.log
echo "=== GM NODDI refit (dPar=1.1e-3) started $(date) ===" > "$log"
n=0
for subj in $(ls -1 "$nifti"); do
  n=$((n+1))
  echo ">>> [$n] $subj $(date +%H:%M:%S)" >> "$log"
  NODDI_NTHREADS=1 python3 run_noddi_gm.py "$subj" >> "$log" 2>&1
done
echo "GM_NODDI_ALL_DONE n=$n $(date)" >> "$log"
