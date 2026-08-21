import pandas as pd, numpy as np, warnings
from scipy.stats import norm
warnings.filterwarnings('ignore')
def z(p): return norm.ppf(np.clip(p,1e-6,1-1e-6))
d=pd.read_csv('/Users/dannyzweben/Desktop/SDN/IMPACT_triallevel.csv')
d=d[d['recall_selection'].astype(str)!='missed'].copy()
d['said_rem']=d['recall_selection'].astype(str).str.startswith('recall')
d['chosen']=d['selected']=='Selected'
rows=[]
for (sid,dom),g in d.groupby(['ID','domain']):
    ch=g[g['chosen']]; un=g[~g['chosen']]
    if len(ch)<10 or len(un)<10: continue
    r={'Subject':sid,'domain':dom}
    nH,nF=len(ch),len(un)
    H,F=ch['said_rem'].sum(),un['said_rem'].sum()
    r['hit']=H/nH; r['fa']=F/nF
    # MISATTRIBUTION = claiming feedback from the person you did NOT choose.
    # Decompose it by whether the claimed feedback matches that trial's real outcome:
    fa=un[un['said_rem']]
    #   source confusion: right event, wrong person (valence matches the pair's real outcome)
    r['fa_source_conf'] = (fa['feedback_acc']=='FeedbackSameAsPair').sum()/nF
    #   full fabrication: wrong person AND wrong feedback
    r['fa_fabrication'] = (fa['feedback_acc']=='FeedbackDifferentThanPair').sum()/nF
    # log-linear corrected rates for stability
    r['fa_ll'] = (F+0.5)/(nF+1)
    r['hit_ll']= (H+0.5)/(nH+1)
    # criterion (response liberalness) -- the nuisance we must hold constant
    r['criterion'] = -0.5*(z(r['hit_ll'])+z(r['fa_ll']))
    rows.append(r)
m=pd.DataFrame(rows)
piv=m.pivot(index='Subject',columns='domain')
piv.columns=[f"{b.upper()}_{a}" for a,b in piv.columns]
piv.reset_index().to_csv('data.check/misattribution_scores.csv',index=False)
s=m[m.domain=='social']
print("=== Decomposing MISATTRIBUTION (social) ===")
print(f"  overall false-alarm rate : {s['fa'].mean():.3f}")
print(f"    source confusion (right event, wrong person): {s['fa_source_conf'].mean():.3f}")
print(f"    full fabrication (wrong event AND person)   : {s['fa_fabrication'].mean():.3f}")
print(f"\nsaved {piv.shape[1]} measures")
