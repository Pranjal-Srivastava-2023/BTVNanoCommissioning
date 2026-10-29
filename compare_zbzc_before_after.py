"""Before / after plots for the 2026-10-28 fixes (type-1 MET EmEF cut, DY Z pT weights).

before = second small run, commit fb54afd (extract with
         git archive fb54afd hists_zbzc_run3 | tar -x -C <before_dir>)
after  = third small run, hists_zbzc_run3/ (b48a524)
Same 20 files per sample in both. For the Z pT weights alone, "all Z events" (before the
MET and jet cuts) are compared: before = hists_zbzc_run3_stage (no weights), after = the
stage histograms of the new run (the MET fix cannot change events before the MET cut).

Usage:  python compare_zbzc_before_after.py <before_dir>
Output: hists_zbzc_compare/ratio_<campaign>.png   data/MC vs Z pT and leading-lepton pT,
                                                  full selection, before vs after
        hists_zbzc_compare/zpt_weights_closure.png data/MC vs Z pT for all Z events,
                                                  before vs after the weights
        hists_zbzc_compare/before_after.txt        the numbers
"""
import glob
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
CAMPAIGNS = ["Summer22", "Summer22EE", "Summer23", "Summer23BPix"]
ERAS = {"Summer22": "2022 C-D", "Summer22EE": "2022 E-G", "Summer23": "2023 C", "Summer23BPix": "2023 D"}
CH_LABEL = {"Zee": r"Z$\to$ee", "Zmm": r"Z$\to\mu\mu$"}
XS = json.load(open("metadata/Zb_Zc_ratio_xsections_run3.json"))
BINS = {"z_pt": [0, 20, 40, 60, 100, 140, 200, 300, 1000],
        "lep0_pt": [20, 60, 100, 140, 200, 300, 1000]}
XLAB = {"z_pt": r"$p_T^{\ell\ell}$ [GeV]", "lep0_pt": r"Leading lepton $p_T$ [GeV]"}
STAGE_BINS = [0, 5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100, 125, 150, 200, 300, 1000]
OUTDIR = "hists_zbzc_compare"
os.makedirs(OUTDIR, exist_ok=True)
before_dir = sys.argv[1]


def load_dir(d):
    out = {}
    for f in glob.glob(f"{d}/zbzc_run3_*.coffea"):
        out.update(load(f))
    return out


def rebin(v, e, edges):
    return np.array([v[(e[:-1] >= a) & (e[:-1] < b)].sum() for a, b in zip(edges[:-1], edges[1:])])


def ratio(out, lumi, var, ch, edges, stage=None):
    """data/MC and its error (data stat + MC stat) in the wide bins."""
    d = m = m2 = 0
    for ds, o in out.items():
        h = o[var][{"channel": ch, "flav": sum, "pflav": sum}]
        if stage:
            h = h[{"stage": sum}]
        e = h.axes[-1].edges
        if ds.startswith(("Muon", "EGamma")):
            if ds.startswith("Muon" if ch == "Zmm" else "EGamma"):
                d = d + rebin(h.values(), e, edges)
            continue
        s = XS[ds] * lumi[ch] / o["sumw"]
        m = m + rebin(h.values(), e, edges) * s
        m2 = m2 + rebin(h.variances(), e, edges) * s * s
    r = d / m
    return r, r * np.sqrt(1 / np.maximum(d, 1) + m2 / m**2), d.sum() / m.sum()


def draw(ax, edges, rows, ylim):
    x = 0.5 * (np.array(edges[:-1]) + np.array(edges[1:]))
    xe = 0.5 * np.diff(edges)
    for i, (lab, (r, err), col, mk) in enumerate(rows):
        sh = (-0.12 if i == 0 else 0.12) * xe
        ax.errorbar(x + sh, r, yerr=err, xerr=xe, fmt=mk, color=col, ms=8,
                    mfc=col if i == 0 else "white", mew=2, label=lab)
    ax.axhline(1, color="grey", ls="--", lw=1)
    ax.set_xscale("log")
    ax.set_xlim(edges[0] if edges[0] > 0 else 8, edges[-1])
    ax.set_ylim(*ylim)
    ax.set_ylabel("Data / MC")


