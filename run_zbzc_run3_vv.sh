#!/bin/bash
# WW, WZ, ZZ of one campaign as a separate job, so they run in parallel with the
# rest of the MC (run_zbzc_run3.sh <c> mc is stopped before it reaches WW).
# Same runner call as run_zbzc_run3.sh; log logs_zbzc_run3/<c>/driver_vv.log.
# usage: ./run_zbzc_run3_vv.sh <campaign>
CAMP=$1
case $CAMP in
  Summer22|Summer22EE) YEAR=2022 ;;
  Summer23|Summer23BPix) YEAR=2023 ;;
  *) echo "unknown campaign $CAMP"; exit 1 ;;
esac
cd "$(dirname "$0")"
source /uscms_data/d3/psrivast/micromamba/bin/activate zbb-btv
JSON=metadata/Zb_Zc_ratio_run3_$CAMP.json
LOG=logs_zbzc_run3/$CAMP
for ds in WW_TuneCP5_13p6TeV_pythia8 WZ_TuneCP5_13p6TeV_pythia8 ZZ_TuneCP5_13p6TeV_pythia8; do
  for try in 1 2 3; do
    echo "$(date +%T) $ds try $try" >> "$LOG"/driver_vv.log
    timeout 14400 python runner.py --wf Zb_Zc_ratio --json $JSON \
      --year $YEAR --campaign $CAMP --executor iterative --limit 20 --only $ds \
      --outputdir hists_zbzc_run3/$CAMP --output zbzc_run3.coffea --overwrite > "$LOG"/${ds%%_TuneCP5*}.log 2>&1
    rc=$?; echo "$(date +%T) $ds exit $rc" >> "$LOG"/driver_vv.log
    [ $rc -eq 0 ] && break
  done
done
echo "$(date +%T) ALL DONE" >> "$LOG"/driver_vv.log
