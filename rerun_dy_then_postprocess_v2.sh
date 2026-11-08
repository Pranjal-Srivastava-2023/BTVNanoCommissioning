#!/bin/bash
# 2026-11-08: in the zbzc_run3_v2 Summer22 run, the DY MLL-50 inclusive job lost 1 of its 20 files
# (XRootD "Operation expired" while preprocessing; the runner still exited 0). After the data driver
# is done, rerun that dataset (same 20 files), require "20/20" in preprocessing, then postprocess.
cd "$(dirname "$0")"
RUN=zbzc_run3_v2; LOG=logs_$RUN/Summer22; DS=DYto2L-2Jets_MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8
until grep -q 'ALL DONE' $LOG/driver_data.log 2>/dev/null; do sleep 120; done
source /uscms_data/d3/psrivast/micromamba/bin/activate zbb-btv
mv $LOG/DYto2L-2Jets_MLL-50.log $LOG/DYto2L-2Jets_MLL-50_try1_19files.log
for try in 1 2 3; do
  echo "$(date +%T) $DS rerun try $try" >> $LOG/driver_mc.log
  timeout 14400 python runner.py --wf Zb_Zc_ratio --json metadata/Zb_Zc_ratio_run3_Summer22.json \
    --year 2022 --campaign Summer22 --executor iterative --limit 20 --only $DS \
    --outputdir hists_$RUN/Summer22 --output zbzc_run3.coffea --overwrite > $LOG/DYto2L-2Jets_MLL-50.log 2>&1
  rc=$?; echo "$(date +%T) $DS rerun exit $rc" >> $LOG/driver_mc.log
  [ $rc -eq 0 ] && grep -q 'Preprocessing 100%.* 20/20 ' $LOG/DYto2L-2Jets_MLL-50.log && break
  echo "$(date +%T) $DS rerun not 20/20 or failed" >> $LOG/driver_mc.log
done
grep -q 'Preprocessing 100%.* 20/20 ' $LOG/DYto2L-2Jets_MLL-50.log || { echo "$(date +%T) DY rerun FAILED, no postprocess"; exit 1; }
echo "$(date +%T) DY rerun OK (20/20)"
exec ./postprocess_zbzc_v2.sh
