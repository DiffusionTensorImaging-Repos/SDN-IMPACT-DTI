#!/usr/bin/env python3
"""Build results_html/hvlt_explorer.html — verbal-learning (HVLT) results explorer.
Dark twin of results_explorer.html: same interactive node-wise table/detail JS, wired to
the HVLT permutation results, with HVLT tract-average effect sizes and HPC-region models."""
import pandas as pd, numpy as np, json, glob, os, warnings
from scipy import stats
from scipy.stats import zscore
import statsmodels.formula.api as smf
warnings.filterwarnings('ignore')

BASE='/Users/dannyzweben/Desktop/SDN/DTI'
R=f'{BASE}/data.check/permutation_results'
AR=f'{BASE}/data.check/analysis_ready'
OUT=f'{BASE}/SDN-IMPACT-DTI/results_html'
COV=['ICV','Mean_tckstats','Count_tckstats','absolute_motion','maternal_age']
TRACTS={'l_vta_l_hipp':('Posterior Left VTA→HPC','L','posterior'),
        'r_vta_r_hipp':('Posterior Right VTA→HPC','R','posterior'),
        'anterior_l_vta_l_hipp':('Anterior Left VTA→HPC','L','anterior'),
        'anterior_r_vta_r_hipp':('Anterior Right VTA→HPC','R','anterior')}
SHORT={'l_vta_l_hipp':'postL','r_vta_r_hipp':'postR','anterior_l_vta_l_hipp':'antL','anterior_r_vta_r_hipp':'antR'}
METRICS=['FA','NDI','ODI','FWF']
OUTS=['hvlt_totalrecall','hvlt_delayedrecall']
OUTLABEL={'hvlt_totalrecall':'Total recall','hvlt_delayedrecall':'Delayed recall'}
FAMILY={'hvlt_totalrecall':('Verbal learning (HVLT)','HVLT'),'hvlt_delayedrecall':('Verbal learning (HVLT)','HVLT')}

# ---- DATA array from HVLT perm results ----
results=[]
for outcome in OUTS:
    for tract in TRACTS:
        for metric in METRICS:
            base=f'{tract}__{metric}__{outcome}'
            summ=f'{R}/{base}_summary.csv'
            if not os.path.exists(summ): continue
            s=pd.read_csv(summ).iloc[0]
            clusters=[]
            cf=f'{R}/{base}_clusters.csv'
            if os.path.exists(cf):
                for _,c in pd.read_csv(cf).iterrows():
                    clusters.append(dict(size=int(c['Size']),start=int(c['StartNode']),end=int(c['EndNode']),
                        p=round(float(c['ClusterPValue']),4),dir=c['Direction'],mean_t=round(float(c['MeanTValue']),3),
                        max_abs_t=round(float(c['MaxAbsTValue']),3),max_abs_t_node=int(c['MaxAbsTNode']),passes=bool(c['PassExtentThreshold'])))
            nw=pd.read_csv(f'{R}/{base}_nodewise.csv')
            tvals=[round(float(x),3) if pd.notna(x) else None for x in nw['t_value']]
            pvals=[round(float(x),4) if pd.notna(x) else None for x in nw['p_value']]
            sig=[int(n) for n,p in zip(nw['Node'],nw['p_value']) if pd.notna(p) and p<0.05]
            passed=any(c['passes'] for c in clusters)
            best_p=min([c['p'] for c in clusters if c['passes']],default=None)
            tl,hemi,ttype=TRACTS[tract]; fam,cond=FAMILY[outcome]
            results.append(dict(id=base,outcome=outcome,outcome_label=OUTLABEL[outcome],family=fam,condition=cond,
                tract=tract,tract_label=tl,hemisphere=hemi,tract_type=ttype,metric=metric,
                N=int(s['N_subjects']),dropped=int(s['N_dropped']),covariates=s['Covariates'],
                n_sig_nodes=int(s['NumNodewiseSignificant']),obs_max_cluster=int(s['ObservedMaxClusterSize']),
                extent_threshold=int(s['ExtentThresholdNodes']),n_passing=int(s['NumClustersPassingExtent']),
                n_perms=int(s['NumPermutations']),passed=passed,best_p=best_p,clusters=clusters,
                sig_node_list=sig,tvals=tvals,pvals=pvals))
lat={}
for r in results:
    k=(r['outcome'],r['metric'],r['tract_type']); lat.setdefault(k,{'L':0,'R':0,'L_nodes':[],'R_nodes':[]})
    lat[k][r['hemisphere']]=r['n_sig_nodes']; lat[k][r['hemisphere']+'_nodes']=r['sig_node_list']
