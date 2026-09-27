#!/bin/bash
# Submit QCD_sf condor jobs one dataset at a time, sequentially, using
# runner.py's existing --only flag against the combined metadata JSON.
# Isolates failures to a single dataset instead of one giant combined run.
#
# Must be run inside the repo's Apptainer container:
#   ./shell coffeateam/coffea-base-almalinux8:0.7.30-py3.10
# with a valid VOMS proxy and Kerberos ticket on this same node.
#
# Usage: [ERA=era] [OUTDIR=dir] [LOGDIR=dir] ./submit_qcd_sf_per_dataset.sh [dataset1 dataset2 ...]
#   ERA is one of 2016preVFP, 2016postVFP, 2017, 2018 (default 2018).
#   With no arguments, runs all datasets in metadata/QCD_sf_run${ERA}_all.json
#   (made by make_qcd_sf_fileset.py).
#   OUTDIR (optional) is passed to runner.py --outputdir, so outputs land in
#   $OUTDIR/hists_QCD_sf_QCD_sf_run${ERA}_all/ instead of the repo root.

set -u

ERA=${ERA:-2018}
case "$ERA" in
    2016preVFP) CAMPAIGN=2016preVFP-UL; YEAR=2016 ;;
    2016postVFP) CAMPAIGN=2016postVFP-UL; YEAR=2016 ;;
    2017) CAMPAIGN=2017-UL; YEAR=2017 ;;
    2018) CAMPAIGN=2018-UL; YEAR=2018 ;;
    *) echo "Unknown ERA=$ERA"; exit 1 ;;
esac
JSON=metadata/QCD_sf_run${ERA}_all.json
OUTDIR=${OUTDIR:-}
LOGDIR=${LOGDIR:-logs_qcd_sf_split}
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
    print(k)
")
fi

echo "ERA=$ERA: submitting ${#DATASETS[@]} dataset(s) sequentially: ${DATASETS[*]}"

for ds in "${DATASETS[@]}"; do
    echo "=== $(date '+%Y-%m-%d %H:%M:%S') starting $ds ==="
    start=$(date +%s)
    python -u runner.py --workflow QCD_sf \
        --json "$JSON" \
        --campaign "$CAMPAIGN" --year "$YEAR" \
        --executor dask/lpc --scaleout "$SCALEOUT" \
        --only "$ds" --skipbadfiles --overwrite \
        ${OUTDIR:+--outputdir "$OUTDIR"} \
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
