#!/bin/bash
# MET > 50 study Phase 2 (2026-11-22): zbzc_run3_metvar = run A (metxy, Z pT weights) + MET_VARIANTS filled side by
# side (MC only, two jobs: DY and tt/VV, both write driver_mc.log). Waits for both "ALL DONE", logs N/N per sample,
# links run A's data (data have no JER: every MET version = nominal MET), copies lumi.json.
# Writes "postprocess done" to logs_zbzc_run3_metvar/postprocess.log (stops the stall watchdog).
cd "$(dirname "$0")"
A=zbzc_run3_metxy; R=zbzc_run3_metvar
LOG=logs_$R/postprocess.log
until [ "$(grep -c 'ALL DONE' logs_$R/Summer22/driver_mc.log 2>/dev/null)" -ge 2 ]; do sleep 60; done
echo "$(date +%T) both MC jobs done" >> $LOG
for f in logs_$R/Summer22/*.log; do
  case $f in *driver_*|*nohup*) continue ;; esac
  pre=$(grep -ao "Preprocessing 100%[^]]*" "$f" | tail -1 | grep -o "[0-9][0-9]*/[0-9][0-9]*" | head -1)
  echo "$R $(basename $f .log) files $pre" >> $LOG
done
grep -h "exit" logs_$R/Summer22/driver_mc.log | grep -v "exit 0" >> $LOG
for f in hists_$A/Summer22/zbzc_run3/zbzc_run3_{Muon,EGamma}_*.coffea; do
  ln -sf "$PWD/$f" hists_$R/Summer22/zbzc_run3/
done
cp hists_zbzc_run3_zpt/Summer22/lumi.json hists_$R/Summer22/lumi.json
echo "$(date +%T) postprocess done" >> $LOG
