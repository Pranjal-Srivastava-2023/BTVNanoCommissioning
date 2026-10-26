"""Integrated luminosity of the data actually processed by the Zb_Zc_ratio Run 3 run.

For each data output in hists_zbzc_run3/<campaign>/zbzc_run3/ the golden-JSON lumisections the
workflow saw (dump_lumi: "run", "lumi") are written to a brilcalc JSON and run
through brilcalc (normtag_PHYSICS, the framework's choice for 2022/2023) inside the
BRIL Apptainer image. 2023 data use only the "0" half of the split PDs
(Muon0, EGamma0), which hold ~50% of the events of every lumisection, so their
lumi is scaled by 0.5. Muon PD -> Zmm, EGamma PD -> Zee; the two channels see
different lumisections, so MC is normalized per channel.

A lumisection split across a processed and an unprocessed file would be counted in
full; checked in DAS for three 2022F lumisections, each sits in a single file.

Writes hists_zbzc_run3/<campaign>/lumi.json: {"Zee": pb, "Zmm": pb, "datasets": {...}}.

Usage:
    python zbzc_lumi.py [campaign ...]
"""
import glob
import json
import os
import subprocess
import sys

import numpy as np
from coffea.util import load

IMG = "/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/cms-cloud/brilws-docker:latest"
NORMTAG = "/cvmfs/cms-bril.cern.ch/cms-lumi-pog/Normtags/normtag_PHYSICS.json"
CAMPAIGNS = ["Summer22", "Summer22EE", "Summer23", "Summer23BPix"]


def channel(ds):
    return "Zmm" if ds.startswith("Muon") else "Zee" if ds.startswith("EGamma") else None


def brilcalc(pairs, fname):
    """Recorded lumi [/pb] of the (run, ls) pairs."""
    runs = {}
    for r, ls in pairs:
        runs.setdefault(str(r), []).append(int(ls))
    compact = {}
    for r, lss in runs.items():
        lss = sorted(set(lss))
        ranges = [[lss[0], lss[0]]]
        for ls in lss[1:]:
            if ls == ranges[-1][1] + 1:
                ranges[-1][1] = ls
            else:
                ranges.append([ls, ls])
        compact[r] = ranges
    with open(fname, "w") as f:
        json.dump(compact, f)
    env = dict(os.environ, APPTAINER_BINDPATH="/cvmfs,/uscms_data,/uscms/home")
    res = subprocess.run(
        ["apptainer", "-s", "exec", "--env",
         "PYTHONPATH=/home/bril/.local/lib/python3.10/site-packages", IMG,
         "brilcalc", "lumi", "--normtag", NORMTAG, "-c", "web", "-u", "/pb",
         "-i", os.path.abspath(fname)],
        capture_output=True, text=True, env=env,
    ).stdout
    summary = res[res.find("#Summary:"):]
    # columns: nfill | nrun | nls | ncms | totdelivered | totrecorded
    return float(summary.split("\n")[4].split("|")[-2])


for camp in sys.argv[1:] or CAMPAIGNS:
    d = f"hists_zbzc_run3/{camp}"
    result = {"Zee": 0.0, "Zmm": 0.0, "datasets": {}}
    for f in sorted(glob.glob(f"{d}/zbzc_run3/zbzc_run3_*.coffea")):
        for ds, o in load(f).items():
            ch = channel(ds)
            if ch is None:
                continue
            pairs = np.unique(np.stack([o["run"].value, o["lumi"].value], axis=1), axis=0)
            lumi = brilcalc(pairs, f"{d}/lumi_{ds}.json")
            frac = 0.5 if ds.split("_")[0].endswith("0") else 1.0
            result["datasets"][ds] = {"nls": len(pairs), "brilcalc_pb": lumi, "factor": frac}
            result[ch] += lumi * frac
            print(f"{camp:13s} {ds:20s} {len(pairs):6d} LS  {lumi:9.2f} /pb  x{frac}")
    print(f"{camp:13s} Zee {result['Zee']:.2f} /pb   Zmm {result['Zmm']:.2f} /pb")
    with open(f"{d}/lumi.json", "w") as f:
        json.dump(result, f, indent=2)
