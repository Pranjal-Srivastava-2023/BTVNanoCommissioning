"""Cutflow and yield tables of one Zb_Zc_ratio Run 3 run, and the comparison of two runs
(e.g. nominal vs MC without JER smearing). Numbers only; the decks read the JSON.

Per run and channel (Zee, Zmm):
  cutflow   raw data events and MC sum(genWeight) x xsec x lumi / sumw (no SFs) after each
            pre-selection and selection step (output["cutflow"/"cutflow_raw"]), split
            into DY / tt / VV; data/MC and the step efficiency (pass / previous step)
  stages    yields with ALL weights (SFs, PU, trigger) from stage_z_pt: Z events before the
            MET and jet cuts, then passing MET < 50, the jet cut, and both (= final)
  tags      final yields with all weights per PNet tag region (z_pt, tag axis)
Columns DY-b / DY-c / DY-l (hadronFlavour of the leading selected jet; "l" also holds
DY events without a selected jet), tt, VV, MC, data, data/MC with stat. errors.

Usage: python make_zbzc_yields.py <run dir> [<reference run dir>]
  writes <run dir>/yields/yields.{txt,json}; with a reference also
  <run dir>/yields/compare_<reference run>.{txt,json} (this run vs reference, per row)
"""
import glob
import json
import os
import sys

import numpy as np
from coffea.util import load

XS = json.load(open("metadata/Zb_Zc_ratio_xsections_run3.json"))
CHANNELS = ["Zee", "Zmm"]
COLS = ["DY-b", "DY-c", "DY-l", "tt", "VV"]
STAGE_ROWS = {
    "Z events": ["none", "MET", "jet", "MET+jet"],
    "MET < 50": ["MET", "MET+jet"],
    ">= 1 jet": ["jet", "MET+jet"],
    "final (MET < 50 + jet)": ["MET+jet"],
}
TAGS = ["incl", "btag_L", "btag_M", "btag_T", "ctag_L", "ctag_M", "ctag_T"]


def kind(ds):
    if ds.startswith("DYto2L"):
        return "DY"
    if ds.startswith("TTto2L2Nu"):
        return "tt"
    if ds.split("_")[0] in ("WW", "WZ", "ZZ"):
        return "VV"
    return "data_Zmm" if ds.startswith("Muon") else "data_Zee"


def run_name(rundir):
    return os.path.basename(os.path.dirname(os.path.normpath(rundir))).replace("hists_", "")


def load_run(rundir):
    out = {}
    for f in sorted(glob.glob(f"{rundir}/zbzc_run3/zbzc_run3_*.coffea")):
        out.update(load(f))
    lumi_file = os.path.join(rundir, "lumi.json")
    lumis = json.load(open(lumi_file))
    return out, lumis


def ratio(d, m, dv, mv):
    r = d / m if m else float("nan")
    e = r * np.sqrt(dv / d**2 + mv / m**2) if d > 0 and m > 0 else float("nan")
    return r, e


