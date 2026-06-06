#!/bin/bash
# cr2: run ONLY the 4 new memory-rate outcomes (64 tests).
# Each Rscript = 1 core. 64 < 128 cores, no contention.
DATA="/data/scratch/dti_perm/analysis_ready"
OUT="/data/scratch/dti_perm/results"
RSCRIPT="/data/scratch/dti_perm/permutation_one.R"
LOG="/data/scratch/dti_perm/perm_v2.log"

mkdir -p "$OUT"

export R_PERM_CORES=1
export R_PERM_N=5000     # Ranesh's standard

JOBS=$(mktemp)
for outcome in SOCIAL_TrueMemRate SOCIAL_FalseMemRate MONETARY_TrueMemRate MONETARY_FalseMemRate; do
  for tract in l_vta_l_hipp r_vta_r_hipp anterior_l_vta_l_hipp anterior_r_vta_r_hipp; do
    for metric in FA NDI ODI FWF; do
      csv="$DATA/${tract}__${metric}__analysis.csv"
      base="${tract}__${metric}__${outcome}"
      echo "$csv|$outcome|${metric}_|$OUT|$base"
    done
  done
done > "$JOBS"

total=$(wc -l < "$JOBS")
echo "=== cr2 v2: $total jobs, 64 concurrent ===" > "$LOG"
echo "Started: $(date)" >> "$LOG"

cat "$JOBS" | xargs -P 64 -I {} bash -c '
  IFS="|" read -r csv outcome prefix outdir base <<< "{}"
  Rscript "'"$RSCRIPT"'" "$csv" "$outcome" "$prefix" "$outdir" "$base" \
    > "$outdir/${base}.stdout" 2>&1
  echo "DONE $base $(date +%T)" >> "'"$LOG"'"
'

echo "V2_ALL_DONE" >> "$LOG"
echo "Finished: $(date)" >> "$LOG"
rm -f "$JOBS"
