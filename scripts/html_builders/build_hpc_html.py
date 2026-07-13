import json
OUT='/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/results_html'
d=json.load(open(f'{OUT}/hpc_region_data.json')); M=d['models']; B=d['bias_models']; qc=d['qc']

def getm(rows,outcome,side,measure,typ):
    for m in rows:
        if m['outcome']==outcome and m['side']==side and m['measure'].startswith(measure) and m['type']==typ: return m
    return {'beta':float('nan'),'p':float('nan'),'n':0}
def pf(p):
    p=float(p); return '&lt;0.001' if p<0.001 else f'{p:g}'
def rowhtml(m,biasdir=False):
    sig='sig' if m['p']<0.05 else ''
    if biasdir: dirw='higher → more +bias' if m['beta']>0 else 'higher → less +bias'
    else: dirw='higher → better' if m['beta']>0 else 'higher → worse'
    b=0.0 if m['beta']==0 else m['beta']  # avoid "-0.0" negative-zero artifact
    return f"<tr class='{sig}'><td>{m['outcome']}</td><td>{m['side']}</td><td>{m['measure']}</td><td>{m['type']}</td><td>{b:+}</td><td>{pf(m['p'])}</td><td>{m['n']}</td><td class='mut'>{dirw}</td></tr>"

soc_ndi=getm(M,'Social d′','Left','NDI','matched')
socfab_ndi=getm(B,'Social FABias','Right','NDI','matched')
dtab=''.join(rowhtml(m) for m in M)
btab=''.join(rowhtml(m,True) for m in B)

