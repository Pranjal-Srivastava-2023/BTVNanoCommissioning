#!/bin/bash
# 2026-11-08, zbzc_run3_v2 Summer22: two datasets silently lost a file in the runner's file validation
# (XRootD "Operation expired"; runner still exits 0):
#  - DY MLL-50 inclusive, file 0ce05172-...: its cmsdcadisk pool does not serve it (fails even with a
#    300 s timeout), but the same LFN reads fine via root://cmsxrootd.fnal.gov/ -> rerun with a sample
#    json where only that URL points to the redirector (same 20 files, same order)
#  - EGamma_Run2022D, file 002aaeb4-...: transient, opens fine now -> plain rerun (5 files)
# Each rerun must show the full file count in preprocessing; then postprocess_zbzc_v2.sh.
cd "$(dirname "$0")"
RUN=zbzc_run3_v2; LOG=logs_$RUN/Summer22
source /uscms_data/d3/psrivast/micromamba/bin/activate zbb-btv
one() {  # dataset json logname nfiles
  for try in 1 2 3; do
    echo "$(date +%T) $1 fix-rerun try $try" >> $LOG/driver_fix.log
    timeout 14400 python runner.py --wf Zb_Zc_ratio --json $2 --year 2022 --campaign Summer22 \
      --executor iterative --limit 20 --only $1 --outputdir hists_$RUN/Summer22 \
      --output zbzc_run3.coffea --overwrite > $LOG/$3.log 2>&1
    rc=$?; echo "$(date +%T) $1 fix-rerun exit $rc" >> $LOG/driver_fix.log
    [ $rc -eq 0 ] && grep -q "Preprocessing 100%.* $4/$4 " $LOG/$3.log && return 0
  done
  return 1
}
one DYto2L-2Jets_MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8 $LOG/../Zb_Zc_ratio_run3_Summer22_dyredir.json DYto2L-2Jets_MLL-50 20 & p1=$!
one EGamma_Run2022D metadata/Zb_Zc_ratio_run3_Summer22.json EGamma_Run2022D 5 & p2=$!
wait $p1; r1=$?; wait $p2; r2=$?
if [ $r1 -ne 0 ] || [ $r2 -ne 0 ]; then echo "$(date +%T) fix-rerun FAILED (DY $r1, EGammaD $r2), no postprocess"; exit 1; fi
echo "$(date +%T) fix-rerun OK: DY 20/20, EGamma_Run2022D 5/5"
exec ./postprocess_zbzc_v2.sh
