#!/usr/bin/env python3
"""Extract per-subject mean/median RT for each of the 4 phases on cluster."""
import os, csv, re
from pathlib import Path
import pandas as pd

TASK_DIR = Path("/data/projects/STUDIES/IMPACT/IMPACT-task/data")
OUT = Path("/data/projects/STUDIES/IMPACT/DTI/derivatives/analysis/rt_summary.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

rows = []
for subj_dir in sorted(TASK_DIR.iterdir()):
    if not subj_dir.is_dir(): continue
    subj = subj_dir.name
    row = {"Subject": subj}
    for phase_name, glob in [("encoding_social",   "*Encoding_social*_A_*.tsv"),
                             ("encoding_monetary", "*Encoding_monetary*_A_*.tsv"),
                             ("recall_social",     "*Recall_social*[!_practice].tsv"),
                             ("recall_monetary",   "*Recall_monetary*[!_practice].tsv")]:
        # Skip practice — main task file usually has _A_
        files = [f for f in subj_dir.glob("*.tsv") if "practice" not in f.name]
        # Filter to this phase
        if "encoding_social" in phase_name:
            files = [f for f in files if "Encoding_social" in f.name and "_A_" in f.name]
        elif "encoding_monetary" in phase_name:
            files = [f for f in files if "Encoding_monetary" in f.name and "_A_" in f.name]
        elif "recall_social" in phase_name:
            files = [f for f in files if "Recall_social" in f.name]
        elif "recall_monetary" in phase_name:
            files = [f for f in files if "Recall_monetary" in f.name]
        if not files:
            row[f"{phase_name}_rt_mean"] = None
            row[f"{phase_name}_rt_median"] = None
            row[f"{phase_name}_n_trials"] = 0
            continue
        try:
            df = pd.read_csv(files[0], sep='\t')
            rts = pd.to_numeric(df['rt'], errors='coerce').dropna()
            row[f"{phase_name}_rt_mean"]   = float(rts.mean()) if len(rts) else None
            row[f"{phase_name}_rt_median"] = float(rts.median()) if len(rts) else None
            row[f"{phase_name}_n_trials"]  = int(len(rts))
        except Exception as e:
            row[f"{phase_name}_rt_mean"] = None
            row[f"{phase_name}_rt_median"] = None
            row[f"{phase_name}_n_trials"] = 0
    rows.append(row)

pd.DataFrame(rows).to_csv(OUT, index=False)
print(f"Wrote {OUT} — {len(rows)} subjects")
