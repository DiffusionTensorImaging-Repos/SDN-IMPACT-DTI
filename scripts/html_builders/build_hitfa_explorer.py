#!/usr/bin/env python3
"""
Build results_html/hitfa_explorer.html — a standalone results explorer for the
recognition components of d': overall HIT RATE and FALSE-ALARM RATE (social &
monetary), tested against VTA->HPC tract microstructure exactly like d'/bias.

Tract-average partial correlations + hippocampus-region betas computed here;
node-wise Freedman-Lane cluster survival read from the cr2 permutation results.
"""
import pandas as pd, numpy as np, os, glob, warnings
from scipy import stats
import statsmodels.formula.api as smf
from scipy.stats import zscore
warnings.filterwarnings('ignore')

BASE = '/Users/dannyzweben/Desktop/SDN/DTI'
AR = f'{BASE}/data.check/analysis_ready'
PR = f'{BASE}/data.check/hitfa_perm_results'          # node-wise summaries/clusters from cr2
OUT = f'{BASE}/SDN-IMPACT-DTI/results_html/hitfa_explorer.html'
COV = ['ICV', 'Mean_tckstats', 'Count_tckstats', 'absolute_motion', 'maternal_age']
TRACTS = [('l_vta_l_hipp', 'post L'), ('r_vta_r_hipp', 'post R'),
          ('anterior_l_vta_l_hipp', 'ant L'), ('anterior_r_vta_r_hipp', 'ant R')]
METRICS = ['FA', 'NDI', 'ODI', 'FWF']
OUTS = [('Social hit rate', 'SOCIAL_hitrate'), ('Social false-alarm rate', 'SOCIAL_farate'),
        ('Monetary hit rate', 'MONETARY_hitrate'), ('Monetary false-alarm rate', 'MONETARY_farate')]

GREEN = 'color:#4ade80;font-weight:700'


def partial_r(tract, metric, out):
    d = pd.read_csv(f'{AR}/{tract}__{metric}__analysis.csv')
    d['mid'] = d[[f'{metric}_{i}' for i in range(25, 75)]].mean(axis=1)
    m = d[['mid', out] + COV].dropna()
    if len(m) < 10 or m[out].std() == 0:
        return np.nan, np.nan
    xr = smf.ols('mid ~ ' + '+'.join(COV), m).fit().resid
    yr = smf.ols(f'{out} ~ ' + '+'.join(COV), m).fit().resid
    return stats.pearsonr(xr, yr)


def survived(tract, metric, out):
    f = f'{PR}/{tract}__{metric}__{out}_summary.csv'
    if not os.path.exists(f):
        return None
    return int(pd.read_csv(f)['NumClustersPassingExtent'].iloc[0]) > 0


def cell(tract, metric, out):
    r, p = partial_r(tract, metric, out)
    if np.isnan(r):
        return '<td>–</td>'
    sup = '<sup>†</sup>' if survived(tract, metric, out) else ''
    style = f' style="{GREEN}"' if (p < 0.05) else ''
    return f'<td{style}>{r:+.2f}{sup}</td>'


def tract_grid():
    rows = []
    for lbl, col in OUTS:
        for i, m in enumerate(METRICS):
            first = f'<td rowspan="4"><b>{lbl}</b></td>' if i == 0 else ''
            cells = ''.join(cell(t, m, col) for t, _ in TRACTS)
            rows.append(f'<tr>{first}<td>{m}</td>{cells}</tr>')
    heads = ''.join(f'<th>{n}</th>' for _, n in TRACTS)
    return ('<table><thead><tr><th>Outcome</th><th>Metric</th>' + heads +
            '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table>')


def surviving_list():
    hits = []
    for lbl, col in OUTS:
        for t, tn in TRACTS:
            for m in METRICS:
                cf = f'{PR}/{t}__{m}__{col}_clusters.csv'
                if not os.path.exists(cf):
                    continue
                c = pd.read_csv(cf)
                c = c[c.get('PassExtentThreshold', pd.Series([], dtype=bool)) == True]
                for _, r in c.iterrows():
                    hits.append(f'<li>{lbl} · {m} · {tn}: nodes {int(r.StartNode)}–{int(r.EndNode)} '
                                f'({r.Direction}), cluster p={r.ClusterPValue:.3f}</li>')
    n_files = len(glob.glob(f'{PR}/*_summary.csv'))
    if not hits:
        return (f'<p class="mut" style="color:#9aa3b2">No cluster survived family-wise correction for any hit-rate '
                f'or false-alarm-rate outcome, in any tract or metric ({n_files}/64 analyses run).</p>')
    return '<ul style="font-size:13px;color:#c9d1e0">' + ''.join(hits) + '</ul>'


