import pandas as pd, numpy as np, json
import statsmodels.formula.api as smf
from scipy.stats import zscore
import warnings; warnings.filterwarnings('ignore')

base='/Users/dannyzweben/Desktop/SDN/DTI/Impact-Analyses'
den=pd.read_csv(f'{base}/hpc_density.csv')
for c in den.columns[1:]: den[c]=pd.to_numeric(den[c],errors='coerce')
ready=pd.read_csv('/Users/dannyzweben/Desktop/SDN/DTI/data.check/analysis_ready/r_vta_r_hipp__NDI__analysis.csv')
# outcomes + covariates straight from the analysis roster (DQ-corrected, recomputed d′, same as the tract models)
cov=ready[['Subject','SOCIAL_dprime','MONETARY_dprime','SOCIAL_FABias','MONETARY_FABias','ICV','absolute_motion','maternal_age']]
df=den.merge(cov,on='Subject',how='inner')

# canonical NODDI in the hippocampus: NDI, ODI, FWF sampled inside the anatomical HPC ROI
NODDI=[('NDI','NDI density'),('ODI','ODI (dispersion)'),('FWF','FWF (free water)')]
for key,_ in NODDI:
    df[f'bilat_{key}']=(df[f'L_HPC_{key}']+df[f'R_HPC_{key}'])/2

print("=== HPC NODDI QC (mean inside HPC ROI) ===")
for key,lbl in NODDI:
    print(f"  {lbl}: L={df[f'L_HPC_{key}'].mean():.3f} R={df[f'R_HPC_{key}'].mean():.3f}  L-R r={df[f'L_HPC_{key}'].corr(df[f'R_HPC_{key}']):.3f}")

def model(outcome,predictor):
    d=df[[outcome,predictor,'ICV','absolute_motion','maternal_age']].dropna().copy()
    for c in [outcome,predictor]: d[c+'_z']=zscore(d[c])
    f=smf.ols(f'{outcome} ~ {predictor}_z + ICV + absolute_motion + maternal_age',d).fit()
    return round(f.params[predictor+'_z'],3),round(f.pvalues[predictor+'_z'],4),len(d)

def run(outcome,oc_lbl,matched_side):
    """matched_side = hemisphere matched to the tract finding for this outcome."""
    cross_side='Right' if matched_side=='Left' else 'Left'
    out=[]
    for key,meas in NODDI:
        ms='L' if matched_side=='Left' else 'R'; cs='L' if cross_side=='Left' else 'R'
        for side,typ,col in [(matched_side,'matched',f'{ms}_HPC_{key}'),
                             (cross_side,'cross',f'{cs}_HPC_{key}'),
                             ('Bilateral','bilateral',f'bilat_{key}')]:
            b,p,n=model(outcome,col)
            out.append(dict(outcome=oc_lbl,side=side,measure=meas,type=typ,beta=b,p=p,n=n))
    return out

# d′: social tract finding is LEFT, monetary would be RIGHT
models =run('SOCIAL_dprime','Social d′','Left')+run('MONETARY_dprime','Monetary d′','Right')
# bias: social bias findings were bilateral, strongest RIGHT; match both to Right, cross = Left
bias   =run('SOCIAL_FABias','Social FABias','Right')+run('MONETARY_FABias','Monetary FABias','Right')

def show(title,rows):
    print(f"\n=== {title} ===")
    print(f"{'Outcome':16s} {'side':10s} {'measure':16s} {'type':9s} {'beta':>7s} {'p':>7s} {'n':>4s}")
    for m in rows:
        print(f"{m['outcome']:16s} {m['side']:10s} {m['measure']:16s} {m['type']:9s} {m['beta']:+.3f} {m['p']:7.3f} {m['n']:4d}{'  *' if m['p']<0.05 else ''}")
show("HPC NODDI -> d′",models); show("HPC NODDI -> positivity bias (FABias)",bias)

qc={'n':int(df[['SOCIAL_dprime']].dropna().shape[0])}
for key,lbl in NODDI:
    qc[f'{key}_L']=round(df[f'L_HPC_{key}'].mean(),3); qc[f'{key}_R']=round(df[f'R_HPC_{key}'].mean(),3)
    qc[f'{key}_LR_r']=round(df[f'L_HPC_{key}'].corr(df[f'R_HPC_{key}']),3)
json.dump({'models':models,'bias_models':bias,'qc':qc,'noddi':[k for k,_ in NODDI]},
   open('/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/results_html/hpc_region_data.json','w'),indent=1)
df.to_csv('/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/data/hpc_region_measures.csv',index=False)
print("\nsaved hpc_region_data.json + hpc_region_measures.csv")
