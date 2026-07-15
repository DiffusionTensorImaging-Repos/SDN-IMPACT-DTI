import json, csv
OUT='/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/results_html'
meta=json.load(open(f'{OUT}/meta_data.json'))
dq=meta['data_quality']; dp=dq['dprime']
bd=json.load(open(f'{OUT}/dprime_breakdown.json'))

def compliance_svg():
    rows=[]
    with open('/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/data/compliance_screen.csv') as f:
        for r in csv.DictReader(f):
            if r['condition']=='SOCIAL': rows.append((r['Subject'],float(r['remember_rate'])*100))
    rows.sort(key=lambda x:x[1]); n=len(rows)
    W,H,PL,PR,PT,PB=640,250,44,14,16,34
    def sx(i): return PL+(W-PL-PR)*i/(n-1)
    def sy(v): return PT+(H-PT-PB)*(1-v/105)
    dots=''
    for i,(sub,rate) in enumerate(rows):
        if rate>=95: c,r='#e34948',5
        elif sub=='s4127': c,r='#1baf7a',6
        else: c,r='#9aa3b2',3.2
        dots+=f'<circle cx="{sx(i):.1f}" cy="{sy(rate):.1f}" r="{r}" fill="{c}"/>'
        if rate>=95 or sub=='s4127':
            dots+=f'<text x="{sx(i):.1f}" y="{sy(rate)-9:.1f}" fill="{c}" font-size="10" text-anchor="middle">{sub}</text>'
    thr=sy(95)
    yt=''.join(f'<text x="{PL-7}" y="{sy(v)+3:.0f}" fill="#6b7280" font-size="9" text-anchor="end">{v}%</text><line x1="{PL-3}" y1="{sy(v):.0f}" x2="{PL}" y2="{sy(v):.0f}" stroke="#3a3f4b"/>' for v in [0,50,95])
    return (f'<svg viewBox="0 0 {W} {H}" width="100%" style="max-width:640px" role="img" aria-label="Sorted remember-rate per mother; s4210 and s1350 exceed the 95% compliance cutoff">'
      f'<line x1="{PL}" y1="{thr:.1f}" x2="{W-PR}" y2="{thr:.1f}" stroke="#e34948" stroke-width="1.3" stroke-dasharray="6 5"/>'
      f'<text x="{W-PR}" y="{thr-5:.0f}" fill="#e34948" font-size="10" text-anchor="end">95% cutoff → excluded</text>'
      f'<line x1="{PL}" y1="{PT}" x2="{PL}" y2="{H-PB}" stroke="#3a3f4b"/><line x1="{PL}" y1="{H-PB}" x2="{W-PR}" y2="{H-PB}" stroke="#3a3f4b"/>'
      f'{yt}{dots}'
      f'<text x="{(PL+W-PR)/2:.0f}" y="{H-6}" fill="#9aa3b2" font-size="10" text-anchor="middle">55 mothers, ranked by "remember" rate (social recall)</text></svg>')
CSVG=compliance_svg()

def pf(p):
    p=float(p); return '&lt;0.001' if p<0.001 else f'{p:g}'
def chip(p): return '<span class="yes">above chance</span>' if float(p)<0.05 else '<span class="no">at chance</span>'

def brow(label,c,hint):
    diff=c['diff']; sig='yes' if c['p']<0.05 else 'no'
    verdict=('<span class="yes">differ</span>' if c['p']<0.05 else '<span class="no">no difference</span>')
    return f"<tr><td>{label}</td><td>{c['social']}</td><td>{c['monetary']}</td><td>{diff:+}</td><td>t={c['t']}, p={pf(c['p'])}</td><td>{verdict}</td></tr>"

