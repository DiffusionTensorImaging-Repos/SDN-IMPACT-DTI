import pandas as pd, numpy as np, json, glob, os
from scipy.stats import pearsonr, ttest_1samp, ttest_rel, wilcoxon, norm

R='/Users/dannyzweben/Desktop/SDN/DTI/data.check/permutation_results'
OUT='/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/results_html'
os.makedirs(OUT,exist_ok=True)

TRACTS={'l_vta_l_hipp':('Posterior Left VTA→HPC','L','posterior'),
        'r_vta_r_hipp':('Posterior Right VTA→HPC','R','posterior'),
        'anterior_l_vta_l_hipp':('Anterior Left VTA→HPC','L','anterior'),
        'anterior_r_vta_r_hipp':('Anterior Right VTA→HPC','R','anterior')}
METRICS=['FA','NDI','ODI','FWF']  # FA + full NODDI family (NDI, ODI, FWF)

FAMILY={'SOCIAL_dprime':('Memory accuracy (d′)','SOCIAL'),
        'MONETARY_dprime':('Memory accuracy (d′)','MONETARY'),
        'SOCIAL_FABias':('Positivity bias — false memories','SOCIAL'),
        'MONETARY_FABias':('Positivity bias — false memories','MONETARY'),
        'SOCIAL_HitRateBias':('Positivity bias — correct memories','SOCIAL'),
        'MONETARY_HitRateBias':('Positivity bias — correct memories','MONETARY')}
OUTLABEL={'SOCIAL_dprime':"Social d′",'MONETARY_dprime':"Monetary d′",
    'SOCIAL_FABias':"Social positivity bias (false mem)",'MONETARY_FABias':"Monetary positivity bias (false mem)",
    'SOCIAL_HitRateBias':"Social positivity bias (hits)",'MONETARY_HitRateBias':"Monetary positivity bias (hits)"}

results=[]
for summ in sorted(glob.glob(f'{R}/*_summary.csv')):
    base=os.path.basename(summ).replace('_summary.csv','')
    # parse tract, metric, outcome
    tract=None
    for t in sorted(TRACTS,key=len,reverse=True):
        if base.startswith(t+'__'):
            tract=t; rest=base[len(t)+2:]; break
    if tract is None: continue
    metric=rest.split('__')[0]; outcome=rest[len(metric)+2:]
    if metric not in METRICS: continue
    if outcome not in FAMILY: continue
    s=pd.read_csv(summ).iloc[0]
    # clusters
    clusters=[]
    cf=f'{R}/{base}_clusters.csv'
    if os.path.exists(cf):
        cdf=pd.read_csv(cf)
        for _,c in cdf.iterrows():
            clusters.append(dict(size=int(c['Size']),start=int(c['StartNode']),end=int(c['EndNode']),
                p=round(float(c['ClusterPValue']),4),dir=c['Direction'],
                mean_t=round(float(c['MeanTValue']),3),max_abs_t=round(float(c['MaxAbsTValue']),3),
                max_abs_t_node=int(c['MaxAbsTNode']),passes=bool(c['PassExtentThreshold'])))
    # nodewise
    nw=pd.read_csv(f'{R}/{base}_nodewise.csv')
    tvals=[round(float(x),3) if pd.notna(x) else None for x in nw['t_value']]
    pvals=[round(float(x),4) if pd.notna(x) else None for x in nw['p_value']]
    sig_nodes=[int(n) for n,p in zip(nw['Node'],nw['p_value']) if pd.notna(p) and p<0.05]
    passed=any(c['passes'] for c in clusters)
    best_p=min([c['p'] for c in clusters if c['passes']],default=None)
    tl,hemi,ttype=TRACTS[tract]
    fam,cond=FAMILY[outcome]
    results.append(dict(id=base,outcome=outcome,outcome_label=OUTLABEL[outcome],family=fam,condition=cond,
        tract=tract,tract_label=tl,hemisphere=hemi,tract_type=ttype,metric=metric,
        N=int(s['N_subjects']),dropped=int(s['N_dropped']),covariates=s['Covariates'],
        n_sig_nodes=int(s['NumNodewiseSignificant']),obs_max_cluster=int(s['ObservedMaxClusterSize']),
        extent_threshold=int(s['ExtentThresholdNodes']),n_passing=int(s['NumClustersPassingExtent']),
        n_perms=int(s['NumPermutations']),passed=passed,best_p=best_p,
        clusters=clusters,sig_node_list=sig_nodes,tvals=tvals,pvals=pvals))

# laterality per (outcome, metric, tract_type): L vs R within the same tract type
lat={}
for r in results:
    key=(r['outcome'],r['metric'],r['tract_type'])
    lat.setdefault(key,{'L':0,'R':0,'L_nodes':[],'R_nodes':[]})
    lat[key][r['hemisphere']]=r['n_sig_nodes']
    lat[key][r['hemisphere']+'_nodes']=r['sig_node_list']
for r in results:
    L=lat[(r['outcome'],r['metric'],r['tract_type'])]
    tot=L['L']+L['R']
    overlap=sorted(set(L['L_nodes'])&set(L['R_nodes']))
    r['laterality']={'L_sig':L['L'],'R_sig':L['R'],
        'pct_left':round(100*L['L']/tot,0) if tot else None,
        'pct_right':round(100*L['R']/tot,0) if tot else None,
        'L_nodes':L['L_nodes'],'R_nodes':L['R_nodes'],'overlap_nodes':overlap}

json.dump(results,open(f'{OUT}/results_data.json','w'))
print(f"Wrote {len(results)} results")
print(f"Passing FWE: {sum(r['passed'] for r in results)}")
