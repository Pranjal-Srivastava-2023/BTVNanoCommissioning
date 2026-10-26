#!/bin/bash
# Stop each campaign's "run_zbzc_run3.sh <c> mc" job when it reaches WW (WW/WZ/ZZ
# run in run_zbzc_run3_vv.sh instead) and mark its log ALL DONE.
cd "$(dirname "$0")"
left="Summer22 Summer22EE Summer23 Summer23BPix"
while [ -n "$left" ]; do
  still=""
  for c in $left; do
    log=logs_zbzc_run3/$c/driver_mc.log
    if tail -1 $log | grep -q 'WW_TuneCP5.* try'; then
      pid=$(ps -eo pid,args | awk -v c="$c" '$0 ~ "run_zbzc_run3.sh "c" mc$" {print $1}')
      if [ -n "$pid" ]; then
        # timeout runs the runner in its own process group: note it, stop the
        # driver first (so it cannot start a retry), then the runner's group
        kids=$(ps -eo pid,ppid,args | awk -v d="$pid" '$2 == d && /timeout/ {print $1}')
        kill -- -"$(ps -o pgid= -p $pid | tr -d ' ')"
        for k in $kids; do kill -- -"$(ps -o pgid= -p $k | tr -d ' ')"; done
      fi
      echo "$(date +%T) stopped before WW (WW/WZ/ZZ in driver_vv.log)" >> $log
      echo "$(date +%T) ALL DONE" >> $log
      echo "$(date +%T) $c mc stopped at WW (pid $pid)"
    elif tail -1 $log | grep -q 'ALL DONE'; then
      :
    else
      still="$still $c"
    fi
  done
  left=$still
  sleep 15
done
