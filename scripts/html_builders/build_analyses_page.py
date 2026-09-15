#!/usr/bin/env python3
"""
Build results_html/analyses.html: the analysis funnel, with every script embedded verbatim under
the step it belongs to. Everything that was run (node-wise, quartiles, whole tract, four metrics,
two subregions), then how it narrowed, then what is reported. Numbers for the model tables come
from results_html/models_data.json and results_data.json (build_results_data.py).
"""
from pathlib import Path
import html, json

ROOT = Path("/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI")
OUT = ROOT / "results_html" / "analyses.html"
MODELS = json.load(open(ROOT / "results_html" / "models_data.json"))
DATA = json.load(open(ROOT / "results_html" / "results_data.json"))
ORDER = ['Social FABias', 'Social d′', 'Social misattribution', 'Monetary FABias', 'Monetary d′', 'Monetary misattribution']
NICE = {'Social FABias': 'Social positive FA bias', 'Monetary FABias': 'Monetary positive FA bias'}


def code(relpath):
    raw = (ROOT / relpath).read_text().rstrip("\n")
    out = []
    for ln in raw.split("\n"):
        e = html.escape(ln); s = ln.lstrip()
        if s.startswith("#") or s.startswith('"""'): e = f'<span class="c">{e}</span>'
        out.append(e)
    return "<pre>" + "\n".join(out) + "</pre>"


def step(cmd, pkg, info, relpath, result=None):
    ob = info + (f'<div class="lead-lbl">Produces</div><p class="res">{result}</p>' if result else "")
    return (f'<div class="step"><div class="stephead"><span class="cmd">{cmd}</span><span class="pkg">{pkg}</span></div><div class="drawers">'
            f'<details class="drawer"><summary>Script</summary><div class="drawerbody">{code(relpath)}</div></details>'
            f'<details class="drawer"><summary>Outputs</summary><div class="drawerbody">{ob}</div></details></div></div>')


def pcell(p, star=True):
    if p is None: return '<td>—</td>'
    s = f'{p:.3f}'.replace('0.', '.', 1) if p >= .001 else '&lt;.001'
    return f'<td class="sig">{s}{" *" if star else ""}</td>' if p < .05 else f'<td>{s}</td>'


def rows(a, metric=None, seg=None):
    return [r for r in MODELS if r['analysis'] == a and (metric is None or r['metric'] == metric) and (seg is None or r['segment'] == seg)]


def whole():
    h = '<table class="dtable"><thead><tr><th>Outcome</th><th>Interaction p</th><th>Main effect b</th><th>Main effect p</th></tr></thead><tbody>'
    for o in ORDER:
        r = next(x for x in rows('whole_tract') if x['outcome'] == o)
        h += f'<tr><td>{NICE.get(o,o)}</td>{pcell(r["interaction_p"],False)}<td>{r["main_b"]:+.3f}</td>{pcell(r["main_p"])}</tr>'
    return h + '</tbody></table>'


def quart(key):
    h = f'<table class="dtable"><thead><tr><th>Outcome</th><th>Q1</th><th>Q2</th><th>Q3</th><th>Q4</th><th>Whole</th></tr></thead><tbody>'
    for o in ORDER:
        c = ''.join(pcell(next(x for x in rows('quartile','NDI',s) if x['outcome']==o)[key], key=='main_p') for s in ['Q1','Q2','Q3','Q4'])
        c += pcell(next(x for x in rows('whole_tract') if x['outcome']==o)[key], key=='main_p')
        h += f'<tr><td>{NICE.get(o,o)}</td>{c}</tr>'
    return h + '</tbody></table>'


def metric():
    h = '<table class="dtable"><thead><tr><th>Main-effect p</th><th>NDI</th><th>ODI</th><th>FWF</th><th>FA</th></tr></thead><tbody>'
    for o in ORDER:
        c = ''.join(pcell(next(x for x in rows('metric',m) if x['outcome']==o)['main_p']) for m in ['NDI','ODI','FWF','FA'])
        h += f'<tr><td>{NICE.get(o,o)}</td>{c}</tr>'
    return h + '</tbody></table>'


def hpc():
    h = '<table class="dtable"><thead><tr><th>Outcome</th><th>β</th><th>p</th></tr></thead><tbody>'
    for o in ORDER:
        r = next(x for x in rows('hpc_gm_ndi') if x['outcome'] == o)
        h += f'<tr><td>{NICE.get(o,o)}</td><td>{r["main_b"]:+.3f}</td>{pcell(r["main_p"])}</tr>'
    return h + '</tbody></table>'