for r in results:
    Ld=lat[(r['outcome'],r['metric'],r['tract_type'])]; tot=Ld['L']+Ld['R']
    r['laterality']={'L_sig':Ld['L'],'R_sig':Ld['R'],'pct_left':round(100*Ld['L']/tot,0) if tot else None,
        'pct_right':round(100*Ld['R']/tot,0) if tot else None,'L_nodes':Ld['L_nodes'],'R_nodes':Ld['R_nodes'],
        'overlap_nodes':sorted(set(Ld['L_nodes'])&set(Ld['R_nodes']))}

# ---- tract-average partial r ----
def partial(tract,metric,out):
    d=pd.read_csv(f'{AR}/{tract}__{metric}__analysis.csv')
    d['mid']=d[[f'{metric}_{i}' for i in range(25,75)]].mean(axis=1)
    m=d[['mid',out]+COV].dropna()
    if len(m)<10: return None,None
    xr=smf.ols('mid ~ '+'+'.join(COV),m).fit().resid; yr=smf.ols(f'{out} ~ '+'+'.join(COV),m).fit().resid
    return stats.pearsonr(xr,yr)
def surv(tract,metric,out):
    f=f'{R}/{tract}__{metric}__{out}_summary.csv'
    return os.path.exists(f) and int(pd.read_csv(f)['NumClustersPassingExtent'].iloc[0])>0
def avg_table():
    rows=''
    for out in OUTS:
        rows+=f'<tr><td colspan="5" style="color:#a78bfa;font-weight:600;padding-top:12px">{OUTLABEL[out]}</td></tr>'
        for metric in METRICS:
            cells=''
            for t in TRACTS:
                r,p=partial(t,metric,out); st=surv(t,metric,out)
                dag='<sup>†</sup>' if st else ''
                style='color:#4ade80;font-weight:700' if (p is not None and p<0.05) else ''
                txt=f'{r:+.2f}'.replace('+','+').replace('-','−') if r is not None else '—'
                cells+=f'<td style="{style}">{txt}{dag}</td>'
            rows+=f'<tr><td>{metric}</td>{cells}</tr>'
    return rows

# ---- HPC region models ----
den=pd.read_csv(f'{BASE}/Impact-Analyses/hpc_density.csv')
for c in den.columns[1:]: den[c]=pd.to_numeric(den[c],errors='coerce')
ready=pd.read_csv(f'{AR}/r_vta_r_hipp__NDI__analysis.csv')[['Subject']+OUTS+['ICV','absolute_motion','maternal_age']]
hdf=den.merge(ready,on='Subject',how='inner')
def hpcmodel(out,pred):
    d=hdf[[out,pred,'ICV','absolute_motion','maternal_age']].dropna()
    d[out+'z']=zscore(d[out]); d[pred+'z']=zscore(d[pred])
    f=smf.ols(f'{out}z ~ {pred}z + ICV + absolute_motion + maternal_age',d).fit()
    return f.params[pred+'z'],f.pvalues[pred+'z'],len(d)
def hpc_table():
    rows=''
    for out in OUTS:
        for key in ['NDI','ODI','FWF']:
            cells=''
            for side in ['L','R']:
                b,p,n=hpcmodel(out,f'{side}_HPC_{key}')
                style='color:#4ade80;font-weight:700' if p<0.05 else ''
                star=' *' if p<0.05 else ''
                cells+=f'<td style="{style}">{b:+.3f}{star}</td>'.replace('+','+').replace('-','−')
            rows+=f'<tr><td>{OUTLABEL[out]}</td><td>{key}</td>{cells}</tr>'
    return rows

# ---- reuse the exact JS + style from the TEMPLATE builder (has __DATA__ placeholders) ----
tpl=open(f'{BASE}/SDN-IMPACT-DTI/scripts/html_builders/build_explorer_html.py').read()
js=tpl[tpl.index('<script>'):tpl.index('</script>')+9]
main=tpl

n_pass=sum(r['passed'] for r in results)
SCRIPTS={'extraction':'run_step27_fa_extraction.py / run_step30_noddi_extraction.py — AFQ-style tract profiling, 100 nodes.',
 'covariates':'extract_imaging_covariates.py — motion, ICV, streamline count + length.',
 'merge':'build_analysis_csvs.py — tract profiles + covariates + outcomes into wide CSVs.',
 'permute':'permutation_base.R — Freedman–Lane 5000-perm cluster-extent test (base-R port).',
 'runner':'run_hvlt2.sh — parallel runner on cr2 (128 cores).'}

