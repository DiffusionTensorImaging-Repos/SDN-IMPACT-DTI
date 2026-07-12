import json
OUT='/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/results_html'
d=json.load(open(f'{OUT}/hpc_region_data.json')); M=d['models']; qc=d['qc']

def row(m):
    sig='sig' if m['p']<0.05 else ''
    dirw = 'higher → better' if m['beta']>0 else 'higher → worse'
    return f"<tr class='{sig}'><td>{m['outcome']}</td><td>{m['side']}</td><td>{m['measure']}</td><td>{m['type']}</td><td>{m['beta']:+}</td><td>{m['p']}</td><td>{m['n']}</td><td class='mut'>{dirw}</td></tr>"
matched=''.join(row(m) for m in M if m['type']=='matched')
cross=''.join(row(m) for m in M if m['type']=='cross')
bilat=''.join(row(m) for m in M if m['type']=='bilateral')
B=d.get('bias_models',[])
def brow(m):
    sig='sig' if m['p']<0.05 else ''
    dirw = 'higher → more +bias' if m['beta']>0 else 'higher → less +bias'
    return f"<tr class='{sig}'><td>{m['outcome']}</td><td>{m['side']}</td><td>{m['measure']}</td><td>{m['type']}</td><td>{m['beta']:+}</td><td>{m['p']}</td><td>{m['n']}</td><td class='mut'>{dirw}</td></tr>"
bias_matched=''.join(brow(m) for m in B if m['type']=='matched')
bias_cross=''.join(brow(m) for m in B if m['type']=='cross')
bias_bilat=''.join(brow(m) for m in B if m['type']=='bilateral')
bias_maxp=max((m['p'] for m in B),default=1); bias_minp=min((m['p'] for m in B),default=1)

REFS=[
 ('FSL FIRST — subcortical segmentation','Patenaude, Smith, Kennedy &amp; Jenkinson (2011), <i>NeuroImage</i> 56(3):907–922. A Bayesian model of shape and appearance for subcortical brain segmentation.','https://doi.org/10.1016/j.neuroimage.2011.02.046'),
 ('FSL FIRST — tool documentation','FMRIB Software Library — FIRST user guide.','https://fsl.fmrib.ox.ac.uk/fsl/docs/#/structural/first'),
 ('NODDI — model','Zhang, Schneider, Wheeler-Kingshott &amp; Alexander (2012), <i>NeuroImage</i> 61(4):1000–1016. NODDI: practical in vivo neurite orientation dispersion and density imaging.','https://doi.org/10.1016/j.neuroimage.2012.03.072'),
 ('AMICO — fast NODDI fitting','Daducci et al. (2015), <i>NeuroImage</i> 105:32–44. Accelerated Microstructure Imaging via Convex Optimization.','https://doi.org/10.1016/j.neuroimage.2014.10.026'),
 ('Tissue-weighted (modulated) NODDI maps','Parker et al. (2021), <i>NeuroImage</i> 245:118749. Partial-volume correction for NODDI via tissue-weighting.','https://doi.org/10.1016/j.neuroimage.2021.118749'),
 ('Signal-detection d′ (memory)','Macmillan &amp; Creelman (2005), <i>Detection Theory: A User&#39;s Guide</i> (2nd ed.). Snodgrass &amp; Corwin (1988), <i>JEP:General</i> 117(1):34–50 (log-linear / edge correction).','https://doi.org/10.1037/0096-3445.117.1.34'),
 ('Hippocampal volume ↔ memory (context)','Van Petten (2004), <i>Neuropsychologia</i> 42(10):1394–1413. Relationship between hippocampal volume and memory ability in healthy individuals — meta-analysis (effects are small).','https://doi.org/10.1016/j.neuropsychologia.2004.04.006'),
]
refs=''.join(f"<div class='ref'><div class='rt'>{t}</div><div class='rd'>{de}</div><a href='{u}' target='_blank'>{u}</a></div>" for t,de,u in REFS)

