#!/bin/bash
# Submit QCD_sf condor jobs one dataset at a time, sequentially, using
# runner.py's existing --only flag against the combined metadata JSON.
# Isolates failures to a single dataset instead of one giant combined run.
#
# Must be run inside the repo's Apptainer container:
#   ./shell coffeateam/coffea-base-almalinux8:0.7.30-py3.10
# with a valid VOMS proxy and Kerberos ticket on this same node.
#
# Usage: ./submit_qcd_sf_per_dataset.sh [dataset1 dataset2 ...]
#   With no arguments, runs all datasets in metadata/QCD_sf_run2018_all.json
#   except DYJetsToLL_2J (already validated on 2026-09-01).

set -u

JSON=metadata/QCD_sf_run2018_all.json
LOGDIR=logs_qcd_sf_split
SUMMARY=$LOGDIR/summary.log
SCALEOUT=8

mkdir -p "$LOGDIR"

if [ "$#" -gt 0 ]; then
    DATASETS=("$@")
else
    mapfile -t DATASETS < <(python3 -c "
import json
d = json.load(open('$JSON'))
for k in d:
    if k != 'DYJetsToLL_2J_TuneCP5_13TeV-amcatnloFXFX-pythia8':
        print(k)
")
fi

echo "Submitting ${#DATASETS[@]} dataset(s) sequentially: ${DATASETS[*]}"

for ds in "${DATASETS[@]}"; do
    echo "=== $(date '+%Y-%m-%d %H:%M:%S') starting $ds ==="
    start=$(date +%s)
    python -u runner.py --workflow QCD_sf \
        --json "$JSON" \
        --campaign 2018-UL --year 2018 \
        --executor dask/lpc --scaleout "$SCALEOUT" \
        --only "$ds" --skipbadfiles --overwrite \
        > "$LOGDIR/${ds}.log" 2>&1
    rc=$?
    end=$(date +%s)
    elapsed=$((end - start))
    status="OK"
    if [ "$rc" -ne 0 ]; then
        status="FAILED(rc=$rc)"
    fi
    echo "$(date '+%Y-%m-%d %H:%M:%S') $ds $status elapsed=${elapsed}s log=$LOGDIR/${ds}.log" | tee -a "$SUMMARY"
done

echo "All submissions done. See $SUMMARY for pass/fail summary."
