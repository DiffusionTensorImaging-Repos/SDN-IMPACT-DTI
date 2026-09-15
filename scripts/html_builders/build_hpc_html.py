#!/usr/bin/env python3
"""
Build results_html/hpc_region_vs_connection.html: hippocampal gray-matter NDI (NODDI refit at the
gray-matter parallel diffusivity) regressed on each memory outcome. Numbers from
results_html/models_data.json (scripts/final_models.py, analysis == 'hpc_gm_ndi').
"""
import json
OUT = '/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/results_html'
M = [r for r in json.load(open(f'{OUT}/models_data.json')) if r['analysis'] == 'hpc_gm_ndi']
ORDER = ['Social FABias', 'Social d′', 'Social misattribution', 'Monetary FABias', 'Monetary d′', 'Monetary misattribution']
NICE = {'Social FABias': 'Social positive FA bias', 'Monetary FABias': 'Monetary positive FA bias'}
DIR = {'Social FABias': 'higher NDI, less positive skew in false memories', 'Social d′': 'higher NDI, better discrimination',
       'Social misattribution': 'higher NDI, fewer misattributions'}

def pcell(p):
    s = f'{p:.3f}'.replace('0.', '.', 1)
    return f'<td class="sig">{s} *</td>' if p < .05 else f'<td>{s}</td>'

rows = ''
for o in ORDER:
    r = next(x for x in M if x['outcome'] == o)
    rows += f'<tr><td>{NICE.get(o,o)}</td><td>{r["main_b"]:+.3f}</td>{pcell(r["main_p"])}<td>{r["n"]}</td><td class="mut">{DIR.get(o,"null")}</td></tr>'

HTML = f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IMPACT · Hippocampal NDI</title>
<link rel="stylesheet" href="_pres.css">
</head><body>
<nav class="topnav">
  <span class="brand">IMPACT · <span>VTA→HPC</span> &amp; Motivated Memory</span>
  <a href="intro.html">Overview</a>
  <a href="background.html">Background</a>
  <a href="pipeline.html">Pipeline</a>
  <a href="analyses.html">Analyses</a>
  <a href="results_explorer.html" class="results">Results ↗</a>
</nav>
<div class="wrap">
  <h1>Hippocampal gray-matter NDI</h1>
  <p class="lead">Does the hippocampus itself carry the memory signal the pathway carries? Neurite density inside the hippocampal ROI, regressed on the same outcomes.</p>

  <h2>Method</h2>
  <p>NODDI in gray matter needs a lower intrinsic parallel diffusivity than white matter. The hippocampal ROI was refit with dPar = 1.1e-3 mm²/s (white-matter default 1.7e-3; isotropic 3.0e-3), restricted to the ROI, and NDI averaged over the bilateral hippocampus (<span class="mono">scripts/run_noddi_gm.py</span>). Each outcome was regressed on that value with ICV, hippocampal volume, absolute motion and maternal age; standardized β. n = 52 social, 53 monetary.</p>
  <div class="formula"><span class="lbl">outcome</span> ~ z(HPC NDI) + ICV + HPC volume + absolute_motion + maternal_age</div>

  <h2>Results</h2>
  <table class="dtable"><thead><tr><th>Outcome</th><th>β</th><th>p</th><th>n</th><th>Direction</th></tr></thead><tbody>{rows}</tbody></table>
  <p class="small">* p &lt; .05. Hippocampal volume on its own predicts none of the six outcomes.</p>

  <h2>Reading it</h2>
  <p>The region converges with the pathway. The same outcomes move, in the same directions, with the same social specificity: neurite density in the hippocampus predicts social d′ and positive false-alarm bias, misattribution is marginal, and every monetary counterpart is null. The effect is not volumetric, since hippocampal volume is a covariate and predicts nothing alone, and it survives the gray-matter diffusivity correction rather than dissolving into orientation dispersion as such effects sometimes do.</p>
  <p class="small">The whole-tract and quartile results this sits alongside are on the <a href="results_explorer.html">Results</a> page; the full funnel is under <a href="analyses.html">Analyses</a>.</p>
</div>
</body></html>'''
open(f'{OUT}/hpc_region_vs_connection.html', 'w').write(HTML)
print(f'wrote hpc_region_vs_connection.html ({len(HTML)} bytes)')
