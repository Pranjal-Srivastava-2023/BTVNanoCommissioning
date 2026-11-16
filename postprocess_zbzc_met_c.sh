#!/bin/bash
# MET study run C (2026-11-16): JER smearing in the type-1 MET only for gen-matched jets (zbzc_run3_metxy_jermatched,
# MC only, launched as two jobs: DY and tt/VV, both write driver_mc.log). Waits for both "ALL DONE", logs N/N per
# sample, links run A's data (same events, same MET XY), copies lumi.json, makes the stack plots (ZBZC_MET=1) and the
# A / B / C comparison (ZBZC_MET_C=1 -> hists_zbzc_run3_metxy_jermatched/Summer22/met_compare/).
# Writes "postprocess done" to logs_zbzc_run3_metxy_jermatched/postprocess.log (stops the stall watchdog).
cd "$(dirname "$0")"
A=zbzc_run3_metxy; R=zbzc_run3_metxy_jermatched
LOG=logs_$R/postprocess.log
until [ "$(grep -c 'ALL DONE' logs_$R/Summer22/driver_mc.log 2>/dev/null)" -ge 2 ]; do sleep 60; done
echo "$(date +%T) both MC jobs done" >> $LOG
for f in logs_$R/Summer22/*.log; do
  case $f in *driver_*|*nohup*) continue ;; esac
  pre=$(grep -ao "Preprocessing 100%[^]]*" "$f" | tail -1 | grep -o "[0-9][0-9]*/[0-9][0-9]*" | head -1)
  echo "$R $(basename $f .log) files $pre" >> $LOG
done
grep -h "exit" logs_$R/Summer22/driver_mc.log | grep -v "exit 0" >> $LOG
source /uscms_data/d3/psrivast/micromamba/bin/activate zbb-btv
for f in hists_$A/Summer22/zbzc_run3/zbzc_run3_{Muon,EGamma}_*.coffea; do
  ln -sf "$PWD/$f" hists_$R/Summer22/zbzc_run3/
done
cp hists_zbzc_run3_zpt/Summer22/lumi.json hists_$R/Summer22/lumi.json
ZBZC_RUN=$R ZBZC_MET=1 python plot_zbzc_run3.py Summer22 > logs_$R/plot_$R.log 2>&1
echo "$(date +%T) plots $R exit $?" >> $LOG
ZBZC_MET_C=1 python plot_zbzc_met_compare.py > logs_$R/met_compare.log 2>&1
echo "$(date +%T) compare exit $?" >> $LOG
echo "$(date +%T) postprocess done" >> $LOG
