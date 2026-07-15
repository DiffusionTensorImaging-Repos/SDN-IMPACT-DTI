"""
d' component breakdown: split each mother's d' into hit rate (memory strength) and
false-alarm rate (false positives), then paired-compare social vs monetary. Applies the
SAME data-quality gates as the analysis: exclude corrupted (<80% recall/encode overlap),
heavily-missed (>1/3 trials), and non-compliant (>=95% "remember" = yes-to-everything).
Writes dprime_breakdown.json for the data-quality page.
"""
import pandas as pd, numpy as np, glob, json
from scipy.stats import norm, ttest_rel

TSV = '/tmp/alltsv'
ROSTER = '/Users/dannyzweben/Desktop/SDN/DTI/data.check/analysis_ready/r_vta_r_hipp__NDI__analysis.csv'
OUT = '/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/results_html/dprime_breakdown.json'
def z(p): return norm.ppf(np.clip(p, 1e-6, 1 - 1e-6))

def comp(subj, cond):
    tag = 'social' if cond == 'SOCIAL' else 'monetary'
    ef = [f for f in glob.glob(f'{TSV}/{subj}/*Encoding_{tag}*.tsv') if 'practice' not in f]
    rf = [f for f in glob.glob(f'{TSV}/{subj}/*Recall_{tag}*.tsv') if 'practice' not in f]
    if not ef or not rf: return None
    enc = pd.read_csv(ef[0], sep='\t'); rec = pd.read_csv(rf[0], sep='\t')
    edec = enc[enc['trial_type'].astype(str).str.startswith(f'decision_{tag}')]
    chosen, notchosen = set(), set()
    for _, r in edec.iterrows():
        if r.get('selection') == 'right': chosen.add(r.get('image_right')); notchosen.add(r.get('image_left'))
        elif r.get('selection') == 'left': chosen.add(r.get('image_left')); notchosen.add(r.get('image_right'))
    allrec = rec[rec['trial_type'].astype(str).str.startswith(f'decision_{tag}')]
    miss = allrec['selection'].astype(str).str.contains('missed|MISSED', case=False, na=False)
    rdec = allrec[~miss]
    rec_imgs = set(rdec['image'].dropna()); overlap = 100 * len(rec_imgs & (chosen | notchosen)) / max(len(rec_imgs), 1)
    pctmiss = 100 * miss.sum() / max(len(allrec), 1)
    isr = rdec['selection'].astype(str).str.startswith('recall')
    if overlap < 80 or pctmiss > 33 or isr.mean() >= 0.95: return None   # DQ + compliance gates
    hit = (isr & rdec['image'].isin(chosen)).sum(); nold = rdec['image'].isin(chosen).sum()
    fa = (isr & rdec['image'].isin(notchosen)).sum(); nnew = rdec['image'].isin(notchosen).sum()
    if nold < 5 or nnew < 5: return None
    return dict(H=hit / nold, F=fa / nnew, dp=z(hit / nold) - z(fa / nnew))

def main():
    roster = pd.read_csv(ROSTER)['Subject'].tolist()
    rows = {}
    for s in roster:
        for cond in ['SOCIAL', 'MONETARY']:
            c = comp(s, cond)
            if c: rows.setdefault(s, {}).update({f'{cond}_H': c['H'], f'{cond}_F': c['F'], f'{cond}_dp': c['dp']})
    df = pd.DataFrame(rows.values())
    both = df.dropna(subset=['SOCIAL_H', 'MONETARY_H'])
    def cell(scol, mcol):
        s, m = both[scol], both[mcol]; t, p = ttest_rel(s, m)
        return dict(social=round(s.mean(), 3), monetary=round(m.mean(), 3), diff=round(s.mean() - m.mean(), 3), t=round(t, 2), p=round(p, 4))
    bd = {'n': len(both), 'hit': cell('SOCIAL_H', 'MONETARY_H'), 'fa': cell('SOCIAL_F', 'MONETARY_F'), 'dprime': cell('SOCIAL_dp', 'MONETARY_dp')}
    json.dump(bd, open(OUT, 'w'), indent=1)
    print(f"dprime_breakdown.json  (n={bd['n']}): hit p={bd['hit']['p']}  fa p={bd['fa']['p']}")

if __name__ == '__main__':
    main()
