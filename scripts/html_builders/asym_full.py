import pandas as pd, numpy as np, json
import statsmodels.formula.api as smf
from scipy.stats import zscore, pearsonr
import warnings; warnings.filterwarnings('ignore')

nd='/Users/dannyzweben/Desktop/SDN/DTI/data.check/step30_noddi'
fa='/Users/dannyzweben/Desktop/SDN/DTI/data.check/step27_fa'
rd='/Users/dannyzweben/Desktop/SDN/DTI/data.check/analysis_ready'
def midtract(tract,metric,lo=25,hi=75):
    if metric=='FA': d=pd.read_csv(f'{fa}/{tract}_fa_nodewise_all_subjects.csv').rename(columns={'FA':'v'})
    else: d=pd.read_csv(f'{nd}/{tract}_noddi_nodewise_all_subjects.csv').rename(columns={metric:'v'})
    return d[(d.Node>=lo)&(d.Node<=hi)].groupby('Subject')['v'].mean()

L=pd.read_csv(f'{rd}/l_vta_l_hipp__NDI__analysis.csv'); R=pd.read_csv(f'{rd}/r_vta_r_hipp__NDI__analysis.csv')
df=pd.DataFrame({'Subject':L['Subject']})
df['SOC']=pd.to_numeric(L['SOCIAL_dprime'],errors='coerce'); df['MON']=pd.to_numeric(L['MONETARY_dprime'],errors='coerce')
df['ICV']=L['ICV']; df['motion']=L['absolute_motion']; df['age']=L['maternal_age']
for met in ['NDI','FA']:
    df[f'L_{met}']=df['Subject'].map(midtract('l_vta_l_hipp',met)); df[f'R_{met}']=df['Subject'].map(midtract('r_vta_r_hipp',met))
    df[f'LI_{met}']=(df[f'L_{met}']-df[f'R_{met}'])/(df[f'L_{met}']+df[f'R_{met}'])
    df[f'SUM_{met}']=df[f'L_{met}']+df[f'R_{met}']
df['LI_count']=(pd.to_numeric(L['Count_tckstats'],errors='coerce')-pd.to_numeric(R['Count_tckstats'],errors='coerce'))/(pd.to_numeric(L['Count_tckstats'],errors='coerce')+pd.to_numeric(R['Count_tckstats'],errors='coerce'))
df['LI_len']=(pd.to_numeric(L['Mean_tckstats'],errors='coerce')-pd.to_numeric(R['Mean_tckstats'],errors='coerce'))/(pd.to_numeric(L['Mean_tckstats'],errors='coerce')+pd.to_numeric(R['Mean_tckstats'],errors='coerce'))
df=df[~df['Subject'].isin(['s1350','s4418'])].copy()
both=df.dropna(subset=['SOC','MON']).copy()
both['mem_asym']=zscore(both['SOC'])-zscore(both['MON'])

def reg(pred,covs):
    m=both.dropna(subset=[pred,'mem_asym']+covs).copy(); m['x']=zscore(m[pred])
    f=smf.ols('mem_asym ~ x + '+' + '.join(covs),m).fit()
    r,p=pearsonr(m[pred],m['mem_asym'])
    return dict(raw_r=round(r,3),raw_p=round(p,4),adj_beta=round(f.params['x'],3),adj_p=round(f.pvalues['x'],4),n=len(m))
COV=['ICV','motion','age']; COVL=COV+['LI_count','LI_len']
res={}
print("=== Q: does tract BALANCE (L−R) predict memory balance (social−monetary)? ===")
for met in ['NDI','FA']:
    res[f'LI_{met}']=reg(f'LI_{met}',COVL); r=res[f'LI_{met}']
    print(f"  LI_{met}:  raw r={r['raw_r']:+.3f} p={r['raw_p']}  |  adj beta={r['adj_beta']:+.3f} p={r['adj_p']}  n={r['n']}   {'** BALANCE EFFECT' if r['adj_p']<0.05 else '(null)'}")
print("\n=== What DOES predict memory balance? bilateral LEVEL (L+R) ===")
for met in ['NDI','FA']:
    res[f'SUM_{met}']=reg(f'SUM_{met}',COV); r=res[f'SUM_{met}']
    print(f"  SUM_{met}: raw r={r['raw_r']:+.3f} p={r['raw_p']}  |  adj beta={r['adj_beta']:+.3f} p={r['adj_p']}  n={r['n']}   {'** LEVEL EFFECT' if r['adj_p']<0.05 else ''}")
print("\n=== which side carries it? ===")
for side in ['L_NDI','R_NDI']:
    res[side]=reg(side,COV); r=res[side]
    print(f"  {side}: raw r={r['raw_r']:+.3f} p={r['raw_p']}  |  adj beta={r['adj_beta']:+.3f} p={r['adj_p']}   {'*' if r['adj_p']<0.05 else ''}")

# formal interaction (fixed): long format, reset index
long=[]
for _,x in both.iterrows():
    for h,ndi in [('L',x['L_NDI']),('R',x['R_NDI'])]:
        for dm,dp in [('soc',x['SOC']),('mon',x['MON'])]:
            long.append(dict(S=x['Subject'],hemi=h,dom=dm,ndi=ndi,dp=dp,ICV=x['ICV'],motion=x['motion'],age=x['age']))
LG=pd.DataFrame(long).dropna(subset=['ndi','dp']).reset_index(drop=True); LG['ndi_z']=zscore(LG['ndi'])
try:
    mm=smf.mixedlm('dp ~ ndi_z*C(hemi)*C(dom) + ICV+motion+age',LG,groups=LG['S'].values).fit()
    three=[k for k in mm.params.index if k.startswith('ndi_z:') and 'hemi' in k and 'dom' in k]
    res['interaction']={k:{'beta':round(mm.params[k],3),'p':round(mm.pvalues[k],4)} for k in three}
    print("\n=== formal NDI × hemisphere × domain interaction (the 'flip' term) ===")
    for k in three: print(f"  {k}: beta={mm.params[k]:+.3f} p={mm.pvalues[k]:.3f}")
except Exception as e:
    print("interaction model failed:",e); res['interaction']=None

# NOTE: HPC region -> BIAS lives in hpc_analysis.py (rendered in hpc_region_vs_connection.html)
scat=both.dropna(subset=['SUM_NDI','mem_asym','ICV','motion','age'])[['Subject','SUM_NDI','LI_NDI','mem_asym']]
res['scatter_sum']=scat.round(4).to_dict('records')
res['n_memasym']=len(both)
json.dump(res,open('/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/results_html/asymmetry_data.json','w'),indent=1)
print("\nsaved asymmetry_data.json")
