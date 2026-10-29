#!/bin/bash
# Slope-study run (ZBZC_RUN=zbzc_run3_stage, same 20 files as hists_zbzc_run3/): wait for
# the eight run_zbzc_run3.sh jobs, check that the analysis histograms are identical to the
# previous run, then make the stage plots and tables per campaign (plot_zbzc_stage.py).
# usage: nohup setsid ./postprocess_zbzc_stage.sh > logs_zbzc_run3_stage/postprocess.log 2>&1 &
cd "$(dirname "$0")"
L=logs_zbzc_run3_stage
until [ "$(cat $L/*/driver_*.log | grep -c 'ALL DONE')" -eq 8 ] && ! grep -L 'RERUN DONE' $L/*/rerun_*.log 2>/dev/null | grep -q .; do sleep 120; done
echo "$(date +%T) all jobs done"
grep -H exit $L/*/driver_*.log | grep -v 'exit 0' && echo "WARNING: failed tries above"
source /uscms_data/d3/psrivast/micromamba/bin/activate zbb-btv
python - <<'PY'
import glob, os
import numpy as np
from coffea.util import load
for c in ["Summer22", "Summer22EE", "Summer23", "Summer23BPix"]:
    bad = []
    for f in sorted(glob.glob(f"hists_zbzc_run3/{c}/zbzc_run3/*.coffea")):
        g = f.replace("hists_zbzc_run3/", "hists_zbzc_run3_stage/")
        if not os.path.exists(g):
            bad.append(f"missing {os.path.basename(g)}"); continue
        a, b = load(f), load(g)
        for ds in a:
            for v in ("z_pt", "z_mass", "n_jet", "lep0_pt"):
                if not np.allclose(a[ds][v].values(), b[ds][v].values(), rtol=1e-6):
                    bad.append(f"{ds} {v} differs")
    print(c, "same as hists_zbzc_run3" if not bad else bad)
PY
for c in Summer22 Summer22EE Summer23 Summer23BPix; do
  echo "$(date +%T) stage plots $c"
  python plot_zbzc_stage.py $c > /dev/null || echo "stage plot $c FAILED"
done
echo "$(date +%T) postprocess done"
