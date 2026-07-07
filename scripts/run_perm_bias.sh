#!/bin/bash
# 4 memory-bias outcomes × 4 tracts × 4 metrics = 64 tests
# xargs -P 64 on cr2 (128 cores), 1 core per Rscript, 5000 perms each.

DATA="/data/scratch/dti_perm/analysis_ready"
OUT="/data/scratch/dti_perm/results"
RSCRIPT="/data/scratch/dti_perm/permutation_one.R"
LOG="/data/scratch/dti_perm/perm_bias.log"

mkdir -p "$OUT"
export R_PERM_CORES=1
export R_PERM_N=5000

JOBS=$(mktemp)
for outcome in SOCIAL_HitRateBias SOCIAL_FABias MONETARY_HitRateBias MONETARY_FABias; do
  for tract in l_vta_l_hipp r_vta_r_hipp anterior_l_vta_l_hipp anterior_r_vta_r_hipp; do
    for metric in FA NDI ODI FWF; do
      csv="$DATA/${tract}__${metric}__analysis.csv"
      base="${tract}__${metric}__${outcome}"
      echo "$csv|$outcome|${metric}_|$OUT|$base"
    done
  done
done > "$JOBS"

total=$(wc -l < "$JOBS")
echo "=== bias run: $total jobs, 64 concurrent ===" > "$LOG"
echo "Started: $(date)" >> "$LOG"

cat "$JOBS" | xargs -P 64 -I {} bash -c '
  IFS="|" read -r csv outcome prefix outdir base <<< "{}"
  Rscript "'"$RSCRIPT"'" "$csv" "$outcome" "$prefix" "$outdir" "$base" \
    > "$outdir/${base}.stdout" 2>&1
  echo "DONE $base $(date +%T)" >> "'"$LOG"'"
'

echo "BIAS_ALL_DONE" >> "$LOG"
echo "Finished: $(date)" >> "$LOG"
rm -f "$JOBS"
