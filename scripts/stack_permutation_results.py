#!/usr/bin/env python3
"""
Stack the per-analysis outputs of permutation_one.R into ONE results CSV for the
Node-wise Tract Explorer (results_html/explorer_viewer.html).

permutation_one.R writes, per analysis (named <tract>__<metric>__<outcome>):
    <base>_nodewise.csv   Node, Estimate, t_value, p_value, df, n
    <base>_summary.csv    Covariates, N_subjects, ExtentThresholdNodes, NumPermutations, ...
    <base>_clusters.csv   ClusterPValue, PassExtentThreshold, ...

This script reads every *_nodewise.csv in a folder, attaches the labels parsed
from the filename plus the per-analysis fields from _summary/_clusters, and
writes one long CSV (one row per node) the explorer loads directly.

Usage:
    python stack_permutation_results.py <results_dir> <out.csv> [--hemi]
      --hemi   also derive a hemisphere column (L/R) from the tract name
               (matches l_/r_/left/right/_L/_R). Omit if your tracts aren't lateralized.

The output columns (the explorer's format):
    outcome, tract, metric, node, t, p, [hemisphere], N, covariates,
    extent_threshold, cluster_p, passed
  + you may append ANY extra label columns (family, condition, cohort ...); each
    becomes a filter in the explorer.
"""
import sys, os, glob, re
import pandas as pd

def hemi_of(tract):
    t = tract.lower()
    if re.search(r'(^|[_\-\s])(l|left|lh)([_\-\s]|$)', t): return 'L'
    if re.search(r'(^|[_\-\s])(r|right|rh)([_\-\s]|$)', t): return 'R'
    return ''

def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    d, out = sys.argv[1], sys.argv[2]
    want_hemi = '--hemi' in sys.argv
    frames = []
    for f in sorted(glob.glob(os.path.join(d, '*_nodewise.csv'))):
        base = os.path.basename(f)[:-len('_nodewise.csv')]
        parts = base.split('__')
        if len(parts) < 3:
            print(f'skip (name not <tract>__<metric>__<outcome>): {base}'); continue
        tract, metric, outcome = parts[0], parts[1], '__'.join(parts[2:])
        nw = pd.read_csv(f)
        row = pd.DataFrame({'outcome': outcome, 'tract': tract, 'metric': metric,
                            'node': nw['Node'], 't': nw['t_value'], 'p': nw['p_value']})
        if want_hemi: row['hemisphere'] = hemi_of(tract)
        # per-analysis fields
        s = os.path.join(d, base + '_summary.csv')
        if os.path.exists(s):
            sm = pd.read_csv(s).iloc[0]
            row['N'] = sm.get('N_subjects'); row['covariates'] = sm.get('Covariates')
            row['extent_threshold'] = sm.get('ExtentThresholdNodes')
        c = os.path.join(d, base + '_clusters.csv')
        cp, passed = None, 0
        if os.path.exists(c):
            cl = pd.read_csv(c)
            if len(cl):
                pc = cl[cl['PassExtentThreshold'] == True]
                if len(pc): cp, passed = float(pc['ClusterPValue'].min()), 1
                else: cp = float(cl['ClusterPValue'].min())
        row['cluster_p'] = cp; row['passed'] = passed
        frames.append(row)
    if not frames:
        print('no *_nodewise.csv found in', d); sys.exit(1)
    allrows = pd.concat(frames, ignore_index=True)
    allrows.to_csv(out, index=False)
    print(f'wrote {out}: {len(frames)} analyses, {len(allrows)} node rows')
    print('columns:', ', '.join(allrows.columns))

if __name__ == '__main__':
    main()
