# Where the analysis landed (post-meeting rerun)

All bilateral, NDI-primary, corrected naming (anterior/posterior = **hippocampus**).
Node-wise = Freedman-Lane, 5000 perms, cluster-extent FWE, 5 covariates
(ICV, tract count, tract length, motion, maternal age).

## The measurement fix that mattered

Raw d′ was broken for one subject: **s1350** (hit=.92, FA=1.00) → d′ = **−3.33**.
Applied the standard **log-linear correction** (Hautus 1995: +0.5 to each count, +1 to each
total, applied uniformly) → that subject becomes −0.80. Snodgrass & Corwin's correction agrees
at r = .998, so the choice between standard corrections is immaterial.

**This single value was suppressing the node-wise result**: raw d′ gave a 24-node cluster against
a 25-node threshold (missed by one). Corrected d′ gives **60 nodes, p = .0016**.

Convergence across estimators (posterior tract, social):
| measure | cluster | p |
|---|---|---|
| d′, log-linear corrected | **60** | **.0016** |
| A′ (nonparametric) | 58 | .002 |
| Pr (hit − FA) | 37 | .018 |
| d′, uncorrected | 24 | ns (missed by 1) |

Report **corrected d′** as primary; A′/Pr are a robustness footnote.

## The two findings — both NDI, both social-specific

### 1. Memory accuracy (d′)
**Node-wise, posterior tract: nodes 1-60, positive, p = .0016, n = 54.**
Higher neurite density → better discrimination of who actually gave social feedback.
- Monetary d′: **0 nodes** (both tracts) — clean domain specificity
- Anterior tract: 10/29 — null
- Criterion (response bias): r = −0.13, ns → this is discrimination, not response style

### 2. Positivity bias in false memories (FABias)
**Node-wise, posterior tract: nodes 26-77, negative, p = .008** (anterior: 43-77, p = .036).
Higher neurite density → fewer positively-skewed false memories.
- Monetary FABias: null
- Robust: Spearman r = −.37 (p=.007), significant in 52/52 leave-one-out runs

### 3. Hippocampus region (GM-corrected NODDI) — converges
Refit with **dPar lowered 1.7e-3 → 1.1e-3** for gray matter (Ranesh's flag; script
`run_noddi_gm.py`). NDI/ODI rank order preserved (r ≈ .98-.995), FWF changed materially (r ≈ .6).

| outcome | L HPC NDI | bilateral |
|---|---|---|
| **Social d′ (corrected)** | **+0.102 (p=.013)** | **+0.089 (p=.031)** |
| Social FABias | −0.051 (p=.072) | −0.055 (p=.053) |
| Monetary (both) | ns | ns |

So **both the pathway and the region** track social memory accuracy. Same direction, same domain.

## What is NOT there (report as specificity, not failure)
- **All monetary outcomes**: 0 nodes throughout
- **Anterior tract**: nothing survives (0/40 node-wise tests in the exploratory sweep)
- **Raw hit rate / raw FA rate**: null — because they correlate r=.83 with each other
  (shared response criterion). The signal lives in the difference, which is what d′ is.
- **Motivated-memory contrast** (valenced vs neutral): no behavioral effect to track
  (social +0.019, p=.22), so no tract relationship either.
- **Gist memory in errors**: 28.4%, *below* chance — errors are true confusions, not partial memories.

## Task-design facts that shape interpretation
- **Every test item was seen at encoding.** Foils are the co-presented pair partner (verified:
  chosen/unchosen share a trial and outcome). So d′ here = **memory for who actually delivered
  feedback**, i.e. source memory — NOT old/new recognition.
- At recall, items appear **one at a time**.
- Performance is near floor: 53% vs 50% chance; only 2/54 individually beat chance on a binomial
  test (which needs ≥59% at 83 trials). Report as a limitation; **not usable as an exclusion**.

## Open calls
1. **Anterior vs posterior**: posterior is empirically stronger everywhere, contra the meeting's
   theory-driven steer to lead anterior. But the d′ cluster spans **nodes 1-60** — the shared
   corridor — so per Ranesh you cannot infer topology from overlapping clusters. Suggest reporting
   bilateral/whole-tract and not pressing the anterior/posterior contrast.
2. Whether FABias stays as a second finding or moves to supplement.

---

# ADDENDUM 2 — misattribution + hippocampal subregions

## Misattribution IS related to the tract (once criterion is held constant)
Raw false-alarm rate is null (r=+0.02) because it is dominated by response liberalness.
Holding that constant:

| model (social, posterior tract NDI) | effect | p |
|---|---|---|
| FA ~ NDI + **hit rate** + covs | β = −0.68 | **.049** |
| FA ~ NDI + **criterion** + covs | β = −0.43 | **.020** |

