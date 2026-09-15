#!/usr/bin/env python3
"""
Build results_html/results_data.json and results_html/models_data.json for the Results Explorer.

Node-wise rows come from two permutation-output directories with the same R schema
(*_summary.csv, *_nodewise.csv, *_clusters.csv; Freedman-Lane, 5000 perms, cluster-extent FWE):
  data.check/sweep_withcount/        NDI, both bilateral tracts, every memory measure that was run
  data.check/bilateral_perm_results/ FA / ODI / FWF (and NDI) for d', FABias, HitRateBias, hit rate, FA rate
The reported outcomes (log-linear d', misattribution, FABias; social and monetary) are flagged so the
explorer can default to them. Model rows (whole tract, quartiles, metric comparison, hippocampal NDI,
HVLT) come from data.check/final_models_summary.csv, written by scripts/final_models.py.
"""
import glob, json, os
import pandas as pd

BASE = '/Users/dannyzweben/Desktop/SDN/DTI'
SWEEP = f'{BASE}/data.check/sweep_withcount'
BILAT = f'{BASE}/data.check/bilateral_perm_results'
MODELS = f'{BASE}/data.check/final_models_summary.csv'
OUT = f'{BASE}/SDN-IMPACT-DTI/results_html'

TRACTS = {'vta_anthipp': ('VTA→anterior hippocampus', 'anterior'),
          'vta_posthipp': ('VTA→posterior hippocampus', 'posterior')}
METRICS = ['NDI', 'ODI', 'FWF', 'FA']
# bilateral dir used different names for two component rates
ALIAS = {'farate': 'fa', 'hitrate': 'hit'}

REPORTED = {'dprime_loglinear', 'fa_adjCriterion', 'FABias'}
LABEL = {  # measure -> (label, family)
    'dprime_loglinear': ("d′ (log-linear)", 'Reported: accuracy'),
    'fa_adjCriterion':  ('Misattribution (FA rate | criterion)', 'Reported: misattribution'),
    'FABias':           ('Positive false-alarm bias', 'Reported: positivity bias'),
    'HitRateBias':      ('Positive hit-rate bias', 'Positivity bias'),
    'hit_pos_minus_neg': ('Hit rate, positive minus negative', 'Positivity bias'),
    'dprime':           ("d′ (uncorrected)", 'Accuracy, other estimators'),
    'dprime_snodgrass': ("d′ (Snodgrass-Corwin)", 'Accuracy, other estimators'),
    'pairsep_dprime':   ("Pair-separation d′", 'Accuracy, other estimators'),
    'pr':               ('Pr (hit − FA)', 'Accuracy, other estimators'),
    'Aprime':           ("A′ (nonparametric)", 'Accuracy, other estimators'),
    'val_dprime':       ("Valence d′", 'Accuracy, other estimators'),
    'hit':              ('Hit rate', 'Recognition components'),
    'fa':               ('False-alarm rate', 'Recognition components'),
    'criterion':        ('Response criterion c', 'Recognition components'),
    'prop_remember':    ('Proportion "remember"', 'Recognition components'),
    'strict_hit':       ('Strict hit (right item and valence)', 'Recognition components'),
    'n_fa':             ('Number of false alarms', 'Recognition components'),
    'fa_ll':            ('False-alarm rate (log-linear)', 'Recognition components'),
    'hit_ll':           ('Hit rate (log-linear)', 'Recognition components'),
    'fa_source_conf':   ('False alarms: source confusion', 'False-alarm subtypes'),
    'fa_fabrication':   ('False alarms: fabrication', 'False-alarm subtypes'),
}
FALLBACK_FAMILY = [('valacc', 'Valence accuracy'), ('gist', 'Gist and precision'), ('precision', 'Gist and precision'),
                   ('rt', 'Reaction time'), ('motivated', 'Valence accuracy'), ('pred', 'Prediction trials'),
                   ('hit_', 'Hit rate by valence')]