def hvlt():
    h = '<table class="dtable"><thead><tr><th>HVLT</th><th>b</th><th>p</th><th>n</th></tr></thead><tbody>'
    for r in rows('hvlt'):
        h += f'<tr><td>{r["outcome"]}</td><td>{r["main_b"]:+.3f}</td>{pcell(r["main_p"])}<td>{r["n"]}</td></tr>'
    return h + '</tbody></table>'


def nodewise():
    lab = {'dprime_loglinear': "d′", 'fa_adjCriterion': 'misattribution', 'FABias': 'positive FA bias'}
    h = '<table class="dtable"><thead><tr><th>Outcome (NDI)</th><th>VTA→anterior hippocampus</th><th>VTA→posterior hippocampus</th></tr></thead><tbody>'
    for cond in ['SOCIAL', 'MONETARY']:
        for meas in ['FABias', 'dprime_loglinear', 'fa_adjCriterion']:
            cells = ''
            for tract in ['vta_anthipp', 'vta_posthipp']:
                r = next(x for x in DATA if x['tract']==tract and x['metric']=='NDI' and x['condition']==cond and x['measure']==meas)
                c = next((c for c in r['clusters'] if c['passes']), None)
                cells += (f'<td class="sig">p = {c["p"]:.3f}, nodes {c["start"]}–{c["end"]}, {c["dir"].lower()}</td>'.replace('0.', '.', 1) if c
                          else f'<td class="mut">ns ({r["obs_max_cluster"]} / {r["extent_threshold"]})</td>')
            h += f'<tr><td>{cond.title()} {lab[meas]}</td>{cells}</tr>'
    return h + '</tbody></table>'


