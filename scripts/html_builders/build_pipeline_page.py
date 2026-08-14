#!/usr/bin/env python3
"""
Build results_html/pipeline.html — the presentation Pipeline page.

Each step is a header (command + package) with TWO buttons:
  • Script  — the VERBATIM block sliced out of ReadMe.md by fence line-range
  • Outputs — the decisions, context, results, and figures from the md
Light/plain styling lives in _pres.css.
"""
from pathlib import Path
import html

ROOT = Path("/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI")
README = ROOT / "ReadMe.md"
OUT = ROOT / "results_html" / "pipeline.html"
LINES = README.read_text().splitlines()  # md line N == LINES[N-1]


def slice_fence(o, c):
    return "\n".join(LINES[o:c - 1])


# bedpostx was not used (MRtrix MSMT-CSD replaced it). A few verbatim scripts
# read the eddy-corrected DWI from a folder that was named bedpostx_input/; rename
# it in the display so nothing reads as if bedpostx was part of the pipeline.
def sanitize(t):
    for a, b in [("bedpostx_input", "eddy_dwi"), ("bedpostx_base", "eddydwi_base"),
                 ("BEDPOSTX", "preproc"), ("BedpostX", "preproc"), ("bedpostx", "preproc")]:
        t = t.replace(a, b)
    return t


def render_script(spec):
    if isinstance(spec, str):
        raw = spec
    elif isinstance(spec, tuple):
        raw = slice_fence(*spec)
    else:
        raw = "\n\n".join(slice_fence(*s) for s in spec)
    raw = sanitize(raw)
    out = []
    for ln in raw.split("\n"):
        e = html.escape(ln)
        if ln.lstrip().startswith("#"):
            e = f'<span class="c">{e}</span>'
        out.append(e)
    return "<pre>" + "\n".join(out) + "</pre>"


def fig(src, cap):
    return (f'<figure class="fig"><img src="../images/{src}" alt="{html.escape(cap)}" loading="lazy">'
            f'<figcaption>{cap}</figcaption></figure>')


def step(cmd, pkg, context, script=None, result=None, figures=None):
    # Outputs drawer
    ob = ""
    if context:
        ob += context
    if result:
        ob += f'<div class="lead-lbl">Result</div><p class="res">{result}</p>'
    if figures:
        for src, cap in figures:
            ob += fig(src, cap)
    drawers = ""
    if script is not None:
        drawers += (f'<details class="drawer"><summary>Script</summary>'
                    f'<div class="drawerbody">{render_script(script)}</div></details>')
    if ob:
        drawers += (f'<details class="drawer"><summary>Outputs</summary>'
                    f'<div class="drawerbody">{ob}</div></details>')
    return (f'<div class="step"><div class="stephead"><span class="cmd">{cmd}</span>'
            f'<span class="pkg">{pkg}</span></div><div class="drawers">{drawers}</div></div>')


def sub(t):
    return f'<div class="subhead">{t}</div>'


# ==================================================== PREPROCESSING
PRE = [sub("Clean the raw data")]
PRE.append(step(
    "dcm2niix", "dcm2niix",
    "<p>Convert the scanner's raw DICOM into NIfTI. Only subjects with all four required scans (T1, diffusion, and the two opposed fieldmaps) were converted.</p>",
    (200, 269),
    "57 usable subjects. 5 dropped here for missing scans (s1253, s1476, s578, s820, s999-pilot)."))
PRE.append(step(
    "antsBrainExtraction.sh", "ANTs",
    "<p>Skull-strip the T1 by warping a brain-only template onto each subject and copying its outline over. We used the NKI adult template (a good average adult brain). Every stripped brain was eyeballed in FSLeyes.</p>",
    (453, 507)))
PRE.append(step(
    "fslroi · fslmerge", "FSL",
    "<p>Build the fieldmap pair. Diffusion scans warp near air/tissue boundaries (susceptibility distortion); to measure it the scanner takes two b0 images with opposite phase-encoding (AP and PA). Here we grab the first b0 of each and stack them.</p>",
    (647, 718)))
