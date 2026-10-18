#!/bin/bash
# 20 files per DY sample, one sample per runner call, timeout + retry against xrootd stalls
# usage: ./run_zbzc_ak4_20files.sh [log dir]   (output: hists_zbzc_ak4_20files/; merge the per-sample coffea files afterwards)
LOG=$(realpath -m "${1:-logs_zbzc_ak4_20files}"); mkdir -p "$LOG"
cd "$(dirname "$0")"
source /uscms_data/d3/psrivast/micromamba/bin/activate zbb-btv
OUT=hists_zbzc_ak4_20files
for ds in $(python3 -c "import json; print(' '.join(json.load(open('metadata/Zb_Zc_ratio_Summer22_DY.json'))))"); do
  for try in 1 2 3; do
    echo "$(date +%T) $ds try $try" >> "$LOG"/driver.log
    timeout 1800 python runner.py --wf Zb_Zc_ratio --json metadata/Zb_Zc_ratio_Summer22_DY.json \
      --year 2022 --campaign Summer22 --executor iterative --limit 20 --only $ds \
      --outputdir $OUT --output zbzc_ak4_20files.coffea --overwrite > "$LOG"/${ds%%_TuneCP5*}.log 2>&1
    rc=$?; echo "$(date +%T) $ds exit $rc" >> "$LOG"/driver.log
    [ $rc -eq 0 ] && break
  done
done
echo "$(date +%T) ALL DONE" >> "$LOG"/driver.log
