#!/usr/bin/env python3
"""
Build results_html/analyses.html — methods + the actual analysis scripts.

Each script sits under the section it belongs to (Script / Outputs drawers,
code embedded VERBATIM). Findings live in the Results panel.
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
        if s.startswith("#") or s.startswith('"""'):
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


s_recompute = step("recompute_dprime_all.py", "pandas · scipy",
    "<p>Recompute d′ straight from each mother's raw Encoding and Recall trials as a transparency check on the study's exported scores.</p>",
    "scripts/html_builders/recompute_dprime_all.py",
    "Matched the export: social r = 0.96, monetary r = 0.99.")
s_compliance = step("compliance_screen.py", "pandas",
    "<p>Pre-analysis gate: flag yes-to-everything responders (remember-rate ≥ 0.95), whose d′ is degenerate, and drop that condition.</p>",
    "scripts/compliance_screen.py",
    "Excludes s4210 from every memory outcome.")
s_bias = step("compute_bias_scores.py", "pandas",
    "<p>Build HitRateBias and FABias from the valence-coded counts, with the zero-valence rule.</p>",
    "scripts/compute_bias_scores.py",
    "The two bias scores per condition, written into the analysis tables.")
s_breakdown = step("dprime_breakdown.py", "pandas · scipy",
    "<p>Split each d′ into hit rate and false-alarm rate, paired social vs. monetary, under the same data-quality and compliance gates.</p>",
    "scripts/dprime_breakdown.py",
    "The hit / false-alarm breakdown above.")
s_buildcsv = step("build_analysis_csvs.py", "pandas",
    "<p>Assemble the 16 analysis tables (4 tracts × 4 metrics): one row per subject, with the outcomes, the 5 covariates, and the 100 node values.</p>",
    "scripts/build_analysis_csvs.py",
    "16 analysis-ready CSVs, the input to the permutation test.")
s_perm = step("permutation_one.R", "R",
    "<p>The node-wise test for one (tract, metric, outcome): fit full vs. reduced at each node, form clusters of adjacent significant nodes, and keep them by cluster-extent FWE against a Freedman-Lane null.</p>",
    "scripts/permutation_one.R",
    "Per-analysis nodewise, clusters, and summary CSVs.")
s_runperm = step("run_all_permutations.sh", "bash",
    "<p>Driver that loops the test over every outcome × tract × metric (96 analyses).</p>",
    "scripts/run_all_permutations.sh",
    "The full grid of result CSVs.")
s_hpc = step("hpc_analysis.py", "statsmodels",
    "<p>Predict each memory outcome from the mean NODDI inside the hippocampus ROI itself (matched, cross, and bilateral), same covariates, to separate a pathway effect from hippocampal tissue.</p>",
    "scripts/html_builders/hpc_analysis.py",
    "hpc_region_data.json, shown on the hippocampus Results page.")
