#!/bin/bash
# Extract hippocampal NODDI from the GM-corrected fit (dPar=1.1e-3)
export FSLDIR=/usr/local/fsl; source $FSLDIR/etc/fslconf/fsl.sh; export PATH=$FSLDIR/bin:$PATH
csd=/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD
gm=/data/projects/STUDIES/IMPACT/DTI/derivatives/NODDI_GM
nifti=/data/projects/STUDIES/IMPACT/DTI/NIFTI
out=/data/projects/STUDIES/IMPACT/DTI/derivatives/NODDI_GM/hpc_density_gm.csv
echo "Subject,L_HPC_NDI,R_HPC_NDI,L_HPC_ODI,R_HPC_ODI,L_HPC_FWF,R_HPC_FWF,L_HPC_vox,R_HPC_vox" > "$out"
for subj in $(ls -1 "$nifti"); do
  nd=$gm/sub-$subj
  L=$csd/$subj/rois/left_HPC_diff.nii.gz; R=$csd/$subj/rois/right_HPC_diff.nii.gz
  [ -f "$nd/fit_NDI_modulated.nii.gz" ] && [ -f "$L" ] || { echo "$subj,,,,,,,," >> "$out"; continue; }
  echo "$subj,$(fslstats $nd/fit_NDI_modulated.nii.gz -k $L -M),$(fslstats $nd/fit_NDI_modulated.nii.gz -k $R -M),$(fslstats $nd/fit_ODI_modulated.nii.gz -k $L -M),$(fslstats $nd/fit_ODI_modulated.nii.gz -k $R -M),$(fslstats $nd/fit_FWF.nii.gz -k $L -M),$(fslstats $nd/fit_FWF.nii.gz -k $R -M),$(fslstats $L -V | awk '{print $1}'),$(fslstats $R -V | awk '{print $1}')" >> "$out"
done
echo "GM_DENSITY_DONE"; wc -l "$out"
