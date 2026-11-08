#!/bin/bash
# Summer22 run of 2026-11-08 (advisor's requests): waits for
#   ZBZC_RUN=zbzc_run3_v2 run_zbzc_run3.sh Summer22 mc|data
# (Zb_Zc_ratio with: Zmm trigger SF from both muons (MUO data/MC efficiencies) and muon pT > 26;
# PNet + DeepJet + RobustParT L/M/T tag regions with their own BTV SFs; met_pt_nm1 (no MET cut);
# pu_ntrue_npv; muvar_* muon-selection variants), then makes the stack plots (+ zoomed plots) and
# yields for the inclusive and all 18 tagged regions.
# Writes "postprocess done" (stall_watchdog with ZBZC_RUN=zbzc_run3_v2 exits).
# usage: setsid nohup ./postprocess_zbzc_v2.sh > logs_zbzc_run3_v2/postprocess.log 2>&1 &
cd "$(dirname "$0")"
RUN=zbzc_run3_v2
for p in mc data; do
  until grep -q 'ALL DONE' logs_$RUN/Summer22/driver_$p.log 2>/dev/null; do sleep 120; done
done
echo "$(date +%T) runs done"
grep -H exit logs_$RUN/Summer22/driver_*.log | grep -v 'exit 0' && echo "WARNING: failed tries above"
source /uscms_data/d3/psrivast/micromamba/bin/activate zbb-btv
for tg in "" DeepJet RobustParT; do
  for wp in L M T; do
    for k in btag ctag; do
      t=${k}${tg}_$wp
      ZBZC_RUN=$RUN ZBZC_TAG=$t python plot_zbzc_run3.py Summer22 > /dev/null || echo "plot $t FAILED"
    done
  done
done
ZBZC_RUN=$RUN ZBZC_TAG=incl python plot_zbzc_run3.py Summer22 > /dev/null || echo "plot incl FAILED"
echo "$(date +%T) postprocess done"
