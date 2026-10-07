"""Plots and yield tables for the Zb_Zc_ratio workflow output (MC only so far).

Each sample is scaled by xsec * lumi / sumw (metadata/Zb_Zc_ratio_xsections_Summer22.json)
and the histograms are stacked by AK8 jet flavour, per channel, log-scale y.
Also writes the Xbb vs Xcc 2D map per flavour group and a cutflow/yield table.

Usage:
    python plot_zbzc.py hists_zbzc_test/test_zbzc/test_zbzc.coffea
"""
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
from coffea.util import load

hep.style.use("CMS")

infile = sys.argv[1]
outdir = os.path.join(os.path.dirname(infile), "plots")
os.makedirs(outdir, exist_ok=True)
xs = json.load(open("metadata/Zb_Zc_ratio_xsections_Summer22.json"))
LUMI = xs["lumi_pb"]
out = load(infile)

FLAVS = ["l", "c", "cc", "b", "bb"]  # bottom to top of the stack
COLORS = {"l": "#9e9e9e", "c": "#7fb3e6", "cc": "#1f5fa8", "b": "#f2a65a", "bb": "#c0392b"}
LABELS = {"l": "light", "c": "c (1 C hadron)", "cc": "cc (≥2 C)", "b": "b (1 B hadron)", "bb": "bb (≥2 B)"}
VARS = ["fj_pt", "fj_eta", "fj_msd", "fj_mreg", "fj_Xbb", "fj_Xcc", "fj_tau21", "n_fj",
        "z_mass", "z_pt", "lep0_pt", "lep1_pt", "lhe_vpt"]


def scaled(name):
    """Sum of all samples' histogram `name`, each scaled to xsec * lumi / sumw."""
    tot = None
    for ds, o in out.items():
        h = o[name] * (xs[ds] * LUMI / o["sumw"])
        tot = h if tot is None else tot + h
    return tot


def label(ax, fontsize=18):
    # data=False already prepends "Simulation"
    hep.cms.label("Preliminary", data=False, lumi=round(LUMI / 1000, 2),
                  com=13.6, ax=ax, fontsize=fontsize)


for var in VARS:
    h = scaled(var)
    fig, axes = plt.subplots(1, 2, figsize=(20, 8))
    for ax, ch in zip(axes, ["Zee", "Zmm"]):
        hs = [h[{"channel": ch, "flav": f}] for f in FLAVS]
        hep.histplot(hs, ax=ax, stack=True, histtype="fill",
                     color=[COLORS[f] for f in FLAVS], label=[LABELS[f] for f in FLAVS])
        ax.set_yscale("log")
        ax.set_ylabel("Events / bin")
        # log-y floor at 0.1 events/bin (bins below that are +/- NLO weight
        # cancellations), headroom above the stacked peak for the legend
        tot = sum(x.values() for x in hs)
        ax.set_ylim(0.1, max(tot.max(), 1.0) * 50)
        ax.text(0.04, 0.94, ch.replace("Zee", r"Z$\to$ee").replace("Zmm", r"Z$\to\mu\mu$"),
                transform=ax.transAxes, fontsize=20, va="top")
        ax.legend(fontsize=14, loc="upper right")
        label(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, f"{var}.png"), dpi=90)
    plt.close(fig)

# Xbb vs Xcc, per flavour group, both channels summed
h2 = scaled("fj_Xbb_Xcc")[{"channel": sum}]
groups = {"b + bb": ["b", "bb"], "c + cc": ["c", "cc"], "light": ["l"]}
fig, axes = plt.subplots(1, 3, figsize=(27, 8))
for ax, (title, fl) in zip(axes, groups.items()):
    hh = sum(h2[{"flav": f}] for f in fl)
    vals = hh.values()
    vals = vals / vals.sum() if vals.sum() > 0 else vals
    m = ax.pcolormesh(hh.axes[0].edges, hh.axes[1].edges, np.clip(vals.T, 1e-5, None),
                      norm=matplotlib.colors.LogNorm(1e-4, 1), cmap="viridis")
    fig.colorbar(m, ax=ax, label="fraction of jets")
    ax.set_xlabel("PNet XbbVsQCD")
    ax.set_ylabel("PNet XccVsQCD")
    ax.text(0.04, 0.94, title, transform=ax.transAxes, fontsize=20, va="top", color="white")
    label(ax, fontsize=13)
fig.tight_layout()
fig.savefig(os.path.join(outdir, "fj_Xbb_vs_Xcc.png"), dpi=90)
plt.close(fig)

# Cutflow (raw MC events per sample) and scaled yields per flavour
lines = [f"input: {infile}", f"lumi: {LUMI / 1000:.2f} /fb, 13.6 TeV, Summer22", ""]
for ch in ["Zee", "Zmm"]:
    lines.append(f"== {ch}: raw MC events passing each step (after the LHE pT(ll) slice)")
    steps = list(next(iter(out.values()))["cutflow_raw"][ch].keys())
    lines.append(f"{'sample':12s}" + "".join(f"{s:>10s}" for s in steps))
    for ds, o in out.items():
        short = ds.split("_TuneCP5")[0].replace("DYto2L-2Jets_MLL-50", "").strip("_") or "inclusive"
        lines.append(f"{short:12s}" + "".join(f"{o['cutflow_raw'][ch][s]:>10d}" for s in steps))
    lines.append("")
lines.append("== raw (unweighted) MC events after full selection, by AK8 jet flavour")
for ch in ["Zee", "Zmm"]:
    lines.append(f"-- {ch}")
    lines.append(f"{'sample':12s}" + "".join(f"{f:>10s}" for f in FLAVS) + f"{'total':>10s}")
    tot = [0] * len(FLAVS)
    for ds, o in out.items():
        short = ds.split("_TuneCP5")[0].replace("DYto2L-2Jets_MLL-50", "").strip("_") or "inclusive"
        n = [o["nevt_flav"][ch][f] for f in FLAVS]
        tot = [t + v for t, v in zip(tot, n)]
        lines.append(f"{short:12s}" + "".join(f"{v:10d}" for v in n) + f"{sum(n):10d}")
    lines.append(f"{'all':12s}" + "".join(f"{v:10d}" for v in tot) + f"{sum(tot):10d}")
lines.append("")
h = scaled("fj_pt")
lines.append("== scaled yields after full selection, by AK8 jet flavour")
lines.append(f"{'':6s}" + "".join(f"{f:>10s}" for f in FLAVS) + f"{'total':>10s}")
for ch in ["Zee", "Zmm"]:
    y = [h[{"channel": ch, "flav": f}].sum(flow=True).value for f in FLAVS]
    lines.append(f"{ch:6s}" + "".join(f"{v:10.1f}" for v in y) + f"{sum(y):10.1f}")
    lines.append(f"{'  frac':6s}" + "".join(f"{v / sum(y):10.3f}" for v in y))
open(os.path.join(os.path.dirname(infile), "yields.txt"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
print("plots in", outdir)