PRE.append(step(
    "topup", "FSL",
    "<p>Estimate the distortion field from the AP/PA pair, plus a corrected b0. The field is fed into eddy so the diffusion volumes get un-distorted in the same motion-correction pass.</p>",
    (829, 893)))
PRE.append(step(
    "fslmaths -Tmean", "FSL",
    "<p>Average the corrected b0 volumes into one clean, low-noise reference, used as the target for brain-masking and motion correction.</p>",
    (985, 1038)))
PRE.append(step(
    "bet", "FSL",
    "<p>Make a brain mask from the mean b0. Later steps only compute inside the mask, which saves time and avoids garbage from outside the brain.</p>",
    (1099, 1150)))
PRE.append(step(
    "dwidenoise · mrdegibbs · dwiextract", "MRtrix3",
    "<p>Three cleanups on the raw diffusion data: remove thermal noise (MP-PCA), remove Gibbs ringing, and drop the unstable b=250 shell (Olson-lab convention).</p>",
    (1255, 1314),
    "Shells kept: b = 0, 1000, 2000, 3250, 5000."))
PRE.append(step(
    "eddy --repol", "FSL",
    "<p>The big correction: head motion, eddy-current distortion, and the susceptibility field (from topup), all at once, with outlier-slice replacement. A corrupted slice (4+ SD below expected) is rebuilt from a model prediction.</p>",
    (1441, 1503)))
PRE.append(step(
    "eddy_quad · eddy_squad", "FSL",
    "<p>Per-subject (QUAD) and group (SQUAD) automated QC, plus a manual FSLeyes scroll-through. The per-subject absolute-motion number becomes a covariate.</p>",
    (1626, 1796),
    "Motion was low across the board. Group mean absolute motion 0.27 mm. The rule was to exclude anyone over 2 mm; nobody hit it.",
    [("qc_summary.png", "Group SQUAD QC summary across all subjects.")]))

PRE.append(sub("Build the fiber model"))
PRE.append(step(
    "dwiextract", "MRtrix3",
    "<p>Make reduced datasets by shell (b=0,1000 and b=0,1000,2000). The tensor model, next, only wants the low shells.</p>",
    (2126, 2190)))
PRE.append(step(
    "dtifit", "FSL",
    "<p>Fit the diffusion tensor on the low shells and derive FA, MD, and RD. FA is one of the four microstructure metrics carried to the analyses.</p>",
    (2277, 2342)))
PRE.append(step(
    "flirt · convert_xfm", "FSL",
    "<p>Compute the linear alignments between diffusion, T1, and MNI space, and invert the set. The one reused later is str2diff (T1 to diffusion), to bring the ROIs into the DWI grid.</p>",
    (2413, 2489)))
PRE.append(step(
    "Atropos · fslstats -V", "ANTs · FSL",
    "<p>Estimate intracranial volume: segment the T1 into CSF/GM/WM and sum. ICV is a covariate so a finding isn't just about head size.</p>",
    (2547, 2617)))
PRE.append(step(
    "pyAFQ BIDS prep", "pyAFQ",
    "<p>We briefly organized the data into BIDS layout to try pyAFQ's automated tractography. No imaging math happened here (copying and renaming only). We ultimately went with MRtrix for tractography and kept pyAFQ only for its tract cleaning (Step 25).</p>"))
PRE.append(step(
    "mrconvert", "MRtrix3",
    "<p>Repackage the eddy-corrected DWI and mask into MRtrix's .mif format, which carries the gradient table inside the file header.</p>",
    (2859, 2911)))
PRE.append(step(
    "dwi2response (dhollander)", "MRtrix3",
    "<p>Estimate the response functions: the diffusion signal of a single perfectly-aligned fiber, plus GM and CSF. These are the reference shapes the deconvolution uses. Dhollander estimates all three from each subject's own data, no atlas.</p>",
    (2994, 3042)))
PRE.append(step(
    "responsemean", "MRtrix3",
    "<p>Average every subject's three response functions into one shared group set, so later differences reflect biology rather than per-subject response noise.</p>",
    (3128, 3156)))
