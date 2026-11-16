#!/bin/bash
# Start one detached Summer22 Zb_Zc_ratio job on THIS node (also over ssh: sets the proxy itself).
# usage: launch_zbzc_job.sh <run name> <workflow> <mc|data> [dataset prefixes, e.g. "Muon"]
# output hists_<run>/Summer22/, logs logs_<run>/Summer22/
cd "$(dirname "$0")"
export X509_USER_PROXY=/uscms/home/psrivast/x509up_u10024
mkdir -p logs_$1/Summer22
ZBZC_RUN=$1 ZBZC_WF=$2 ZBZC_DSETS="$4" ZBZC_JSON=logs_zbzc_run3_v2/Zb_Zc_ratio_run3_Summer22_dyredir.json \
  setsid nohup ./run_zbzc_run3.sh Summer22 $3 > logs_$1/Summer22/nohup_$3.out 2>&1 < /dev/null &
echo "$(date +%T) $(hostname -s) launched $1 $2 $3 $4"
