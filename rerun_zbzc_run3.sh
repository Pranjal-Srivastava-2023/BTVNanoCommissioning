#!/bin/bash
# Rerun one dataset of the Zb_Zc_ratio Run 3 small run (same runner call as
# run_zbzc_run3.sh, 3 tries). Logs to logs_zbzc_run3/<c>/rerun_<dataset>.log
# (not driver_*.log, which postprocess_zbzc_run3.sh counts), ending "RERUN DONE".
# usage: ./rerun_zbzc_run3.sh <campaign> <dataset>
CAMP=$1
DS=$2
case $CAMP in
  Summer22|Summer22EE) YEAR=2022 ;;
  Summer23|Summer23BPix) YEAR=2023 ;;
  *) echo "unknown campaign $CAMP"; exit 1 ;;
esac
cd "$(dirname "$0")"
source /uscms_data/d3/psrivast/micromamba/bin/activate zbb-btv
LOG=logs_zbzc_run3/$CAMP/rerun_${DS%%_TuneCP5*}.log
for try in 1 2 3; do
  echo "$(date +%T) $DS try $try" >> $LOG
  timeout 14400 python runner.py --wf Zb_Zc_ratio --json metadata/Zb_Zc_ratio_run3_$CAMP.json \
    --year $YEAR --campaign $CAMP --executor iterative --limit 20 --only $DS \
    --outputdir hists_zbzc_run3/$CAMP --output zbzc_run3.coffea --overwrite > logs_zbzc_run3/$CAMP/${DS%%_TuneCP5*}.log 2>&1
  rc=$?; echo "$(date +%T) $DS exit $rc" >> $LOG
  [ $rc -eq 0 ] && break
done
echo "$(date +%T) RERUN DONE" >> $LOG