S = dict(
 dprime=step("dprime_corrections.py", "pandas · scipy",
   "<p>d′ from each mother's raw trials with the log-linear correction (0.5 added to each count, 1 to each total), so boundary hit or false-alarm rates stay finite. Snodgrass–Corwin is computed alongside as a check.</p>",
   "scripts/dprime_corrections.py", "Corrected d′ per condition; the two corrections agree at r = .998."),
 misattrib=step("misattribution_scores.py", "pandas · statsmodels",
   "<p>False-alarm rate residualized on the response criterion c, so the score is claiming feedback from someone who never gave it, net of overall willingness to say remember.</p>",
   "scripts/misattribution_scores.py", "Misattribution per condition."),
 bias=step("compute_bias_scores.py", "pandas",
   "<p>Positive minus negative rate, separately for false memories (FABias) and correct memories (HitRateBias), with the zero-valence rule for mothers who never used one valence.</p>",
   "scripts/compute_bias_scores.py", "The two bias scores per condition."),
 compliance=step("compliance_screen.py", "pandas",
   "<p>Pre-analysis gate: any condition with a remember rate of 95% or more is a yes-to-everything response set with no discrimination, and is dropped.</p>",
   "scripts/compliance_screen.py", "Excludes s4210 from every memory outcome."),
 binomial=step("binomial_test.py", "scipy",
   "<p>Per-subject binomial test of recognition against chance, one-sided.</p>",
   "scripts/binomial_test.py", "2 of 54 clear individually on social, 9 of 54 on monetary, none on both. At a median of 83 trials the per-subject test has almost no resolution."),
 breakdown=step("dprime_breakdown.py", "pandas · scipy",
   "<p>Split d′ into hit rate and false-alarm rate and compare social against monetary, paired, under the same data-quality gates.</p>",
   "scripts/dprime_breakdown.py", "The hit / false-alarm table above."),
 biascmp=step("bias_comparisons.py", "pandas · scipy",
   "<p>Social against monetary bias, paired; each bias split into its positive and negative rate; and total bias, the proportion of all reported memories that were positive.</p>",
   "scripts/bias_comparisons.py", "The tables above; data.check/bias_comparisons.csv."),
 bilat=step("build_bilateral_csvs.py", "pandas",
   "<p>Average the left and right 100-node profiles per subject after verifying they are aligned end to end; sum streamline count, average length. One CSV per tract × metric.</p>",
   "scripts/build_bilateral_csvs.py", "data.check/analysis_ready_bilateral/vta_{anthipp,posthipp}__{NDI,ODI,FWF,FA}__analysis.csv"),
 mid50=step("mid50_correlations.py", "pandas",
   "<p>Average each metric over the mid-tract nodes (25 to 74) and correlate left against right, per subject.</p>",
   "scripts/mid50_correlations.py", "The L / R correlation table above."),
 lrplot=step("lr_scatterplots.py", "matplotlib",
   "<p>The scatterplots above.</p>", "scripts/lr_scatterplots.py", "images/lr_scatterplots_mid50.png"),
 perm=step("permutation_one.R", "R",
   "<p>The node-wise test for one tract × metric × outcome: full against reduced model at each node, contiguous significant nodes form clusters, clusters kept by cluster-extent FWE against 5000 Freedman–Lane permutations.</p>",
   "scripts/permutation_one.R", "Per-analysis nodewise, clusters and summary CSVs."),
 runner=step("run_perm_cr2.sh", "bash",
   "<p>Runs every tract × metric × outcome in parallel on the cluster, one core each.</p>",
   "scripts/run_perm_cr2.sh", "data.check/sweep_withcount/ and data.check/bilateral_perm_results/"),
 final=step("final_models.py", "statsmodels",
   "<p>Whole-tract and quartile mixed models with both subregions and a subregion term; the same whole-tract model for ODI, FWF and FA; hippocampal gray-matter NDI; HVLT. Every table in this page's model sections comes from this script.</p>",
   "scripts/final_models.py", "data.check/final_models_summary.csv"),
 gm=step("run_noddi_gm.py", "AMICO",
   "<p>NODDI refit inside the hippocampal ROI at the gray-matter intrinsic parallel diffusivity, 1.1e-3 mm²/s, instead of the white-matter default of 1.7e-3.</p>",
   "scripts/run_noddi_gm.py", "Bilateral hippocampal NDI, ODI, FWF per subject (Impact-Analyses/hpc_density_gm.csv)."),
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
  <p class="lead">Everything that was run, in the order it narrowed: three spatial resolutions, four microstructure metrics, two hippocampal subregions, two feedback domains. Then the three decisions that reduce it to one bilateral pathway, one metric, and three social effects.</p>
  <p class="small">n = 52 social (faces), 53 monetary (doors). Covariates in every tract model: ICV, tract length, streamline count, absolute head motion, maternal age. * p &lt; .05.</p>

  <h2>Memory scoring</h2>
  <p>Three outcomes per domain, computed from each mother's raw trial files after two screens: broken recall sessions (s1694, s1350 social) and a compliance gate for yes-to-everything responding (s4210).</p>
  <h3>Accuracy: d′</h3>
  <div class="formula"><span class="lbl">d′</span> = z(hit rate) − z(false-alarm rate) <span class="note">log-linear corrected</span></div>
  {S['dprime']}
  {S['compliance']}
  <h3>Misattribution</h3>
  <div class="formula"><span class="lbl">misattribution</span> = residual of false-alarm rate on criterion c <span class="note">false memories net of response bias</span></div>
  {S['misattrib']}
  <h3>Positivity bias</h3>
  <div class="two">
    <div class="formula"><span class="lbl">FABias</span><br>= FA rate<sub>pos</sub> − FA rate<sub>neg</sub><br><span class="note">skew in <b>false</b> memories</span></div>
    <div class="formula"><span class="lbl">HitRateBias</span><br>= hit rate<sub>pos</sub> − hit rate<sub>neg</sub><br><span class="note">skew in <b>correct</b> memories</span></div>
  </div>
  <p class="small">Positive and negative refer to how she remembered each item. Total bias, used below, is simply the proportion of all reported memories that were positive.</p>
  {S['bias']}

  <h2>Is memory real?</h2>
  <p>The task is hard and d′ is small. Pooled across mothers, memory is above chance on every test.</p>
  <table class="dtable"><thead><tr><th>Test</th><th>Faces (social)</th><th>Doors (monetary)</th></tr></thead><tbody>
    <tr><td>Recognition accuracy vs 50%</td><td>51.5%, <span class="sig">p = .023</span></td><td>53.9%, <span class="sig">p &lt; .001</span></td></tr>
    <tr><td>Correct feedback among recognized items vs 33%</td><td>37.2%, <span class="sig">p = .003</span></td><td>38.2%, <span class="sig">p = .0003</span></td></tr>
    <tr><td>d′ vs 0</td><td>+0.088, <span class="sig">p = .018</span> (n = 52)</td><td>+0.208, <span class="sig">p &lt; .001</span> (n = 53)</td></tr>
    <tr><td>RT, recognized vs correctly rejected</td><td>1679 vs 1800 ms, −121 ms, <span class="sig">p = .0008</span></td><td>1640 vs 1749 ms, −109 ms, <span class="sig">p = .0003</span></td></tr>
    <tr><td>RT, named feedback correctly vs wrong</td><td>1640 vs 1680 ms, −40 ms, p = .119</td><td>1598 vs 1658 ms, −59 ms, <span class="sig">p = .011</span></td></tr>
  </tbody></table>
  {S['binomial']}
  <h3>Social vs monetary</h3>
  <table class="dtable"><thead><tr><th>Component</th><th>Social</th><th>Monetary</th><th>Differ?</th></tr></thead><tbody>
    <tr><td>Hit rate</td><td>0.556</td><td>0.538</td><td>no (p = .46)</td></tr>
    <tr><td>False-alarm rate</td><td>0.524</td><td>0.459</td><td class="sig">yes (p = .012)</td></tr>
    <tr><td>d′</td><td>+0.088</td><td>+0.208</td><td class="sig">yes (p = .048)</td></tr>
  </tbody></table>
  <p class="small">Paired, n = 52. Items are remembered equally well in both domains; the lower social d′ is more false alarms. Social and monetary d′ correlate at r = −.13 (p = .37).</p>
  {S['breakdown']}

  <h2>Behavioral bias</h2>
  <table class="dtable"><thead><tr><th>Reported memories</th><th>Positive</th><th>Negative</th><th>Neutral</th></tr></thead><tbody>
    <tr><td>Faces</td><td>58.5%</td><td>20.4%</td><td>21.1%</td></tr>
    <tr><td>Doors</td><td>57.9%</td><td>24.9%</td><td>17.2%</td></tr>
  </tbody></table>
  <p>Both far above the 33% baseline (p &lt; 1e-12) and not different from each other (p = .85). The accuracy-based scores agree: positive false-alarm bias above zero for faces (+.068, p = .013) and doors (+.072, p = .002); hit-rate bias stronger (+.121 and +.120, both p &lt; .0001); neither differs across domains (p = .82, .79). Each loads on the positive side (social: positive hit rate .334 vs negative .215, p = .0001; positive FA rate .305 vs negative .228, p = .005; monetary the same pattern). The bias is domain-general. Only its relation to microstructure is social-specific.</p>
  {S['biascmp']}

  <h2>Everything we ran</h2>
  <table class="dtable"><thead><tr><th></th><th>Node-wise (100 nodes)</th><th>Quartiles (4 × 25)</th><th>Whole tract</th></tr></thead><tbody>
    <tr><td class="mut">Model</td><td>per node, Freedman–Lane permutation, cluster-extent FWE</td><td>mixed model, both subregions, subregion term</td><td>mixed model, both subregions, subregion term</td></tr>
    <tr><td class="mut">Metrics</td><td>NDI, ODI, FWF, FA</td><td>NDI</td><td>NDI, ODI, FWF, FA</td></tr>
    <tr><td class="mut">Subregions</td><td>anterior, posterior separately</td><td>both in one model</td><td>both in one model</td></tr>
    <tr><td class="mut">Question</td><td>where along the tract</td><td>does it vary by segment or subregion</td><td>is there an effect; does subregion matter</td></tr>
  </tbody></table>

  <h3>Bilateral tracts</h3>
  <p>Left and right profiles were verified aligned before averaging (node 0 at the VTA, node 99 at the hippocampus; L[i] vs R[i] r = +.98 anterior, +.97 posterior, versus −.90 / −.95 if one side were flipped). Mid-tract averages correlate across hemispheres:</p>
  <table class="dtable"><thead><tr><th>Tract</th><th>FA</th><th>NDI</th><th>ODI</th><th>FWF</th></tr></thead><tbody>
    <tr><td>VTA→posterior hippocampus</td><td>0.52</td><td>0.86</td><td>0.88</td><td>0.70</td></tr>
    <tr><td>VTA→anterior hippocampus</td><td>0.53</td><td>0.81</td><td>0.80</td><td>0.70</td></tr>
  </tbody></table>
  <figure class="fig"><img src="../images/lr_scatterplots_mid50.png" alt="Left versus right hemisphere, mid-tract averages" loading="lazy"><figcaption>Each point a subject; dashed line is identity. n = 57.</figcaption></figure>
  {S['bilat']}
  {S['mid50']}
  {S['lrplot']}

  <h3>Node-wise</h3>
  <div class="formula"><span class="lbl">full</span>&nbsp;&nbsp;&nbsp; y ~ node + ICV + Mean_tckstats + Count_tckstats + absolute_motion + maternal_age<br><span class="lbl">reduced</span>&nbsp; y ~ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ICV + Mean_tckstats + Count_tckstats + absolute_motion + maternal_age</div>
  <p>At each node the observed t on the node value is compared against 5000 Freedman–Lane permutations of the reduced-model residuals. Contiguous nodes with p &lt; .05 form a cluster; the cluster survives if its extent exceeds the 95th percentile of the null maximum. NDI, bilateral:</p>
  {nodewise()}
  <p class="small">Across the full sweep (86 measures × 2 tracts) no monetary test survives. FA, ODI and FWF were run in the same batch; their results are in the <a href="results_explorer.html">Results</a> browser. Two of the three social effects reach threshold only in the posterior tract, and the clusters sit at nodes 27 to 55 where the two bundles share tissue. Whether that is a subregional difference is what the next two analyses test.</p>
  {S['perm']}
  {S['runner']}

  <h3>Quartiles</h3>
  <p>The whole-tract model below, with NDI averaged within each quarter. Q1 is nodes 0 to 24 at the VTA end, Q4 is 75 to 99 at the hippocampus.</p>
  <p class="small">Interaction p</p>{quart('interaction_p')}
  <p class="small">Main-effect p, interaction dropped</p>{quart('main_p')}

  <h3>Whole tract, both subregions in one model</h3>
  <p>NDI averaged over all 100 nodes, one value per subject per subregion, stacked long so each subject contributes two rows. NDI regressed on memory, subregion and the covariates, with a random intercept for subject; each row carries its own tract length and streamline count. Maximum likelihood; the interaction model adds memory × subregion and is compared by likelihood-ratio test on 1 df.</p>
  {whole()}
  {S['final']}

  <h2>How we narrowed</h2>
  <h3>Two subregions to one pathway</h3>
  <p>The memory × subregion interaction is droppable for every outcome on the whole-tract average and in 18 of 20 quartile tests; the two exceptions, d′ and misattribution at Q2, do not survive correction across the four. The node-wise clusters sit before the bundles separate, so the anterior and posterior labels are not describing different tissue there. The distinction would have earned its keep only if significant nodes had landed past the divergence, closer to the hippocampus. They did not. The pathway is one bilateral VTA→hippocampus tract.</p>
  <h3>Four metrics to NDI</h3>
  {metric()}
  <p>NDI is the only metric carrying all three social effects while leaving every monetary outcome null. FA tracks it and serves as the supplement for traditional-DTI readers. FWF adds only the bias effect plus a control-domain hit (monetary misattribution, p = .041) and is dropped. ODI's bias effect runs in the same direction as NDI rather than opposite, which is atypical for the pair; it is reported with that caveat or left out.</p>
  <h3>Node-wise to whole tract</h3>
  <p>Contrasting the VTA-end quartile against the hippocampus-end quartile, with mean and difference entered together, is null for all three social outcomes (difference p = .44, .45, .95) while the mean carries the effect. The signal is diffuse along the tract. Cluster-extent thresholding is built to find focal runs, and with per-node t near 2.0 along the whole length it has no headroom here. Node-wise results are descriptive; the whole-tract model is the inferential unit.</p>

  <h2>What we report</h2>
  <p>One bilateral VTA→hippocampus pathway, NDI, whole-tract model with a subregion term. Higher neurite density predicts better discrimination of who gave the feedback, fewer misattributions, and less positivity skew in false memories. All three monetary counterparts are null; monetary misattribution runs the opposite way. No subregional claim. The quartiles show the bias effect is uniform along the tract; they are not a localization claim.</p>

  <h2>Hippocampus and HVLT</h2>
  <p>Hippocampal gray-matter NDI, refit at the gray-matter parallel diffusivity and regressed on each outcome with ICV, hippocampal volume, motion and maternal age. Standardized β. Hippocampal volume on its own predicts none of them.</p>
  {hpc()}
  {S['gm']}
  <p>HVLT under the collapsed whole-tract specification with each subregion's streamline count entered separately. HVLT trial 1 and RAFT social d′ correlate at −.05, so this is a separate finding rather than convergent validation.</p>
  {hvlt()}
</div>
</body></html>
"""
OUT.write_text(HTML)
print(f"wrote {OUT.name} ({len(HTML)//1024} KB)")