PRE.append(step(
    "dwi2fod (msmt_csd)", "MRtrix3",
    "<p>The core fiber model. MSMT-CSD decomposes each voxel's signal into a fiber orientation distribution using all shells and the group responses. The white-matter FOD is what streamlines grow from.</p>",
    (3243, 3296)))
PRE.append(step(
    "mtnormalise", "MRtrix3",
    "<p>Rescale the FODs so intensities are comparable across tissues and people (correcting scanner drift, coil sensitivity). The normalized WM FOD is the final input to tractography.</p>",
    (3387, 3444)))

# ==================================================== TRACTOGRAPHY
PROV = ('<div class="callout"><b>The three ROI inputs</b> (from Ranesh Mopuru, Olson lab; all MNI space). '
        'Seed = VTA, Pauli atlas at 25%. Target = hippocampus, Harvard-Oxford at 50%. '
        'Tract atlas = his VTA-HPC group mean, built from ~170 HCP 7T subjects, used to build the exclusion corridor.</div>')
TRACT = [sub("Fiber drawing"), PROV]
TRACT.append(step(
    "antsRegistrationSyNQuick.sh", "ANTs (SyN)",
    "<p>The ROIs live in MNI space; tracking has to happen in each subject's diffusion space. First a nonlinear (SyN) warp of MNI to the subject's T1, needed because our T1s aren't already diffusion-aligned, unlike the HCP data the atlas came from.</p>",
    (3556, 3614)))
TRACT.append(step(
    "antsApplyTransforms · flirt", "ANTs · FSL",
    "<p>Push all six ROIs (VTA, hippocampus, tract atlas, both hemispheres) from MNI to T1 to diffusion, chaining the SyN warp then the str2diff matrix. Nearest-neighbor interpolation (binary masks), re-binarized after. Output per subject in CSD/&lt;subj&gt;/rois/, visually QC'd on the diffusion image.</p>",
    (3720, 3834),
    "All ROIs land in plausible anatomical positions on the diffusion image.",
    [("roi_qc_wholebrain_left_VTA.png", "Left VTA seed (Pauli 25%) warped to diffusion space, s1000."),
     ("roi_qc_zoomed_left_HPC.png", "Left hippocampus target (Harvard-Oxford 50%), zoomed."),
     ("roi_qc_zoomed_left_tract_atlas.png", "Left VTA-HPC tract atlas (Ranesh's HCP group mean) in diffusion space.")]))
TRACT.append(step(
    "fslmaths: exclusion mask", "FSL",
    "<p>Ranesh's original pipeline used 13 separate anatomical exclusion ROIs. His approved shortcut: take his group tract atlas, dilate it 2 voxels into a corridor, add the VTA and hippocampus, then invert, so allowed = the corridor and excluded = everything else. One mask instead of thirteen. This is also what lets us drop the FOD cutoff so low in the next step.</p>",
    (4007, 4091),
    "57/57 pass all 7 audit checks. Inclusion corridor 1,526 to 1,934 voxels (mean ~1,720), consistent across subjects. VTA and HPC fully contained."))
TRACT.append(step(
    "tckgen: FOD-cutoff test", "MRtrix3",
    "<p>The one tuned parameter: the FOD amplitude cutoff (when tracking stops). Ranesh used 0.06 at 7T; 3T is noisier, so we tested 0.1 / 0.08 / 0.06 / 0.01 on 5 pilot subjects, both hemispheres. Because the exclusion corridor already constrains tracking, the usual downside of a low cutoff (spurious fibers) doesn't apply, so we could go lower than expected.</p>"
    "<p>Runs hitting the 1000 target: <b>0.1</b> 2/10 (too strict for 3T); <b>0.08</b> ~5/10 (inconsistent, s606 L = 309); <b>0.06</b> 10/10; <b>0.01</b> 10/10 and about 5x more seed-efficient. Paths were virtually identical to 0.06 (same arc, length ~44 vs ~47 mm). The 0.01 TDI is slightly thicker, which the cleaning step then tightens below the 0.06 bundle anyway.</p>",
    (4213, 4387),
    "Cutoff 0.01 chosen for the full run. Ranesh confirmed it is robust with the atlas-based exclusion mask.",
    [("cutoff_compare_s169_l.png", "TDI at 0.06 (left) vs 0.01 (right), s169 left tract. Same VTA-HPC arc."),
     ("cutoff_stats_comparison.png", "Streamline counts and lengths across the 5 test subjects, four cutoffs.")]))
