import json, numpy as np
OUT='/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/results_html'
d=json.load(open(f'{OUT}/asymmetry_data.json'))

def fmt(m): return f"β={m['adj_beta']:+.3f}, p={m['adj_p']}"
LI_NDI,LI_FA=d['LI_NDI'],d['LI_FA']
SUM_NDI,SUM_FA=d['SUM_NDI'],d['SUM_FA']
Ln,Rn=d['L_NDI'],d['R_NDI']

def prow(label,m,thresh=0.05):
    sig='sig' if m['adj_p']<thresh else ''
    return (f"<tr class='{sig}'><td>{label}</td><td>{m['raw_r']:+}</td><td>{m['raw_p']}</td>"
            f"<td>{m['adj_beta']:+}</td><td>{m['adj_p']}</td><td>{m['n']}</td></tr>")

balance_tbl=prow('Tract balance — NDI &nbsp;<code>(L−R)/(L+R)</code>',LI_NDI)+prow('Tract balance — FA &nbsp;<code>(L−R)/(L+R)</code>',LI_FA)
level_tbl=prow('Bilateral level — NDI &nbsp;<code>L+R</code>',SUM_NDI)+prow('Bilateral level — FA &nbsp;<code>L+R</code>',SUM_FA)
side_tbl=prow('Left NDI (mid-tract)',Ln)+prow('Right NDI (mid-tract)',Rn)

# ---- inline SVG scatter: bilateral SUM_NDI (x) vs memory balance (y) ----
pts=d['scatter_sum']
xs=np.array([p['SUM_NDI'] for p in pts]); ys=np.array([p['mem_asym'] for p in pts])
W,H=620,420; PL,PR,PT,PB=64,24,28,52
x0,x1=xs.min(),xs.max(); y0,y1=ys.min(),ys.max()
xpad=(x1-x0)*.06; ypad=(y1-y0)*.08; x0-=xpad;x1+=xpad;y0-=ypad;y1+=ypad
def sx(v): return PL+(v-x0)/(x1-x0)*(W-PL-PR)
def sy(v): return H-PB-(v-y0)/(y1-y0)*(H-PT-PB)
b1,b0=np.polyfit(xs,ys,1); lx0,lx1=xs.min(),xs.max()
dots=''.join(f"<circle cx='{sx(x):.1f}' cy='{sy(y):.1f}' r='4.5' fill='#a78bfa' fill-opacity='0.72' stroke='#0f1117' stroke-width='0.6'/>" for x,y in zip(xs,ys))
# axis ticks
xticks=np.linspace(xs.min(),xs.max(),4); yticks=np.linspace(ys.min(),ys.max(),5)
xtk=''.join(f"<text x='{sx(t):.1f}' y='{H-PB+18}' fill='#9aa3b2' font-size='10' text-anchor='middle'>{t:.2f}</text><line x1='{sx(t):.1f}' y1='{H-PB}' x2='{sx(t):.1f}' y2='{H-PB+4}' stroke='#2c3140'/>" for t in xticks)
ytk=''.join(f"<text x='{PL-9}' y='{sy(t)+3:.1f}' fill='#9aa3b2' font-size='10' text-anchor='end'>{t:+.1f}</text><line x1='{PL-4}' y1='{sy(t):.1f}' x2='{PL}' y2='{sy(t):.1f}' stroke='#2c3140'/>" for t in yticks)
zero=f"<line x1='{PL}' y1='{sy(0):.1f}' x2='{W-PR}' y2='{sy(0):.1f}' stroke='#3a4152' stroke-dasharray='4 4'/>" if y0<0<y1 else ''
scatter=f'''<svg viewBox="0 0 {W} {H}" width="100%" style="max-width:640px" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="{W}" height="{H}" fill="none"/>
<line x1="{PL}" y1="{PT}" x2="{PL}" y2="{H-PB}" stroke="#2c3140"/><line x1="{PL}" y1="{H-PB}" x2="{W-PR}" y2="{H-PB}" stroke="#2c3140"/>
{zero}{xtk}{ytk}
<line x1="{sx(lx0):.1f}" y1="{sy(b0+b1*lx0):.1f}" x2="{sx(lx1):.1f}" y2="{sy(b0+b1*lx1):.1f}" stroke="#22c55e" stroke-width="2.4"/>
{dots}
<text x="{(PL+W-PR)/2:.0f}" y="{H-10}" fill="#c9d1e0" font-size="12" text-anchor="middle" font-weight="600">Bilateral VTA→HPC NDI  (Left + Right, mid-tract)  →</text>
<text x="16" y="{(PT+H-PB)/2:.0f}" fill="#c9d1e0" font-size="12" text-anchor="middle" font-weight="600" transform="rotate(-90 16 {(PT+H-PB)/2:.0f})">← more monetary   ·   memory balance   ·   more social →</text>
</svg>'''

