#!/usr/bin/env python3
# ============================================================
# NODDI refit for GRAY MATTER (hippocampus) — corrected dPar
# ============================================================
# Per Ranesh (2026-08-14 meeting): "when you run NODDI in gray matter versus
# white matter, you have to tweak the parallel diffusivity parameter, because
# water diffuses differently in gray matter and white matter. So if you didn't
# lower the parameter, you might have to rerun that."
#
# Our Step-29 fit used AMICO's default dPar = 1.7e-3 (the WHITE-matter value),
# so hippocampal (gray matter) NDI/ODI/FWF from that fit are not valid.
#
# This refits with dPar = 1.1e-3 (standard GM intrinsic parallel diffusivity)
# and restricts the fit to the hippocampus ROI, so it runs in seconds/subject
# instead of refitting the whole brain.
#
# Usage: python3 run_noddi_gm.py <subject_id>
# ============================================================
import os, sys, time
from pathlib import Path

nb_threads = int(os.environ.get("NODDI_NTHREADS", "8"))
os.environ["OPENBLAS_NUM_THREADS"] = str(nb_threads)
os.environ["OMP_NUM_THREADS"] = str(nb_threads)

import amico, numpy as np, nibabel as nib

DPAR_GM = 1.1E-3      # <-- the one number: lowered from the 1.7e-3 WM default
DISO    = 3.0E-3
B0_THR  = 100

bedpostx_root = Path("/data/projects/STUDIES/IMPACT/DTI/derivatives/BEDPOSTX")
csd_root      = Path("/data/projects/STUDIES/IMPACT/DTI/derivatives/CSD")
gm_root       = Path("/data/projects/STUDIES/IMPACT/DTI/derivatives/NODDI_GM")
gm_root.mkdir(parents=True, exist_ok=True)

setup_dir = gm_root / "amico"
if not setup_dir.exists():
    cwd = os.getcwd(); os.chdir(str(gm_root)); amico.setup(); os.chdir(cwd)

subj = sys.argv[1]
t0 = time.time()

si = bedpostx_root / subj / "bedpostx_input"
dwi, bvals, bvecs = si/"data.nii.gz", si/"bvals", si/"bvecs"
Lroi = csd_root/subj/"rois"/"left_HPC_diff.nii.gz"
Rroi = csd_root/subj/"rois"/"right_HPC_diff.nii.gz"
for f in [dwi,bvals,bvecs,Lroi,Rroi]:
    if not f.exists():
        print(f"!!! [{subj}] MISSING {f}"); sys.exit(1)

out = gm_root / f"sub-{subj}"; out.mkdir(exist_ok=True)

# hippocampus-only mask (L + R union) -> fit only these voxels
li, ri = nib.load(str(Lroi)), nib.load(str(Rroi))
hm = ((li.get_fdata()>0)|(ri.get_fdata()>0)).astype(np.uint8)
mask_path = out/"hpc_mask.nii.gz"
nib.save(nib.Nifti1Image(hm, li.affine, li.header), str(mask_path))
print(f"[{subj}] hippocampus mask voxels: {int(hm.sum())}")

scheme = out/f"sub-{subj}_scheme.scheme"
amico.util.fsl2scheme(str(bvals), str(bvecs), str(scheme), bStep=200)

ae = amico.Evaluation(str(gm_root), f"sub-{subj}", str(out))
ae.set_config('nthreads', nb_threads)
ae.set_config('BLAS_nthreads', 1)
ae.set_config('doSaveModulatedMaps', True)
ae.set_config('doComputeRMSE', True)
ae.load_data(str(dwi), str(scheme), str(mask_path), b0_thr=B0_THR)

ae.set_model("NODDI")
# THE FIX: lower the intrinsic parallel diffusivity for gray matter
ae.model.set(DPAR_GM, DISO, ae.model.IC_VFs, ae.model.IC_ODs, False)
print(f"[{subj}] dPar set to {ae.model.dPar} (WM default is 0.0017)")

ae.generate_kernels(regenerate=True)
ae.load_kernels()
ae.fit()
ae.save_results(save_dir_avg=True)

print(f"[OK] [{subj}] GM NODDI done in {(time.time()-t0)/60:.1f} min")
print(f"SUBJ_DONE:{subj}")
