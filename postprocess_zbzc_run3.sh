#!/bin/bash
# Wait for the twelve jobs (4 campaigns x mc/data/vv) to finish, then
# make the lumi, plots, tables and a draft deck (summary page left to be written).
# usage: nohup setsid ./postprocess_zbzc_run3.sh > logs_zbzc_run3/postprocess.log 2>&1 &
cd "$(dirname "$0")"
until [ "$(cat logs_zbzc_run3/*/driver_*.log | grep -c 'ALL DONE')" -eq 12 ]; do sleep 120; done
echo "$(date +%T) all jobs done"
grep -H exit logs_zbzc_run3/*/driver_*.log | grep -v 'exit 0' && echo "WARNING: failed tries above"
source /uscms_data/d3/psrivast/micromamba/bin/activate zbb-btv
python zbzc_lumi.py || exit 1
for c in Summer22 Summer22EE Summer23 Summer23BPix all; do
  echo "$(date +%T) plots $c"
  python plot_zbzc_run3.py $c > /dev/null || echo "plot $c FAILED"
done
python make_zbzc_run3_slides_pdf.py all
echo "$(date +%T) postprocess done"