TRACT.append(step(
    "tckgen: full run (all 57)", "MRtrix3",
    "<p>Same command at production budget: 2,500 streamlines from up to 25M seed attempts, cutoff 0.01. Later repeated with a second (anterior) VTA-HPC atlas Ranesh provided, giving four tracts: posterior L/R and anterior L/R.</p>",
    (4535, 4648),
    "114/114 posterior runs hit 2,500 streamlines. Seed usage 511K to 2.03M (avg ~1.1M, about 4.4% of the cap), no subject near the budget. Anterior set: all 114 also hit 2,500."))
TRACT.append(sub("Cleaning"))
TRACT.append(step(
    "clean_bundle (Mahalanobis)", "pyAFQ",
    "<p>Prune anatomically implausible streamlines by Mahalanobis distance: anything more than 3 SD from the bundle's core shape, or 2 SD off in length, dropped over 5 rounds. Ported from Ranesh's cleaning script.</p>",
    (4781, 4913),
    "114/114 cleaned, retention 26.4% to 57.5% (avg ~39%), no bundle emptied. The cleaned 0.01 tract is tighter (length SD ~3.5-4.5 mm) than both the uncleaned 0.01 and the conservative 0.06 (~5-7 mm), which validates the permissive-cutoff plus cleaning approach.",
    [("cleaned_compare_s169_l.png", "s169 left: 0.06 conservative, 0.01 uncleaned, 0.01 cleaned. The cleaned 0.01 is the most focused."),
     ("cleaned_stats_comparison.png", "Length variability across test subjects; the cleaned 0.01 bars (green) are consistently lowest.")]))
TRACT.append(step(
    "tckmap: visual QC", "MRtrix3 · Python",
    "<p>For every cleaned tract, a track-density image overlaid on the mean b0 to eyeball the shape, with auto-flags for anything too sparse (&lt;50 voxels) or too diffuse (&gt;5000).</p>",
    (5053, 5197),
    "All 114 (and the anterior set) passed and show the expected VTA to hippocampus arc.",
    [("step26_qc_s169_left.png", "Cleaned left VTA-HPC TDI on mean b0, s169."),
     ("step26_qc_s0105_left.png", "Cleaned left VTA-HPC TDI on mean b0, s0105-pilot.")]))

# ==================================================== MICROSTRUCTURE
MICRO = [step(
    "afq_profile: FA", "dipy",
    "<p>Sample FA at 100 nodes evenly spaced along the tract. Every streamline is oriented the same way (via a QuickBundles centroid, so node 1 is always the same end), resampled to 100 points, and Gaussian-weighted (core streamlines count more). Analyses use the middle nodes (~25-75); the ends are dropped for partial-volume contamination. Ported from Ranesh's nodewise_noddi.py.</p>",
    (5476, 5610),
    "228 FA profiles (4 tracts x 57 subjects), zero skips. Each tract CSV is 5,701 rows (57 x 100 + header).",
    [("step27_fa_profile_s1000_posterior_l.png", "FA along the posterior left tract, s1000: peaks in deep WM (~0.53), drops toward HPC (0.29)."),
     ("step27_fa_profile_s1000_anterior_l.png", "FA along the anterior left tract, s1000: similar start, different late-tract shape.")])]
