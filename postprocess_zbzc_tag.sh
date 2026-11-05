#!/bin/bash
# Summer22 b/c-tagged kinematics (2026-11-05): waits for
#   ZBZC_RUN=zbzc_run3_tag run_zbzc_run3.sh Summer22 mc|data
# (Zb_Zc_ratio with MET filters, PNet L/M/T tag regions + BTV SFs, no Z pT weights), then makes the
# stack plots + yields for the inclusive and the b- and c-tagged (L, M, T) leading jet.
# Writes "postprocess done" (stall_watchdog with ZBZC_RUN=zbzc_run3_tag exits).
# usage: nohup setsid ./postprocess_zbzc_tag.sh > logs_zbzc_run3_tag/postprocess.log 2>&1 &
cd "$(dirname "$0")"
for p in mc data; do
  until grep -q 'ALL DONE' logs_zbzc_run3_tag/Summer22/driver_$p.log 2>/dev/null; do sleep 120; done
done
echo "$(date +%T) runs done"
grep -H exit logs_zbzc_run3_tag/Summer22/driver_*.log | grep -v 'exit 0' && echo "WARNING: failed tries above"
source /uscms_data/d3/psrivast/micromamba/bin/activate zbb-btv
for t in incl btag_L ctag_L btag_M ctag_M btag_T ctag_T; do
  ZBZC_RUN=zbzc_run3_tag ZBZC_TAG=$t python plot_zbzc_run3.py Summer22 > /dev/null || echo "plot $t FAILED"
done
echo "$(date +%T) postprocess done"
