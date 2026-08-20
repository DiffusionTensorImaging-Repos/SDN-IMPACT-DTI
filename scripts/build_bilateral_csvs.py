#!/usr/bin/env python3
"""
Collapse the left+right VTA->hippocampus tracts into bilateral tracts (post-meeting).

Averages the L and R 100-node microstructure profiles per subject (verified aligned:
node 0 = VTA end, node 99 = hippocampus end, L[i] vs R[i] r~0.98). Produces bilateral
analysis CSVs named by the CORRECT convention (anterior/posterior modifies the
HIPPOCAMPUS): vta_anthipp (VTA->anterior hippocampus) and vta_posthipp.

Covariates: ICV / motion / age unchanged (per subject); tract count = L+R (total
streamlines), tract mean length = mean(L,R). Outcomes unchanged.

Out: data.check/analysis_ready_bilateral/<vta_anthipp|vta_posthipp>__<metric>__analysis.csv
"""
import pandas as pd, numpy as np
from pathlib import Path

AR = Path("/Users/dannyzweben/Desktop/SDN/DTI/data.check/analysis_ready")
OUT = Path("/Users/dannyzweben/Desktop/SDN/DTI/data.check/analysis_ready_bilateral")
OUT.mkdir(exist_ok=True, parents=True)

METRICS = ["FA", "NDI", "ODI", "FWF"]
# (bilateral name, left tract, right tract)
PAIRS = [
    ("vta_anthipp",  "anterior_l_vta_l_hipp", "anterior_r_vta_r_hipp"),
    ("vta_posthipp", "l_vta_l_hipp",          "r_vta_r_hipp"),
]
NONNODE = ["Subject", "absolute_motion", "ICV", "maternal_age",
           "SOCIAL_dprime", "MONETARY_dprime",
           "SOCIAL_HitRateBias", "SOCIAL_FABias", "MONETARY_HitRateBias", "MONETARY_FABias",
           "SOCIAL_TrueMemRate", "SOCIAL_FalseMemRate", "MONETARY_TrueMemRate", "MONETARY_FalseMemRate",
           "SOCIAL_hitrate", "SOCIAL_farate", "MONETARY_hitrate", "MONETARY_farate"]

for bil, ltr, rtr in PAIRS:
    for m in METRICS:
        lf = AR / f"{ltr}__{m}__analysis.csv"
        rf = AR / f"{rtr}__{m}__analysis.csv"
        if not lf.exists() or not rf.exists():
            print(f"  skip {bil} {m}: missing {lf.name if not lf.exists() else rf.name}"); continue
        L = pd.read_csv(lf); R = pd.read_csv(rf)
        node_cols = [c for c in L.columns if c.startswith(f"{m}_") and c.split("_")[-1].isdigit()]
        keep = [c for c in NONNODE if c in L.columns]
        out = L[keep].copy()
        Ri = R.set_index("Subject")
        # bilateral node profile = mean(L, R) per node
        for c in node_cols:
            out[c] = (L.set_index("Subject")[c] + Ri[c]).values / 2.0
        # tract covariates: count = sum, mean length = mean
        out["Count_tckstats"] = (L.set_index("Subject")["Count_tckstats"] + Ri["Count_tckstats"]).values
        out["Mean_tckstats"]  = (L.set_index("Subject")["Mean_tckstats"]  + Ri["Mean_tckstats"]).values / 2.0
        # order: covariates then node cols
        cov = ["Subject", "absolute_motion", "ICV", "maternal_age", "Mean_tckstats", "Count_tckstats"]
        outcomes = [c for c in keep if c not in ("Subject", "absolute_motion", "ICV", "maternal_age")]
        out = out[cov + outcomes + node_cols]
        out.to_csv(OUT / f"{bil}__{m}__analysis.csv", index=False)
        print(f"  wrote {bil}__{m}__analysis.csv  shape={out.shape}  (nodes={len(node_cols)})")

print("bilateral CSVs written to", OUT)
