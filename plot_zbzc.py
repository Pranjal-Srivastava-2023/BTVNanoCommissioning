"""Plots and yield tables for the Zb_Zc_ratio workflow output (MC only so far).

Each sample is scaled by xsec * lumi / sumw (metadata/Zb_Zc_ratio_xsections_Summer22.json)
and the histograms are stacked by jet flavour, per channel, log-scale y.
Works for both the AK4 (Zb_Zc_ratio) and AK8 (Zb_Zc_ratio_AK8) outputs, detected
from the histogram names. Also writes the 2D tagger map per flavour group
(AK4: PNet CvL vs CvB, AK8: XbbVsQCD vs XccVsQCD) and a cutflow/yield table.
For AK4 every variable is also stacked by partonFlavour (<var>_parton.png), and the
hadron x parton flavour migration is plotted (flav_migration.png) and tabulated.

Usage:
    python plot_zbzc.py hists_zbzc_ak4_test/test_zbzc_ak4/test_zbzc_ak4.coffea
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

AK4 = "jet_pt" in next(iter(out.values()))
JET = "AK4" if AK4 else "AK8"
COLORS = {"l": "#9e9e9e", "c": "#7fb3e6", "cc": "#1f5fa8", "b": "#f2a65a", "bb": "#c0392b"}
ZVARS = ["z_mass", "z_pt", "lep0_pt", "lep1_pt", "lhe_vpt"]
if AK4:
    FLAVS = ["l", "c", "b"]  # bottom to top of the stack
    LABELS = {"l": "light", "c": "c (hadronFlavour 4)", "b": "b (hadronFlavour 5)"}
    VARS = ["jet_pt", "jet_eta", "jet_PNetB", "jet_PNetCvL", "jet_PNetCvB", "n_jet"] + ZVARS
    MAP2D = ("jet_CvL_CvB", "PNet CvL", "PNet CvB", {"b": ["b"], "c": ["c"], "light": ["l"]})
    PFLAVS = ["none", "g", "uds", "c", "b"]
    PCOLORS = {"none": "#d9d9d9", "g": "#6aa84f", "uds": "#9e9e9e", "c": "#7fb3e6", "b": "#f2a65a"}
    PLABELS = {"none": "no parton (0)", "g": "g (21)", "uds": "uds (1-3)",
               "c": "c (partonFlavour 4)", "b": "b (partonFlavour 5)"}
else:
    FLAVS = ["l", "c", "cc", "b", "bb"]
    LABELS = {"l": "light", "c": "c (1 C hadron)", "cc": "cc (≥2 C)", "b": "b (1 B hadron)", "bb": "bb (≥2 B)"}
    VARS = ["fj_pt", "fj_eta", "fj_msd", "fj_mreg", "fj_Xbb", "fj_Xcc", "fj_tau21", "n_fj"] + ZVARS
    MAP2D = ("fj_Xbb_Xcc", "PNet XbbVsQCD", "PNet XccVsQCD",
             {"b + bb": ["b", "bb"], "c + cc": ["c", "cc"], "light": ["l"]})


def scaled(name, keep="flav"):
    """Sum of all samples' histogram `name`, each scaled to xsec * lumi / sumw.

    AK4 histograms have both a hadron ("flav") and a parton ("pflav") flavour axis;
    the one not in `keep` is summed over (keep=None keeps both)."""
    tot = None
    for ds, o in out.items():
        h = o[name] * (xs[ds] * LUMI / o["sumw"])
        tot = h if tot is None else tot + h
    for ax in ("flav", "pflav"):
        if keep and ax != keep and ax in tot.axes.name:
            tot = tot[{ax: sum}]
    return tot


def label(ax, fontsize=18):
    # data=False already prepends "Simulation"
    hep.cms.label("Preliminary", data=False, lumi=round(LUMI / 1000, 2),
                  com=13.6, ax=ax, fontsize=fontsize)


def stack(var, axname, flavs, colors, labels, suffix=""):
    h = scaled(var, axname)
    fig, axes = plt.subplots(1, 2, figsize=(20, 8))
    for ax, ch in zip(axes, ["Zee", "Zmm"]):
        hs = [h[{"channel": ch, axname: f}] for f in flavs]
        hep.histplot(hs, ax=ax, stack=True, histtype="fill",
                     color=[colors[f] for f in flavs], label=[labels[f] for f in flavs])
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
    fig.savefig(os.path.join(outdir, f"{var}{suffix}.png"), dpi=90)
    plt.close(fig)


for var in VARS:
    stack(var, "flav", FLAVS, COLORS, LABELS)
    if AK4:
        stack(var, "pflav", PFLAVS, PCOLORS, PLABELS, "_parton")

if AK4:
    # hadron x parton flavour migration (scaled), each hadron-flavour row normalized to 1
    hm = scaled(VARS[0], keep=None)
    HF = ["b", "c", "l"]
    PF = PFLAVS[::-1]
    mig = {ch: np.array([[hm[{"channel": ch, "flav": f, "pflav": p}].sum(flow=True).value for p in PF]
                         for f in HF]) for ch in ["Zee", "Zmm"]}
    fig, axes = plt.subplots(1, 2, figsize=(20, 7.5))
    for ax, ch in zip(axes, ["Zee", "Zmm"]):
        frac = mig[ch] / mig[ch].sum(axis=1, keepdims=True)
        ax.imshow(np.clip(frac, 0, 1), cmap="Blues", vmin=0, vmax=1)
        for i in range(len(HF)):
            for j in range(len(PF)):
                ax.text(j, i, f"{100 * frac[i, j]:.1f}%", ha="center", va="center", fontsize=17,
                        color="white" if frac[i, j] > 0.5 else "black")
        ax.set_xticks(range(len(PF)), PF)
        ax.set_yticks(range(len(HF)), ["b (5)", "c (4)", "light (0)"])
        ax.set_xlabel("partonFlavour")
        ax.set_ylabel("hadronFlavour")
        ax.minorticks_off()
        ax.set_title(ch.replace("Zee", r"Z$\to$ee").replace("Zmm", r"Z$\to\mu\mu$")
                     + ": fraction of each hadron flavour", fontsize=18)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "flav_migration.png"), dpi=90)
    plt.close(fig)

# 2D tagger map, per flavour group, both channels summed
name2d, xlab, ylab, groups = MAP2D
h2 = scaled(name2d)[{"channel": sum}]
fig, axes = plt.subplots(1, 3, figsize=(27, 8))
for ax, (title, fl) in zip(axes, groups.items()):
    hh = sum(h2[{"flav": f}] for f in fl)
    vals = hh.values()
    vals = vals / vals.sum() if vals.sum() > 0 else vals
    m = ax.pcolormesh(hh.axes[0].edges, hh.axes[1].edges, np.clip(vals.T, 1e-5, None),
                      norm=matplotlib.colors.LogNorm(1e-4, 1), cmap="viridis")
    fig.colorbar(m, ax=ax, label="fraction of jets")
    ax.set_xlabel(xlab)
    ax.set_ylabel(ylab)
    ax.text(0.04, 0.94, title, transform=ax.transAxes, fontsize=20, va="top", color="white")
    label(ax, fontsize=13)
fig.tight_layout()
fig.savefig(os.path.join(outdir, f"{name2d}.png"), dpi=90)
plt.close(fig)

# Cutflow (raw MC events per sample) and scaled yields per flavour
lines = [f"input: {infile}", f"lumi: {LUMI / 1000:.2f} /fb, 13.6 TeV, Summer22, {JET} jets", ""]
for ch in ["Zee", "Zmm"]:
    lines.append(f"== {ch}: raw MC events passing each step (after the LHE pT(ll) slice)")
    steps = list(next(iter(out.values()))["cutflow_raw"][ch].keys())
    lines.append(f"{'sample':12s}" + "".join(f"{s:>10s}" for s in steps))
    for ds, o in out.items():
        short = ds.split("_TuneCP5")[0].replace("DYto2L-2Jets_MLL-50", "").strip("_") or "inclusive"
        lines.append(f"{short:12s}" + "".join(f"{o['cutflow_raw'][ch][s]:>10d}" for s in steps))
    lines.append("")
lines.append(f"== raw (unweighted) MC events after full selection, by {JET} jet flavour")
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
h = scaled(VARS[0])
lines.append(f"== scaled yields after full selection, by {JET} jet flavour")
lines.append(f"{'':6s}" + "".join(f"{f:>10s}" for f in FLAVS) + f"{'total':>10s}")
for ch in ["Zee", "Zmm"]:
    y = [h[{"channel": ch, "flav": f}].sum(flow=True).value for f in FLAVS]
    lines.append(f"{ch:6s}" + "".join(f"{v:10.1f}" for v in y) + f"{sum(y):10.1f}")
    lines.append(f"{'  frac':6s}" + "".join(f"{v / sum(y):10.3f}" for v in y))
if AK4:
    hp = scaled(VARS[0], "pflav")
    lines.append("")
    lines.append("== scaled yields after full selection, by AK4 jet partonFlavour")
    lines.append(f"{'':6s}" + "".join(f"{f:>10s}" for f in PFLAVS) + f"{'total':>10s}")
    for ch in ["Zee", "Zmm"]:
        y = [hp[{"channel": ch, "pflav": f}].sum(flow=True).value for f in PFLAVS]
        lines.append(f"{ch:6s}" + "".join(f"{v:10.1f}" for v in y) + f"{sum(y):10.1f}")
        lines.append(f"{'  frac':6s}" + "".join(f"{v / sum(y):10.3f}" for v in y))
    lines.append("")
    lines.append("== hadron (rows) x parton (columns) flavour migration")
    for ch in ["Zee", "Zmm"]:
        lines.append(f"-- {ch}: scaled, fraction of each hadron-flavour row")
        lines.append(f"{'':8s}" + "".join(f"{p:>10s}" for p in PF))
        for f, row in zip(HF, mig[ch]):
            lines.append(f"{f:8s}" + "".join(f"{v / row.sum():10.3f}" for v in row))
        lines.append(f"-- {ch}: raw (unweighted) events")
        lines.append(f"{'':8s}" + "".join(f"{p:>10s}" for p in PF))
        for f in HF:
            n = [sum(o["nevt_migration"][ch][f"{f}|{p}"] for o in out.values()) for p in PF]
            lines.append(f"{f:8s}" + "".join(f"{v:10d}" for v in n))
open(os.path.join(os.path.dirname(infile), "yields.txt"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
print("plots in", outdir)
