#!/bin/bash
# Kill Zb_Zc_ratio runner processes that stall on xrootd reads (CPU time grows by
# < 5 s over two 5-minute checks); the run_zbzc_run3*.sh drivers then retry them.
# Stops once postprocess_zbzc_run3.sh has finished (logs_$ZBZC_RUN/postprocess.log).
cd "$(dirname "$0")"
RUN=${ZBZC_RUN:-zbzc_run3}
declare -A last stuck
while ! grep -q 'postprocess done' logs_$RUN/postprocess.log 2>/dev/null; do
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
      echo "$(date +%T) killing stalled pid $pid: $(tr '\0' ' ' < /proc/$pid/cmdline | grep -o 'run3_[A-Za-z0-9]*.json --year [0-9]* --campaign [A-Za-z0-9]* .*--only [^ ]*' | sed 's/ --year.*--only / /')"
      kill $pid
    fi
  done
  sleep 300
done
echo "$(date +%T) postprocess done, watchdog exits"
