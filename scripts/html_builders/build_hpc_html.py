import json
OUT='/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/results_html'
d=json.load(open(f'{OUT}/hpc_region_data.json')); M=d['models']; qc=d['qc']

def row(m):
    # Only highlight genuine (social) significant rows; monetary is the null control, so an
    # incidental p<0.05 on a monetary cross/bilateral pairing must NOT read as a real finding.
    sig='sig' if (m['p']<0.05 and str(m['outcome']).startswith('Social')) else ''
    dirw = 'higher → better' if m['beta']>0 else 'higher → worse'
    return f"<tr class='{sig}'><td>{m['outcome']}</td><td>{m['side']}</td><td>{m['measure']}</td><td>{m['type']}</td><td>{m['beta']:+}</td><td>{m['p']}</td><td>{m['n']}</td><td class='mut'>{dirw}</td></tr>"
matched=''.join(row(m) for m in M if m['type']=='matched')
cross=''.join(row(m) for m in M if m['type']=='cross')
bilat=''.join(row(m) for m in M if m['type']=='bilateral')
B=d.get('bias_models',[])
def brow(m):
    sig='sig' if (m['p']<0.05 and str(m['outcome']).startswith('Social')) else ''
    dirw = 'higher → more +bias' if m['beta']>0 else 'higher → less +bias'
    return f"<tr class='{sig}'><td>{m['outcome']}</td><td>{m['side']}</td><td>{m['measure']}</td><td>{m['type']}</td><td>{m['beta']:+}</td><td>{m['p']}</td><td>{m['n']}</td><td class='mut'>{dirw}</td></tr>"
bias_matched=''.join(brow(m) for m in B if m['type']=='matched')
bias_cross=''.join(brow(m) for m in B if m['type']=='cross')
bias_bilat=''.join(brow(m) for m in B if m['type']=='bilateral')
bias_maxp=max((m['p'] for m in B),default=1); bias_minp=min((m['p'] for m in B),default=1)
def getm(models,outcome,side,measure,typ):
    for m in models:
        if m['outcome']==outcome and m['side']==side and m['measure']==measure and m['type']==typ: return m
    return {'beta':float('nan'),'p':float('nan'),'n':0}
soc_lndi   = getm(M,'Social d′','Left','NDI density','matched')      # the new significant region effect
soc_bilndi = getm(M,'Social d′','Bilateral','NDI density','bilateral')
soc_lvol   = getm(M,'Social d′','Left','volume','matched')
mon_rndi   = getm(M,'Monetary d′','Right','NDI density','matched')
socfab_rndi= getm(B,'Social FABias','Right','NDI density','matched')
# largest volume p across d′ models (to justify "volume silent")
vol_ps=[m['p'] for m in M if m['measure']=='volume']
vol_minp=min(vol_ps) if vol_ps else 1

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
<p>Our VTA→HPC <b>tract</b> microstructure relates to memory — and specifically to <b>social</b> memory. Social d′ tracks the <b>left</b> tract (denser → better; the whole tract survives correction) and social positivity bias tracks the tract <b>bilaterally</b> across all four microstructure metrics, while <b>monetary</b> memory shows <i>no</i> surviving tract relationship. So the signal is domain-specific and pathway-based.</p>
<p><b>The discriminating test:</b> does the hippocampal <i>region</i> itself — its <b>size</b> (volume) and its <b>tissue microstructure</b> (neurite density) — predict memory? Separating these two matters: if memory tracked hippocampal <i>size</i>, the tract effects might just be a proxy for "bigger/healthier hippocampus." If it tracked hippocampal <i>density</i>, the signal would be a microstructural property that could be shared between the pathway and its target. And if the region were silent entirely, the memory-relevant structure would live purely in the <b>connection</b>.</p>
<p class="mut" style="font-size:13px">Result preview: the answer is not a clean "region is silent." Hippocampal <b>volume</b> is silent, but hippocampal <b>density</b> is <i>not</i> — it tracks social memory in the same direction as the tract. So the real dissociation is <b>size vs. microstructure</b>, and the density findings appear to be a circuit-wide signature rather than a purely connectional one. Details below.</p>
</div>

