#!/usr/bin/env python3
"""
Per-subject binomial test on raw recognition (Deepu's request, 2026-08-14 meeting).

Question: is each mother individually above chance at telling old (chosen at encoding)
from new (foil) items? A d' near 0 could be real-but-small memory, or noise hovering
around chance. The binomial test labels who is actually above chance.

Recognition is "remember" (recall_*) vs "predict" (predict_*): responding remember to
an old item = hit; responding predict to a new item = correct rejection. Old/new and
remember/predict are both ~balanced in the data, so chance = 0.5.

Out: data.check/binomial_test_subjects.csv (per subject x domain: correct, n, acc, p, pass)
"""
import pandas as pd
from scipy.stats import binomtest

TRIAL = '/Users/dannyzweben/Desktop/SDN/IMPACT_triallevel.csv'
ROSTER = '/Users/dannyzweben/Desktop/SDN/DTI/data.check/analysis_ready_bilateral/vta_anthipp__NDI__analysis.csv'
OUT = '/Users/dannyzweben/Desktop/SDN/DTI/data.check/binomial_test_subjects.csv'

d = pd.read_csv(TRIAL)
d = d[d['recall_selection'].astype(str) != 'missed'].copy()
d['isrec'] = d['recall_selection'].astype(str).str.startswith('recall')
d['old'] = d['selected'] == 'Selected'
roster = set(pd.read_csv(ROSTER)['Subject'])

rows = []
for (sid, dom), g in d.groupby(['ID', 'domain']):
    if sid not in roster or len(g) < 10:
        continue
    correct = int(((g['isrec']) & (g['old'])).sum() + ((~g['isrec']) & (~g['old'])).sum())
    n = int(len(g))
    p = binomtest(correct, n, 0.5, alternative='greater').pvalue
    rows.append(dict(ID=sid, domain=dom, correct=correct, n=n,
                     acc=correct / n, p=p, passed=bool(p < 0.05)))

r = pd.DataFrame(rows)
r.to_csv(OUT, index=False)

print("=== per-subject binomial test (recognition vs chance, one-sided) ===")
for dom in ['social', 'monetary']:
    s = r[r['domain'] == dom]
    print(f"  {dom:9s}: {int(s['passed'].sum())}/{len(s)} above chance "
          f"({100*s['passed'].mean():.0f}%) | acc mean={s['acc'].mean():.3f} "
          f"sd={s['acc'].std():.3f} max={s['acc'].max():.3f} | median trials={s['n'].median():.0f}")

p = r.pivot_table(index='ID', columns='domain', values='passed').fillna(0).astype(bool)
if {'social', 'monetary'} <= set(p.columns):
    print(f"  pass BOTH: {int((p['social'] & p['monetary']).sum())} | "
          f"pass EITHER: {int((p['social'] | p['monetary']).sum())} | "
          f"pass NEITHER: {int((~p['social'] & ~p['monetary']).sum())}")
print(f"  -> wrote {OUT}")
