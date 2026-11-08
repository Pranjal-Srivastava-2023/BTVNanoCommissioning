"""Z->ee vs Z->mumu in the 2026-11-08 Summer22 run (advisor: 'muon channel looks different from electrons').
1. data/MC per selection stage (stage_z_pt: 'none' = fails MET < 50 and has no jet, 'MET' = MET < 50 and
   0 jets, 'jet' = >= 1 jet but MET > 50, 'MET+jet' = final selection; their sum = all Z events)
   and the straight-line slope of data/MC vs pT(ll) (0-400 GeV, % per 100 GeV, fit weighted by the
   expected error sqrt(MC + MC var)/MC as in compare_zbzc_njet_slope.py).
2. data/MC per leading-lepton |eta| region at the final selection.
3. The same pT(ll), lead-lepton pT and jet pT slope fit (10 GeV bins, final selection, incl) on three runs:
   hists_zbzc_run3_ge1j (DY Z pT weights ON), hists_zbzc_run3_tag (the 237-page deck, weights off),
   hists_zbzc_run3_v2 (this run).
usage: python compare_zbzc_v2_channels.py ; output hists_zbzc_run3_v2/Summer22/channels_summary.{txt,json}
"""
import glob
import json

import numpy as np
from coffea.util import load

XS = json.load(open("metadata/Zb_Zc_ratio_xsections_run3.json"))
LUMI = json.load(open("hists_zbzc_run3/Summer22/lumi.json"))
OUTD = "hists_zbzc_run3_v2/Summer22"


def load_run(d):
    out = {}
    for f in sorted(glob.glob(f"{d}/Summer22/zbzc_run3/zbzc_run3_*.coffea")):
        out.update(load(f))
    return out


def data_mc(out, var, ch, extra):
    data = mc = None
    for ds, o in out.items():
        h = o[var]
        names = [a.name for a in h.axes]
        sel = {k: v for k, v in {"channel": ch, "flav": sum, "pflav": sum, "tag": "incl", **extra}.items() if k in names}
        h = h[sel]
        if not ds.startswith(("Muon", "EGamma")):
            h = h * (XS[ds] * LUMI[ch] / o["sumw"])
            mc = h if mc is None else mc + h
        elif ds.startswith("Muon" if ch == "Zmm" else "EGamma"):
            data = h if data is None else data + h
    return data.axes[0].edges, data.values(), mc.values(), mc.variances()


def slope(edges, d, m, mv, fr):
    c = 0.5 * (edges[1:] + edges[:-1])
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(m > 0, d / m, np.nan)
        e = np.sqrt(m + mv) / m
    s = (c > fr[0]) & (c < fr[1]) & np.isfinite(r) & (e > 0)
    p, cov = np.polyfit(c[s], r[s], 1, w=1 / e[s], cov="unscaled")
    return 1e4 * p[0], 1e4 * np.sqrt(cov[0, 0])


def ratio(d, m, mv):
    r = d.sum() / m.sum()
    return r, r * np.hypot(d.sum() ** -0.5, np.sqrt(mv.sum()) / m.sum())


J, T = {"stages": {}, "eta": {}, "runs": {}}, []
v2 = load_run("hists_zbzc_run3_v2")
T.append("== data/MC per selection stage and slope vs pT(ll) (0-400 GeV, %/100 GeV)")
for st, lab in ((sum, "all Z events"), ("MET", "MET<50, 0 jets"), ("none", "MET>50, 0 jets"),
                ("jet", "MET>50, >=1 jet"), ("MET+jet", "final: MET<50, >=1 jet")):
    J["stages"][lab] = {}
    for ch in ("Zee", "Zmm"):
        e, d, m, mv = data_mc(v2, "stage_z_pt", ch, {"stage": st})
        r, re_ = ratio(d, m, mv)
        sl = slope(e, d, m, mv, (0, 400))
        J["stages"][lab][ch] = dict(data=float(d.sum()), mc=float(m.sum()), r=r, re=re_, slope=sl[0], slope_err=sl[1])
        T.append(f"{lab:24s} {ch}  data {d.sum():8.0f}  MC {m.sum():10.1f}  data/MC {r:.3f}+-{re_:.3f}  slope {sl[0]:+6.2f}+-{sl[1]:.2f}")
T.append("\n== final selection: data/MC per leading-lepton |eta| region")
REG = ((0, 0.8), (0.8, 1.2), (1.2, 2.0), (2.0, 2.5))
for ch in ("Zee", "Zmm"):
    e, d, m, mv = data_mc(v2, "lep0_eta", ch, {})
    c = 0.5 * (e[1:] + e[:-1])
    J["eta"][ch] = []
    cells = []
    for a, b in REG:
        s = (abs(c) > a) & (abs(c) < b)
        r, re_ = ratio(d[s], m[s], mv[s])
        J["eta"][ch].append((f"{a}-{b}", r, re_))
        cells.append(f"{a}-{b}: {r:.3f}+-{re_:.3f}")
    T.append(f"{ch}  " + "  ".join(cells))
T.append("\n== same slope fit (10 GeV bins, final selection, %/100 GeV) on three runs")
FITS = {"z_pt": (0, 400), "lep0_pt": (35, 300), "jet_pt": (30, 300)}
for run, lab in (("hists_zbzc_run3_ge1j", "Oct 29-Nov 2, DY Z pT weights ON"), ("hists_zbzc_run3_tag", "237-page deck (weights off)"),
                 ("hists_zbzc_run3_v2", "this run (new muon trigger SF, pT>26)")):
    out = v2 if run.endswith("v2") else load_run(run)
    J["runs"][run] = {"label": lab}
    for ch in ("Zee", "Zmm"):
        cells = {}
        for var, fr in FITS.items():
            e, d, m, mv = data_mc(out, var, ch, {})
            cells[var] = slope(e, d, m, mv, fr)
        r = data_mc(out, "z_pt", ch, {})
        J["runs"][run][ch] = dict(r=float(r[1].sum() / r[2].sum()), **{k: list(v) for k, v in cells.items()})
        T.append(f"{run:22s} {ch} data/MC {r[1].sum() / r[2].sum():.3f} | " +
                 " | ".join(f"{k} {v[0]:+5.1f}+-{v[1]:.1f}" for k, v in cells.items()) + f"   ({lab})")
open(f"{OUTD}/channels_summary.txt", "w").write("\n".join(T) + "\n")
json.dump(J, open(f"{OUTD}/channels_summary.json", "w"), indent=1)
print("\n".join(T))
