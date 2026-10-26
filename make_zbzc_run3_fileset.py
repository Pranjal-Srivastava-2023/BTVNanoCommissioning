"""Build the Zb_Zc_ratio Run 3 filesets (MC + data) from DAS, one per campaign.

MC (all files listed; run with --limit 20): DY->ll amcatnloFXFX inclusive MLL-50 +
PTLL-100/200/400/600 (stitched in the workflow), TTto2L2Nu, WW, WZ, ZZ. The plain
130X production is used (no JMENano, no ext).

Data (22Sep2023 NanoAODv12): NFILES_DATA files per channel per campaign, split
over the campaign's run eras in proportion to their file counts and spread evenly
through each era's sorted file list. One key per PD and era ("Muon_Run2022C"),
since the workflow matches the data JEC era from the dataset name.
2023 data come in two halves (Muon0/Muon1, EGamma0/EGamma1) that split the
events of every lumisection about 50/50; only the "0" half is used, so its
brilcalc lumi must be scaled by 0.5 (done in zbzc_lumi.py).

Writes metadata/Zb_Zc_ratio_run3_<campaign>.json. Needs a VOMS proxy.

Usage:
    python3 make_zbzc_run3_fileset.py [campaign ...]
"""
import json
import subprocess
import sys

DAS = "/cvmfs/cms.cern.ch/common/dasgoclient"
XROOTD = "root://cmsxrootd.fnal.gov//"
NFILES_DATA = 20

MC_TIER = {
    "Summer22": "Run3Summer22NanoAODv12",
    "Summer22EE": "Run3Summer22EENanoAODv12",
    "Summer23": "Run3Summer23NanoAODv12",
    "Summer23BPix": "Run3Summer23BPixNanoAODv12",
}
MC_SAMPLES = [
    "DYto2L-2Jets_MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8",
    "DYto2L-2Jets_MLL-50_PTLL-100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8",
    "DYto2L-2Jets_MLL-50_PTLL-200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8",
    "DYto2L-2Jets_MLL-50_PTLL-400_TuneCP5_13p6TeV_amcatnloFXFX-pythia8",
    "DYto2L-2Jets_MLL-50_PTLL-600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8",
    "TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8",
    "WW_TuneCP5_13p6TeV_pythia8",
    "WZ_TuneCP5_13p6TeV_pythia8",
    "ZZ_TuneCP5_13p6TeV_pythia8",
]
# campaign -> channel PD -> run eras (all 22Sep2023 versions of an era are merged)
DATA = {
    "Summer22": {"Muon": ["Run2022C", "Run2022D"], "EGamma": ["Run2022C", "Run2022D"]},
    "Summer22EE": {
        "Muon": ["Run2022E", "Run2022F", "Run2022G"],
        "EGamma": ["Run2022E", "Run2022F", "Run2022G"],
    },
    "Summer23": {"Muon0": ["Run2023C"], "EGamma0": ["Run2023C"]},
    "Summer23BPix": {"Muon0": ["Run2023D"], "EGamma0": ["Run2023D"]},
}


def das(query):
    return subprocess.run(
        [DAS, f"-query={query}"], capture_output=True, text=True, check=True
    ).stdout.split()


def spread(files, n):
    """n files evenly spaced through the sorted list (all of them if n >= len)."""
    files = sorted(files)
    if n >= len(files):
        return files
    return [files[int(i * len(files) / n)] for i in range(n)]


def build(campaign):
    fileset = {}
    for sample in MC_SAMPLES:
        dsets = [
            d
            for d in das(f"dataset=/{sample}/{MC_TIER[campaign]}*/NANOAODSIM")
            if "JMENano" not in d and "_ext" not in d
        ]
        if len(dsets) != 1:
            sys.exit(f"{campaign} {sample}: expected one dataset, got {dsets}")
        files = das(f"file dataset={dsets[0]}")
        fileset[sample] = [XROOTD + f for f in sorted(files)]
        print(f"{campaign:13s} {len(files):5d} files  {dsets[0]}")

    for pd, eras in DATA[campaign].items():
        per_era = {}
        for era in eras:
            dsets = das(f"dataset=/{pd}/{era}-22Sep2023*/NANOAOD")
            per_era[era] = sorted(f for d in dsets for f in das(f"file dataset={d}"))
            print(f"{campaign:13s} {len(per_era[era]):5d} files  /{pd}/{era} ({len(dsets)} datasets)")
        ntot = sum(len(f) for f in per_era.values())
        for era, files in per_era.items():
            n = max(1, round(NFILES_DATA * len(files) / ntot))
            fileset[f"{pd}_{era}"] = [XROOTD + f for f in spread(files, n)]
            print(f"{'':13s} -> {n} files for {pd}_{era}")

    out = f"metadata/Zb_Zc_ratio_run3_{campaign}.json"
    with open(out, "w") as f:
        json.dump(fileset, f, indent=4)
    print("wrote", out)


for c in sys.argv[1:] or list(MC_TIER):
    build(c)
