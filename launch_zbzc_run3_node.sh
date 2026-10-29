#!/bin/bash
# Start one part (mc|data) of the Zb_Zc_ratio Run 3 small run for all four campaigns on THIS node,
# plus a stall watchdog for this node (it only sees local runner processes); with "post" also the
# postprocess waiter. Meant to be started over ssh, so it sets the grid proxy itself.
# usage: ssh -n <node> /path/launch_zbzc_run3_node.sh <mc|data> [post]
cd "$(dirname "$0")"
export X509_USER_PROXY=/uscms/home/psrivast/x509up_u10024  # not set in ssh shells
for c in Summer22 Summer22EE Summer23 Summer23BPix; do
  mkdir -p logs_zbzc_run3/$c
  setsid nohup ./run_zbzc_run3.sh $c $1 > logs_zbzc_run3/$c/nohup_$1.out 2>&1 < /dev/null &
done
setsid nohup ./stall_watchdog_zbzc_run3.sh > logs_zbzc_run3/stall_watchdog_$(hostname -s).log 2>&1 < /dev/null &
[ "$2" = post ] && setsid nohup ./postprocess_zbzc_run3.sh > logs_zbzc_run3/postprocess.log 2>&1 < /dev/null &
echo "$(date +%T) $(hostname -s) launched $1 $2"
