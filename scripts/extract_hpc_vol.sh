#!/bin/bash
export FSLDIR=/usr/local/fsl; source $FSLDIR/etc/fslconf/fsl.sh; export PATH=$FSLDIR/bin:$PATH
base=/data/projects/STUDIES/IMPACT/DTI/derivatives/FIRST_HPC
nifti=/data/projects/STUDIES/IMPACT/DTI/NIFTI
out=$base/hpc_volumes.csv
echo "Subject,L_HPC_vol_mm3,R_HPC_vol_mm3" > "$out"
for subj in $(ls -1 "$nifti"); do
  seg=$base/$subj/${subj}_all_fast_firstseg.nii.gz
  [ -f "$seg" ] || { echo "$subj,," >> "$out"; continue; }
  # label 17 = Left-Hippocampus, 53 = Right-Hippocampus; -V gives "nvox volume_mm3"
  lv=$(fslstats "$seg" -l 16.5 -u 17.5 -V 2>/dev/null | awk '{print $2}')
  rv=$(fslstats "$seg" -l 52.5 -u 53.5 -V 2>/dev/null | awk '{print $2}')
  echo "$subj,$lv,$rv" >> "$out"
done
echo VOL_DONE
