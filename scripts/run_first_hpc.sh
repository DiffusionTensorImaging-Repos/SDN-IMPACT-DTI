#!/bin/bash
export FSLDIR=/usr/local/fsl
source $FSLDIR/etc/fslconf/fsl.sh
export PATH=$FSLDIR/bin:$PATH
ants=/data/projects/STUDIES/IMPACT/DTI/derivatives/ANTs
out=/data/projects/STUDIES/IMPACT/DTI/derivatives/FIRST_HPC
nifti=/data/projects/STUDIES/IMPACT/DTI/NIFTI
mkdir -p "$out"
log=$out/first.log
echo "start $(date)" > "$log"

process(){
  subj=$1
  t1=$ants/$subj/${subj}_BrainExtractionBrain.nii.gz
  [ -f "$t1" ] || { echo "MISSING $subj" >> "$log"; return; }
  od=$out/$subj; mkdir -p "$od"
  [ -f "$od/${subj}_all_fast_firstseg.nii.gz" ] && { echo "skip $subj" >> "$log"; return; }
  run_first_all -s L_Hipp,R_Hipp -b -i "$t1" -o "$od/$subj" >> "$log" 2>&1
  echo "done $subj $(date +%T)" >> "$log"
}
export -f process; export ants out FSLDIR log

for s in $(ls -1 "$nifti"); do
  process "$s" &
  while [ "$(jobs -r | wc -l)" -ge 16 ]; do sleep 5; done
done
wait
echo "FIRST_ALL_DONE $(date)" >> "$log"
