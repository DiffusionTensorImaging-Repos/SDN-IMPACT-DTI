import pandas as pd, numpy as np, json, os, re
from scipy.stats import pearsonr, ttest_1samp, ttest_rel, wilcoxon, norm
OUT='/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/results_html'
allx=pd.read_csv('/Users/dannyzweben/Desktop/SDN/DTI/Impact-Analyses/IMPACT-AllDemographics_DATA_2026-06-03_1428.csv').rename(columns={'sub_id':'Subject'})
allx=allx[allx['Subject'].notna()].drop_duplicates('Subject')
red=pd.read_csv('/Users/dannyzweben/Desktop/SDN/DTI/Impact-Analyses/IMPACT_REDCap_clean_093024.csv').rename(columns={'sub_id':'Subject'}).drop_duplicates('Subject')
grp=pd.read_csv('/Users/dannyzweben/Desktop/SDN/DTI/Impact-Analyses/IMPACT_grouped_export.csv').drop_duplicates('ID').rename(columns={'ID':'Subject'})
ready=pd.read_csv('/Users/dannyzweben/Desktop/SDN/DTI/data.check/analysis_ready/r_vta_r_hipp__NDI__analysis.csv')
subs=set(ready['Subject'])
A=allx[allx['Subject'].isin(subs)].copy()
R=red[red['Subject'].isin(subs)].copy()
G=grp[grp['Subject'].isin(subs)].copy()

RACE={0:'Am. Indian/AK Native',1:'Asian',2:'Native Hawaiian/PI',3:'Black/African American',4:'White',5:'Other'}
EDU={0:'≤8th grade',1:'Some high school',2:'HS grad/GED',3:'Some college',4:'4-yr degree',5:"Master's",6:'Doctoral'}
MAR={0:'Never married',1:'Married',2:'Separated',3:'Divorced',4:'Widowed',5:'Other'}
ETH={0:'Hispanic/Latino',1:'Not Hispanic/Latino'}
def income_num(x):
    if pd.isna(x): return np.nan
    s=re.sub(r'[^0-9.]','',str(x))
    try:
        v=float(s)
        return v*1000 if v<1000 else v
    except: return np.nan

# maternal age = the SAME coalesced value used in every analysis (REDCap ∪ newer AllDemographics),
# read from the corrected analysis roster so the demographic card's N matches the analytic N exactly.
age=pd.to_numeric(ready.set_index('Subject').reindex(sorted(subs))['maternal_age'],errors='coerce')
inc=A['demo_poc_57'].map(income_num) if 'demo_poc_57' in A else pd.Series(dtype=float)
# race checkboxes demo_poc_53___0..5
race_counts={}
for k,lbl in RACE.items():
    col=f'demo_poc_53___{k}'
    if col in A: race_counts[lbl]=int(pd.to_numeric(A[col],errors='coerce').fillna(0).sum())
race_counts={k:v for k,v in race_counts.items() if v>0}
def vc(col,mp):
    if col not in A: return {}
    return {mp.get(int(k),str(k)):int(v) for k,v in pd.to_numeric(A[col],errors='coerce').value_counts().sort_index().items()}
demo={'n_dti':len(subs),'n_with_demo':int(age.notna().sum()),
 'age':{'mean':round(age.mean(),1),'sd':round(age.std(),1),'min':int(age.min()),'max':int(age.max()),'n':int(age.notna().sum())},
 'ethnicity':vc('demo_poc_52',ETH),'race':race_counts,
 'education':vc('demo_poc_56',EDU),'marital':vc('demo_poc_42',MAR),
 'income':{'median':int(inc.median()),'mean':int(inc.mean()),'min':int(inc.min()),'max':int(inc.max()),'n':int(inc.notna().sum())} if inc.notna().sum() else {}}
clin_cols={'Social anxiety (SCAARED)':'scaared_adult_socanx_pnrscoring','GAD (SCAARED)':'scaared_adult_gad_pnrscoring',
    'Depression (IDAS-II gen.)':'idasii_adult_gendepression_pnrscoring','Perceived stress (PSS)':'pss_adult_total_pnrscoring',
    'Emotion-reg diff. (DERS)':'ders_adult_total_pnrscoring','CTQ total maltreatment':'ctqsf_adult_totalmaltreatment_pnrscoring',
    'BAS reward-resp.':'bas_adult_rewrespon_pnrscoring','BIS':'bis_adult_sum_pnrscoring'}