REFS=[
 ('Laterality index — standard formula','Seghier (2008), <i>Magnetic Resonance Imaging</i> 26(5):594–601. The (L−R)/(L+R) laterality index: robustness and reliability. The canonical bounded [−1,+1] asymmetry metric.','https://doi.org/10.1016/j.mri.2007.10.010'),
 ('AFQ node-wise tract profiling','Yeatman, Dougherty, Myall, Wandell &amp; Feldman (2012), <i>PLoS ONE</i> 7(11):e49790. Tract profiles of white matter properties: automating fiber-tract quantification.','https://doi.org/10.1371/journal.pone.0049790'),
 ('NODDI — neurite density','Zhang, Schneider, Wheeler-Kingshott &amp; Alexander (2012), <i>NeuroImage</i> 61(4):1000–1016.','https://doi.org/10.1016/j.neuroimage.2012.03.072'),
 ('Difference scores &amp; the interaction they encode','Judd, McClelland &amp; Ryan (2017), <i>Data Analysis: A Model-Comparison Approach</i> (3rd ed.), ch. on within-subject contrasts — a regression on a difference score is the test of the corresponding condition × predictor interaction.','https://doi.org/10.4324/9781315744131'),
 ('Signal-detection d′','Macmillan &amp; Creelman (2005), <i>Detection Theory: A User&#39;s Guide</i> (2nd ed.).','https://doi.org/10.4324/9781410611147'),
]
refs=''.join(f"<div class='ref'><div class='rt'>{t}</div><div class='rd'>{de}</div><a href='{u}' target='_blank'>{u}</a></div>" for t,de,u in REFS)

