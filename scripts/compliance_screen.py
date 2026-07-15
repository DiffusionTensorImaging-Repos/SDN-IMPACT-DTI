"""
Compliance screen — a PRE-ANALYSIS data-quality gate for the memory task.

Flags "yes-to-everything" responders: mothers who pressed "remember" to ~all items
(old AND new foils), so they never discriminated. Their d' is degenerate (hit rate =
false-alarm rate) and their responses carry no memory signal — they must be excluded
from every memory outcome BEFORE the tract analyses (catching this late forces re-runs).

Rule: exclude a condition if the subject called >= 95% of items "remember"
(equivalently, a false-alarm rate >= 0.95 — saying "remember" to nearly every new foil).

Usage: python compliance_screen.py   ->  prints the screen + writes compliance_screen.csv
"""
import pandas as pd, numpy as np, glob, os

TSV_ROOT = '/tmp/alltsv'   # raw per-subject trial files
ROSTER   = '/Users/dannyzweben/Desktop/SDN/DTI/data.check/analysis_ready/r_vta_r_hipp__NDI__analysis.csv'
OUT      = '/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/data/compliance_screen.csv'
THRESH   = 0.95

def screen(subj, cond):
    tag = 'social' if cond == 'SOCIAL' else 'monetary'
    ef = [f for f in glob.glob(f'{TSV_ROOT}/{subj}/*Encoding_{tag}*.tsv') if 'practice' not in f]
    rf = [f for f in glob.glob(f'{TSV_ROOT}/{subj}/*Recall_{tag}*.tsv')   if 'practice' not in f]
    if not ef or not rf:
        return None
    enc = pd.read_csv(ef[0], sep='\t'); rec = pd.read_csv(rf[0], sep='\t')
    edec = enc[enc['trial_type'].astype(str).str.startswith(f'decision_{tag}')]
    chosen, notchosen = set(), set()
    for _, r in edec.iterrows():
        if r.get('selection') == 'right': chosen.add(r.get('image_right')); notchosen.add(r.get('image_left'))
        elif r.get('selection') == 'left': chosen.add(r.get('image_left')); notchosen.add(r.get('image_right'))
    rdec = rec[rec['trial_type'].astype(str).str.startswith(f'decision_{tag}')]
    rdec = rdec[~rdec['selection'].astype(str).str.contains('missed|MISSED', case=False, na=False)]
    if len(rdec) == 0:
        return None
    isrecall = rdec['selection'].astype(str).str.startswith('recall')  # "I remember this"
    new = rdec['image'].isin(notchosen)
    return dict(remember_rate=round(isrecall.mean(), 3),
                fa_rate=round((isrecall & new).sum() / max(new.sum(), 1), 3))

def main():
    roster = pd.read_csv(ROSTER)['Subject'].tolist()
    rows = []
    for s in roster:
        for cond in ['SOCIAL', 'MONETARY']:
            r = screen(s, cond)
            if r:
                rows.append(dict(Subject=s, condition=cond, **r,
                                 non_compliant=bool(r['remember_rate'] >= THRESH)))
    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    df.to_csv(OUT, index=False)
    flagged = df[df['non_compliant']]
    print(f"Compliance screen (threshold: remember-rate >= {THRESH:.0%}):")
    print(f"  {df['Subject'].nunique()} mothers screened across both conditions.")
    print(f"  NON-COMPLIANT (excluded from that condition's memory outcomes):")
    if flagged.empty:
        print("    none")
    for r in flagged.itertuples():
        print(f"    {r.Subject} [{r.condition}]: remember-rate={r.remember_rate:.0%}  false-alarm-rate={r.fa_rate:.0%}")
    print(f"  -> wrote {OUT}")

if __name__ == '__main__':
    main()