def label_for(measure):
    if measure in LABEL:
        return LABEL[measure]
    fam = next((f for k, f in FALLBACK_FAMILY if measure.startswith(k) or k in measure), 'Other measures')
    return (measure.replace('_', ' '), fam)


def parse(base):
    """'vta_posthipp__NDI__SOCIAL_FABias' -> (tract, metric, condition, measure)"""
    tract, metric, outcome = base.split('__', 2)
    cond, measure = outcome.split('_', 1)
    return tract, metric, cond, ALIAS.get(measure, measure)


def load_one(d, base):
    s = pd.read_csv(f'{d}/{base}_summary.csv').iloc[0]
    clusters = []
    cf = f'{d}/{base}_clusters.csv'
    if os.path.exists(cf) and os.path.getsize(cf) > 0:
        cdf = pd.read_csv(cf)
        for _, c in cdf.iterrows():
            clusters.append(dict(size=int(c['Size']), start=int(c['StartNode']), end=int(c['EndNode']),
                                 p=round(float(c['ClusterPValue']), 4), dir=c['Direction'],
                                 mean_t=round(float(c['MeanTValue']), 3), passes=bool(c['PassExtentThreshold'])))
    nw = pd.read_csv(f'{d}/{base}_nodewise.csv')
    tvals = [round(float(x), 3) if pd.notna(x) else None for x in nw['t_value']]
    pvals = [round(float(x), 4) if pd.notna(x) else None for x in nw['p_value']]
    sig = [int(n) for n, p in zip(nw['Node'], nw['p_value']) if pd.notna(p) and p < 0.05]
    tract, metric, cond, measure = parse(base)
    tl, ttype = TRACTS[tract]
    lab, fam = label_for(measure)
    passed = any(c['passes'] for c in clusters)
    return dict(id=f'{tract}__{metric}__{cond}_{measure}', tract=tract, tract_label=tl, tract_type=ttype,
                metric=metric, condition=cond, measure=measure, outcome=f'{cond}_{measure}',
                outcome_label=lab, family=fam, reported=(measure in REPORTED and metric == 'NDI'),
                N=int(s['N_subjects']), dropped=int(s['N_dropped']), n_perms=int(s['NumPermutations']),
                n_sig_nodes=int(s['NumNodewiseSignificant']), obs_max_cluster=int(s['ObservedMaxClusterSize']),
                extent_threshold=int(s['ExtentThresholdNodes']), n_passing=int(s['NumClustersPassingExtent']),
                passed=passed, best_p=min([c['p'] for c in clusters if c['passes']], default=None),
                clusters=clusters, sig_node_list=sig, tvals=tvals, pvals=pvals,
                covariates='ICV, tract length, streamline count, absolute motion, maternal age')


rows, seen = [], set()
for d in (SWEEP, BILAT):                       # sweep first so NDI rows come from the settled runs
    for summ in sorted(glob.glob(f'{d}/*_summary.csv')):
        base = os.path.basename(summ)[:-len('_summary.csv')]
        tract, metric, cond, measure = parse(base)
        if tract not in TRACTS or metric not in METRICS:
            continue
        key = (tract, metric, cond, measure)
        if key in seen:
            continue
        seen.add(key)
        rows.append(load_one(d, base))

rows.sort(key=lambda r: (not r['reported'], r['family'], r['condition'], r['measure'], r['metric'], r['tract']))
json.dump(rows, open(f'{OUT}/results_data.json', 'w'))

m = pd.read_csv(MODELS)
json.dump(m.where(pd.notna(m), None).to_dict('records'), open(f'{OUT}/models_data.json', 'w'))

print(f'results_data.json: {len(rows)} node-wise analyses '
      f'({sum(r["reported"] for r in rows)} reported, {sum(r["passed"] for r in rows)} FWE-significant)')
print('  by metric:', {k: sum(r['metric'] == k for r in rows) for k in METRICS})
print(f'models_data.json: {len(m)} model rows')
