import pandas as pd, numpy as np, glob, json, os
from scipy.stats import norm, pearsonr
def z(p): return norm.ppf(np.clip(p,1e-6,1-1e-6))
base='/tmp/alltsv'
grp=pd.read_csv('/Users/dannyzweben/Desktop/SDN/DTI/Impact-Analyses/IMPACT_grouped_export.csv').drop_duplicates('ID')
ready=pd.read_csv('/Users/dannyzweben/Desktop/SDN/DTI/data.check/analysis_ready/r_vta_r_hipp__NDI__analysis.csv')
subs=set(ready['Subject'])

def recompute(subj,cond):
    tag='social' if cond=='SOCIAL' else 'monetary'
    dt='decision_social' if cond=='SOCIAL' else 'decision_monetary'
    ef=[f for f in glob.glob(f'{base}/{subj}/*Encoding_{tag}*.tsv') if 'practice' not in f]
    rf=glob.glob(f'{base}/{subj}/*Recall_{tag}*.tsv'); rf=[f for f in rf if 'practice' not in f]
    if not ef or not rf: return None
    enc=pd.read_csv(ef[0],sep='\t'); rec=pd.read_csv(rf[0],sep='\t')
    edec=enc[enc['trial_type'].astype(str).str.startswith(f'decision_{tag}')].copy()
    chosen,notchosen=set(),set()
    for _,r in edec.iterrows():
        if r.get('selection')=='right': chosen.add(r.get('image_right')); notchosen.add(r.get('image_left'))
        elif r.get('selection')=='left': chosen.add(r.get('image_left')); notchosen.add(r.get('image_right'))
    rdec=rec[rec['trial_type']==dt].copy(); rdec=rdec[rdec['selection']!='missed']
    isrecall=rdec['selection'].astype(str).str.startswith('recall')
    hit=((isrecall)&(rdec['image'].isin(chosen))).sum(); nold=rdec['image'].isin(chosen).sum()
    fatot=((isrecall)&(rdec['image'].isin(notchosen))).sum(); nnew=rdec['image'].isin(notchosen).sum()
    if nold<5 or nnew<5: return None
    H=hit/nold; F=fatot/nnew
    return z(H)-z(F)

rows=[]
for subj in sorted(subs):
    row={'Subject':subj}
    for cond in ['SOCIAL','MONETARY']:
        mine=recompute(subj,cond)
        rep=grp[grp['ID']==subj][f'{cond}_dprime']
        row[f'{cond}_mine']=round(mine,4) if mine is not None else None
        row[f'{cond}_reported']=round(float(rep.iloc[0]),4) if len(rep) and pd.notna(rep.iloc[0]) else None
    rows.append(row)
df=pd.DataFrame(rows)
# correlations
res={}
for cond in ['SOCIAL','MONETARY']:
    d=df[[f'{cond}_mine',f'{cond}_reported']].dropna()
    r,p=pearsonr(d[f'{cond}_mine'],d[f'{cond}_reported'])
    res[cond]={'r':round(r,4),'n':len(d)}
print("Recompute vs reported:",res)
# save sample rows for HTML (subjects with both)
df.to_json('/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/results_html/dprime_recompute.json',orient='records')
# NOTE: does NOT write meta_data['data_quality']['dprime_recompute'] — build_demo_dq.py is the
# single source of truth for that value (analysis d′ vs export on the clean roster). This script's
# recompute↔export r can include DQ-excluded sessions and must not clobber the published value.
print("NOTE: meta_data recompute is owned by build_demo_dq.py; not overwriting here.")
