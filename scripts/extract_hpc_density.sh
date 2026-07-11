#!/bin/bash
export FSLDIR=/usr/local/fsl
source $FSLDIR/etc/fslconf/fsl.sh
export PATH=$FSLDIR/bin:$PATH
csd=/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD
noddi=/data/projects/STUDIES/IMPACT/DTI/derivatives/NODDI
nifti=/data/projects/STUDIES/IMPACT/DTI/NIFTI
out=/data/projects/STUDIES/IMPACT/DTI/derivatives/FIRST_HPC/hpc_density.csv
echo "Subject,L_HPC_NDI,R_HPC_NDI,L_HPC_ODI,R_HPC_ODI,L_HPC_FWF,R_HPC_FWF,L_HPC_vox,R_HPC_vox" > "$out"
for subj in $(ls -1 "$nifti"); do
  nd=$noddi/sub-$subj
  Lroi=$csd/$subj/rois/left_HPC_diff.nii.gz
  Rroi=$csd/$subj/rois/right_HPC_diff.nii.gz
  [ -f "$nd/fit_NDI_modulated.nii.gz" ] && [ -f "$Lroi" ] || { echo "$subj,,,,,,,," >> "$out"; continue; }
  lndi=$(fslstats "$nd/fit_NDI_modulated.nii.gz" -k "$Lroi" -M 2>/dev/null)
  rndi=$(fslstats "$nd/fit_NDI_modulated.nii.gz" -k "$Rroi" -M 2>/dev/null)
  lodi=$(fslstats "$nd/fit_ODI_modulated.nii.gz" -k "$Lroi" -M 2>/dev/null)
  rodi=$(fslstats "$nd/fit_ODI_modulated.nii.gz" -k "$Rroi" -M 2>/dev/null)
  lfwf=$(fslstats "$nd/fit_FWF.nii.gz" -k "$Lroi" -M 2>/dev/null)
  rfwf=$(fslstats "$nd/fit_FWF.nii.gz" -k "$Rroi" -M 2>/dev/null)
  lv=$(fslstats "$Lroi" -V 2>/dev/null | awk '{print $1}')
  rv=$(fslstats "$Rroi" -V 2>/dev/null | awk '{print $1}')
  echo "$subj,$lndi,$rndi,$lodi,$rodi,$lfwf,$rfwf,$lv,$rv" >> "$out"
done
echo "DENSITY_DONE"