<div class="section"><h2>Methods (the #1-specific approach)</h2>
<p><b>Hippocampal volume</b> — subject-native segmentation with <b>FSL FIRST</b> (Bayesian shape/appearance model; the FSL gold standard for subcortical structures) run on each mother's own T1, extracting left and right hippocampus (FreeSurfer labels 17/53). This is the canonical structural memory measure.</p>
<p><b>Hippocampal density</b> — mean <b>NODDI neurite-density index (NDI, tissue-weighted)</b> inside the anatomical hippocampus ROI, in native diffusion space (no new registration). A microstructural "density" read to triangulate with volume.</p>
<p><b>Models</b> — d′ regressed on each HPC measure, <b>hemisphere-matched to the tract findings</b> (Left HPC → social, Right HPC → monetary) plus all cross-pairings and bilateral, each controlling for <b>intracranial volume, absolute head motion, and maternal age</b>. Predictors z-scored (β = standardized).</p>
<div class="formula">Social d′  ~ Left  HPC (volume | NDI) + ICV + motion + age
Monetary d′ ~ Right HPC (volume | NDI) + ICV + motion + age
d′ = z(hit rate) − z(false-alarm rate)</div>
<div class="mut" style="font-size:12.5px">Segmentation QC: left HPC {qc['L_vol_mean']} mm³, right {qc['R_vol_mean']} mm³ (normal adult range); L–R volume r = {qc['LR_vol_r']}. <b>Corrected roster n = {qc['n']}</b> (2 pilot scans removed; maternal age recovered for all 55 from current demographics). Models run at <b>n = 54</b> for d′ and <b>52–53</b> for bias after covariate/outcome listwise deletion. One segmentation flag (s4459, implausibly small L-HPC) does not affect the volume result, which is null regardless.</div>
</div>

<div class="section"><h2>Results — hippocampal <i>volume</i> is silent, but <i>density</i> is not</h2>
<h3 style="font-size:14px;color:var(--mut)">Hemisphere-matched</h3>
<table><thead><tr><th>Outcome</th><th>HPC side</th><th>Measure</th><th>Match</th><th>β (std)</th><th>p</th><th>n</th><th>direction</th></tr></thead><tbody>{matched}</tbody></table>
<h3 style="font-size:14px;color:var(--mut)">Cross-pairings</h3>
<table><thead><tr><th>Outcome</th><th>HPC side</th><th>Measure</th><th>Match</th><th>β (std)</th><th>p</th><th>n</th><th>direction</th></tr></thead><tbody>{cross}</tbody></table>
<h3 style="font-size:14px;color:var(--mut)">Bilateral (mean L+R)</h3>
<table><thead><tr><th>Outcome</th><th>HPC side</th><th>Measure</th><th>Match</th><th>β (std)</th><th>p</th><th>n</th><th>direction</th></tr></thead><tbody>{bilat}</tbody></table>
<div class="callout key"><b>Hippocampal volume carries no memory signal</b> — the hemisphere-matched volume tests are firmly null (social p={soc_lvol['p']}, monetary p={getm(M,'Monetary d′','Right','volume','matched')['p']}; smallest volume p across all d′ models = {vol_minp}, a monetary trend). So the tract effects are <b>not</b> a proxy for hippocampal size. <b>But density is a different story:</b> left-hippocampal NDI density predicts social d′ (β={soc_lndi['beta']:+}, <b>p={soc_lndi['p']}</b>), and the bilateral density effect is also significant (β={soc_bilndi['beta']:+}, p={soc_bilndi['p']}) — the <i>same</i> left-lateralised, positive direction as the social tract finding. Monetary d′ tracks neither volume nor density. So it is specifically hippocampal <b>neurite density</b>, not size, that carries a social-memory signal.</div>
</div>

<div class="section"><h2>Results — bias: a density trend, no volume effect</h2>
<p>The tract's most robust findings were not accuracy but <b>positivity bias</b> (FABias — the tendency to falsely "remember" positive events more than negative ones). So the same discriminating test has to be run for bias: does the hippocampal <i>region</i> predict how positively biased a mother's false memories are? Same models — HPC volume and NDI density, in the right hemisphere (shown here as the matched cell) plus left, cross-pairings, and bilateral, all covariate-adjusted. (The tract bias findings are themselves bilateral, so both hemispheres are relevant.)</p>
<h3 style="font-size:14px;color:var(--mut)">Hemisphere-matched (right HPC — where the bias findings were)</h3>
<table><thead><tr><th>Outcome</th><th>HPC side</th><th>Measure</th><th>Match</th><th>β (std)</th><th>p</th><th>n</th><th>direction</th></tr></thead><tbody>{bias_matched}</tbody></table>
<h3 style="font-size:14px;color:var(--mut)">Cross-pairings</h3>
<table><thead><tr><th>Outcome</th><th>HPC side</th><th>Measure</th><th>Match</th><th>β (std)</th><th>p</th><th>n</th><th>direction</th></tr></thead><tbody>{bias_cross}</tbody></table>
<h3 style="font-size:14px;color:var(--mut)">Bilateral (mean L+R)</h3>
<table><thead><tr><th>Outcome</th><th>HPC side</th><th>Measure</th><th>Match</th><th>β (std)</th><th>p</th><th>n</th><th>direction</th></tr></thead><tbody>{bias_bilat}</tbody></table>
<div class="callout key"><b>For bias, volume again predicts nothing interpretable</b> — the only nominal volume hits are both for the monetary domain (which has no surviving tract finding at all): a cross-hemisphere pairing (left volume, p={getm(B,'Monetary FABias','Left','volume','cross')['p']}) and the bilateral mean (p={getm(B,'Monetary FABias','Bilateral','volume','bilateral')['p']}). Neither aligns with a real effect, so both read as incidental (and are not highlighted as findings above). For density, social positivity bias shows a <b>trend</b> with right-hippocampal NDI (β={socfab_rndi['beta']:+}, p={socfab_rndi['p']}), same negative direction as the tract — consistent with the density story but not significant. So bias, unlike accuracy, does not yet show a clear region effect.</div>
</div>

<div class="section"><h2>Interpretation — size vs. microstructure</h2>
<div class="callout"><b>The dissociation is size vs. microstructure — not region vs. connection.</b> Hippocampal <i>volume</i> is silent, so the tract findings are not a proxy for a bigger or healthier hippocampus. But hippocampal <i>neurite density</i> is <b>not</b> silent: it predicts social d′ (β={soc_lndi['beta']:+}, p={soc_lndi['p']}) in the same left-lateralised, positive direction as the tract. So the density signal is a property of the <b>broader circuit tissue</b> — present in both the pathway and its hippocampal target — rather than something unique to the connection. The honest read: <b>memory tracks neurite density, not hippocampal size, and that density signature is shared between the VTA→HPC tract and the hippocampus itself.</b></div>
<div class="callout" style="border-left-color:#eab308"><b>What this does and doesn't establish — and a correction.</b> An earlier version of this analysis, run on an underpowered n=42 sample (depressed by a stale demographics file that dropped ~12 mothers with recoverable ages), showed only nulls and concluded "the region is silent." With the corrected sample (n=54), a real region effect emerges, so that earlier claim was a power artifact and has been updated. Bounded conclusions now: <b>(1)</b> hippocampal <i>volume</i> is robustly <b>not</b> the driver; <b>(2)</b> hippocampal <i>density</i> carries a social-memory signal paralleling the tract, so the density effects are <b>circuit-wide, not strictly connection-specific</b>; <b>(3)</b> the effect is modest (p≈.01–.04, left hemisphere, social only; monetary and bias show nothing significant) and needs replication. The tract is one node in a density-related circuit, not an isolated cause.</div>
</div>

<div class="section"><h2>Method references (documentation)</h2>{refs}</div>

<div class="section" style="text-align:center;color:var(--mut);font-size:13px">
Data: <code>data/hpc_region_measures.csv</code> · Segmentation: <code>scripts/run_first_hpc.sh</code> · Density: <code>scripts/extract_hpc_density.sh</code> · Models: <code>scripts/html_builders/hpc_analysis.py</code><br><br>
<a class="back" href="results_explorer.html">← Results Explorer</a> &nbsp;·&nbsp; <a class="back" href="data_quality.html">Data-Quality & d′ →</a>
</div>
</div></body></html>'''
open(f'{OUT}/hpc_region_vs_connection.html','w').write(html)
print("wrote hpc_region_vs_connection.html",len(html),"bytes")