clin={}
for lbl,c in clin_cols.items():
    if c in R.columns:
        v=pd.to_numeric(R[c],errors='coerce')
        if v.notna().sum(): clin[lbl]={'mean':round(v.mean(),1),'sd':round(v.std(),1),'n':int(v.notna().sum())}
demo['clinical']=clin

def z(p): return norm.ppf(np.clip(p,1e-6,1-1e-6))
sd=pd.to_numeric(ready['SOCIAL_dprime'],errors='coerce'); md=pd.to_numeric(ready['MONETARY_dprime'],errors='coerce')
both=pd.concat([sd,md],axis=1).dropna(); r,p=pearsonr(both.iloc[:,0],both.iloc[:,1])
tS,pS=ttest_1samp(sd.dropna(),0); tM,pM=ttest_1samp(md.dropna(),0)
paired=pd.concat([sd,md],axis=1).dropna(); tp,pp=ttest_rel(paired.iloc[:,0],paired.iloc[:,1]); w,pw=wilcoxon(paired.iloc[:,0],paired.iloc[:,1])
dq={'dprime':{
 'social':{'n':int(sd.notna().sum()),'mean':round(sd.mean(),3),'sd':round(sd.std(),3),'t_vs0':round(tS,2),'p_vs0':round(pS,4)},
 'monetary':{'n':int(md.notna().sum()),'mean':round(md.mean(),3),'sd':round(md.std(),3),'t_vs0':round(tM,2),'p_vs0':round(pM,4)},
 'correlation':{'r':round(r,3),'p':round(p,3),'n':len(both)},
 'paired_diff':{'mean_diff':round((paired.iloc[:,0]-paired.iloc[:,1]).mean(),3),'t':round(tp,2),'p':round(pp,4),'wilcoxon_p':round(pw,4)}}}
recomp=[]
for cond in ['SOCIAL','MONETARY']:
    TM=pd.to_numeric(G[f'{cond}_TrueMem'],errors='coerce'); FM=pd.to_numeric(G[f'{cond}_FalseMem'],errors='coerce')
    TP=pd.to_numeric(G[f'{cond}_TruePred'],errors='coerce'); FP=pd.to_numeric(G[f'{cond}_FalsePred'],errors='coerce')
    H=TM/(TM+TP); F=FM/(FM+FP); dpm=pd.Series(z(H.values)-z(F.values),index=H.index); rep=pd.to_numeric(G[f'{cond}_dprime'],errors='coerce')
    d=pd.concat([dpm,rep],axis=1).dropna(); rr,_=pearsonr(d.iloc[:,0],d.iloc[:,1])
    recomp.append({'cond':cond,'r_with_reported':round(rr,4),'n':len(d)})
dq['dprime_recompute']=recomp
rt=pd.read_csv('/Users/dannyzweben/Desktop/SDN/DTI/Impact-Analyses/rt_summary.csv'); rt=rt[rt['Subject'].isin(subs)]
rtstats={}
for ph in ['encoding_social','encoding_monetary','recall_social','recall_monetary']:
    v=pd.to_numeric(rt[f'{ph}_rt_mean'],errors='coerce'); rtstats[ph]={'mean':round(v.mean(),3),'sd':round(v.std(),3),'n':int(v.notna().sum())}
mrg=rt.merge(ready[['Subject','SOCIAL_dprime','MONETARY_dprime']],on='Subject'); rtcorr=[]
for lbl,rc,oc in [('Social d′ × social-recall RT','recall_social_rt_mean','SOCIAL_dprime'),('Monetary d′ × monetary-recall RT','recall_monetary_rt_mean','MONETARY_dprime')]:
    d=mrg[[rc,oc]].apply(pd.to_numeric,errors='coerce').dropna(); rr,pp2=pearsonr(d[rc],d[oc]); rtcorr.append({'label':lbl,'r':round(rr,3),'p':round(pp2,4),'n':len(d)})
dd=rt[['recall_social_rt_mean','recall_monetary_rt_mean']].apply(pd.to_numeric,errors='coerce').dropna(); tt,ptt=ttest_rel(dd.iloc[:,0],dd.iloc[:,1])
dq['rt']={'phase_means':rtstats,'corr_with_dprime':rtcorr,'social_vs_monetary_recall':{'t':round(tt,2),'p':round(ptt,3),'n':len(dd)}}
json.dump({'demographics':demo,'data_quality':dq},open(f'{OUT}/meta_data.json','w'),indent=1)
print("OK. age",demo['age']['mean'],"race",demo['race'],"corr r",dq['dprime']['correlation']['r'])
print("recompute",recomp)