html=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>IMPACT — Hippocampal NODDI vs. VTA→HPC connection</title>
<style>
:root{{--bg:#0f1117;--card:#1a1d27;--card2:#232733;--ink:#e6e9ef;--mut:#9aa3b2;--line:#2c3140;--accent:#a78bfa;--yes:#22c55e;}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:14.5px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}
header{{padding:22px 26px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#171a24,#0f1117)}}
h1{{margin:0 0 4px;font-size:22px}}.sub{{color:var(--mut);font-size:13px}}
.wrap{{padding:20px 26px;max-width:1000px;margin:0 auto}}
.section{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 22px;margin:16px 0}}
.section h2{{margin:0 0 6px;font-size:17px;color:var(--accent)}}
table{{width:100%;border-collapse:collapse;font-size:13px;margin:8px 0}}
th{{text-align:left;color:var(--mut);font-weight:600;font-size:10.5px;text-transform:uppercase;letter-spacing:.04em;padding:7px 9px;border-bottom:1px solid var(--line)}}
td{{padding:8px 9px;border-bottom:1px solid #20242f}}
tr.sig td{{background:rgba(34,197,94,.08)}}
.callout{{background:var(--card2);border-left:3px solid var(--accent);border-radius:6px;padding:12px 15px;margin:12px 0;font-size:13.5px}}
.callout.key{{border-left-color:var(--yes)}}
.formula{{font-family:ui-monospace,Menlo,monospace;background:#12141c;border:1px solid var(--line);border-radius:8px;padding:14px 16px;font-size:13px;line-height:1.7;color:#c9d1e0}}
a.back{{color:var(--accent);text-decoration:none}} .mut{{color:var(--mut)}}
</style></head><body>
<header><h1>Hippocampal <i>NODDI</i> vs. VTA→HPC <i>connection</i></h1>
<div class="sub">Does the hippocampal <b>region</b> itself carry the memory signal, or is it specific to the <b>pathway</b>? &nbsp;·&nbsp; <a class="back" href="results_explorer.html">← Results Explorer</a></div></header>
<div class="wrap">

<div class="section"><h2>The question</h2>
<p>The VTA→HPC <b>tract</b> relates to social memory, and specifically through <b>neurite density (NDI)</b>. Is that a property of the <i>connection</i>, or does the hippocampal <i>gray matter</i> itself carry the same signal? We run <b>canonical NODDI inside the hippocampus</b> — the standard three-compartment model's outputs (<b>NDI</b> neurite density, <b>ODI</b> orientation dispersion, <b>FWF</b> free-water fraction) averaged within each mother's anatomical hippocampus ROI — and ask whether they predict memory the way the tract does. (Hippocampal <i>volume</i> is not used; this is a microstructure question, not a size question.)</p>
</div>

<div class="section"><h2>Methods</h2>
<p><b>Region measure</b> — mean <b>NODDI NDI, ODI, and FWF</b> inside the anatomical hippocampus ROI, in native diffusion space (same NODDI maps as the tract analysis; no new registration). <b>Models</b> — d′ and positivity bias regressed on each HPC NODDI measure, <b>hemisphere-matched to the tract findings</b> (left HPC → social, right HPC → monetary; bias matched to the right-leaning bias findings), plus cross-pairings and bilateral, controlling for <b>intracranial volume, head motion, and maternal age</b>. Predictors z-scored (β = standardized).</p>
<div class="formula">Social d′  ~ Left  HPC (NDI | ODI | FWF) + ICV + motion + age
Monetary d′ ~ Right HPC (NDI | ODI | FWF) + ICV + motion + age</div>
<div class="mut" style="font-size:12.5px">HPC NODDI (mean in ROI): NDI L={qc['NDI_L']}/R={qc['NDI_R']} (L–R r={qc['NDI_LR_r']}) · ODI L={qc['ODI_L']}/R={qc['ODI_R']} · FWF L={qc['FWF_L']}/R={qc['FWF_R']}. Models run at n=53 (social d′) / 54 (monetary d′) / 51–53 (bias), corrected roster.</div>
</div>

<div class="section"><h2>Results — memory accuracy (d′)</h2>
<table><thead><tr><th>Outcome</th><th>HPC side</th><th>NODDI measure</th><th>Match</th><th>β (std)</th><th>p</th><th>n</th><th>direction</th></tr></thead><tbody>{dtab}</tbody></table>
<div class="callout key"><b>Only neurite density (NDI) tracks memory — and only for social.</b> Left-hippocampal NDI predicts social d′ (β={soc_ndi['beta']:+}, <b>p={pf(soc_ndi['p'])}</b>), the <i>same</i> left-lateralised, positive direction as the social tract finding. <b>ODI (dispersion) and FWF (free water) are silent</b> for both domains, and monetary d′ tracks none of the three. So among the NODDI compartments, the memory-relevant one in the hippocampus is specifically <b>neurite density</b> — exactly the compartment that carried the tract effect.</div>
</div>

<div class="section"><h2>Results — positivity bias (FABias)</h2>
<table><thead><tr><th>Outcome</th><th>HPC side</th><th>NODDI measure</th><th>Match</th><th>β (std)</th><th>p</th><th>n</th><th>direction</th></tr></thead><tbody>{btab}</tbody></table>
<div class="callout"><b>For bias, a density trend in the same direction.</b> Social positivity bias shows a trend with hippocampal NDI (right β={socfab_ndi['beta']:+}, p={pf(socfab_ndi['p'])}; bilateral similar), the same negative direction as the tract, but not significant. ODI, FWF, and all monetary tests are null. Bias is carried by the pathway more than the region.</div>
</div>

<div class="section"><h2>Interpretation</h2>
<div class="callout"><b>A neurite-density signature shared between the pathway and its target.</b> The memory-relevant hippocampal signal is not size and not just any microstructure — it is specifically <b>neurite density (NDI)</b>, the very compartment that carries the VTA→HPC tract effect, in the same hemisphere and direction (left, positive, social). Dispersion (ODI) and free water (FWF) carry nothing. So the density effect is best read as a property of the <b>broader circuit tissue</b> — present in both the connection and the hippocampal gray matter — rather than something unique to the tract.</div>
<div class="callout" style="border-left-color:#eab308"><b>Bounded conclusions.</b> (1) The effect is specific to <b>neurite density</b> — ODI and FWF are silent, so this is not a generic "denser/healthier hippocampus" story. (2) It is <b>social-specific</b> — monetary tracks no HPC NODDI measure. (3) It is <b>modest</b> (social d′ p≈0.04, one hemisphere; social bias only a trend) and needs replication. The hippocampus is one node in a density-related social-memory circuit, not an isolated cause.</div>
</div>
<div class="section" style="text-align:center;color:var(--mut);font-size:13px"><a class="back" href="results_explorer.html">← Back to Results Explorer</a></div>
</div></body></html>'''
open(f'{OUT}/hpc_region_vs_connection.html','w').write(html)
print("wrote hpc_region_vs_connection.html (NODDI)",len(html),"bytes")