def hpc_grid():
    den = pd.read_csv(f'{BASE}/Impact-Analyses/hpc_density.csv')
    for c in den.columns[1:]:
        den[c] = pd.to_numeric(den[c], errors='coerce')
    ready = pd.read_csv(f'{AR}/r_vta_r_hipp__NDI__analysis.csv')
    cov = ready[['Subject'] + [c for _, c in OUTS] + ['ICV', 'absolute_motion', 'maternal_age']]
    df = den.merge(cov, on='Subject', how='inner')
    df['bilat_NDI'] = (df['L_HPC_NDI'] + df['R_HPC_NDI']) / 2

    def model(o, p):
        d = df[[o, p, 'ICV', 'absolute_motion', 'maternal_age']].dropna().copy()
        d[p + '_z'] = zscore(d[p])
        f = smf.ols(f'{o} ~ {p}_z + ICV + absolute_motion + maternal_age', d).fit()
        return f.params[p + '_z'], f.pvalues[p + '_z']
    rows = []
    for lbl, col in OUTS:
        cs = []
        for p in ['L_HPC_NDI', 'R_HPC_NDI', 'bilat_NDI']:
            b, pv = model(col, p)
            st = f' style="{GREEN}"' if pv < 0.05 else ''
            cs.append(f'<td{st}>{b:+.3f}</td>')
        rows.append(f'<tr><td>{lbl}</td>{"".join(cs)}</tr>')
    return ('<table><thead><tr><th>Outcome</th><th>NDI left</th><th>NDI right</th>'
            '<th>NDI bilateral</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table>')


NOTE = ('background:#232733;border-left:3px solid #a78bfa;border-radius:6px;padding:11px 14px;'
        'margin:2px 0 14px;font-size:12.5px;color:#c9d1e0')
HTML = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IMPACT — Hit rate &amp; false-alarm rate</title>
<style>
:root{{--bg:#0f1117;--card:#1a1d27;--card2:#232733;--ink:#e6e9ef;--mut:#9aa3b2;--line:#2c3140;--accent:#a78bfa;}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}
header{{padding:22px 26px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#171a24,#0f1117)}}
h1{{margin:0 0 4px;font-size:21px}} .sub{{color:var(--mut);font-size:13px}}
a{{color:var(--accent);text-decoration:none}}
.wrap{{padding:20px 26px;max-width:1200px;margin:0 auto}}
.section{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin:16px 0}}
.section h2{{margin:0 0 12px;font-size:16px;color:var(--accent)}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{text-align:left;color:var(--mut);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.04em;padding:8px 10px;border-bottom:1px solid var(--line);white-space:nowrap}}
td{{padding:8px 10px;border-bottom:1px solid #20242f;font-variant-numeric:tabular-nums}}
.legend{{font-size:12px;color:var(--mut);margin-top:10px}}
.script{{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:#c9d1e0;background:#12141c;border:1px solid var(--line);border-radius:8px;padding:10px;margin-top:4px;white-space:pre-wrap;line-height:1.45}}
summary{{cursor:pointer}}
</style></head><body>
<header>
<h1>IMPACT · Recognition components — hit rate &amp; false-alarm rate</h1>
<div class="sub">The two ingredients of d′ (<b>d′ = z(hit rate) − z(false-alarm rate)</b>), tested against VTA→HPC tract microstructure exactly like d′ and bias: 4 outcomes (social &amp; monetary × hit rate, FA rate) × 4 tracts × 4 metrics. Freedman–Lane, 5000-perm cluster-extent FWE at α=.05. &nbsp;·&nbsp; <a href="results_explorer.html">← main results explorer (d′ &amp; bias)</a></div>
</header>
<div class="wrap">

<div class="section"><h2>Tract averages</h2>
<div class="note" style="{NOTE}">Hit rate = P("remember" | old item she chose); false-alarm rate = P("remember" | foil). Each cell is the mid-tract (nodes 25–74) partial correlation of the metric with the outcome, covariates removed. <b style="color:#4ade80">Green</b> = p&lt;.05 on the average; <b>†</b> = node-wise cluster survived (cluster-extent FWE).</div>
<details style="margin:4px 0 10px"><summary style="color:#a78bfa;font-size:12.5px;font-weight:600">Each value is a partial correlation <b>r</b> — click for the model</summary>
<div class="script">For one outcome × tract × metric:
  mid   = mean of the tract's middle nodes (25-74), per subject
  x_res = residuals of  lm(mid     ~ ICV + Mean_tckstats + Count_tckstats + absolute_motion + maternal_age)
  y_res = residuals of  lm(outcome ~ ICV + Mean_tckstats + Count_tckstats + absolute_motion + maternal_age)
  r     = cor(x_res, y_res)      # partial correlation, covariates removed; two-sided p; n=52/53
Node-wise: at each of 100 nodes  lm(outcome ~ node + same covariates); adjacent p&lt;.05 nodes form a cluster,
kept if longer than the 95th percentile of the max chance cluster over 5000 Freedman-Lane permutations.</div>
</details>
{tract_grid()}
</div>

<div class="section"><h2>Surviving node-wise clusters</h2>
{surviving_list()}
</div>

<div class="section"><h2>Hippocampus</h2>
<div class="note" style="{NOTE}">Mean NDI inside the hippocampus ROI (left / right / bilateral), same covariates. β per SD.</div>
{hpc_grid()}
<div class="legend"><b style="color:#4ade80">Green</b> = p&lt;.05; β per standard deviation, n=52/53.</div>
</div>

</div></body></html>
"""

if __name__ == '__main__':
    open(OUT, 'w').write(HTML)
    print(f"wrote {OUT} ({len(HTML)} bytes)")
