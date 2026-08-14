#!/usr/bin/env python3
"""
Build results_html/analyses.html — the presentation Analyses page.

Methods + the actual analysis scripts (embedded VERBATIM from the repo), organized
with Script / Outputs drawers like the Pipeline page. Study findings live in the
Results panel, not here.
"""
from pathlib import Path
import html

ROOT = Path("/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI")
OUT = ROOT / "results_html" / "analyses.html"


def code(relpath):
    raw = (ROOT / relpath).read_text().rstrip("\n")
    out = []
    for ln in raw.split("\n"):
        e = html.escape(ln)
        s = ln.lstrip()
        if s.startswith("#") or s.startswith('"""') or s.startswith("# "):
            e = f'<span class="c">{e}</span>'
        out.append(e)
    return "<pre>" + "\n".join(out) + "</pre>"


def step(cmd, pkg, info, relpath, result=None):
    ob = info + (f'<div class="lead-lbl">Produces</div><p class="res">{result}</p>' if result else "")
    return (f'<div class="step"><div class="stephead"><span class="cmd">{cmd}</span>'
            f'<span class="pkg">{pkg}</span></div><div class="drawers">'
            f'<details class="drawer"><summary>Script</summary><div class="drawerbody">{code(relpath)}</div></details>'
            f'<details class="drawer"><summary>Outputs</summary><div class="drawerbody">{ob}</div></details>'
            f'</div></div>')


MEM_SCRIPTS = (
    step("recompute_dprime_all.py", "pandas · scipy",
         "<p>Recompute d′ straight from each mother's raw Encoding and Recall trial files (build the set of faces she chose vs. saw-but-did-not-choose, count remember responses, d′ = z(hit) − z(FA)) as a transparency check on the study's exported scores.</p>",
         "scripts/html_builders/recompute_dprime_all.py",
         "Recompute vs. export matched closely: social r = 0.96, monetary r = 0.99.")
    + step("compliance_screen.py", "pandas",
         "<p>A pre-analysis data-quality gate. Flags yes-to-everything responders (pressed remember to essentially every item, old and new), whose d′ is degenerate. Rule: exclude a condition at a remember-rate of 0.95 or higher.</p>",
         "scripts/compliance_screen.py",
         "Excludes s4210 (100% remember on both tasks) from every memory outcome, before the tract analyses.")
    + step("compute_bias_scores.py", "pandas",
         "<p>Build the two positivity-bias scores from the valence-coded counts, applying the zero-valence rule (a 0/0 term is set to 0 rather than dropping the subject). Valid only where that condition's d′ is valid.</p>",
         "scripts/compute_bias_scores.py",
         "HitRateBias and FABias per condition, written into the 16 analysis tables.")
    + step("dprime_breakdown.py", "pandas · scipy",
         "<p>Split each d′ into its hit rate and false-alarm rate and paired-compare social vs. monetary, under the same data-quality and compliance gates as the analysis.</p>",
         "scripts/dprime_breakdown.py",
         "The hit / false-alarm breakdown above (hits equal; social false-alarms higher).")
)

ANALYSIS_SCRIPTS = (
    step("build_analysis_csvs.py", "pandas",
         "<p>Assemble the 16 analysis tables (4 tracts × 4 metrics). Each row is a subject; columns are the outcomes, the 5 covariates, and the 100 along-tract node values, merged from the node-profile CSVs, REDCap, and the imaging covariates.</p>",
         "scripts/build_analysis_csvs.py",
         "16 analysis-ready CSVs, the input to the permutation test.")
    + step("permutation_one.R", "R",
         "<p>The node-wise test for one (tract, metric, outcome). At each of 100 nodes it fits the full vs. reduced model and records the t on the node term; adjacent significant nodes form clusters; the null is the Freedman-Lane permutation (shuffle reduced-model residuals, refit, 5,000 times) and clusters are kept by cluster-extent FWE.</p>",
         "scripts/permutation_one.R",
         "Per-analysis nodewise, clusters, and summary CSVs. Surviving clusters are in the Results browser.")
    + step("run_all_permutations.sh", "bash",
         "<p>Driver that loops permutation_one.R over every outcome × tract × metric. Across the memory and bias outcomes this is 6 × 4 × 4 = 96 analyses, one core each.</p>",
         "scripts/run_all_permutations.sh",
         "The full grid of per-analysis result CSVs.")
    + step("hpc_analysis.py", "statsmodels",
         "<p>The hippocampus control: predict each memory outcome from the mean NODDI inside the hippocampus ROI itself (matched, cross, and bilateral hemispheres), with the same nuisance covariates, to separate a pathway effect from generic hippocampal tissue.</p>",
         "scripts/html_builders/hpc_analysis.py",
         "hpc_region_data.json, shown on the hippocampus Results page.")
    + step("mid50_correlations.py", "pandas",
         "<p>Average each metric over the mid-tract nodes (25 to 74) and correlate left vs. right hemisphere, per subject, as the lateralization check.</p>",
         "scripts/mid50_correlations.py",
         "The L / R correlation table above.")
)