s_lat = step("mid50_correlations.py", "pandas",
    "<p>Average each metric over the mid-tract nodes (25 to 74) and correlate left vs. right hemisphere, per subject.</p>",
    "scripts/mid50_correlations.py",
    "The L / R correlation table above.")

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
  <p class="lead">Memory was scored as accuracy (d′) and two positivity-bias scores, then tested node by node against each tract's microstructure.</p>

  <h2>Memory scoring</h2>
  <p>Per condition (social faces, monetary doors): one accuracy score and two positivity-bias scores.</p>

  <h3>Accuracy: d′</h3>
  <div class="formula"><span class="lbl">d′</span> = z(hit rate) − z(false-alarm rate)</div>
  <p class="small"><b>Hit rate</b> = proportion of items she chose that she later calls "remember." <b>False-alarm rate</b> = proportion of non-chosen foils she calls "remember." d′ is high when hits are common and false alarms rare.</p>
  {s_recompute}
  {s_compliance}

  <h3>Positivity bias: two scores</h3>
  <div class="two">
    <div class="formula"><span class="lbl">HitRateBias</span><br>= TrueMem<sub>pos</sub>/Total<sub>pos</sub> − TrueMem<sub>neg</sub>/Total<sub>neg</sub><br><span class="note">skew in <b>correct</b> memories</span></div>
    <div class="formula"><span class="lbl">FABias</span><br>= FalseMem<sub>pos</sub>/Total<sub>pos</sub> − FalseMem<sub>neg</sub>/Total<sub>neg</sub><br><span class="note">skew in <b>false</b> memories</span></div>
  </div>
  <p class="small">Zero-valence rule: a 0/0 term is set to 0 (defined, maximally positive) rather than dropping the subject.</p>
  {s_bias}

  <h3>The scores</h3>
  <table class="dtable"><thead><tr><th>Score</th><th>Social</th><th>Monetary</th><th>n</th></tr></thead><tbody>
    <tr><td>d′</td><td>0.10 ± 0.29</td><td>0.22 ± 0.33</td><td>52 / 53</td></tr>
    <tr><td>HitRateBias</td><td>+0.12 ± 0.19</td><td>+0.12 ± 0.16</td><td>52 / 53</td></tr>
    <tr><td>FABias</td><td>+0.07 ± 0.19</td><td>+0.07 ± 0.16</td><td>52 / 53</td></tr>
  </tbody></table>

  <h3>Is memory above chance?</h3>
  <table class="dtable"><thead><tr><th>Condition</th><th>mean d′</th><th>t vs 0</th><th>p</th></tr></thead><tbody>
    <tr><td>Social</td><td>+0.098</td><td>2.47</td><td class="sig">0.017</td></tr>
    <tr><td>Monetary</td><td>+0.215</td><td>4.77</td><td class="sig">&lt;0.001</td></tr>
  </tbody></table>
  <p>Both above chance. Social and monetary d′ are uncorrelated (r = -0.15, p = 0.29): distinct abilities.</p>

  <h3>Why social d′ is lower</h3>
  <table class="dtable"><thead><tr><th>Component</th><th>Social</th><th>Monetary</th><th>paired test</th></tr></thead><tbody>
    <tr><td>Hit rate</td><td>0.560</td><td>0.539</td><td>p = 0.395</td></tr>
    <tr><td>False-alarm rate</td><td>0.527</td><td>0.460</td><td class="sig">p = 0.008</td></tr>
    <tr><td>d′</td><td>0.098</td><td>0.218</td><td>p = 0.073</td></tr>
  </tbody></table>
  <p>Hit rates are equal; the social task just produces more false alarms. The lower social d′ is more false positives, not weaker memory, which is exactly where the social signal lives.</p>
  {s_breakdown}

  <h3>How the scores relate</h3>
  <table class="dtable"><thead><tr><th>Pair</th><th>r</th><th>p</th></tr></thead><tbody>
    <tr><td>Social d′ × Monetary d′</td><td>-0.15</td><td>0.29</td></tr>
    <tr><td>HitRateBias: social × monetary</td><td class="sig">+0.40</td><td class="sig">0.004</td></tr>
    <tr><td>Social d′ × Social HitRateBias</td><td>+0.28</td><td>0.043</td></tr>
  </tbody></table>

  <h2>The tract test</h2>
  <p>Six outcomes (social and monetary × d′, HitRateBias, FABias) tested against each tract's along-node microstructure, for all four metrics, plus the hippocampus region.</p>

  <h3>Model, per node</h3>
  <p>At each of the 100 nodes, the outcome on that node's microstructure value plus five covariates: ICV, tract streamline count and mean length, head motion, and maternal age.</p>
  <div class="formula"><span class="lbl">full</span>&nbsp;&nbsp;&nbsp; y ~ node + ICV + Mean_tckstats + Count_tckstats + absolute_motion + maternal_age<br><span class="lbl">reduced</span>&nbsp; y ~ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ICV + Mean_tckstats + Count_tckstats + absolute_motion + maternal_age</div>
  {s_buildcsv}

  <h3>Correction: cluster-extent FWE</h3>
  <p>Adjacent significant nodes form a cluster; the null is a Freedman-Lane permutation (shuffle the reduced-model residuals, refit all 100 nodes, 5,000 times), and a cluster is kept only if it beats 95% of the chance clusters. Run across 96 analyses.</p>
  {s_perm}
  {s_runperm}

  <h3>Within the hippocampus</h3>
  <p>The same framework, but predicting memory from the mean NODDI inside the hippocampus ROI itself instead of along the tract, to separate a pathway effect from hippocampal tissue.</p>
  {s_hpc}

  <h3>Check: hemisphere consistency</h3>
  <p>Left and right tracts should measure the same thing. Mid-tract (nodes 25 to 74) averages correlated across hemispheres (n = 57):</p>
  <table class="dtable"><thead><tr><th>Tract</th><th>FA</th><th>NDI</th><th>ODI</th><th>FWF</th></tr></thead><tbody>
    <tr><td>Posterior VTA→HPC</td><td>0.52</td><td>0.86</td><td>0.88</td><td>0.70</td></tr>
    <tr><td>Anterior VTA→HPC</td><td>0.53</td><td>0.81</td><td>0.80</td><td>0.70</td></tr>
  </tbody></table>
  <figure class="fig"><img src="../images/lr_scatterplots_mid50.png" alt="Left versus right hemisphere scatterplots, mid-tract node averages" loading="lazy"><figcaption>Each point a subject; dashed line is identity. Top row posterior, bottom row anterior.</figcaption></figure>
  {s_lat}

</div>
</body></html>
"""
OUT.write_text(HTML)
print(f"wrote {OUT} ({len(HTML)} bytes)")