MICRO.append(step(
    "NODDI fit (modulated maps)", "AMICO",
    "<p>Fit NODDI on all shells with AMICO, giving three interpretable maps per voxel: NDI (neurite density), ODI (orientation dispersion), FWF (free-water fraction). We saved the modulated NDI/ODI (tissue-weighted partial-volume correction, per Parker et al. 2021), the version Ranesh used. FWF has no modulated version; the tissue-weighting is itself the correction. Config: bStep=200, b0_thr=100, doSaveModulatedMaps=True, doComputeRMSE=True.</p>",
    ("amico.util.fsl2scheme(bvals, bvecs, bStep=200)   # round b to nearest 200\n"
     "ae = amico.Evaluation(study_dir, subject)\n"
     "ae.set_model('NODDI')\n"
     "ae.load_data(dwi, scheme, mask, b0_thr=100)\n"
     "ae.generate_kernels(regenerate=True)\n"
     "ae.fit()\n"
     "ae.save_results()   # -> fit_NDI_modulated, fit_ODI_modulated, fit_FWF, fit_RMSE"),
    "57/57 pass, full set of NODDI outputs. 3 subjects hit a kernel-directory race on the parallel pass and were re-run serially."))
MICRO.append(step(
    "afq_profile: NDI · ODI · FWF", "dipy",
    "<p>The FA-profiling step again (identical orient plus Gaussian-weighted profiling, same helpers), applied to the three NODDI maps. This produces the main microstructure measurements the statistics use.</p>",
    ("# identical machinery to the FA step; only the sampled map changes:\n"
     "NDI = profile_metric('fit_NDI_modulated.nii.gz', sl_oriented)\n"
     "ODI = profile_metric('fit_ODI_modulated.nii.gz', sl_oriented)\n"
     "FWF = profile_metric('fit_FWF.nii.gz',           sl_oriented)"),
    "684 profiles (4 tracts x 57 subjects x 3 metrics), zero skips.",
    [("step30_NDI_profile_s1000_posterior_l.png", "NDI along the posterior left tract, s1000."),
     ("step30_ODI_profile_s1000_posterior_l.png", "ODI along the same tract: higher at the endpoints, low in deep WM."),
     ("step30_FWF_profile_s1000_posterior_l.png", "FWF: low in deep WM, climbs near the HPC end (CSF proximity).")]))
MICRO.append(step(
    "fslstats -k HPC -M", "FSL",
    "<p>One extra measurement for a control analysis: the mean NODDI value inside the hippocampus ROI itself (the region, not the pathway). Same Harvard-Oxford hippocampus warped to diffusion space. Lets us ask whether memory tracks the tract specifically or just hippocampal tissue in general.</p>",
    ("fslstats fit_NDI_modulated.nii.gz -k left_HPC_diff.nii.gz -M   # mean NDI, left HPC\n"
     "# repeated for ODI, FWF and the right hemisphere")))


def cat(name, desc, items, first=False):
    inner = "".join(items)
    op = " open" if first else ""
    return (f'<details class="catgroup"{op}><summary><span class="cname">{name}</span>'
            f'<span class="cdesc">{desc}</span></summary><div class="catbody">{inner}</div></details>')


HTML = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IMPACT · Pipeline</title>
<link rel="stylesheet" href="_pres.css">
</head><body>
<nav class="topnav">
  <span class="brand">IMPACT · <span>VTA→HPC</span> &amp; Motivated Memory</span>
  <a href="intro.html">Overview</a>
  <a href="background.html">Background</a>
  <a href="pipeline.html" class="active">Pipeline</a>
  <a href="analyses.html">Analyses</a>
  <a href="results_explorer.html" class="results">Results ↗</a>
</nav>
<div class="wrap">
  <h1>Pipeline</h1>
  <p class="lead">Preprocessing, tractography, and microstructure. The script and outputs for each step are behind it.</p>
  <p class="small">57 subjects, run in parallel on the Temple cluster inside tmux. Scripts are verbatim from the project <a href="https://github.com/DiffusionTensorImaging-Repos/SDN-IMPACT-DTI">ReadMe</a> (Steps 1–30); audit blocks omitted.</p>

  {cat('Preprocessing', 'standard cleanup + fiber model · MRtrix / FSL / ANTs', PRE, first=True)}
  {cat('Tractography', 'draw the VTA→HPC tract, then clean it · MRtrix3 / ANTs / pyAFQ', TRACT)}
  {cat('Microstructure', 'FA + NODDI along each tract · dipy / AMICO', MICRO)}

</div>
</body></html>
"""
OUT.write_text(HTML)
print(f"wrote {OUT} ({len(HTML)} bytes)")