html=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Flip — Tract Balance vs. Tract Level</title>
<style>
:root{{--bg:#0f1117;--card:#1a1d27;--card2:#232733;--ink:#e6e9ef;--mut:#9aa3b2;--line:#2c3140;--accent:#a78bfa;--yes:#22c55e;--warn:#eab308;}}
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
.mut{{color:var(--mut)}}
.callout{{background:var(--card2);border-left:3px solid var(--accent);border-radius:6px;padding:13px 16px;margin:12px 0;font-size:13.5px}}
.callout.key{{border-left-color:var(--yes)}} .callout.no{{border-left-color:#ef4444}} .callout.warn{{border-left-color:var(--warn)}}
.ref{{background:var(--card2);border:1px solid var(--line);border-radius:9px;padding:11px 14px;margin:8px 0}}
.ref .rt{{font-weight:600;font-size:13.5px}}.ref .rd{{color:var(--mut);font-size:12.5px;margin:3px 0 5px}}.ref a{{color:var(--accent);font-size:12px;word-break:break-all;text-decoration:none}}
a.back{{color:var(--accent);text-decoration:none}} code{{background:#12141c;border:1px solid var(--line);border-radius:4px;padding:1px 5px;font-size:12.5px}}
.formula{{font-family:ui-monospace,Menlo,monospace;background:#12141c;border:1px solid var(--line);border-radius:8px;padding:12px 15px;font-size:13px;color:#c9d1e0;line-height:1.6}}
.verdict{{display:inline-block;font-weight:700;font-size:12px;padding:3px 10px;border-radius:20px;margin-left:6px}}
.vno{{background:rgba(239,68,68,.15);color:#fca5a5;border:1px solid rgba(239,68,68,.4)}}
.vyes{{background:rgba(34,197,94,.15);color:#86efac;border:1px solid rgba(34,197,94,.4)}}
.figwrap{{text-align:center;background:#12141c;border:1px solid var(--line);border-radius:10px;padding:14px;margin:12px 0}}
</style></head><body>
<header><h1>Is the hemispheric &ldquo;flip&rdquo; a laterality effect? <span class="mut" style="font-size:15px">Tract balance vs. tract level</span></h1>
<div class="sub">Social memory loaded on the <b>left</b> tract, monetary on the <b>right</b> — opposite signs. Is that a left/right <b>balance</b> phenomenon, or something else? &nbsp;·&nbsp; <a class="back" href="results_explorer.html">← Results Explorer</a></div></header>
<div class="wrap">

<div class="section"><h2>The question</h2>
<p>The two headline accuracy findings point in opposite directions: <b>social</b> d′ tracks the <b>left</b> VTA→HPC tract (denser → better), <b>monetary</b> d′ tracks the <b>right</b> tract (denser → worse). Read side-by-side, that looks like a <b>laterality</b> story:</p>
<div class="callout"><b>Hypothesis:</b> do mothers whose <b>left</b> tract is stronger than their right tend to be <b>better at social memory</b> (relative to monetary), while mothers with a stronger <b>right</b> tract are <b>better at monetary</b>? If so, the flip is one real thing — the left/right <i>balance</i> of this pathway sets which kind of memory you are tuned for.</p></div>
<p>This is worth testing directly, because two opposite-signed correlations sitting next to each other is not, by itself, evidence of a coherent asymmetry. It could be a genuine balance effect — or an artifact of analysing four cells (L/R × social/monetary) separately.</p>
</div>

<div class="section"><h2>How we tested it</h2>
<p><b>Tract balance (predictor).</b> For each mother, a <b>laterality index</b> on the deep-white-matter mid-tract (nodes 25–75, avoiding endpoint partial-volume) — computed on <b>both</b> NDI (density) and FA (coherence). Using the whole mid-tract, <i>not</i> the specific significant cluster nodes, so we are not re-selecting the nodes that produced the original finding.</p>
<p><b>Memory balance (outcome).</b> Social and monetary d′ are first <b>z-scored within-sample</b> (their raw scales differ), then differenced: <code>z(social) − z(monetary)</code> = a mother's relative social-vs-monetary memory advantage. This is a meaningful dimension precisely because the two d′s are essentially <b>uncorrelated</b> (r ≈ −0.04) — the difference is signal, not shared variance.</p>
<div class="formula">Laterality index  LI = (Left − Right) / (Left + Right)      (mid-tract, NDI &amp; FA)
Memory balance    = z(social d′) − z(monetary d′)
Test:  memory_balance ~ LI + ICV + motion + age + streamline-count-LI + length-LI</div>
<p class="mut" style="font-size:12.5px">Two task non-completers excluded (social d′ enters the outcome). Predictor z-scored (β = standardized). Streamline count/length <i>asymmetry</i> included as nuisance covariates — controlling the lateralized confound, not just the global one.</p>
</div>

<div class="section"><h2>Result 1 — the balance hypothesis is <span class="verdict vno">NOT SUPPORTED</span></h2>
<table><thead><tr><th>Predictor → memory balance</th><th>raw r</th><th>raw p</th><th>adj. β</th><th>adj. p</th><th>n</th></tr></thead><tbody>{balance_tbl}</tbody></table>
<div class="callout no"><b>Tract balance does not predict memory balance.</b> Neither density asymmetry ({fmt(LI_NDI)}) nor coherence asymmetry ({fmt(LI_FA)}) is associated with whether a mother is relatively better at social vs. monetary memory. Left-dominant mothers are <b>not</b> tuned toward social memory. The flip is <b>not</b> a left/right competition.</div>
</div>

<div class="section"><h2>Result 2 — it is the <i>level</i>, not the balance <span class="verdict vyes">SUPPORTED</span></h2>
<p>If it is not the difference between hemispheres, what predicts the social-vs-monetary tradeoff? The <b>total</b> — bilateral tract level (Left + Right):</p>
<table><thead><tr><th>Predictor → memory balance</th><th>raw r</th><th>raw p</th><th>adj. β</th><th>adj. p</th><th>n</th></tr></thead><tbody>{level_tbl}</tbody></table>
<p class="mut" style="font-size:13px">And it is carried by <b>both</b> hemispheres, roughly equally — not one side:</p>
<table><thead><tr><th>Single-side predictor</th><th>raw r</th><th>raw p</th><th>adj. β</th><th>adj. p</th><th>n</th></tr></thead><tbody>{side_tbl}</tbody></table>
<div class="figwrap">{scatter}<div class="mut" style="font-size:12px;margin-top:6px">Each dot = one mother. Higher <b>overall</b> VTA→HPC neurite density (x) → relatively <b>more social, less monetary</b> memory (y). Green line = covariate-free fit shown for display; statistics above are covariate-adjusted.</div></div>
<div class="callout key"><b>Higher overall bilateral VTA→HPC density and coherence shift the whole system toward social and away from monetary memory</b> (NDI {fmt(SUM_NDI)}; FA {fmt(SUM_FA)}). This is <i>why</i> the two original findings had opposite signs: it was never a contest between hemispheres — more tract (on either side) pushes memory toward the social domain and away from the monetary one, so the <b>difference</b> (social − monetary) rises with the <b>sum</b> (L + R), not with the imbalance (L − R).</div>
</div>

<div class="section"><h2>What this changes about the story</h2>
<div class="callout"><b>Before:</b> &ldquo;social memory is left-lateralized, monetary is right-lateralized&rdquo; — a puzzling, fragile double dissociation that reads like it might be noise.<br><br>
<b>After:</b> &ldquo;the overall strength of the VTA→HPC pathway biases memory toward the social domain at the expense of the monetary one.&rdquo; One bilateral individual-differences dimension, not a hemispheric flip. That is a cleaner and more defensible claim — and it reframes the odd <i>negative</i> monetary effect not as a hemisphere-specific quirk but as the other end of a single tradeoff axis.</div>
</div>

<div class="section"><h2>Honest caveats</h2>
<div class="callout warn"><b>This is a reframing of the same data, not independent replication.</b> The bilateral-level effect is the single interaction that the two original cluster findings logically imply; testing it here characterizes the phenomenon correctly but does not add out-of-sample confirmation. A regression on the difference score <i>is</i> the corresponding domain × predictor interaction test — the balance-null and level-effect are two readouts of the same model, not independent experiments.</div>
<div class="callout warn"><b>Small sample, mid-range p-values.</b> n≈40 after covariate/d′ listwise deletion; the level effects are p≈0.01–0.03, real but not bulletproof. The direct-question answer (balance = null) is robust across both metrics; the &ldquo;it&rsquo;s the sum&rdquo; conclusion follows algebraically from social(+) and monetary(−) sharing a density substrate and is corroborated empirically here.</div>
</div>

<div class="section"><h2>Method references (documentation)</h2>{refs}</div>

<div class="section" style="text-align:center;color:var(--mut);font-size:13px">
Data: <code>data/asymmetry_measures.csv</code> · Models: <code>scripts/html_builders/asym_full.py</code> · Mid-tract profiles: <code>data.check/step27_fa/</code>, <code>data.check/step30_noddi/</code><br><br>
<a class="back" href="results_explorer.html">← Results Explorer</a> &nbsp;·&nbsp; <a class="back" href="hpc_region_vs_connection.html">HPC Region vs. Connection →</a>
</div>
</div></body></html>'''
open(f'{OUT}/asymmetry.html','w').write(html)
print("wrote asymmetry.html",len(html),"bytes")