HTML = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IMPACT · Analyses</title>
<link rel="stylesheet" href="_pres.css">
</head><body>
<nav class="topnav">
  <span class="brand">IMPACT · <span>VTA→HPC</span> &amp; Motivated Memory</span>
  <a href="intro.html">Overview</a>
  <a href="background.html">Background</a>
  <a href="pipeline.html">Pipeline</a>
  <a href="analyses.html" class="active">Analyses</a>
  <a href="results_explorer.html" class="results">Results ↗</a>
</nav>
<div class="wrap">
  <h1>Analyses</h1>
  <p class="lead">The RAFT feedback-memory task, how the memory outcomes are scored from it, and how each is tested against the along-tract microstructure. The findings themselves live in the <a href="results_explorer.html">Results</a> browser.</p>

  <h2>The task</h2>
  <p>On each encoding trial a pair of stimuli appears and the mother chooses one; her choice is followed by valenced feedback: a positive (green) or negative (red) outcome, or a neutral one. Two domains are interleaved: <b>faces</b> (social) and <b>doors</b> (monetary). A later surprise recognition test presents old and new stimuli and asks which she saw, and memory is scored from that test.</p>
  <figure class="fig"><img src="../images/raft_task.jpg" alt="RAFT task schematic: face pairs (social) and door pairs (monetary), each choice followed by positive, negative, or neutral feedback" loading="lazy"><figcaption>The RAFT task. Faces (social, left) and doors (monetary, right); each chosen pair returns a green (positive), red (negative), or neutral (empty) outcome.</figcaption></figure>

  <h2>1 · Calculating memory</h2>
  <p>From the feedback task, each mother gets, per condition (social faces, monetary doors), one accuracy score and two positivity-bias scores.</p>

  <h3>Accuracy: d′</h3>
  <div class="formula"><span class="lbl">d′</span> = z(hit rate) − z(false-alarm rate)<br><span class="note">z is the inverse-normal. Higher d′ means better discrimination of chosen items from foils.</span></div>
  <p class="small"><b>Hit rate</b> is the proportion of items she chose during the task that she later calls "remember" (correct). <b>False-alarm rate</b> is the proportion of non-chosen foils she calls "remember" (incorrect). d′ is high when hits are common and false alarms are rare.</p>

  <h3>Positivity bias: two scores</h3>
  <div class="two">
    <div class="formula"><span class="lbl">HitRateBias</span><br>= TrueMem<sub>pos</sub>/Total<sub>pos</sub> − TrueMem<sub>neg</sub>/Total<sub>neg</sub><br><span class="note">positivity skew in <b>correct</b> memories</span></div>
    <div class="formula"><span class="lbl">FABias</span><br>= FalseMem<sub>pos</sub>/Total<sub>pos</sub> − FalseMem<sub>neg</sub>/Total<sub>neg</sub><br><span class="note">positivity skew in <b>false</b> memories</span></div>
  </div>
  <p class="small">Zero-valence rule: a term whose denominator is 0 (a mother who produced no memories of one valence) is set to 0, giving her a defined, maximally-positive score rather than dropping her. Compliance is screened first, so it never rescues a yes-to-everything responder.</p>

  <h3>The scores across mothers</h3>
  <table class="dtable"><thead><tr><th>Score</th><th>Social, M ± SD</th><th>Monetary, M ± SD</th><th>n</th></tr></thead><tbody>
    <tr><td>d′ (accuracy)</td><td>0.10 ± 0.29</td><td>0.22 ± 0.33</td><td>52 / 53</td></tr>
    <tr><td>HitRateBias</td><td>+0.12 ± 0.19</td><td>+0.12 ± 0.16</td><td>52 / 53</td></tr>
    <tr><td>FABias</td><td>+0.07 ± 0.19</td><td>+0.07 ± 0.16</td><td>52 / 53</td></tr>
  </tbody></table>

  <h3>Is memory above chance?</h3>
  <table class="dtable"><thead><tr><th>Condition</th><th>mean d′</th><th>t vs 0</th><th>p</th><th>verdict</th></tr></thead><tbody>
    <tr><td>Social</td><td>+0.098</td><td>2.47</td><td class="sig">0.017</td><td>above chance</td></tr>
    <tr><td>Monetary</td><td>+0.215</td><td>4.77</td><td class="sig">&lt;0.001</td><td>above chance</td></tr>
  </tbody></table>
  <p>Both are above chance. Social and monetary d′ are also uncorrelated at the subject level (r = -0.15, p = 0.29): they are distinct abilities, not two views of one signal.</p>

  <h3>Why is social d′ lower than monetary?</h3>
  <p>d′ has two ingredients: the hit rate (memory strength) and the false-alarm rate (false positives). Splitting them shows the difference is entirely in false alarms.</p>
  <table class="dtable"><thead><tr><th>Component</th><th>Social</th><th>Monetary</th><th>diff (S−M)</th><th>paired test</th><th>differ?</th></tr></thead><tbody>
    <tr><td>Hit rate</td><td>0.560</td><td>0.539</td><td>+0.021</td><td>t=0.86, p=0.395</td><td>no</td></tr>
    <tr><td>False-alarm rate</td><td>0.527</td><td>0.460</td><td>+0.067</td><td>t=2.77, p=0.008</td><td class="sig">yes</td></tr>
    <tr><td>d′</td><td>0.098</td><td>0.218</td><td>−0.119</td><td>t=−1.83, p=0.073</td><td>no</td></tr>
  </tbody></table>
  <p>Social and monetary items are remembered equally well; hit rates are essentially identical (0.56 vs 0.54, p = 0.40). The only difference is that the social task produces significantly more false alarms (0.527 vs 0.460, p = 0.008). So the lower social d′ is not weaker memory, it is more false positives, which is exactly where the social signal lives.</p>

  <h3>How the scores relate</h3>
  <table class="dtable"><thead><tr><th>Pair</th><th>r</th><th>p</th><th>reading</th></tr></thead><tbody>
    <tr><td>Social d′ × Monetary d′</td><td>-0.15</td><td>0.29</td><td>independent abilities</td></tr>
    <tr><td>HitRateBias: social × monetary</td><td class="sig">+0.40</td><td class="sig">0.004</td><td>positivity in correct memories is trait-like across domains</td></tr>
    <tr><td>Social d′ × Social HitRateBias</td><td>+0.28</td><td>0.043</td><td>better social accuracy goes with more positive correct memories</td></tr>
    <tr><td>d′ × FABias (within domain)</td><td>≈ -0.13</td><td>ns</td><td>accuracy unrelated to false-memory skew</td></tr>
  </tbody></table>

  <div class="subhead">Scripts</div>
  {MEM_SCRIPTS}

  <h2>2 · Analyses</h2>
  <p>Six outcomes (social and monetary × d′, HitRateBias, FABias) tested against each tract's along-node microstructure, for all four metrics, plus a hippocampus-region control.</p>

  <h3>Model, per node</h3>
  <p>At each of the 100 nodes, a linear model of the outcome on that node's microstructure value plus five nuisance covariates: ICV, tract streamline count and mean length (so a result is not just a bigger or denser tract), head motion, and maternal age.</p>
  <div class="formula"><span class="lbl">full</span>&nbsp;&nbsp;&nbsp; y ~ node + ICV + Mean_tckstats + Count_tckstats + absolute_motion + maternal_age<br><span class="lbl">reduced</span>&nbsp; y ~ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ICV + Mean_tckstats + Count_tckstats + absolute_motion + maternal_age</div>

  <h3>Correction: cluster-extent FWE by permutation</h3>
  <p>Neighboring significant nodes form a cluster. To keep 100 tests from inflating false positives, the null is built by Freedman-Lane permutation: take the reduced model's residuals, shuffle them, re-run all 100 nodes, 5,000 times, recording the largest chance cluster each time. An observed cluster counts only if it beats 95% of those. Run across 6 outcomes × 4 tracts × 4 metrics = 96 analyses.</p>

  <h3>Hippocampus control</h3>
  <p>The same framework, but predicting memory from the mean NODDI inside the hippocampus ROI itself (hemisphere-matched, same covariates) instead of along the tract. This separates a pathway effect from generic hippocampal tissue. Results on the <a href="hpc_region_vs_connection.html">hippocampus page</a>.</p>

  <h3>Check: hemisphere consistency (lateralization)</h3>
  <p>Left and right tracts should be measuring the same thing. Correlating the mid-tract (nodes 25 to 74) average of each metric across hemispheres, per subject (n = 57):</p>
  <table class="dtable"><thead><tr><th>Tract</th><th>FA</th><th>NDI</th><th>ODI</th><th>FWF</th></tr></thead><tbody>
    <tr><td>Posterior VTA→HPC</td><td>0.52</td><td>0.86</td><td>0.88</td><td>0.70</td></tr>
    <tr><td>Anterior VTA→HPC</td><td>0.53</td><td>0.81</td><td>0.80</td><td>0.70</td></tr>
  </tbody></table>
  <figure class="fig"><img src="../images/lr_scatterplots_mid50.png" alt="Left versus right hemisphere scatterplots, mid-tract node averages" loading="lazy"><figcaption>Each point is a subject; dashed line is identity, red is best-fit. Top row posterior, bottom row anterior.</figcaption></figure>
  <p>Neurite density and orientation dispersion are highly consistent across hemispheres (r ≈ 0.80 to 0.88); free water is moderate (≈ 0.70); FA is noisier (≈ 0.52).</p>

  <div class="subhead">Scripts</div>
  {ANALYSIS_SCRIPTS}

  <p class="small" style="margin-top:24px">Findings: <a href="results_explorer.html">Results browser</a> · <a href="data_quality.html">data quality</a> · <a href="hpc_region_vs_connection.html">hippocampus</a></p>
</div>
</body></html>
"""

OUT.write_text(HTML)
print(f"wrote {OUT} ({len(HTML)} bytes)")
