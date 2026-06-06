import pandas as pd
from pathlib import Path

R = Path("/Users/dannyzweben/Desktop/SDN/DTI/data.check/permutation_results")

# Master summary table
all_summaries = []
all_hits = []  # significant clusters

for s in sorted(R.glob("*_summary.csv")):
    base = s.stem.replace("_summary", "")
    df = pd.read_csv(s)
    df["base"] = base
    all_summaries.append(df)

    # Parse tract/metric/outcome from base
    # format: <tract>__<metric>__<outcome>
    parts = base.split("__")
    tract = parts[0]
    metric = parts[1]
    outcome = "__".join(parts[2:])

    # Now load clusters file if present
    cf = R / f"{base}_clusters.csv"
    if cf.exists():
        cdf = pd.read_csv(cf)
        if len(cdf):
            cdf = cdf.copy()
            cdf["tract"] = tract; cdf["metric"] = metric; cdf["outcome"] = outcome
            all_hits.append(cdf)

S = pd.concat(all_summaries, ignore_index=True)
print(f"Total tests: {len(S)}")

# Add tract/metric/outcome
S["tract"] = S["base"].str.split("__").str[0]
S["metric"] = S["base"].str.split("__").str[1]
S["outcome"] = S["base"].apply(lambda x: "__".join(x.split("__")[2:]))

# Save master summary
out = S[["outcome","tract","metric","N_subjects","NodesTested","NumNodewiseSignificant",
         "NumClustersFormed","ObservedMaxClusterSize","ExtentThresholdNodes",
         "NumClustersPassingExtent"]].copy()
out.to_csv(R / "ALL_summaries_compact.csv", index=False)

# Filter to hits (clusters passing extent threshold)
if all_hits:
    H = pd.concat(all_hits, ignore_index=True)
    H = H[H["PassExtentThreshold"] == True].copy()
    H = H.sort_values(["ClusterPValue","Size"], ascending=[True, False])
    H = H[["outcome","tract","metric","Size","StartNode","EndNode","Direction",
           "MeanTValue","MaxAbsTValue","MaxAbsTNode","ClusterPValue","ExtentThresholdNodes"]]
    H.to_csv(R / "ALL_SIGNIFICANT_clusters.csv", index=False)
    print(f"\n=== {len(H)} CLUSTERS PASS EXTENT CORRECTION ===\n")
    print(H.to_string(index=False))
else:
    print("\n=== NO significant clusters anywhere ===")

# Also: marginal hits (clusters with sig nodes but didn't pass threshold)
marginal = out[(out["NumNodewiseSignificant"] > 5) & (out["NumClustersPassingExtent"] == 0)]
print(f"\n=== {len(marginal)} tests with ≥5 sig nodes but no cluster passing correction ===")
if len(marginal):
    print(marginal.to_string(index=False))
