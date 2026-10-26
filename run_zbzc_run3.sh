#!/bin/bash
# Zb_Zc_ratio Run 3 small run for one campaign: every dataset in
# metadata/Zb_Zc_ratio_run3_<campaign>.json, 20 files each (the data keys are
# pre-sampled to 20 files per channel), one runner call per dataset with a
# timeout + retry against xrootd stalls.
# usage: ./run_zbzc_run3.sh <Summer22|Summer22EE|Summer23|Summer23BPix> [mc|data|all]
# (the reads are xrootd-bound, so the MC and data parts of a campaign can run as
# two parallel jobs)
# output: hists_zbzc_run3/<campaign>/zbzc_run3/zbzc_run3_<dataset>.coffea, logs in logs_zbzc_run3/<campaign>/
CAMP=$1
PART=${2:-all}
case $CAMP in
  Summer22|Summer22EE) YEAR=2022 ;;
  Summer23|Summer23BPix) YEAR=2023 ;;
  *) echo "unknown campaign $CAMP"; exit 1 ;;
esac
cd "$(dirname "$0")"
source /uscms_data/d3/psrivast/micromamba/bin/activate zbb-btv
JSON=metadata/Zb_Zc_ratio_run3_$CAMP.json
OUT=hists_zbzc_run3/$CAMP
LOG=logs_zbzc_run3/$CAMP; mkdir -p "$LOG"
DSETS=$(python3 -c "
import json
keys = list(json.load(open('$JSON')))
isdata = lambda k: k.startswith(('Muon', 'EGamma'))
print(' '.join(k for k in keys if '$PART' == 'all' or ('$PART' == 'data') == isdata(k)))")
for ds in $DSETS; do
  for try in 1 2 3; do
    echo "$(date +%T) $ds try $try" >> "$LOG"/driver_$PART.log
    timeout 14400 python runner.py --wf Zb_Zc_ratio --json $JSON \
      --year $YEAR --campaign $CAMP --executor iterative --limit 20 --only $ds \
      --outputdir $OUT --output zbzc_run3.coffea --overwrite > "$LOG"/${ds%%_TuneCP5*}.log 2>&1
    rc=$?; echo "$(date +%T) $ds exit $rc" >> "$LOG"/driver_$PART.log
    [ $rc -eq 0 ] && break
  done
done
echo "$(date +%T) ALL DONE" >> "$LOG"/driver_$PART.log