lines = []
for c in CAMPAIGNS:
    lumi = json.load(open(f"hists_zbzc_run3/{c}/lumi.json"))
    old = load_dir(f"{before_dir}/hists_zbzc_run3/{c}/zbzc_run3")
    new = load_dir(f"hists_zbzc_run3/{c}/zbzc_run3")
    fig, axes = plt.subplots(2, 2, figsize=(20, 13))
    lines.append(f"\n== {c} ({ERAS[c]}), full selection, data/MC before -> after")
    for row, var in enumerate(["z_pt", "lep0_pt"]):
        for col, ch in enumerate(["Zee", "Zmm"]):
            ed = BINS[var]
            ro, eo, to = ratio(old, lumi, var, ch, ed)
            rn, en, tn = ratio(new, lumi, var, ch, ed)
            ax = axes[row, col]
            draw(ax, ed, [(f"before (total {to:.3f})", (ro, eo), "#888888", "o"),
                          (f"after (total {tn:.3f})", (rn, en), "#C0392B", "s")], (0.4, 1.4))
            ax.set_xlabel(XLAB[var])
            ax.legend(fontsize=16, loc="lower left", title=CH_LABEL[ch], title_fontsize=18)
            hep.cms.label("Preliminary", data=True, ax=ax, fontsize=18, rlabel=f"{ERAS[c]} (13.6 TeV)")
            lines.append(f"  {var:8s}{ch}: total {to:.3f} -> {tn:.3f} | " + "  ".join(
                f"{a}-{b}: {p:.2f}->{q:.2f}±{s:.2f}" for a, b, p, q, s in zip(ed[:-1], ed[1:], ro, rn, en)))
    fig.tight_layout()
    fig.savefig(f"{OUTDIR}/ratio_{c}.png", dpi=80)
    plt.close(fig)

# Z pT weights alone: all Z events, before the MET and jet cuts
fig, axes = plt.subplots(2, 4, figsize=(32, 13), sharey=True)
lines.append("\n== all Z events (before MET and jet cuts), data/MC vs Z pT, before -> after the Z pT weights")
for col, c in enumerate(CAMPAIGNS):
    lumi = json.load(open(f"hists_zbzc_run3/{c}/lumi.json"))
    old = load_dir(f"hists_zbzc_run3_stage/{c}/zbzc_run3")
    new = load_dir(f"hists_zbzc_run3/{c}/zbzc_run3")
    for row, ch in enumerate(["Zee", "Zmm"]):
        ro, eo, to = ratio(old, lumi, "stage_z_pt", ch, STAGE_BINS, stage=True)
        rn, en, tn = ratio(new, lumi, "stage_z_pt", ch, STAGE_BINS, stage=True)
        ax = axes[row, col]
        draw(ax, STAGE_BINS, [("before (no weights)", (ro, eo), "#888888", "o"),
                              ("after (Z pT weights)", (rn, en), "#C0392B", "s")], (0.75, 1.25))
        ax.set_xlim(2, 1000)
        ax.set_xlabel(r"$p_T^{\ell\ell}$ [GeV]")
        note = " (fit here)" if ch == "Zmm" else " (check)"
        ax.legend(fontsize=15, loc="lower left", title=f"{CH_LABEL[ch]}{note}, {ERAS[c]}", title_fontsize=16)
        rms_o, rms_n = np.std(ro / to), np.std(rn / tn)
        lines.append(f"  {c:13s}{ch}: rms over bins {rms_o:.3f} -> {rms_n:.3f}; total {to:.3f} -> {tn:.3f}")
fig.tight_layout()
fig.savefig(f"{OUTDIR}/zpt_weights_closure.png", dpi=70)
plt.close(fig)

with open(f"{OUTDIR}/before_after.txt", "w") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines))
