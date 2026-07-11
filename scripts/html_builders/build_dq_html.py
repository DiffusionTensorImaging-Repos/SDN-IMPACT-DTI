import json
OUT='/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/results_html'
meta=json.load(open(f'{OUT}/meta_data.json'))
dq=meta['data_quality']; dp=dq['dprime']; rc=dq['dprime_recompute']; rt=dq['rt']

def sig(p): return '<span class="yes">significant</span>' if p<0.05 else '<span class="no">n.s.</span>'

recomp_rows=''.join(f"<tr><td>{r['cond'].title()}</td><td>r = {r['r_with_reported']}</td><td>{r['n']}</td></tr>" for r in rc)
rtphase=''.join(f"<tr><td>{k.replace('_',' ').title()}</td><td>{v['mean']} s</td><td>{v['sd']}</td><td>{v['n']}</td></tr>" for k,v in rt['phase_means'].items())
rtcorr=''.join(f"<tr><td>{c['label']}</td><td>r = {c['r']}</td><td>{c['p']}</td><td>{c['n']}</td><td>{sig(c['p'])}</td></tr>" for c in rt['corr_with_dprime'])

html=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>IMPACT — Data Quality &amp; d′ Background</title>
<style>
:root{{--bg:#0f1117;--card:#1a1d27;--card2:#232733;--ink:#e6e9ef;--mut:#9aa3b2;--line:#2c3140;--accent:#a78bfa;--yes:#22c55e;--no:#64748b;}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:14.5px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}
header{{padding:22px 26px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#171a24,#0f1117)}}
h1{{margin:0 0 4px;font-size:22px}}.sub{{color:var(--mut);font-size:13px}}
.wrap{{padding:20px 26px;max-width:1000px;margin:0 auto}}
.section{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 22px;margin:16px 0}}
.section h2{{margin:0 0 6px;font-size:17px;color:var(--accent)}}
.section .lead{{color:var(--mut);font-size:13px;margin-bottom:14px}}
table{{width:100%;border-collapse:collapse;font-size:13.5px;margin:8px 0}}
th{{text-align:left;color:var(--mut);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.04em;padding:8px 10px;border-bottom:1px solid var(--line)}}
td{{padding:9px 10px;border-bottom:1px solid #20242f}}
.big{{font-size:20px;font-weight:700}}
.yes{{color:var(--yes);font-weight:600}}.no{{color:var(--no);font-weight:600}}
.stat{{display:inline-block;background:var(--card2);border:1px solid var(--line);border-radius:9px;padding:12px 15px;margin:4px 6px 4px 0}}
.stat .k{{color:var(--mut);font-size:11px;text-transform:uppercase}}.stat .v{{font-size:20px;font-weight:700;margin-top:2px}}
.callout{{background:var(--card2);border-left:3px solid var(--accent);border-radius:6px;padding:12px 15px;margin:12px 0;font-size:13.5px}}
.formula{{font-family:ui-monospace,Menlo,monospace;background:#12141c;border:1px solid var(--line);border-radius:8px;padding:14px 16px;font-size:13.5px;line-height:1.7;color:#c9d1e0}}
a.back{{color:var(--accent);text-decoration:none}}
.mut{{color:var(--mut)}}
</style></head><body>
<header><h1>IMPACT · Data Quality &amp; d′ Background</h1>
<div class="sub">Everything you need to trust the memory measures — computed in <b>our analysis sample</b>. &nbsp;·&nbsp; <a class="back" href="results_explorer.html">← Back to Results Explorer</a></div></header>
<div class="wrap">

<div class="section">
<h2>1 · Are social and monetary d′ the same thing?</h2>
<div class="lead">Signal-detection sensitivity for the two memory conditions, in our DTI cohort.</div>
<div>
 <span class="stat"><div class="k">Social d′</div><div class="v">{dp['social']['mean']:+} <span class="mut" style="font-size:12px">± {dp['social']['sd']}</span></div><div class="mut" style="font-size:11px">n={dp['social']['n']}</div></span>
 <span class="stat"><div class="k">Monetary d′</div><div class="v">{dp['monetary']['mean']:+} <span class="mut" style="font-size:12px">± {dp['monetary']['sd']}</span></div><div class="mut" style="font-size:11px">n={dp['monetary']['n']}</div></span>
</div>
<h3 style="font-size:14px;color:var(--mut);margin-top:16px">Each vs chance (d′ = 0)</h3>
<table><thead><tr><th>Measure</th><th>mean</th><th>t vs 0</th><th>p</th><th>verdict</th></tr></thead><tbody>
<tr><td>Social d′</td><td>{dp['social']['mean']:+}</td><td>{dp['social']['t_vs0']}</td><td>{dp['social']['p_vs0']}</td><td>{'<span class=yes>above chance</span>' if dp['social']['p_vs0']<0.05 else '<span class=no>at chance</span>'}</td></tr>
<tr><td>Monetary d′</td><td>{dp['monetary']['mean']:+}</td><td>{dp['monetary']['t_vs0']}</td><td>{dp['monetary']['p_vs0']}</td><td>{'<span class=yes>above chance</span>' if dp['monetary']['p_vs0']<0.05 else '<span class=no>at chance</span>'}</td></tr>
</tbody></table>
<h3 style="font-size:14px;color:var(--mut);margin-top:16px">Correlated with each other?</h3>
<div class="callout"><b>No.</b> Pearson r = <b>{dp['correlation']['r']}</b>, p = {dp['correlation']['p']} (n={dp['correlation']['n']}). The two memory scores are essentially independent — a subject good at social memory isn't necessarily good at monetary memory. This supports treating the social and monetary tract findings as a genuine dissociation, not two views of one signal.</div>
<h3 style="font-size:14px;color:var(--mut)">Significantly different from each other?</h3>
<table><thead><tr><th>Test</th><th>mean diff (soc−mon)</th><th>stat</th><th>p</th></tr></thead><tbody>
<tr><td>Paired t-test</td><td>{dp['paired_diff']['mean_diff']:+}</td><td>t = {dp['paired_diff']['t']}</td><td>{dp['paired_diff']['p']}</td></tr>
<tr><td>Wilcoxon signed-rank</td><td>—</td><td>—</td><td>{dp['paired_diff']['wilcoxon_p']}</td></tr>
</tbody></table>
<div class="mut" style="font-size:12.5px">Parametric test marginal; non-parametric significant → social discrimination is slightly higher on average, but the two remain uncorrelated at the subject level.</div>
</div>

<div class="section">
<h2>2 · How d′ was calculated</h2>
<div class="lead">Standard signal-detection theory. "Old" items = faces you <i>chose</i> at encoding (received feedback); "new" items = faces you saw but did <i>not</i> choose (foils).</div>
<div class="formula">hit rate  (H) = # "remember" responses to OLD faces / # OLD faces
false-alarm (F) = # "remember" responses to NEW faces / # NEW faces

d′ = z(H) − z(F)        <span class="mut"># z = inverse-normal (probit)</span>
bias c = −½ · (z(H) + z(F))   <span class="mut"># criterion / response bias</span></div>
<div class="callout">Our independent recomputation of d′ from the raw trial files reproduces the analysis values almost exactly:
<table style="margin-top:8px"><thead><tr><th>Condition</th><th>correlation (ours vs used)</th><th>n</th></tr></thead><tbody>{recomp_rows}</tbody></table>
So the d′ we analyzed is a standard valence-blind recognition d′ — verified end-to-end.</div>
</div>

<div class="section">
<h2>3 · Does response time confound the findings?</h2>
<div class="lead">Mean response time per phase, and whether RT drives the tract effects.</div>
<table><thead><tr><th>Phase</th><th>mean RT</th><th>SD</th><th>n</th></tr></thead><tbody>{rtphase}</tbody></table>
<div class="callout"><b>RT did not differ between social and monetary recall</b> (t = {rt['social_vs_monetary_recall']['t']}, p = {rt['social_vs_monetary_recall']['p']}, n={rt['social_vs_monetary_recall']['n']}) — the two tasks were matched on speed.</div>
<h3 style="font-size:14px;color:var(--mut)">RT × d′ (individual differences)</h3>
<table><thead><tr><th>Relationship</th><th>r</th><th>p</th><th>n</th><th></th></tr></thead><tbody>{rtcorr}</tbody></table>
<div class="callout" style="border-left-color:var(--yes)"><b>The tract findings are NOT an RT artifact.</b> Monetary d′ correlates with RT (slower → better), so we re-ran all three monetary FWE clusters with recall-RT added as a covariate. <b>All three survived and got slightly stronger:</b>
<table style="margin-top:8px"><thead><tr><th>Monetary cluster</th><th>original p</th><th>+ RT covariate</th></tr></thead><tbody>
<tr><td>Posterior R · NDI (d′)</td><td>0.017</td><td><b>0.011</b></td></tr>
<tr><td>Posterior R · NDI (false-mem rate)</td><td>0.018</td><td><b>0.014</b></td></tr>
<tr><td>Anterior R · FWF (d′)</td><td>0.048</td><td><b>0.037</b></td></tr>
</tbody></table>
The tract-microstructure signal is independent of response caution.</div>
</div>

<div class="section" style="text-align:center;color:var(--mut);font-size:13px">
Covariates in every model: absolute head motion (eddy QUAD) · intracranial volume · streamline count · mean streamline length · maternal age.<br>
Handedness was not collected in IMPACT (verified across REDCap, DICOM/JSON, and task files) and is therefore omitted.<br><br>
<a class="back" href="results_explorer.html">← Back to Results Explorer</a>
</div>
</div></body></html>'''
open(f'{OUT}/data_quality.html','w').write(html)
print("wrote data_quality.html",len(html),"bytes")
