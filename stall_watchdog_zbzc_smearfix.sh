#!/bin/bash
# Stall watchdog for run_zbzc_run3_smearfix.sh (same rule as stall_watchdog_zbzc_run3.sh:
# kill a runner whose CPU time grows by < 5 s over two 5-minute checks; the driver retries).
cd "$(dirname "$0")"
declare -A last stuck
while [ $(grep -l 'ALL DONE' logs_zbzc_run3_smearfix/*/driver.log 2>/dev/null | wc -l) -lt 4 ]; do
  for pid in $(pgrep -f '^python runner.py --wf Zb_Zc_ratio'); do
    t=$(ps -o time= -p $pid | awk -F: '{print $1*3600 + $2*60 + $3}')
    [ -z "$t" ] && continue
    if [ -n "${last[$pid]}" ] && [ $((t - ${last[$pid]})) -lt 5 ]; then
      stuck[$pid]=$((${stuck[$pid]:-0} + 1))
    else
      stuck[$pid]=0
    fi
    last[$pid]=$t
    if [ "${stuck[$pid]}" -ge 2 ]; then
      echo "$(date +%T) killing stalled pid $pid: $(tr '\0' ' ' < /proc/$pid/cmdline | grep -o -- '--campaign [A-Za-z0-9]* .*--only [^ ]*')"
      kill $pid
    fi
  done
  sleep 300
done
echo "$(date +%T) all drivers done, watchdog exits"
