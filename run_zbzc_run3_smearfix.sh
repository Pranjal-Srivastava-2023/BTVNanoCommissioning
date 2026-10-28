#!/bin/bash
# Check of the electron smearing fix (EGM_shifts: one random number per electron, not per
# event): rerun the DY and ttbar MC of one campaign, 20 files each as in run_zbzc_run3.sh,
# into hists_zbzc_run3_smearfix/<campaign>/. Data, VV and lumi are unchanged by the fix and
# are taken from hists_zbzc_run3/<campaign>/ by compare_zee_smearfix.py.
# usage: ./run_zbzc_run3_smearfix.sh <Summer22|Summer22EE|Summer23|Summer23BPix>
CAMP=$1
case $CAMP in
  Summer22|Summer22EE) YEAR=2022 ;;
  Summer23|Summer23BPix) YEAR=2023 ;;
  *) echo "unknown campaign $CAMP"; exit 1 ;;
esac
cd "$(dirname "$0")"
source /uscms_data/d3/psrivast/micromamba/bin/activate zbb-btv
JSON=metadata/Zb_Zc_ratio_run3_$CAMP.json
OUT=hists_zbzc_run3_smearfix/$CAMP
LOG=logs_zbzc_run3_smearfix/$CAMP; mkdir -p "$LOG"
DSETS=$(python3 -c "
import json
print(' '.join(k for k in json.load(open('$JSON')) if k.startswith(('DYto2L', 'TTto2L2Nu'))))")
for ds in $DSETS; do
  for try in 1 2 3; do
    echo "$(date +%T) $ds try $try" >> "$LOG"/driver.log
    timeout 14400 python runner.py --wf Zb_Zc_ratio --json $JSON \
      --year $YEAR --campaign $CAMP --executor iterative --limit 20 --only $ds \
      --outputdir $OUT --output zbzc_run3.coffea --overwrite > "$LOG"/${ds%%_TuneCP5*}.log 2>&1
    rc=$?; echo "$(date +%T) $ds exit $rc" >> "$LOG"/driver.log
    [ $rc -eq 0 ] && break
  done
done
echo "$(date +%T) ALL DONE" >> "$LOG"/driver.log
