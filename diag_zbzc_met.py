"""MET / jet diagnostic for the Zb_Zc_ratio Run 3 slope study: rerun the workflow on a
few files with one change to the framework's jet/MET corrections, patched at run time
(utils/correction.py itself is not changed):

    nominal   as in the analysis
    emef      type-1 PuppiMET without jets of EM fraction >= 0.9 (the JME type-1
              recipe; correction.py applies this cut only for NanoAODv15, so for v12
              the electrons' own jets enter the type-1 sum)
    nojer     MC jets and type-1 MET without JER smearing (data unchanged)

Usage: python diag_zbzc_met.py <variant> <campaign> <dataset> <nfiles> <outdir> [first_file]
Reads the files of <dataset> from metadata/Zb_Zc_ratio_run3_<campaign>.json and writes
<outdir>/diag_<variant>_<dataset>.coffea (same histograms as the workflow).
"""
import json
import os
import sys

import awkward as ak
from coffea import processor
from coffea.nanoevents import PFNanoAODSchema
from coffea.util import save

import BTVNanoCommissioning.utils.correction as correction
from BTVNanoCommissioning.workflows import workflows

variant, camp, ds, nfiles, outdir = sys.argv[1:6]
first = int(sys.argv[6]) if len(sys.argv) > 6 else 0
year = "2022" if camp.startswith("Summer22") else "2023"

if variant == "emef":
    _calc = correction.calc_T1_MET

    def calc_T1_MET(met_raw, met_nano, jets, campaign, systematic=False):
        # the NanoAODv15 branch of the jet mask is the one with EmEF < 0.9
        return _calc(met_raw, met_nano, jets, "Summer24", systematic)

    correction.calc_T1_MET = calc_T1_MET
elif variant == "nojer":
    _get_jer = correction.get_JER

    def get_JER(*args, **kwargs):
        return ak.ones_like(_get_jer(*args, **kwargs))

    correction.get_JER = get_JER
elif variant != "nominal":
    raise KeyError(variant)

files = json.load(open(f"metadata/Zb_Zc_ratio_run3_{camp}.json"))[ds][first:first + int(nfiles)]
# no Z pT weights: compared with the unweighted hists_zbzc_run3_stage run
proc = workflows["Zb_Zc_ratio"](year, camp, outdir, False, False, False, 200000, zpt_reweight=False)  # isSyst must be a real False: "False" runs all 35 shifts into the same histograms
out = processor.run_uproot_job(
    {ds: files}, treename="Events", processor_instance=proc,
    executor=processor.iterative_executor,
    executor_args={"schema": PFNanoAODSchema, "xrootdtimeout": 900},
    chunksize=200000,
)
os.makedirs(outdir, exist_ok=True)
save(out, f"{outdir}/diag_{variant}_{ds}.coffea")
print("DIAG DONE", variant, camp, ds, len(files))
