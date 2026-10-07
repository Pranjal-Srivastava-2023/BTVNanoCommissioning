"""Build the Zb_Zc_ratio Summer22 DY->ll fileset from DAS.

The PTLL-X samples are inclusive above X; the workflow stitches them by LHE
pT(ll) slice and the inclusive MLL-50 sample covers pT(ll) < 100 (see STITCH in
workflows/Zb_Zc_ratio.py).

Writes metadata/Zb_Zc_ratio_Summer22_DY.json. Needs a VOMS proxy and
cmsset_default.sh (dasgoclient).

Usage:
    python3 make_zbzc_fileset.py
"""
import json
import subprocess

XROOTD = "root://cmsxrootd.fnal.gov//"
TAIL = "Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5"
DATASETS = [
    f"/DYto2L-2Jets_MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/{TAIL}-v5/NANOAODSIM",
    f"/DYto2L-2Jets_MLL-50_PTLL-100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/{TAIL}-v3/NANOAODSIM",
    f"/DYto2L-2Jets_MLL-50_PTLL-200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/{TAIL}-v2/NANOAODSIM",
    f"/DYto2L-2Jets_MLL-50_PTLL-400_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/{TAIL}-v2/NANOAODSIM",
    f"/DYto2L-2Jets_MLL-50_PTLL-600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/{TAIL}-v2/NANOAODSIM",
]

fileset = {}
for das in DATASETS:
    files = subprocess.run(
        ["dasgoclient", f"-query=file dataset={das}"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    fileset[das.split("/")[1]] = [XROOTD + f for f in sorted(files)]
    print(f"{len(files):5d} files  {das.split('/')[1]}")

out = "metadata/Zb_Zc_ratio_Summer22_DY.json"
with open(out, "w") as f:
    json.dump(fileset, f, indent=4)
print("wrote", out)
