#!/usr/bin/env python3
"""L vs R hemisphere scatterplots for FA + NODDI mid-50 averages."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

wide = pd.read_csv("/Users/dannyzweben/Desktop/SDN/DTI/data.check/mid50_summary/mid50_averages_per_subject.csv", index_col=0)

tract_pairs = [
    ("Posterior", "l_vta_l_hipp", "r_vta_r_hipp"),
    ("Anterior", "anterior_l_vta_l_hipp", "anterior_r_vta_r_hipp"),
]
metrics = ["FA", "NDI", "ODI", "FWF"]

fig, axes = plt.subplots(2, 4, figsize=(16, 8))
fig.suptitle("L vs R Hemisphere — Mid-50 Node Averages (nodes 25-74)",
             fontsize=15, fontweight='bold')

for row, (label, lt, rt) in enumerate(tract_pairs):
    for col, m in enumerate(metrics):
        ax = axes[row, col]
        x = wide[f"{lt}__{m}"]
        y = wide[f"{rt}__{m}"]
        r = x.corr(y)

        # Scatter
        ax.scatter(x, y, s=35, alpha=0.6, edgecolor='black', linewidth=0.4,
                   color='#2196F3' if row == 0 else '#FF9800')

        # Identity + best-fit line
        lim_min = min(x.min(), y.min())
        lim_max = max(x.max(), y.max())
        rng = lim_max - lim_min
        lim_min -= rng * 0.05
        lim_max += rng * 0.05
        ax.plot([lim_min, lim_max], [lim_min, lim_max],
                color='gray', linestyle='--', linewidth=0.8, alpha=0.5)

        # Linear fit
        coef = np.polyfit(x, y, 1)
        xfit = np.array([lim_min, lim_max])
        ax.plot(xfit, np.polyval(coef, xfit),
                color='red', linewidth=1.2, alpha=0.7)

        ax.set_xlim(lim_min, lim_max)
        ax.set_ylim(lim_min, lim_max)
        ax.set_xlabel(f"Left {m}")
        ax.set_ylabel(f"Right {m}")
        ax.set_title(f"{label} VTA→HPC — {m}\nr = {r:.3f}",
                     fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.2)

plt.tight_layout()
out = Path("/Users/dannyzweben/Desktop/SDN/DTI/data.check/mid50_summary/lr_scatterplots_mid50.png")
plt.savefig(out, dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved: {out}")
