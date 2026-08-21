#!/usr/bin/env python3
"""
d-prime with the standard corrections for boundary hit/FA rates.

Raw d' is undefined at rates of 0 or 1. In this dataset s1350 (hit=.92, FA=1.00) produced
d' = -3.33, which suppressed the node-wise cluster test (24 nodes vs a 25 threshold).

  log-linear (Hautus 1995): (hits+0.5)/(n_old+1), (fa+0.5)/(n_new+1) -- applied to EVERYONE
  Snodgrass & Corwin (1988): adjust only boundary values by 1/(2N)

The two agree at r = .998. Log-linear is used as primary.

Note: in this task the "new" items are the co-presented pair partners (seen but not chosen),
so d' indexes memory for WHICH person delivered feedback, i.e. source memory.

Out: data.check/dprime_corrected.csv
"""
import pandas as pd, numpy as np
from scipy.stats import norm

TRIAL='/Users/dannyzweben/Desktop/SDN/IMPACT_triallevel.csv'
OUT='/Users/dannyzweben/Desktop/SDN/DTI/data.check/dprime_corrected.csv'
def z(p): return norm.ppf(np.clip(p,1e-6,1-1e-6))

d=pd.read_csv(TRIAL)
d=d[d['recall_selection'].astype(str)!='missed'].copy()
d['said_rem']=d['recall_selection'].astype(str).str.startswith('recall')
d['chosen']=d['selected']=='Selected'

rows=[]
for (sid,dom),g in d.groupby(['ID','domain']):
    ch=g[g['chosen']]; un=g[~g['chosen']]
    if len(ch)<10 or len(un)<10: continue
    H,nH=ch['said_rem'].sum(),len(ch); F,nF=un['said_rem'].sum(),len(un)
    h,f=H/nH,F/nF
    ll=z((H+0.5)/(nH+1))-z((F+0.5)/(nF+1))
    sh,sf=h,f
    if sh==1: sh=1-1/(2*nH)
    if sh==0: sh=1/(2*nH)
    if sf==1: sf=1-1/(2*nF)
    if sf==0: sf=1/(2*nF)
    rows.append(dict(Subject=sid,domain=dom,hit=h,fa=f,
                     dprime_raw=z(h)-z(f),dprime_loglinear=ll,dprime_snodgrass=z(sh)-z(sf)))
m=pd.DataFrame(rows)
piv=m.pivot(index='Subject',columns='domain',values=['dprime_loglinear','dprime_snodgrass'])
piv.columns=[f"{b.upper()}_{a}" for a,b in piv.columns]
piv.reset_index().to_csv(OUT,index=False)
s=m[m.domain=='social']
print(f"corrected d' written. social: raw SD={s.dprime_raw.std():.3f} -> loglinear SD={s.dprime_loglinear.std():.3f}")
print(f"loglinear vs snodgrass r={s[['dprime_loglinear','dprime_snodgrass']].corr().iloc[0,1]:.4f}")
print(f"-> {OUT}")
