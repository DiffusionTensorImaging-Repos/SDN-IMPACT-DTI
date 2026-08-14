#!/bin/bash
# HVLT outcomes: 2 outcomes x 4 tracts x 4 metrics = 32 node-wise permutation tests
DATA="/Users/dannyzweben/Desktop/SDN/DTI/data.check/analysis_ready"
OUT="/Users/dannyzweben/Desktop/SDN/DTI/data.check/permutation_results"
RSCRIPT="/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/scripts/permutation_one.R"
OUTCOMES=("hvlt_totalrecall" "hvlt_delayedrecall")
TRACTS=("l_vta_l_hipp" "r_vta_r_hipp" "anterior_l_vta_l_hipp" "anterior_r_vta_r_hipp")
METRICS=("FA" "NDI" "ODI" "FWF")
n=0; t=$((${#OUTCOMES[@]}*${#TRACTS[@]}*${#METRICS[@]}))
for o in "${OUTCOMES[@]}"; do for tr in "${TRACTS[@]}"; do for m in "${METRICS[@]}"; do
  n=$((n+1)); base="${tr}__${m}__${o}"
  echo "[$n/$t] $base"
  Rscript "$RSCRIPT" "$DATA/${tr}__${m}__analysis.csv" "$o" "${m}_" "$OUT" "$base" 2>&1 | tail -1
done; done; done
echo "HVLT_PERMS_DONE"
