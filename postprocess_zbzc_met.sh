#!/bin/bash
# MET study 2026-11-16: wait for the runs zbzc_run3_metxy (mc + data) and zbzc_run3_metxy_nojer (mc), check that every
# log read N/N files, link run A's data outputs into run B (data have no JER smearing), copy lumi.json (same data files
# as the zpt run), make the stack plots of both runs (ZBZC_MET=1) and the A-vs-B comparison. Writes
# "postprocess done" to logs_zbzc_run3_metxy/postprocess.log at the end (stops the stall watchdog).
cd "$(dirname "$0")"
LOG=logs_zbzc_run3_metxy/postprocess.log
A=zbzc_run3_metxy; B=zbzc_run3_metxy_nojer
until grep -q "ALL DONE" logs_$A/Summer22/driver_mc.log 2>/dev/null && grep -q "ALL DONE" logs_$A/Summer22/driver_data.log 2>/dev/null \
      && grep -q "ALL DONE" logs_$B/Summer22/driver_mc.log 2>/dev/null; do sleep 60; done
echo "$(date +%T) all drivers done" >> $LOG
for r in $A $B; do
  for f in logs_$r/Summer22/*.log; do
    case $f in *driver_*|*nohup*) continue ;; esac
    pre=$(grep -ao "Preprocessing 100%[^]]*" "$f" | tail -1 | grep -o "[0-9]*/[0-9]*")
    echo "$r $(basename $f .log) files $pre" >> $LOG
  done
done
grep -h "exit" logs_$A/Summer22/driver_*.log logs_$B/Summer22/driver_mc.log | grep -v "exit 0" >> $LOG
source /uscms_data/d3/psrivast/micromamba/bin/activate zbb-btv
for f in hists_$A/Summer22/zbzc_run3/zbzc_run3_{Muon,EGamma}_*.coffea; do
  ln -sf "$PWD/$f" hists_$B/Summer22/zbzc_run3/
done
cp hists_zbzc_run3_zpt/Summer22/lumi.json hists_$A/Summer22/lumi.json
cp hists_zbzc_run3_zpt/Summer22/lumi.json hists_$B/Summer22/lumi.json
for r in $A $B; do
  ZBZC_RUN=$r ZBZC_MET=1 python plot_zbzc_run3.py Summer22 > logs_$A/plot_$r.log 2>&1
  echo "$(date +%T) plots $r exit $?" >> $LOG
done
python plot_zbzc_met_compare.py > logs_$A/met_compare.log 2>&1
echo "$(date +%T) compare exit $?" >> $LOG
echo "$(date +%T) postprocess done" >> $LOG
