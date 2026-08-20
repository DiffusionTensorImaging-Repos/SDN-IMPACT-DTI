#!/usr/bin/env python3
"""
Bias comparisons requested at the 2026-08-14 meeting.

1. Social vs monetary bias (paired) — is the bias bigger in social? (Deepu: this is
   what would support treating monetary as the low-salience/near-neutral condition.)
2. Split each subtraction bias into its positive and negative halves — is the effect
   driven by the positive rate or the negative rate ("increasing signal" vs
   "reducing interference")?
3. Simple behavioral positivity bias (Johanna, PNAS-style): of ALL your memory
   responses, what proportion were positive? No accuracy involved.

Out: data.check/bias_comparisons.csv  (+ printed tests)
"""
import pandas as pd, numpy as np
from scipy.stats import ttest_rel, ttest_1samp

GRP = '/Users/dannyzweben/Desktop/SDN/DTI/Impact-Analyses/IMPACT_grouped_export.csv'
TRIAL = '/Users/dannyzweben/Desktop/SDN/IMPACT_triallevel.csv'
ROSTER = '/Users/dannyzweben/Desktop/SDN/DTI/data.check/analysis_ready_bilateral/vta_anthipp__NDI__analysis.csv'
OUT = '/Users/dannyzweben/Desktop/SDN/DTI/data.check/bias_comparisons.csv'

ready = pd.read_csv(ROSTER)
roster = set(ready['Subject'])
g = pd.read_csv(GRP).rename(columns={'ID': 'Subject'}).drop_duplicates('Subject')
g = g[g['Subject'].isin(roster)].copy()


def rate(num, den):
    n = pd.to_numeric(num, errors='coerce'); d = pd.to_numeric(den, errors='coerce')
    return np.where(d > 0, n / d.replace(0, np.nan), 0.0)


# --- component rates behind each bias score ---
for c in ['SOCIAL', 'MONETARY']:
    g[f'{c}_Hit_pos'] = rate(g[f'{c}_TrueMem_positive'],  g[f'{c}_Total_pos'])
    g[f'{c}_Hit_neg'] = rate(g[f'{c}_TrueMem_negative'],  g[f'{c}_Total_neg'])
    g[f'{c}_FA_pos']  = rate(g[f'{c}_FalseMem_positive'], g[f'{c}_Total_pos'])
    g[f'{c}_FA_neg']  = rate(g[f'{c}_FalseMem_negative'], g[f'{c}_Total_neg'])
    g[f'{c}_HitRateBias'] = g[f'{c}_Hit_pos'] - g[f'{c}_Hit_neg']
    g[f'{c}_FABias']      = g[f'{c}_FA_pos']  - g[f'{c}_FA_neg']

# --- simple behavioral positivity bias: % of ALL memory responses that were positive ---
d = pd.read_csv(TRIAL)
d = d[d['recall_selection'].astype(str) != 'missed'].copy()
d['isrec'] = d['recall_selection'].astype(str).str.startswith('recall')
mem = d[d['isrec']].copy()
mem['val'] = mem['recall_selection'].astype(str).str.replace('recall_', '', regex=False)
rows = []
for (sid, dom), gg in mem.groupby(['ID', 'domain']):
    if sid not in roster or len(gg) < 5:
        continue
    rows.append(dict(Subject=sid, domain=dom, n_mem=len(gg),
                     pct_positive=(gg['val'] == 'positive').mean(),
                     pct_negative=(gg['val'] == 'negative').mean(),
                     pct_neutral=(gg['val'] == 'neutral').mean()))
simple = pd.DataFrame(rows)
piv = simple.pivot_table(index='Subject', columns='domain', values='pct_positive')

print("=== 1. Social vs monetary bias (paired) ===")
res = []
for name in ['HitRateBias', 'FABias']:
    m = g[[f'SOCIAL_{name}', f'MONETARY_{name}']].dropna()
    t, p = ttest_rel(m[f'SOCIAL_{name}'], m[f'MONETARY_{name}'])
    print(f"  {name:12s}: social={m[f'SOCIAL_{name}'].mean():+.3f}  monetary={m[f'MONETARY_{name}'].mean():+.3f}  "
          f"t={t:+.2f} p={p:.3f} n={len(m)}")
    res.append(dict(test=f'{name} social vs monetary', social=m[f'SOCIAL_{name}'].mean(),
                    monetary=m[f'MONETARY_{name}'].mean(), t=t, p=p, n=len(m)))

print("\n=== 2. Is each bias driven by the positive or the negative side? ===")
print("   (each rate tested against the other; bias = pos - neg)")
for c in ['SOCIAL', 'MONETARY']:
    for name, pos, neg in [('HitRateBias', f'{c}_Hit_pos', f'{c}_Hit_neg'),
                           ('FABias',      f'{c}_FA_pos',  f'{c}_FA_neg')]:
        m = g[[pos, neg]].dropna()
        t, p = ttest_rel(m[pos], m[neg])
        print(f"  {c:8s} {name:12s}: pos-rate={m[pos].mean():.3f}  neg-rate={m[neg].mean():.3f}  "
              f"diff={m[pos].mean()-m[neg].mean():+.3f}  t={t:+.2f} p={p:.4f}")
        res.append(dict(test=f'{c} {name} pos vs neg rate', social=m[pos].mean(),
                        monetary=m[neg].mean(), t=t, p=p, n=len(m)))

print("\n=== 3. Simple behavioral positivity bias (% of all memories that were positive) ===")
for dom in ['social', 'monetary']:
    s = simple[simple['domain'] == dom]
    t, p = ttest_1samp(s['pct_positive'], 1/3)   # vs equal use of pos/neg/neutral
    print(f"  {dom:9s}: {100*s['pct_positive'].mean():.1f}% positive, "
          f"{100*s['pct_negative'].mean():.1f}% negative, {100*s['pct_neutral'].mean():.1f}% neutral "
          f"| vs 33.3%: t={t:+.2f} p={p:.2g} n={len(s)}")
if {'social', 'monetary'} <= set(piv.columns):
    m = piv.dropna()
    t, p = ttest_rel(m['social'], m['monetary'])
    print(f"  social vs monetary % positive: t={t:+.2f} p={p:.3f} n={len(m)}")

simple.to_csv(OUT, index=False)
print(f"\n-> wrote {OUT}")
