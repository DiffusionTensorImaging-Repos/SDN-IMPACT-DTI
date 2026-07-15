"""
Positivity-bias scores (HitRateBias, FABias) from the study's valence-coded counts,
with the zero-valence rule, written into the analysis-ready CSVs.

Two scores per condition:
  HitRateBias = TrueMem_pos/Total_pos  - TrueMem_neg/Total_neg   (bias in CORRECT memories)
  FABias      = FalseMem_pos/Total_pos - FalseMem_neg/Total_neg  (bias in FALSE  memories)

Zero-valence rule: a term whose denominator is 0 is set to 0 (the subject produced zero
memories of that valence, so that rate is 0 — not undefined). This gives a DEFINED, maximal
score to valid mothers who never used one valence (e.g. never judged a face a "loss" =
maximally positive), instead of dropping them. It changes only zero-valence subjects; every
other score is identical to the plain difference. Non-compliant mothers (see
compliance_screen.py) are already NaN in d' and stay excluded here — this rule never rescues
a "yes-to-everything" responder, because compliance is screened first.

Validity: a bias score is kept exactly where that condition's d' is valid (same DQ gates),
and NaN otherwise. Run AFTER d' + compliance exclusions are applied to analysis_ready.
"""
import pandas as pd, numpy as np, glob

GRP = '/Users/dannyzweben/Desktop/SDN/DTI/Impact-Analyses/IMPACT_grouped_export.csv'
AR  = '/Users/dannyzweben/Desktop/SDN/DTI/data.check/analysis_ready'

def rate(numer, denom):
    n = pd.to_numeric(numer, errors='coerce'); d = pd.to_numeric(denom, errors='coerce')
    return np.where(d > 0, n / d.replace(0, np.nan), 0.0)   # zero-valence rule: 0/0 -> 0

def bias_table():
    g = pd.read_csv(GRP).rename(columns={'ID': 'Subject'}).drop_duplicates('Subject')
    out = g[['Subject']].copy()
    for c in ['SOCIAL', 'MONETARY']:
        out[f'{c}_HitRateBias'] = rate(g[f'{c}_TrueMem_positive'],  g[f'{c}_Total_pos']) - rate(g[f'{c}_TrueMem_negative'],  g[f'{c}_Total_neg'])
        out[f'{c}_FABias']      = rate(g[f'{c}_FalseMem_positive'], g[f'{c}_Total_pos']) - rate(g[f'{c}_FalseMem_negative'], g[f'{c}_Total_neg'])
    return out

def main():
    b = bias_table()
    biascols = [c for c in b.columns if c != 'Subject']
    dcol = {'SOCIAL_HitRateBias': 'SOCIAL_dprime', 'SOCIAL_FABias': 'SOCIAL_dprime',
            'MONETARY_HitRateBias': 'MONETARY_dprime', 'MONETARY_FABias': 'MONETARY_dprime'}
    for f in glob.glob(f'{AR}/*__analysis.csv'):
        df = pd.read_csv(f)
        merged = df[['Subject']].merge(b, on='Subject', how='left')
        for bc in biascols:
            valid = pd.to_numeric(df[dcol[bc]], errors='coerce').notna()   # bias valid where d' is valid
            df[bc] = np.where(valid.values, merged[bc].values, np.nan)
        df.to_csv(f, index=False)
    # report Ns on the reference file
    ref = pd.read_csv(f'{AR}/r_vta_r_hipp__NDI__analysis.csv')
    print("Bias scores written (zero-valence rule; valid where d' is valid). Per-outcome N:")
    for bc in ['SOCIAL_FABias', 'SOCIAL_HitRateBias', 'MONETARY_FABias', 'MONETARY_HitRateBias']:
        print(f"  {bc:22s} N={pd.to_numeric(ref[bc], errors='coerce').notna().sum()}")

if __name__ == '__main__':
    main()