STYLE=main[main.index('<style>'):main.index('</style>')+8]
html=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IMPACT VTA→HPC — Verbal Learning (HVLT) Explorer</title>
{STYLE}</head><body>
<header>
<h1>IMPACT · VTA→HPC Tract Microstructure — Verbal Learning (HVLT) Explorer</h1>
<div class="sub">Exploratory: the same node-wise pipeline applied to Hopkins Verbal Learning Test scores — 2 outcomes (Total Recall, Delayed Recall) × 4 tracts × 4 metrics (FA + NODDI). Freedman–Lane, 5000 permutations, cluster-extent FWE at α=0.05, n=42. Click any row for detail. &nbsp;·&nbsp; <a class="back" href="results_explorer.html">→ Motivated-memory results</a></div>
</header>
<div class="wrap">

<div class="section"><h2>Tract averages</h2>
<div class="note" style="background:#232733;border-left:3px solid #a78bfa;border-radius:6px;padding:11px 14px;margin:2px 0 14px;font-size:12.5px;color:#c9d1e0">Mid-tract (nodes 25–74) partial correlation of each metric with the HVLT score, covariates removed, n=42. <b style="color:#4ade80">Green</b> = p&lt;.05 on the average; <b>†</b> = the node-wise cluster survived FWE. n=42 is modest, so most tract-level effects are trends.</div>
<table><thead><tr><th>Metric</th><th>post L</th><th>post R</th><th>ant L</th><th>ant R</th></tr></thead><tbody>
{avg_table()}
</tbody></table>
<div class="legend">Direction is positive for FA/NDI (denser, more-anisotropic white matter → better verbal learning), matching the motivated-memory NDI effect. Only <b>anterior-right NDI × Total Recall</b> survives FWE at the node-wise level.</div>
</div>

<div class="section"><h2>All results</h2>
<div class="controls">
<span><label>Outcome</label><select id="f_family"></select></span>
<span><label>Condition</label><select id="f_cond"></select></span>
<span><label>Tract</label><select id="f_tract"></select></span>
<span><label>Hemisphere</label><select id="f_hemi"></select></span>
<span><label>Metric</label><select id="f_metric"></select></span>
<span><label>Show</label><select id="f_sig"><option value="all">All</option><option value="sig">FWE-significant only</option><option value="trend">≥5 sig nodes</option></select></span>
<input id="f_search" placeholder="search…" style="min-width:130px">
<span class="count" id="count"></span>
</div>
<table id="tbl"><thead><tr>
<th data-k="outcome_label">Outcome</th><th data-k="family">Family</th><th data-k="condition">Cond</th>
<th data-k="tract_label">Tract</th><th data-k="hemisphere">Hemi</th><th data-k="tract_type">Type</th>
<th data-k="metric">Metric</th><th data-k="N">N</th><th data-k="n_sig_nodes">Sig nodes</th>
<th data-k="obs_max_cluster">Max cluster</th><th data-k="extent_threshold">Thresh</th>
<th data-k="best_p">Cluster p</th><th data-k="passed">FWE</th>
</tr></thead><tbody id="tbody"></tbody></table>
<div class="legend">FWE = cluster passes permutation extent threshold. Node values are partial-regression t-statistics (outcome on that node's metric + covariates).</div>
</div>

<div class="section"><h2>Hippocampus</h2>
<div class="note" style="background:#232733;border-left:3px solid #a78bfa;border-radius:6px;padding:11px 14px;margin:2px 0 14px;font-size:12.5px;color:#c9d1e0">NODDI sampled inside the anatomical hippocampus ROI itself (not along the tract), same covariates, n=42. β per SD; * p&lt;.05.</div>
<table><thead><tr><th>Outcome</th><th>Metric</th><th>HPC left</th><th>HPC right</th></tr></thead><tbody>
{hpc_table()}
</tbody></table>
<div class="legend"><b>Hippocampal NDI predicts verbal learning, bilaterally</b>: Total Recall × left NDI β=+.37 (p=.028) and right NDI β=+.40 (p=.012); Delayed Recall × right NDI β=+.37 (p=.021). Same direction (denser neurites → better memory) as the motivated-memory finding, and here bilateral. ODI and FWF are null.</div>
</div>

</div>
{js.replace('__DATA__',json.dumps(results)).replace('__META__','{}').replace('__SCRIPTS__',json.dumps(SCRIPTS))}
</body></html>'''
open(f'{OUT}/hvlt_explorer.html','w').write(html)
print(f'wrote hvlt_explorer.html ({len(html)} bytes) · {len(results)} analyses · {n_pass} FWE-significant')
