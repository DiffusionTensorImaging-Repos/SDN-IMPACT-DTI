"""
Add overall hit rate and false-alarm rate (social & monetary) as analysis outcomes.

Hit rate  = P("remember" | old item she chose at encoding)   = TrueMem / N_old
FA  rate  = P("remember" | foil she did not choose)          = FalseMem / N_new
computed per subject from the trial-level data (recall response = recall_*).

Written into every analysis-ready CSV, gated to the SAME roster as d' (valid only
where that condition's d' is valid — so the non-compliant / broken sessions stay out).
"""
import pandas as pd, numpy as np, glob

TRIAL = '/Users/dannyzweben/Desktop/SDN/IMPACT_triallevel.csv'
AR    = '/Users/dannyzweben/Desktop/SDN/DTI/data.check/analysis_ready'

def hitfa_table():
    d = pd.read_csv(TRIAL)
    d = d[d['recall_selection'].astype(str) != 'missed'].copy()
    d['isrecall'] = d['recall_selection'].astype(str).str.startswith('recall')
    d['old'] = d['selected'] == 'Selected'
    rows = []
    for (sid, dom), g in d.groupby(['ID', 'domain']):
        old, new = g[g['old']], g[~g['old']]
        if len(old) < 5 or len(new) < 5:
            continue
        rows.append({'Subject': sid, 'cond': dom.upper(),
                     'hitrate': old['isrecall'].mean(), 'farate': new['isrecall'].mean()})
    t = pd.DataFrame(rows)
    wide = t.pivot(index='Subject', columns='cond', values=['hitrate', 'farate'])
    wide.columns = [f'{c}_{m}' for m, c in wide.columns]   # SOCIAL_hitrate, ...
    return wide.reset_index()

def main():
    hf = hitfa_table()
    cols = ['SOCIAL_hitrate', 'SOCIAL_farate', 'MONETARY_hitrate', 'MONETARY_farate']
    gate = {'SOCIAL_hitrate': 'SOCIAL_dprime', 'SOCIAL_farate': 'SOCIAL_dprime',
            'MONETARY_hitrate': 'MONETARY_dprime', 'MONETARY_farate': 'MONETARY_dprime'}
    for f in glob.glob(f'{AR}/*__analysis.csv'):
        df = pd.read_csv(f)
        merged = df[['Subject']].merge(hf, on='Subject', how='left')
        for c in cols:
            valid = pd.to_numeric(df[gate[c]], errors='coerce').notna()
            df[c] = np.where(valid.values, merged[c].values, np.nan)
        df.to_csv(f, index=False)
    ref = pd.read_csv(f'{AR}/r_vta_r_hipp__NDI__analysis.csv')
    print("Added hit/FA-rate outcomes (gated to d' roster). Means on analysis roster:")
    for c in cols:
        x = pd.to_numeric(ref[c], errors='coerce').dropna()
        print(f"  {c:18s} mean={x.mean():.3f}  n={len(x)}")

if __name__ == '__main__':
    main()