html=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>HPC Region vs VTA→HPC Connection — Specificity Analysis</title>
<style>
:root{{--bg:#0f1117;--card:#1a1d27;--card2:#232733;--ink:#e6e9ef;--mut:#9aa3b2;--line:#2c3140;--accent:#a78bfa;--yes:#22c55e;}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:14.5px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}
header{{padding:22px 26px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#171a24,#0f1117)}}
h1{{margin:0 0 4px;font-size:22px}}.sub{{color:var(--mut);font-size:13px}}
.wrap{{padding:20px 26px;max-width:1000px;margin:0 auto}}
.section{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 22px;margin:16px 0}}
.section h2{{margin:0 0 8px;font-size:17px;color:var(--accent)}}
table{{width:100%;border-collapse:collapse;font-size:13.5px;margin:8px 0}}
th{{text-align:left;color:var(--mut);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.04em;padding:8px 10px;border-bottom:1px solid var(--line)}}
td{{padding:9px 10px;border-bottom:1px solid #20242f}}
tr.sig td{{background:rgba(34,197,94,.08)}}
.mut{{color:var(--mut)}} .big{{font-size:19px;font-weight:700}}
.callout{{background:var(--card2);border-left:3px solid var(--accent);border-radius:6px;padding:13px 16px;margin:12px 0;font-size:13.5px}}
.callout.key{{border-left-color:var(--yes)}}
.stat{{display:inline-block;background:var(--card2);border:1px solid var(--line);border-radius:9px;padding:11px 14px;margin:4px 6px 4px 0}}
.stat .k{{color:var(--mut);font-size:11px;text-transform:uppercase}}.stat .v{{font-size:19px;font-weight:700;margin-top:2px}}
.ref{{background:var(--card2);border:1px solid var(--line);border-radius:9px;padding:11px 14px;margin:8px 0}}
.ref .rt{{font-weight:600;font-size:13.5px}}.ref .rd{{color:var(--mut);font-size:12.5px;margin:3px 0 5px}}.ref a{{color:var(--accent);font-size:12px;word-break:break-all;text-decoration:none}}
a.back{{color:var(--accent);text-decoration:none}} code{{background:#12141c;border:1px solid var(--line);border-radius:4px;padding:1px 5px;font-size:12.5px}}
.formula{{font-family:ui-monospace,Menlo,monospace;background:#12141c;border:1px solid var(--line);border-radius:8px;padding:12px 15px;font-size:13px;color:#c9d1e0;line-height:1.6}}
</style></head><body>
<header><h1>Hippocampal <i>region</i> vs. VTA→HPC <i>connection</i> — a specificity test</h1>
<div class="sub">Does the hippocampus <b>itself</b> relate to memory, or is the memory-relevant signal specific to the <b>pathway</b>? &nbsp;·&nbsp; <a class="back" href="results_explorer.html">← Results Explorer</a></div></header>
<div class="wrap">

<div class="section"><h2>The question</h2>
<p>Our VTA→HPC <b>tract</b> microstructure relates to memory with a striking <b>hemispheric sign-flip</b>: social memory loads on the <b>left</b> tract (positive), monetary on the <b>right</b> (negative). A flip like that is either meaningful (a property of the specific connection) or noise.</p>
<p><b>The discriminating test:</b> does the hippocampal <i>region</i> itself — its size and its tissue density — predict memory? If the region carried the memory signal in a simple way, the tract effects might just be a proxy for "healthier hippocampus." If the region is <i>silent</i> while the pathway is not, the memory-relevant structure lives in the <b>connection</b>, not the gray-matter bulk — making the tract findings pathway-specific.</p>
</div>

<div class="section"><h2>Methods (the #1-specific approach)</h2>
<p><b>Hippocampal volume</b> — subject-native segmentation with <b>FSL FIRST</b> (Bayesian shape/appearance model; the FSL gold standard for subcortical structures) run on each mother's own T1, extracting left and right hippocampus (FreeSurfer labels 17/53). This is the canonical structural memory measure.</p>
<p><b>Hippocampal density</b> — mean <b>NODDI neurite-density index (NDI, tissue-weighted)</b> inside the anatomical hippocampus ROI, in native diffusion space (no new registration). A microstructural "density" read to triangulate with volume.</p>
<p><b>Models</b> — d′ regressed on each HPC measure, <b>hemisphere-matched to the tract findings</b> (Left HPC → social, Right HPC → monetary) plus all cross-pairings and bilateral, each controlling for <b>intracranial volume, absolute head motion, and maternal age</b>. Predictors z-scored (β = standardized).</p>
<div class="formula">Social d′  ~ Left  HPC (volume | NDI) + ICV + motion + age
Monetary d′ ~ Right HPC (volume | NDI) + ICV + motion + age
d′ = z(hit rate) − z(false-alarm rate)</div>
<div class="mut" style="font-size:12.5px">Segmentation QC: left HPC {qc['L_vol_mean']} mm³, right {qc['R_vol_mean']} mm³ (normal adult range); L–R volume r = {qc['LR_vol_r']}. One FIRST failure (s4459, implausibly small L-HPC) flagged and excluded from robustness checks — results unchanged. Analysis n = {qc['n']} (models n=42 after covariate/d′ listwise deletion).</div>
</div>

<div class="section"><h2>Results — the hippocampus itself is silent</h2>
<h3 style="font-size:14px;color:var(--mut)">Hemisphere-matched</h3>
<table><thead><tr><th>Outcome</th><th>HPC side</th><th>Measure</th><th>Match</th><th>β (std)</th><th>p</th><th>n</th><th>direction</th></tr></thead><tbody>{matched}</tbody></table>
<h3 style="font-size:14px;color:var(--mut)">Cross-pairings</h3>
<table><thead><tr><th>Outcome</th><th>HPC side</th><th>Measure</th><th>Match</th><th>β (std)</th><th>p</th><th>n</th><th>direction</th></tr></thead><tbody>{cross}</tbody></table>
<h3 style="font-size:14px;color:var(--mut)">Bilateral (mean L+R)</h3>
<table><thead><tr><th>Outcome</th><th>HPC side</th><th>Measure</th><th>Match</th><th>β (std)</th><th>p</th><th>n</th><th>direction</th></tr></thead><tbody>{bilat}</tbody></table>
<div class="callout key"><b>No hippocampal volume or density measure significantly predicted d′ in either domain</b> (all p &gt; 0.13; nothing survives). Volume betas are weakly positive and consistent across domains (no flip); NDI shows only a faint hint of the same social-vs-monetary asymmetry, but nothing significant.</div>
</div>

<div class="section"><h2>Results — the hippocampus is also silent for <i>bias</i></h2>
<p>The tract's most robust findings were not accuracy but <b>positivity bias</b> (FABias — the tendency to falsely "remember" positive events more than negative ones). So the same discriminating test has to be run for bias: does the hippocampal <i>region</i> predict how positively biased a mother's false memories are? Same models — HPC volume and NDI density, hemisphere-matched to the (right-lateralised) bias findings, plus cross-pairings and bilateral, all covariate-adjusted.</p>
<h3 style="font-size:14px;color:var(--mut)">Hemisphere-matched (right HPC — where the bias findings were)</h3>
<table><thead><tr><th>Outcome</th><th>HPC side</th><th>Measure</th><th>Match</th><th>β (std)</th><th>p</th><th>n</th><th>direction</th></tr></thead><tbody>{bias_matched}</tbody></table>
<h3 style="font-size:14px;color:var(--mut)">Cross-pairings</h3>
<table><thead><tr><th>Outcome</th><th>HPC side</th><th>Measure</th><th>Match</th><th>β (std)</th><th>p</th><th>n</th><th>direction</th></tr></thead><tbody>{bias_cross}</tbody></table>
<h3 style="font-size:14px;color:var(--mut)">Bilateral (mean L+R)</h3>
<table><thead><tr><th>Outcome</th><th>HPC side</th><th>Measure</th><th>Match</th><th>β (std)</th><th>p</th><th>n</th><th>direction</th></tr></thead><tbody>{bias_bilat}</tbody></table>
<div class="callout key"><b>No hippocampal volume or density measure predicted positivity bias either</b> (all p &gt; {bias_minp:.2f}; nothing significant). The region is silent for bias just as it was for accuracy.</div>
</div>

<div class="section"><h2>Interpretation — what this buys the tract story</h2>
<div class="callout"><b>The region is silent for <i>both</i> accuracy and bias; the pathway is not.</b> Hippocampal size and neurite density carry no detectable signal for d′ <i>or</i> for positivity bias, yet the VTA→HPC <i>tract</i> does (at cluster level, for both). So the memory-relevant structural variance in this circuit is <b>not</b> attributable to hippocampal bulk properties — it is a feature of the <b>connection</b>. Concretely: the tract effects are not a proxy for "bigger/denser hippocampus," which strengthens the case that the hemispheric tract flip — and the bias effects — are genuine, pathway-specific phenomena rather than downstream shadows of gray-matter differences.</div>
<div class="callout" style="border-left-color:#eab308"><b>Honest caveat — this is a null, and nulls are weak.</b> n=42 is underpowered, and hippocampal-volume↔memory effects are small in healthy adults (typically r ≈ 0.1–0.2; see Van Petten 2004). Absence of a region effect here is consistent with pathway-specificity but does <i>not</i> prove the hippocampus is irrelevant — a larger sample could reveal a small region effect. The claim is bounded: "the tract signal is not explained by hippocampal size/density in this sample," not "the hippocampus does not matter."</div>
</div>

<div class="section"><h2>Method references (documentation)</h2>{refs}</div>

<div class="section" style="text-align:center;color:var(--mut);font-size:13px">
Data: <code>data/hpc_region_measures.csv</code> · Segmentation: <code>scripts/run_first_hpc.sh</code> · Density: <code>scripts/extract_hpc_density.sh</code> · Models: <code>scripts/html_builders/hpc_analysis.py</code><br><br>
<a class="back" href="results_explorer.html">← Results Explorer</a> &nbsp;·&nbsp; <a class="back" href="data_quality.html">Data-Quality & d′ →</a>
</div>
</div></body></html>'''
open(f'{OUT}/hpc_region_vs_connection.html','w').write(html)
print("wrote hpc_region_vs_connection.html",len(html),"bytes")
