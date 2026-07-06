import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import pearsonr, spearmanr

df = pd.read_csv('/Users/dannyzweben/Desktop/SDN/DTI/data.check/analysis_ready/l_vta_l_hipp__NDI__analysis.csv')
d = df[['Subject','SOCIAL_dprime','MONETARY_dprime']].dropna()

r,p = pearsonr(d.SOCIAL_dprime, d.MONETARY_dprime)
rs,ps = spearmanr(d.SOCIAL_dprime, d.MONETARY_dprime)

fig, ax = plt.subplots(figsize=(7, 7))
ax.scatter(d.SOCIAL_dprime, d.MONETARY_dprime, s=60, alpha=0.7, edgecolor='black', linewidth=0.5, color='#2196F3')

# Best-fit
coef = np.polyfit(d.SOCIAL_dprime, d.MONETARY_dprime, 1)
xf = np.array([d.SOCIAL_dprime.min(), d.SOCIAL_dprime.max()])
ax.plot(xf, np.polyval(coef, xf), color='red', lw=1.5, label='OLS fit')

# Chance = 0 reference lines
ax.axhline(0, color='gray', lw=0.6, linestyle='--', alpha=0.5)
ax.axvline(0, color='gray', lw=0.6, linestyle='--', alpha=0.5)

ax.set_xlabel("SOCIAL d'", fontsize=13)
ax.set_ylabel("MONETARY d'", fontsize=13)
ax.set_title(f"Social vs Monetary memory d'  (n = {len(d)})\nPearson r = {r:.3f}, p = {p:.3f}  |  Spearman r = {rs:.3f}, p = {ps:.3f}",
             fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.2)
ax.legend(fontsize=10)

plt.tight_layout()
out = "/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/images/dprime_social_vs_monetary.png"
plt.savefig(out, dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved {out}")
print(f"Pearson r = {r:.4f}, p = {p:.4f}")
