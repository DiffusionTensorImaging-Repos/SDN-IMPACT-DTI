import pandas as pd, numpy as np, json
import statsmodels.formula.api as smf
from scipy.stats import zscore
import warnings; warnings.filterwarnings('ignore')

base='/Users/dannyzweben/Desktop/SDN/DTI/Impact-Analyses'
vol=pd.read_csv(f'{base}/hpc_volumes.csv')
den=pd.read_csv(f'{base}/hpc_density.csv')
for c in den.columns[1:]: den[c]=pd.to_numeric(den[c],errors='coerce')
ready=pd.read_csv('/Users/dannyzweben/Desktop/SDN/DTI/data.check/analysis_ready/r_vta_r_hipp__NDI__analysis.csv')
# covariates from ready file: ICV, absolute_motion, maternal_age + d'
cov=ready[['Subject','SOCIAL_dprime','MONETARY_dprime','ICV','absolute_motion','maternal_age']]
df=vol.merge(den,on='Subject',how='outer').merge(cov,on='Subject',how='inner')

# ---- QC: FIRST volume sanity ----
print("=== HPC VOLUME QC (mm3) ===")
for c in ['L_HPC_vol_mm3','R_HPC_vol_mm3']:
    v=df[c]; print(f"  {c}: mean={v.mean():.0f} sd={v.std():.0f} range=[{v.min():.0f},{v.max():.0f}]")
    # flag >3.5 SD outliers (FIRST failures)
    z=(v-v.mean())/v.std(); out=df.loc[abs(z)>3.5,'Subject'].tolist()
    if out: print(f"    ⚠ possible FIRST outliers: {out}")
# asymmetry / L-R correlation sanity
print(f"  L-R volume corr: r={df['L_HPC_vol_mm3'].corr(df['R_HPC_vol_mm3']):.3f}")
print(f"  L-R NDI corr:    r={df['L_HPC_NDI'].corr(df['R_HPC_NDI']):.3f}")

df['L_HPC_vol']=df['L_HPC_vol_mm3']; df['R_HPC_vol']=df['R_HPC_vol_mm3']
def model(outcome,predictor,covs='ICV + absolute_motion + maternal_age'):
    d=df[[outcome,predictor,'ICV','absolute_motion','maternal_age']].dropna().copy()
    for c in [outcome,predictor]: d[c+'_z']=zscore(d[c])
    f=smf.ols(f'{outcome} ~ {predictor}_z + {covs}',d).fit()
    return f.params[predictor+'_z'],f.pvalues[predictor+'_z'],len(d)

print("\n=== HEMISPHERE-MATCHED MODELS (d' ~ HPC measure + ICV + motion + age) ===")
rows=[]
combos=[
 ('Social d′','SOCIAL_dprime','Left','L_HPC_vol','volume','matched'),
 ('Monetary d′','MONETARY_dprime','Right','R_HPC_vol','volume','matched'),
 ('Social d′','SOCIAL_dprime','Right','R_HPC_vol','volume','cross'),
 ('Monetary d′','MONETARY_dprime','Left','L_HPC_vol','volume','cross'),
 ('Social d′','SOCIAL_dprime','Left','L_HPC_NDI','NDI density','matched'),
 ('Monetary d′','MONETARY_dprime','Right','R_HPC_NDI','NDI density','matched'),
 ('Social d′','SOCIAL_dprime','Right','R_HPC_NDI','NDI density','cross'),
 ('Monetary d′','MONETARY_dprime','Left','L_HPC_NDI','NDI density','cross'),
]
print(f"{'Outcome':13s} {'HPC side':9s} {'Measure':12s} {'type':8s} {'beta':>7s} {'p':>7s} {'n':>4s}")
for oc_lbl,oc,side,pred,meas,typ in combos:
    b,p,n=model(oc,pred)
    star='  *' if p<0.05 else ''
    print(f"{oc_lbl:13s} {side:9s} {meas:12s} {typ:8s} {b:+.3f} {p:7.3f} {n:4d}{star}")
    rows.append(dict(outcome=oc_lbl,side=side,measure=meas,type=typ,beta=round(b,3),p=round(p,4),n=n))

# bilateral summary (mean L+R)
df['bilat_vol']=(df['L_HPC_vol']+df['R_HPC_vol'])/2
df['bilat_ndi']=(df['L_HPC_NDI']+df['R_HPC_NDI'])/2
print("\n=== BILATERAL (mean L+R) ===")
for oc_lbl,oc in [('Social d′','SOCIAL_dprime'),('Monetary d′','MONETARY_dprime')]:
    for pred,meas in [('bilat_vol','volume'),('bilat_ndi','NDI density')]:
        b,p,n=model(oc,pred)
        rows.append(dict(outcome=oc_lbl,side='Bilateral',measure=meas,type='bilateral',beta=round(b,3),p=round(p,4),n=n))
        print(f"  {oc_lbl} ~ {meas}: beta={b:+.3f} p={p:.3f} n={n} {'*' if p<0.05 else ''}")

json.dump({'models':rows,
   'qc':{'L_vol_mean':round(df['L_HPC_vol'].mean()),'R_vol_mean':round(df['R_HPC_vol'].mean()),
         'LR_vol_r':round(df['L_HPC_vol'].corr(df['R_HPC_vol']),3),
         'n':len(df)}},
   open('/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/results_html/hpc_region_data.json','w'),indent=1)
df.to_csv('/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/data/hpc_region_measures.csv',index=False)
print("\nsaved hpc_region_data.json + hpc_region_measures.csv")

# ===== ROBUSTNESS: exclude FIRST outlier s4459 =====
print("\n\n===== EXCLUDING FIRST outlier s4459 =====")
df=df[df['Subject']!='s4459'].copy()
print(f"n now = {df[['SOCIAL_dprime','L_HPC_vol']].dropna().shape[0]}")
for oc_lbl,oc,side,pred,meas in [
 ('Social d′','SOCIAL_dprime','Left','L_HPC_vol','volume'),
 ('Monetary d′','MONETARY_dprime','Right','R_HPC_vol','volume'),
 ('Social d′','SOCIAL_dprime','Left','L_HPC_NDI','NDI'),
 ('Monetary d′','MONETARY_dprime','Right','R_HPC_NDI','NDI')]:
    b,p,n=model(oc,pred)
    print(f"  {oc_lbl} ~ {side} HPC {meas}: beta={b:+.3f} p={p:.3f} n={n} {'*' if p<0.05 else ''}")
