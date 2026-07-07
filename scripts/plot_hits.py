import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

R = Path("/Users/dannyzweben/Desktop/SDN/DTI/data.check/permutation_results")
out_dir = Path("/Users/dannyzweben/Desktop/SDN/DTI/data.check/permutation_plots")
out_dir.mkdir(exist_ok=True)

HITS = [
    {"base": "l_vta_l_hipp__NDI__SOCIAL_dprime", "outcome": "SOCIAL d'",
     "tract": "Posterior Left VTA→HPC", "metric": "NDI",
     "cluster": "4-48", "p": 0.014, "color": "#2196F3"},
    {"base": "r_vta_r_hipp__NDI__MONETARY_dprime", "outcome": "MONETARY d'",
     "tract": "Posterior Right VTA→HPC", "metric": "NDI",
     "cluster": "36-74", "p": 0.017, "color": "#F44336"},
    {"base": "r_vta_r_hipp__NDI__MONETARY_FalseMemRate", "outcome": "MONETARY False-mem rate",
     "tract": "Posterior Right VTA→HPC", "metric": "NDI",
     "cluster": "42-79", "p": 0.018, "color": "#9C27B0"},
    {"base": "anterior_r_vta_r_hipp__FWF__MONETARY_dprime", "outcome": "MONETARY d'",
     "tract": "Anterior Right VTA→HPC", "metric": "FWF",
     "cluster": "39-58", "p": 0.048, "color": "#FF9800"},
    # --- Bias hits (new) ---
    {"base": "r_vta_r_hipp__NDI__SOCIAL_FABias", "outcome": "SOCIAL FABias",
     "tract": "Posterior Right VTA→HPC", "metric": "NDI",
     "cluster": "36-67", "p": 0.026, "color": "#00BCD4"},
    {"base": "r_vta_r_hipp__FA__SOCIAL_FABias", "outcome": "SOCIAL FABias",
     "tract": "Posterior Right VTA→HPC", "metric": "FA",
     "cluster": "39-63", "p": 0.032, "color": "#4CAF50"},
    {"base": "r_vta_r_hipp__FA__MONETARY_FABias", "outcome": "MONETARY FABias",
     "tract": "Posterior Right VTA→HPC", "metric": "FA",
     "cluster": "1-23", "p": 0.039, "color": "#795548"},
    {"base": "l_vta_l_hipp__FA__SOCIAL_FABias", "outcome": "SOCIAL FABias",
     "tract": "Posterior Left VTA→HPC", "metric": "FA",
     "cluster": "43-64", "p": 0.047, "color": "#607D8B"},
]

fig, axes = plt.subplots(2, 4, figsize=(22, 10))
axes = axes.flatten()
fig.suptitle("Significant Clusters — Per-Node t-values (Freedman–Lane, 5000 perms, α=0.05)",
             fontsize=15, fontweight='bold')

for ax, h in zip(axes, HITS):
    nw = pd.read_csv(R / f"{h['base']}_nodewise.csv")
    sig_lo, sig_hi = [int(x) for x in h["cluster"].split("-")]

    # All nodes — line plot of t-values
    ax.plot(nw["Node"], nw["t_value"], color="black", lw=1.2)
    ax.axhline(0, color="gray", lw=0.6)
    ax.axhline(2, color="red", linestyle="--", lw=0.6, alpha=0.6, label="|t| ≈ p<0.05")
    ax.axhline(-2, color="red", linestyle="--", lw=0.6, alpha=0.6)

    # Highlight significant cluster
    in_cluster = (nw["Node"] >= sig_lo) & (nw["Node"] <= sig_hi)
    ax.fill_between(nw["Node"], nw["t_value"], 0,
                    where=in_cluster, alpha=0.4, color=h["color"],
                    label=f"Cluster {h['cluster']}, p = {h['p']:.3f}")

    ax.set_xlabel("Node along tract (0 = VTA, 99 = HPC)")
    ax.set_ylabel(f"t-value ({h['metric']} ~ outcome)")
    ax.set_title(f"{h['outcome']}\n{h['tract']} — {h['metric']}",
                 fontsize=12, fontweight='bold')
    ax.set_ylim(-4, 4)
    ax.legend(loc='lower left', fontsize=9)
    ax.grid(True, alpha=0.2)

plt.tight_layout()
out_png = out_dir / "permutation_hits.png"
plt.savefig(out_png, dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved {out_png}")