Higher NDI → **fewer misattributions**. So the story is not only "false alarms are less positive"
(FABias) — it is **fewer false memories AND less biased ones**. Three convergent effects on the
same tract, all social, all NDI:
1. better discrimination (d′, p=.0016) 2. fewer misattributions (p=.020) 3. less positive skew (p=.008)

Error subtypes do **not** separate (source confusion r=+.07, full fabrication r=+.005, both ns),
so this is overall misattribution rather than a specific error type.

## Hippocampal subregions (uncal apex, MNI y = −21; Poppenk et al. 2013)
Divider built in MNI, warped through the same ANTs→FLIRT chain as the ROIs, intersected with each
subject's HPC. Validated: L 161 ant + 175 post = 336 = whole ROI. Script `scripts/split_hpc.py`;
values in `data/hpc_subregion_ndi.csv` (GM-corrected NODDI, dPar=1.1e-3).

**Social d′ (corrected):**
| L ant | L post | R ant | R post |
|---|---|---|---|
| **+.082 (p=.046)** | **+.100 (p=.015)** | +.065 (p=.11) | +.044 (p=.29) |

**Misattribution (FA | criterion):**
| L ant | L post | R ant | R post | bilat post |
|---|---|---|---|---|
| −.009 (ns) | **−.022 (p=.013)** | **−.018 (p=.037)** | −.015 (p=.098) | **−.019 (p=.027)** |

Monetary null in all four subregions, both outcomes. FABias is a consistent negative trend
(p=.06–.16) but does not clear .05 at the region level.

**Two observations:** the region effects are **left-lateralized**, and **posterior ≥ anterior**
for both d′ and misattribution. Combined with the tract results, this is now **two independent
lines of evidence** against leading with anterior — and unlike the overlapping tracts, the region
division is anatomically unambiguous. Worth raising with Deepu directly.

---

# ⚠️ CORRECTION (supersedes the d′ numbers above)

**Roster bug found and fixed.** When the exploratory memory measures were merged into the bilateral
CSVs, the merge dropped the gated `SOCIAL_dprime` column and replaced it with an ungated
recomputation, re-admitting **s4210** (non-compliant, 100% "remember" rate) and **s1350**
(broken session). The node-wise d′ test therefore ran at n=54 instead of n=52.
All four original per-tract files were always correct at n=52; only the bilateral files drifted.

### Node-wise results on the CORRECT roster (n=52 social / 53 monetary)

| tract | outcome | cluster | threshold | p | verdict |
|---|---|---|---|---|---|
| posterior | **Social FABias** | 52 | 26 | **.0076** | robust |
| anterior | **Social FABias** | 35 | 28 | **.036** | holds |
| posterior | Social d′ (corrected) | 27 | 25 | **.045** | marginal |
| posterior | Social Pr | 28 | 25 | .043 | marginal |
| anterior | Social d′ / Pr | 0 | 29 | — | null |
| both | Monetary d′ | 0 | 27 | — | null |

**The previously reported d′ result (60 nodes, p=.0016) was inflated by the two improperly
included subjects. The true value is 27 nodes, p=.045.**

**Consequence: FABias is the primary finding, not d′.** FABias survives in BOTH tracts and its
numbers never changed (it was always correctly gated). d′ is marginal and should be reported as
suggestive.

### The anterior/posterior "dissociation" is a covariate artifact
Mid-tract NDI correlates **r = +0.977** between the two tracts — they are nearly the same
measurement. With matched covariates they behave identically:

| covariates | anterior | posterior |
|---|---|---|
| shared (ICV, motion, age) | +0.275 (p=.048) | +0.305 (p=.028) |
| + each tract's own length/count | +0.070 (p=.62) | +0.334 (p=.015) |

The driver is **`Count_tckstats`**: anterior streamline count itself correlates with d′
(r=+0.295, p=.034), so controlling for it removes the shared signal. Adding anterior *length*
alone leaves the effect intact (r=+0.267, p=.056); adding *count* collapses it.

**Open decision:** `Count_tckstats` may be over-controlling, since streamline count partly indexes
the same white-matter organization NDI measures. Options: (a) shared covariates as primary with
tract-size as sensitivity, or (b) keep it and label the analysis conservative. Worth asking Ranesh.

### Binomial test — already done, no further work needed
2/54 social above chance individually, but with 83 trials an individual needs ≥59% accuracy to be
detectable and the sample mean is 51.4%. It is a power limitation, not evidence of no memory, and
cannot be used as a filter (n=2). Report as a limitation sentence.
