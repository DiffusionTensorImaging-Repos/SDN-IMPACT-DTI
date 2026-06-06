#!/bin/bash
# cr2: 128 cores idle. Run all 80 tests in parallel, 1 core each (no foreach overhead).
# Each test ~8 min serial. With 80 parallel on 128 cores, finishes in ~10 min wall.

DATA="/data/scratch/dti_perm/analysis_ready"
OUT="/data/scratch/dti_perm/results"
RSCRIPT="/data/scratch/dti_perm/permutation_one.R"
LOG="/data/scratch/dti_perm/perm_all.log"

rm -rf "$OUT"
mkdir -p "$OUT"

export R_PERM_CORES=1     # each Rscript = 1 process, no foreach workers
export R_PERM_N=5000      # Ranesh's standard

JOBS=$(mktemp)
for outcome in SOCIAL_dprime MONETARY_dprime ctqsf_adult_totalmaltreatment_pnrscoring ctqsf_adult_totalabuse_pnrscoring ctqsf_adult_totalneglect_pnrscoring; do
  for tract in l_vta_l_hipp r_vta_r_hipp anterior_l_vta_l_hipp anterior_r_vta_r_hipp; do
    for metric in FA NDI ODI FWF; do
      csv="$DATA/${tract}__${metric}__analysis.csv"
      base="${tract}__${metric}__${outcome}"
      echo "$csv|$outcome|${metric}_|$OUT|$base"
    done
  done
done > "$JOBS"

total=$(wc -l < "$JOBS")
echo "=== cr2 run: $total jobs, 80 concurrent (xargs -P 80), 1 core each ===" > "$LOG"
echo "Started: $(date)" >> "$LOG"

cat "$JOBS" | xargs -P 80 -I {} bash -c '
  IFS="|" read -r csv outcome prefix outdir base <<< "{}"
  Rscript "'"$RSCRIPT"'" "$csv" "$outcome" "$prefix" "$outdir" "$base" \
    > "$outdir/${base}.stdout" 2>&1
  echo "DONE $base $(date +%T)" >> "'"$LOG"'"
'

echo "ALL_DONE" >> "$LOG"
echo "Finished: $(date)" >> "$LOG"
rm -f "$JOBS"
