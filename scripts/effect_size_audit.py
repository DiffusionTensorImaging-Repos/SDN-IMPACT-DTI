#!/usr/bin/env python3
"""
Effect-size audit: for every finding (a tract/metric/outcome with a surviving
cluster), report the subject-level partial correlation (mid-tract NDI-style
average, covariates residualized) in ALL FOUR tracts.

Why: the node-wise cluster test runs on along-tract profiles whose nodes are
highly autocorrelated, so one tract is effectively one subject-level test, and
"significant on the left, zero nodes on the right" can be a p<.05 threshold
difference between two same-direction effects rather than a real dissociation.
This script puts the effect sizes next to the significance so the maps are not
over-read.
"""
import pandas as pd, numpy as np, os, warnings
from scipy import stats
import statsmodels.formula.api as smf
warnings.filterwarnings('ignore')

AR = '/Users/dannyzweben/Desktop/SDN/DTI/data.check/analysis_ready'
PR = '/Users/dannyzweben/Desktop/SDN/DTI/data.check/permutation_results'
COV = ['ICV', 'Mean_tckstats', 'Count_tckstats', 'absolute_motion', 'maternal_age']
TRACTS = {'l_vta_l_hipp': 'postL', 'r_vta_r_hipp': 'postR',
          'anterior_l_vta_l_hipp': 'antL', 'anterior_r_vta_r_hipp': 'antR'}
METRICS = ['FA', 'NDI', 'ODI', 'FWF']
OUTS = ['SOCIAL_dprime', 'MONETARY_dprime', 'SOCIAL_HitRateBias',
        'SOCIAL_FABias', 'MONETARY_HitRateBias', 'MONETARY_FABias']


def partial_r(tract, metric, out):
    """mid-tract (nodes 25-74) partial correlation of metric with outcome, covariates out."""
    d = pd.read_csv(f'{AR}/{tract}__{metric}__analysis.csv')
    d['mid'] = d[[f'{metric}_{i}' for i in range(25, 75)]].mean(axis=1)
    m = d[['mid', out] + COV].dropna()
    if len(m) < 10 or m[out].std() == 0:
        return np.nan, np.nan, len(m)
    xr = smf.ols('mid ~ ' + '+'.join(COV), m).fit().resid
    yr = smf.ols(f'{out} ~ ' + '+'.join(COV), m).fit().resid
    r, p = stats.pearsonr(xr, yr)
    return r, p, len(m)


def survives(tract, metric, out):
    f = f'{PR}/{tract}__{metric}__{out}_summary.csv'
    if not os.path.exists(f):
        return None
    return int(pd.read_csv(f)['NumClustersPassingExtent'].iloc[0])


def main():
    print(f"{'outcome':20s} {'metric':4s}  " + '  '.join(f'{s:>12s}' for s in TRACTS.values()))
    for out in OUTS:
        for metric in METRICS:
            surv = {t: survives(t, metric, out) for t in TRACTS}
            if not any(surv.values()):
                continue
            cells = []
            for t in TRACTS:
                r, p, n = partial_r(t, metric, out)
                star = '*' if surv[t] else ' '
                cells.append(f'{r:+.2f}{star}(p{p:.2f})')
            print(f'{out:20s} {metric:4s}  ' + '  '.join(f'{c:>12s}' for c in cells))
    print("\n* = surviving cluster (cluster-extent FWE). r = mid-tract partial correlation.")


if __name__ == '__main__':
    main()
