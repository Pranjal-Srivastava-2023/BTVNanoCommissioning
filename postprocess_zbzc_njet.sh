#!/bin/bash
# Summer22 Z + 1 jet check: waits for the two reruns (10 GeV pT bins)
#   ZBZC_RUN=zbzc_run3_ge1j                          run_zbzc_run3.sh Summer22 mc|data  (N_jet >= 1)
#   ZBZC_RUN=zbzc_run3_1j ZBZC_WF=Zb_Zc_ratio_1jet   run_zbzc_run3.sh Summer22 mc|data  (N_jet = 1)
# then makes the usual stack plots + yields for both, the eta-phi maps split by N jets and the
# ge1j-vs-1j slope comparison. Writes "postprocess done" (stall_watchdog with ZBZC_RUN=zbzc_run3_1j exits).
cd "$(dirname "$0")"
for r in ge1j 1j; do for p in mc data; do
  until grep -q 'ALL DONE' logs_zbzc_run3_$r/Summer22/driver_$p.log 2>/dev/null; do sleep 120; done
done; done
echo "$(date +%T) runs done"
source /uscms_data/d3/psrivast/micromamba/bin/activate zbb-btv
for r in ge1j 1j; do ZBZC_RUN=zbzc_run3_$r python plot_zbzc_run3.py Summer22; done
python plot_zbzc_etaphi_nj.py Summer22 hists_zbzc_run3_ge1j
python compare_zbzc_njet_slope.py Summer22
echo "$(date +%T) postprocess done"