html=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>IMPACT — Memory data &amp; d′</title>
<style>
:root{{--bg:#0f1117;--card:#1a1d27;--card2:#232733;--ink:#e6e9ef;--mut:#9aa3b2;--line:#2c3140;--accent:#a78bfa;--yes:#22c55e;--no:#64748b;}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:14.5px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}
header{{padding:22px 26px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#171a24,#0f1117)}}
h1{{margin:0 0 4px;font-size:22px}}.sub{{color:var(--mut);font-size:13px}}
.wrap{{padding:20px 26px;max-width:960px;margin:0 auto}}
.section{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 22px;margin:16px 0}}
.section h2{{margin:0 0 6px;font-size:17px;color:var(--accent)}}
.section .lead{{color:var(--mut);font-size:13px;margin-bottom:14px}}
table{{width:100%;border-collapse:collapse;font-size:13.5px;margin:8px 0}}
th{{text-align:left;color:var(--mut);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.04em;padding:8px 10px;border-bottom:1px solid var(--line)}}
td{{padding:9px 10px;border-bottom:1px solid #20242f}}
.yes{{color:var(--yes);font-weight:600}}.no{{color:var(--no);font-weight:600}}
.stat{{display:inline-block;background:var(--card2);border:1px solid var(--line);border-radius:9px;padding:12px 15px;margin:4px 6px 4px 0}}
.stat .k{{color:var(--mut);font-size:11px;text-transform:uppercase}}.stat .v{{font-size:20px;font-weight:700;margin-top:2px}}
.callout{{background:var(--card2);border-left:3px solid var(--accent);border-radius:6px;padding:12px 15px;margin:12px 0;font-size:13.5px}}
.callout.key{{border-left-color:var(--yes)}}
.formula{{font-family:ui-monospace,Menlo,monospace;background:#12141c;border:1px solid var(--line);border-radius:8px;padding:14px 16px;font-size:13.5px;line-height:1.7;color:#c9d1e0}}
a.back{{color:var(--accent);text-decoration:none}} .mut{{color:var(--mut)}}
</style></head><body>
<header><h1>IMPACT · Memory data &amp; d′</h1>
<div class="sub">How the memory scores are computed, cleaned, and what they show — for the {dp['social']['n']}–{dp['monetary']['n']} mothers in the tract analyses. &nbsp;·&nbsp; <a class="back" href="results_explorer.html">← Results Explorer</a></div></header>
<div class="wrap">

<div class="section">
<h2>1 · How d′ is computed</h2>
<div class="lead">Standard signal-detection theory, computed directly from each mother's raw trial files.</div>
<p>At encoding, a mother chooses between two faces (social) or two doors (monetary). At recall she sees items and says whether she "remembers" each. "Old" items = the ones she <i>chose</i> at encoding; "new" items = the foils she saw but did <i>not</i> choose.</p>
<div class="formula">hit rate  (H) = "remember" responses to OLD items / # OLD items
false-alarm (F) = "remember" responses to NEW items / # NEW items

d′ = z(H) − z(F)        <span class="mut"># z = inverse-normal (probit)</span></div>
<div class="callout">d′ is computed <b>directly from each mother's raw trial files</b> with this standard formula — one transparent computation, straight from the responses.</div>
</div>

<div class="section">
<h2>2 · Data cleaning — two screens, applied before any analysis</h2>
<div class="lead">Nothing was removed to chase a result. Two objective screens catch unusable sessions; the d′ formula never changes. Both are run <i>before</i> the tract analyses (catching them late forces re-runs).</div>

<h3 style="font-size:14px;color:var(--mut);margin-top:6px">Screen 1 — broken sessions</h3>
<table><thead><tr><th>Subject</th><th>Problem</th><th>Excluded from</th></tr></thead><tbody>
<tr><td><b>s1694</b></td><td>Only 16% of "recalled" items were ever shown at encoding — a corrupted / mismatched session (and >½ missed on monetary)</td><td>both conditions</td></tr>
<tr><td><b>s1350</b></td><td>Missed &gt; ⅓ of the <i>social</i> recall trials (monetary session clean)</td><td>social only</td></tr>
</tbody></table>

<h3 style="font-size:14px;color:var(--mut);margin-top:16px">Screen 2 — compliance ("yes-to-everything")</h3>
<p>A mother who presses "remember" to nearly every item — the new foils <i>and</i> the old items — isn't discriminating at all: her hit rate and false-alarm rate are both ≈ 1, so her d′ ≈ 0 carries no memory signal (it's a stuck "yes," not memory). We exclude any condition where the "remember" rate is <b>≥ 95%</b> (equivalently, a false-alarm rate ≥ 95% — saying "remember" to nearly every new foil). Script: <code>scripts/compliance_screen.py</code>.</p>
<table><thead><tr><th>Subject</th><th>"Remember" rate</th><th>Excluded from</th></tr></thead><tbody>
<tr><td><b>s4210</b></td><td>100% social &amp; 100% monetary (FA rate 100%) — pressed "remember" to every single item</td><td>both conditions (all outcomes)</td></tr>
</tbody></table>
<div style="margin:14px 0 4px">{CSVG}</div>
<div class="callout"><b>s4210 is non-compliant, not biased.</b> It's important not to confuse her with a genuinely positive responder: she said "remember" to <i>everything</i>, so her d′ and her bias are both meaningless. She is removed from every memory outcome.</div>

<h3 style="font-size:14px;color:var(--mut);margin-top:16px">Bias scoring — the zero-valence rule</h3>
<p>Each positivity bias is a <b>positive-rate − negative-rate</b> contrast. A <i>valid</i> mother who simply never used one valence (e.g. never judged a face a "loss") has a <code>0 ÷ 0</code> negative term. We set that term to <b>0</b> — she produced zero negative memories, so her negative rate is 0, not undefined — giving her a <b>defined, maximal-positivity</b> score instead of dropping her. This changes only zero-valence subjects; every other score is identical to the plain difference, and (because compliance is screened first) it never rescues a "yes-to-everything" responder. Script: <code>scripts/compute_bias_scores.py</code>.</p>
<div class="callout key"><b>Example — s4127.</b> Compliant (55% "remember" rate, real discrimination) but never once attributed a memory to "loss" — the most positively-biased mother in the sample. The rule gives her <b>FABias = +0.27</b> and <b>HitRateBias = +0.17</b> (≈ 90th percentile), so she is <i>kept</i> and scored, rather than lost to a divide-by-zero.</div>
</div>

<div class="section">
<h2>3 · Is memory above chance?</h2>
<div class="lead">Both conditions, tested against d′ = 0.</div>
<div>
 <span class="stat"><div class="k">Social d′</div><div class="v">{dp['social']['mean']:+} <span class="mut" style="font-size:12px">± {dp['social']['sd']}</span></div><div class="mut" style="font-size:11px">n={dp['social']['n']}</div></span>
 <span class="stat"><div class="k">Monetary d′</div><div class="v">{dp['monetary']['mean']:+} <span class="mut" style="font-size:12px">± {dp['monetary']['sd']}</span></div><div class="mut" style="font-size:11px">n={dp['monetary']['n']}</div></span>
</div>
<table style="margin-top:12px"><thead><tr><th>Measure</th><th>mean d′</th><th>t vs 0</th><th>p</th><th>verdict</th></tr></thead><tbody>
<tr><td>Social</td><td>{dp['social']['mean']:+}</td><td>{dp['social']['t_vs0']}</td><td>{pf(dp['social']['p_vs0'])}</td><td>{chip(dp['social']['p_vs0'])}</td></tr>
<tr><td>Monetary</td><td>{dp['monetary']['mean']:+}</td><td>{dp['monetary']['t_vs0']}</td><td>{pf(dp['monetary']['p_vs0'])}</td><td>{chip(dp['monetary']['p_vs0'])}</td></tr>
</tbody></table>
<div class="callout key"><b>Both are above chance.</b> Social and monetary d′ are also uncorrelated at the subject level (r = {dp['correlation']['r']}, p = {pf(dp['correlation']['p'])}) — they are distinct abilities, not two views of one signal.</div>
</div>

<div class="section">
<h2>4 · Why is social d′ lower than monetary? — the breakdown</h2>
<div class="lead">d′ has two ingredients: hit rate (memory strength) and false-alarm rate (false positives). Splitting them shows the difference is <b>entirely</b> in false alarms.</div>
<table><thead><tr><th>Component</th><th>Social</th><th>Monetary</th><th>diff (S−M)</th><th>paired test</th><th>differ?</th></tr></thead><tbody>
{brow('Hit rate <span class="mut">(remembered correctly)</span>',bd['hit'],'')}
{brow('False-alarm rate <span class="mut">(false positives)</span>',bd['fa'],'')}
{brow("d′ <span class=\"mut\">(overall sensitivity)</span>",bd['dprime'],'')}
</tbody></table>
<div class="callout key"><b>Social and monetary items are remembered equally well</b> — hit rates are essentially identical ({bd['hit']['social']} vs {bd['hit']['monetary']}, p = {pf(bd['hit']['p'])}). The <i>only</i> difference is that the social task produces <b>significantly more false alarms</b> ({bd['fa']['social']} vs {bd['fa']['monetary']}, <b>p = {pf(bd['fa']['p'])}</b>): mothers more often falsely "remember" social faces they never chose. So the lower social d′ is <b>not weaker memory — it's more false positives</b>.</div>
<div class="callout">This is exactly the phenomenon the tract findings are about. The robust VTA→HPC effect is on <b>social positivity bias in false memories</b> — and here we see, at the behavioural level, that false memories are precisely what distinguishes the social task. Memory <i>strength</i> is matched across domains; the social signal lives in the <i>false-alarm</i> side.</div>
</div>

<div class="section" style="text-align:center;color:var(--mut);font-size:13px">
Covariates in every tract model: absolute head motion · intracranial volume · streamline count · mean streamline length · maternal age.<br>
d′ recomputed from raw trial files (<code>scripts/html_builders/recompute_dprime_all.py</code>); 2 sessions excluded for data quality.<br><br>
<a class="back" href="results_explorer.html">← Back to Results Explorer</a>
</div>
</div></body></html>'''
open(f'{OUT}/data_quality.html','w').write(html)
print("wrote clean data_quality.html",len(html),"bytes")