def summarise(out, lumis):
    res = {}
    for ch in CHANNELS:
        steps = list(next(iter(out.values()))["cutflow_raw"][ch].keys())
        cf = {k: np.zeros(len(steps)) for k in ("DY", "tt", "VV", "data")}
        for ds, o in out.items():
            k = kind(ds)
            if k in ("DY", "tt", "VV"):
                cf[k] += np.array([o["cutflow"][ch][s] for s in steps]) * XS[ds] * lumis[ch] / o["sumw"]
            elif k == f"data_{ch}":
                cf["data"] += np.array([o["cutflow_raw"][ch][s] for s in steps], dtype=float)
        mc = cf["DY"] + cf["tt"] + cf["VV"]
        cutflow = []
        for i, s in enumerate(steps):
            row = {"step": s, **{k: float(v[i]) for k, v in cf.items()}, "MC": float(mc[i])}
            row["data/MC"] = float(cf["data"][i] / mc[i]) if mc[i] else float("nan")
            if i:
                row["eff_data"] = float(cf["data"][i] / cf["data"][i - 1]) if cf["data"][i - 1] else float("nan")
                row["eff_MC"] = float(mc[i] / mc[i - 1]) if mc[i - 1] else float("nan")
            cutflow.append(row)

        def yields(hname, sel):
            y = {c: [0.0, 0.0] for c in COLS + ["data"]}
            for ds, o in out.items():
                k = kind(ds)
                if k.startswith("data") and k != f"data_{ch}":
                    continue
                h = o[hname][{"channel": ch, **sel}]
                if k == "DY":
                    for fl in ("b", "c", "l"):
                        hh = h[{"flav": fl, "pflav": sum}]
                        sc = XS[ds] * lumis[ch] / o["sumw"]
                        val = hh.values(flow=True).sum(); var = hh.variances(flow=True).sum()
                        y[f"DY-{fl}"][0] += val * sc
                        y[f"DY-{fl}"][1] += var * sc**2
                    continue
                hh = h[{"flav": sum, "pflav": sum}]
                val = hh.values(flow=True).sum(); var = hh.variances(flow=True).sum()
                if k in ("tt", "VV"):
                    sc = XS[ds] * lumis[ch] / o["sumw"]
                    y[k][0] += val * sc
                    y[k][1] += var * sc**2
                else:
                    y["data"][0] += val
                    y["data"][1] += var
            mcv = sum(y[c][0] for c in COLS)
            mcvar = sum(y[c][1] for c in COLS)
            r, e = ratio(y["data"][0], mcv, y["data"][1], mcvar)
            return {**{c: y[c][0] for c in COLS}, "MC": mcv, "MC_err": float(np.sqrt(mcvar)),
                    "data": y["data"][0], "data/MC": r, "data/MC_err": e}

        stages = {}
        for row, sts in STAGE_ROWS.items():
            stages[row] = yields("stage_z_pt", {"stage": sts})
        tags = {t: yields("z_pt", {"tag": t}) for t in TAGS}
        res[ch] = {"cutflow": cutflow, "stages": stages, "tags": tags}
    return res


def fmt_yield_table(L, title, rows):
    L.append(f"-- {title} (all weights)")
    L.append(f"{'':26s}" + "".join(f"{c:>10s}" for c in COLS) + f"{'MC':>11s}{'data':>10s}{'data/MC':>16s}")
    for name, y in rows.items():
        L.append(f"{name:26s}" + "".join(f"{y[c]:10.0f}" for c in COLS)
                 + f"{y['MC']:11.0f}{y['data']:10.0f}   {y['data/MC']:.3f} +- {y['data/MC_err']:.3f}")


def write_run(rundir, res):
    L = [f"Run {run_name(rundir)} ({rundir}): cutflow and yields", ""]
    for ch in CHANNELS:
        L.append(f"== {ch}: cutflow, raw data events vs MC sum(genWeight) x xsec x lumi / sumw (no SFs)")
        L.append("   data PDs are trigger-selected: data/MC means something from 'trigger' on")
        L.append(f"{'step':12s}{'DY':>12s}{'tt':>10s}{'VV':>9s}{'MC':>12s}{'data':>12s}{'data/MC':>9s}{'eff MC':>8s}{'eff data':>9s}")
        for r in res[ch]["cutflow"]:
            L.append(f"{r['step']:12s}{r['DY']:12.0f}{r['tt']:10.0f}{r['VV']:9.0f}{r['MC']:12.0f}{r['data']:12.0f}"
                     f"{r['data/MC']:9.3f}" + (f"{r['eff_MC']:8.3f}{r['eff_data']:9.3f}" if "eff_MC" in r else ""))
        fmt_yield_table(L, f"{ch}: Z events by stage", res[ch]["stages"])
        fmt_yield_table(L, f"{ch}: final selection per PNet tag region", res[ch]["tags"])
        L.append("")
    os.makedirs(f"{rundir}/yields", exist_ok=True)
    open(f"{rundir}/yields/yields.txt", "w").write("\n".join(L) + "\n")
    json.dump(res, open(f"{rundir}/yields/yields.json", "w"), indent=1)
    print("\n".join(L))


