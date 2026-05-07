#!/usr/bin/env python3
"""
Mid-50-nodes (25-74) average + L/R hemisphere correlations.
Per Ranesh's request before the meeting.
"""
import pandas as pd
import numpy as np
from pathlib import Path

fa_dir = Path("/Users/dannyzweben/Desktop/SDN/DTI/data.check/step27_fa")
nd_dir = Path("/Users/dannyzweben/Desktop/SDN/DTI/data.check/step30_noddi")
out_dir = Path("/Users/dannyzweben/Desktop/SDN/DTI/data.check/mid50_summary")
out_dir.mkdir(exist_ok=True, parents=True)

# Mid 50 nodes (Ranesh's request)
mid_nodes = list(range(25, 75))  # nodes 25..74 inclusive

# === Load and process per-tract averages ===
results = {}  # results[(tract_label, metric)] = pd.Series indexed by Subject
metrics_per_tract = {}  # for combining FA + NODDI per tract

for tract in ["l_vta_l_hipp", "r_vta_r_hipp", "anterior_l_vta_l_hipp", "anterior_r_vta_r_hipp"]:
    # FA
    fa = pd.read_csv(fa_dir / f"{tract}_fa_nodewise_all_subjects.csv")
    fa_mid = fa[fa["Node"].isin(mid_nodes)].groupby("Subject")["FA"].mean()
    results[(tract, "FA")] = fa_mid

    # NODDI
    nd = pd.read_csv(nd_dir / f"{tract}_noddi_nodewise_all_subjects.csv")
    nd_mid = nd[nd["Node"].isin(mid_nodes)].groupby("Subject")[["NDI", "ODI", "FWF"]].mean()
    for col in ["NDI", "ODI", "FWF"]:
        results[(tract, col)] = nd_mid[col]

# === Build a wide table: rows=Subject, cols=tract_metric ===
wide = pd.DataFrame()
for (tract, metric), series in results.items():
    wide[f"{tract}__{metric}"] = series
wide.to_csv(out_dir / "mid50_averages_per_subject.csv")
print(f"Wide table saved: {out_dir / 'mid50_averages_per_subject.csv'}  shape={wide.shape}\n")

# === L vs R correlations ===
def lr_pair(tract_pair, metric):
    l_col = f"{tract_pair[0]}__{metric}"
    r_col = f"{tract_pair[1]}__{metric}"
    s = wide[[l_col, r_col]].dropna()
    return s.iloc[:, 0].corr(s.iloc[:, 1]), len(s)

posterior = ("l_vta_l_hipp", "r_vta_r_hipp")
anterior = ("anterior_l_vta_l_hipp", "anterior_r_vta_r_hipp")

print("=" * 72)
print("L vs R correlations (mid 50 nodes, nodes 25-74)")
print("=" * 72)
print(f"{'Tract':<22} {'Metric':<6} {'L vs R r':>10}  {'n':>4}")
print("-" * 72)
for label, pair in [("Posterior VTA→HPC", posterior), ("Anterior VTA→HPC", anterior)]:
    for metric in ["FA", "NDI", "ODI", "FWF"]:
        r, n = lr_pair(pair, metric)
        print(f"{label:<22} {metric:<6} {r:>10.3f}  {n:>4}")
    print()

# === Save correlation table ===
rows = []
for label, pair in [("Posterior VTA→HPC", posterior), ("Anterior VTA→HPC", anterior)]:
    for metric in ["FA", "NDI", "ODI", "FWF"]:
        r, n = lr_pair(pair, metric)
        rows.append({"Tract_Pair": label, "Metric": metric, "L_vs_R_r": round(r, 3), "n": n})
pd.DataFrame(rows).to_csv(out_dir / "lr_correlations_mid50.csv", index=False)
print(f"\nCorr table saved: {out_dir / 'lr_correlations_mid50.csv'}")
