"""Compare the MET / jet diagnostic runs (diag_zbzc_met.py) with the nominal stage run.

For every campaign with outputs in hists_zbzc_diag/<campaign>/: efficiency of the MET < 50 cut
and of the >= 1 jet cut for all Z events (before both cuts), data and DY MC, nominal
(hists_zbzc_run3_stage, same first 20 files) vs each variant; and the MET-cut efficiency in
bins of Z pT. Only datasets that have a diag output enter (both nominal and variant use the
same datasets). Data variants only exist for emef; nojer does not touch data, so its
comparison uses the nominal data on both sides.

Output: hists_zbzc_diag/diag_tables.txt (also printed)
"""
import glob
import json
import os

import numpy as np
from coffea.util import load

XS = json.load(open("metadata/Zb_Zc_ratio_xsections_run3.json"))
PT_EDGES = [0, 10, 20, 30, 50, 100, 200, 300, 1000]
MET_PASS = ["MET", "MET+jet"]
JET_PASS = ["jet", "MET+jet"]


def is_data(ds):
    return ds.startswith(("Muon", "EGamma"))


def zpt(o, ch, stages):
    h = o["stage_z_pt"][{"channel": ch, "flav": sum, "pflav": sum}]
    vals = sum(h[{"stage": s}].values() for s in stages)
    e = h.axes["pt"].edges if "pt" in h.axes.name else h.axes[-1].edges
    idx = [int(np.where(np.isclose(e, x))[0][0]) for x in PT_EDGES]
    return np.array([vals[a:b].sum() for a, b in zip(idx[:-1], idx[1:])])


def collect(files, c, ch):
    """(all Z, pass MET, pass jet) per Z pT bin, for data of channel ch and for DY MC."""
    lumi = json.load(open(f"hists_zbzc_run3/{c}/lumi.json"))
    res = {"data": np.zeros((3, len(PT_EDGES) - 1)), "DY": np.zeros((3, len(PT_EDGES) - 1))}
    for f in files:
        for ds, o in load(f).items():
            if is_data(ds):
                if not ds.startswith("Muon" if ch == "Zmm" else "EGamma"):
                    continue
                key, s = "data", 1.0
            elif ds.startswith("DYto2L"):
                key, s = "DY", XS[ds] * lumi[ch] / o["sumw"]
            else:
                continue
            all4 = ["none", "MET", "jet", "MET+jet"]
            res[key] += s * np.array([zpt(o, ch, all4), zpt(o, ch, MET_PASS), zpt(o, ch, JET_PASS)])
    return res


lines = []
for cdir in sorted(glob.glob("hists_zbzc_diag/*/")):
    c = os.path.basename(cdir.rstrip("/"))
    variants = sorted({os.path.basename(f).split("_")[1] for f in glob.glob(f"{cdir}diag_*.coffea")})
    for v in variants:
        vfiles = sorted(glob.glob(f"{cdir}diag_{v}_*.coffea"))
        dsets = [os.path.basename(f)[len(f"diag_{v}_"):-len(".coffea")] for f in vfiles]
        nfiles = [f"hists_zbzc_run3_stage/{c}/zbzc_run3/zbzc_run3_{d}.coffea" for d in dsets]
        if not any(is_data(d) for d in dsets):
            # MC-only variant (nojer): data unchanged, use the nominal data on both sides
            ndata = [f for f in glob.glob(f"hists_zbzc_run3_stage/{c}/zbzc_run3/zbzc_run3_*.coffea")
                     if is_data(os.path.basename(f)[len("zbzc_run3_"):])]
            nfiles, vfiles = nfiles + ndata, vfiles + ndata
        lines.append(f"\n=== {c}  variant {v}  ({len(dsets)} datasets: {', '.join(d.split('_TuneCP5')[0] for d in dsets)})")
        for ch in ["Zee", "Zmm"]:
            nom, var = collect(nfiles, c, ch), collect(vfiles, c, ch)
            lines.append(f"  {ch}: efficiency of the cut for all Z events (before MET and jet cuts)")
            lines.append("           MET<50 nom -> var         >=1 jet nom -> var")
            for k in ["data", "DY"]:
                if nom[k][0].sum() == 0 or var[k][0].sum() == 0:
                    continue
                n, w = nom[k].sum(axis=1), var[k].sum(axis=1)
                lines.append(f"    {k:5s} {n[1] / n[0]:.4f} -> {w[1] / w[0]:.4f}      {n[2] / n[0]:.4f} -> {w[2] / w[0]:.4f}")
            if all(nom[k][0].sum() > 0 for k in ["data", "DY"]):
                lines.append("    MET<50 efficiency per Z pT bin: data | DY nom -> var | data/DY nom -> var")
                for i, (a, b) in enumerate(zip(PT_EDGES[:-1], PT_EDGES[1:])):
                    d = nom["data"][1, i] / nom["data"][0, i] if nom["data"][0, i] else np.nan
                    dv = var["data"][1, i] / var["data"][0, i] if var["data"][0, i] else d
                    mn = nom["DY"][1, i] / nom["DY"][0, i] if nom["DY"][0, i] else np.nan
                    mv = var["DY"][1, i] / var["DY"][0, i] if var["DY"][0, i] else np.nan
                    lines.append(f"      {a:4g}-{b:<5g} {d:.3f}->{dv:.3f} | {mn:.3f} -> {mv:.3f} | {d / mn:.3f} -> {dv / mv:.3f}")

with open("hists_zbzc_diag/diag_tables.txt", "w") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines))