def write_compare(rundir, refdir, res, ref):
    a, b = run_name(rundir), run_name(refdir)
    L = [f"{a} vs {b}: MC, data and data/MC per row; 'MC ratio' = MC({a}) / MC({b})", ""]
    cmp = {}
    for ch in CHANNELS:
        cmp[ch] = {"cutflow": [], "stages": {}, "tags": {}}
        L.append(f"== {ch}: cutflow (no SFs)")
        L.append(f"{'step':12s}{'MC ' + b:>16s}{'MC ' + a:>16s}{'MC ratio':>10s}{'data ' + b:>14s}{'data ' + a:>14s}"
                 f"{'d/MC ' + b:>12s}{'d/MC ' + a:>12s}")
        for r0, r1 in zip(ref[ch]["cutflow"], res[ch]["cutflow"]):
            row = {"step": r1["step"], "MC_ref": r0["MC"], "MC": r1["MC"], "MC_ratio": r1["MC"] / r0["MC"],
                   "data_ref": r0["data"], "data": r1["data"], "dmc_ref": r0["data/MC"], "dmc": r1["data/MC"]}
            cmp[ch]["cutflow"].append(row)
            L.append(f"{row['step']:12s}{row['MC_ref']:16.0f}{row['MC']:16.0f}{row['MC_ratio']:10.4f}{row['data_ref']:14.0f}"
                     f"{row['data']:14.0f}{row['dmc_ref']:12.3f}{row['dmc']:12.3f}")
        for sec, title in (("stages", "Z events by stage"), ("tags", "final selection per PNet tag region")):
            L.append(f"-- {ch}: {title} (all weights)")
            L.append(f"{'':26s}{'MC ' + b:>14s}{'MC ' + a:>14s}{'MC ratio':>10s}{'data/MC ' + b:>22s}{'data/MC ' + a:>22s}")
            for name in res[ch][sec]:
                y0, y1 = ref[ch][sec][name], res[ch][sec][name]
                row = {"MC_ref": y0["MC"], "MC": y1["MC"], "MC_ratio": y1["MC"] / y0["MC"] if y0["MC"] else float("nan"),
                       "data_ref": y0["data"], "data": y1["data"],
                       "dmc_ref": y0["data/MC"], "dmc_ref_err": y0["data/MC_err"],
                       "dmc": y1["data/MC"], "dmc_err": y1["data/MC_err"]}
                cmp[ch][sec][name] = row
                L.append(f"{name:26s}{row['MC_ref']:14.0f}{row['MC']:14.0f}{row['MC_ratio']:10.4f}"
                         f"{row['dmc_ref']:14.3f} +- {row['dmc_ref_err']:.3f}{row['dmc']:14.3f} +- {row['dmc_err']:.3f}")
        L.append("")
    open(f"{rundir}/yields/compare_{b}.txt", "w").write("\n".join(L) + "\n")
    json.dump(cmp, open(f"{rundir}/yields/compare_{b}.json", "w"), indent=1)
    print("\n".join(L))


if __name__ == "__main__":
    rundir = sys.argv[1]
    res = summarise(*load_run(rundir))
    write_run(rundir, res)
    if len(sys.argv) > 2:
        refdir = sys.argv[2]
        ref_json = f"{refdir}/yields/yields.json"
        ref = json.load(open(ref_json)) if os.path.exists(ref_json) else None
        if ref is None:
            ref = summarise(*load_run(refdir))
            write_run(refdir, ref)
        write_compare(rundir, refdir, res, ref)
