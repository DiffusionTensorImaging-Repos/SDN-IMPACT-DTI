#!/usr/bin/env python3
"""
Split the hippocampus ROI into ANTERIOR and POSTERIOR at the uncal apex (MNI y = -21),
the standard division (Poppenk et al. 2013, TiCS).

Builds a half-space mask in MNI space, warps it through the SAME transform chain the ROIs
used (ANTs mni2t1 warp -> FLIRT str2diff), then intersects with each subject's HPC ROI.

Usage: python3 split_hpc.py <subject>
"""
import os,sys,subprocess
import numpy as np, nibabel as nib

Y_CUT = -21.0
FSL='/usr/local/fsl'
MNI=f'{FSL}/data/standard/MNI152_T1_1mm_brain.nii.gz'
CSD='/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD'
TR='/data/projects/STUDIES/IMPACT/DTI/derivatives/TRANSFORMS'
ANTS='/data/tools/ANTs/bin'
env=dict(os.environ, FSLDIR=FSL, PATH=f"{FSL}/bin:{ANTS}:"+os.environ.get('PATH',''),
         FSLOUTPUTTYPE='NIFTI_GZ')
def run(c): subprocess.run(c,shell=True,check=True,env=env,capture_output=True)

subj=sys.argv[1]
work=f'{CSD}/{subj}/rois'
tmp=f'/tmp/hpcsplit_{subj}'; os.makedirs(tmp,exist_ok=True)

# 1. anterior half-space in MNI (y > -21)
mni=nib.load(MNI); shp=mni.shape; aff=mni.affine
j=np.arange(shp[1])
ymm=aff[1,1]*j + aff[1,3]          # MNI y for each voxel index along dim2
ant=np.zeros(shp,dtype=np.uint8)
ant[:, ymm > Y_CUT, :] = 1
ant_mni=f'{tmp}/ant_mni.nii.gz'
nib.save(nib.Nifti1Image(ant,aff,mni.header), ant_mni)

# 2. MNI -> T1 (ANTs, same as ROI warping) -> T1 -> diffusion (FLIRT)
t1=f'{CSD}/{subj}/reg/mni2t1_Warped.nii.gz'
t1brain=[p for p in [f'{CSD}/{subj}/reg/mni2t1_Warped.nii.gz'] if os.path.exists(p)][0]
run(f'antsApplyTransforms -d 3 -i {ant_mni} -r {t1brain} -o {tmp}/ant_t1.nii.gz '
    f'-t {CSD}/{subj}/reg/mni2t1_1Warp.nii.gz -t {CSD}/{subj}/reg/mni2t1_0GenericAffine.mat -n NearestNeighbor')
ref=f'{CSD}/{subj}/qc/mean_b0.nii.gz'
run(f'flirt -in {tmp}/ant_t1.nii.gz -ref {ref} -applyxfm -init {TR}/{subj}/str2diff_{subj}.mat '
    f'-out {tmp}/ant_diff.nii.gz -interp nearestneighbour')
run(f'fslmaths {tmp}/ant_diff.nii.gz -thr 0.5 -bin {tmp}/ant_diff.nii.gz')

# 3. intersect with each HPC ROI
out={}
for side,roi in [('L',f'{work}/left_HPC_diff.nii.gz'),('R',f'{work}/right_HPC_diff.nii.gz')]:
    run(f'fslmaths {roi} -mas {tmp}/ant_diff.nii.gz {work}/{side}_HPC_ant_diff.nii.gz')
    run(f'fslmaths {tmp}/ant_diff.nii.gz -binv {tmp}/post_diff.nii.gz')
    run(f'fslmaths {roi} -mas {tmp}/post_diff.nii.gz {work}/{side}_HPC_post_diff.nii.gz')
    for part in ['ant','post']:
        v=subprocess.run(f'fslstats {work}/{side}_HPC_{part}_diff.nii.gz -V',shell=True,
                         env=env,capture_output=True,text=True).stdout.split()[0]
        out[f'{side}_{part}']=int(v)
tot=subprocess.run(f'fslstats {work}/left_HPC_diff.nii.gz -V',shell=True,env=env,
                   capture_output=True,text=True).stdout.split()[0]
print(f"{subj}: L_ant={out['L_ant']} L_post={out['L_post']} (whole L={tot}) | "
      f"R_ant={out['R_ant']} R_post={out['R_post']}")
