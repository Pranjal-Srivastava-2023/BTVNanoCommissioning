#!/bin/bash
# Wait for the eight jobs (4 campaigns x mc/data; VV inside mc since 2026-10-28) to finish, then
# make the lumi, plots, tables and a draft deck per campaign (summary page left to be
# written). Campaigns are kept separate: no combined 2022+2023 output (user, 2026-10-26).
# usage: nohup setsid ./postprocess_zbzc_run3.sh > logs_zbzc_run3/postprocess.log 2>&1 &
cd "$(dirname "$0")"
until [ "$(cat logs_zbzc_run3/*/driver_*.log | grep -c 'ALL DONE')" -eq 8 ] && ! grep -L 'RERUN DONE' logs_zbzc_run3/*/rerun_*.log 2>/dev/null | grep -q .; do sleep 120; done
echo "$(date +%T) all jobs done"
grep -H exit logs_zbzc_run3/*/driver_*.log | grep -v 'exit 0' && echo "WARNING: failed tries above"
source /uscms_data/d3/psrivast/micromamba/bin/activate zbb-btv
python zbzc_lumi.py || exit 1
for c in Summer22 Summer22EE Summer23 Summer23BPix; do
  echo "$(date +%T) plots $c"
  python plot_zbzc_run3.py $c > /dev/null || echo "plot $c FAILED"
done
for c in Summer22 Summer22EE Summer23 Summer23BPix; do
  python make_zbzc_run3_slides_pdf.py $c || echo "deck $c FAILED"
done
echo "$(date +%T) postprocess done"
