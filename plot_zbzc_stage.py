"""Data/MC slope study for the Zb_Zc_ratio Run 3 run: where does the slope in Z pT
(and so in lepton pT) come from?

Reads the stage_* histograms of hists_zbzc_run3_stage/<campaign>/zbzc_run3/ (Z events
before the MET < 50 and >= 1 jet cuts, split by which of the two cuts they pass)
and draws data/MC for four selections:
    Z only         all Z events (trigger, two leptons, OS, Z mass)
    Z + MET        MET < 50
    Z + jet        >= 1 jet
    Z + MET + jet  both = the analysis selection
If the slope is already there for "Z only", it is the DY generator Z pT; if it
only appears with the jet / MET cut, it is jet or MET modelling.
MC is scaled as in plot_zbzc_run3.py (xsec * lumi / sumw); lumi.json from
hists_zbzc_run3/<campaign>/ (same files and lumisections).

Usage:  python plot_zbzc_stage.py <campaign>
Output: hists_zbzc_run3_stage/<campaign>/plots/stage_*.png, stage_tables.txt
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

ERAS = {"Summer22": "2022 C-D", "Summer22EE": "2022 E-G", "Summer23": "2023 C", "Summer23BPix": "2023 D"}
CHANNELS = ["Zee", "Zmm"]
CH_LABEL = {"Zee": r"Z$\to$ee", "Zmm": r"Z$\to\mu\mu$"}
SELS = {
    "Z only": ["none", "MET", "jet", "MET+jet"],
    "Z + MET < 50": ["MET", "MET+jet"],
    "Z + $\\geq$1 jet": ["jet", "MET+jet"],
    "Z + MET + jet": ["MET+jet"],
}
PLAIN = {k: k.replace("$\\geq$", ">=") for k in SELS}  # for the text tables
COLORS = ["#222222", "#1f77b4", "#d62728", "#2ca02c"]
VARS = {
    "z_pt": r"$p_T^{\ell\ell}$ [GeV]",
    "lep0_pt": r"Leading lepton $p_T$ [GeV]",
    "lep1_pt": r"Subleading lepton $p_T$ [GeV]",
    "lep0_eta": r"Leading lepton $\eta$",
    "met_pt": r"PUPPI $p_T^{miss}$ [GeV]",
}
XS = json.load(open("metadata/Zb_Zc_ratio_xsections_run3.json"))

camp = sys.argv[1]
indir = f"hists_zbzc_run3_stage/{camp}"
plotdir = os.path.join(indir, "plots")
os.makedirs(plotdir, exist_ok=True)
OUT = {}
for f in sorted(glob.glob(f"{indir}/zbzc_run3/zbzc_run3_*.coffea")):
    OUT.update(load(f))
LUMI = json.load(open(f"hists_zbzc_run3/{camp}/lumi.json"))


def is_data(ds, ch):
    return ds.startswith("Muon" if ch == "Zmm" else "EGamma")


def get(var, ch, stages):
    """data, MC, MC variance (all backgrounds summed), DY only, bin edges."""
    d = m = w2 = dy = 0
    for ds, o in OUT.items():
        h = o[f"stage_{var}"][{"channel": ch, "flav": sum, "pflav": sum}]
        h = sum(h[{"stage": s}] for s in stages)
        if is_data(ds, ch):
            d = d + h.values()
        elif not ds.startswith(("Muon", "EGamma")):
            s = XS[ds] * LUMI[ch] / o["sumw"]
            m = m + h.values() * s
            w2 = w2 + h.variances() * s * s
            if ds.startswith("DYto2L"):
                dy = dy + h.values() * s
    zero = np.zeros(len(h.axes[0]))
    return d + zero, m + zero, w2 + zero, dy + zero, h.axes[0].edges


tables = []
for var, xlabel in VARS.items():
    fig, axes = plt.subplots(1, 2, figsize=(20, 8))
    for ax, ch in zip(axes, CHANNELS):
        tables.append(f"\n{var}  {ch}  (data/MC per bin, stat. error from data)")
        for i, ((name, stages), col) in enumerate(zip(SELS.items(), COLORS)):
            d, m, w2, _, e = get(var, ch, stages)
            with np.errstate(divide="ignore", invalid="ignore"):
                r = d / m
                err = np.sqrt(d + w2 * r**2) / m
            ok = (m > 0) & (d > 0)
            x = 0.5 * (e[1:] + e[:-1])
            # small x offset per selection so that the markers do not overlap
            x = x * 10 ** (0.015 * (i - 1.5)) if var.endswith("pt") else x + 0.03 * (i - 1.5)
            ax.errorbar(x[ok], r[ok], yerr=err[ok], fmt="o",
                        ms=4, color=col, label=f"{name}  (total {d.sum() / m.sum():.3f})")
            tables.append(f"  {PLAIN[name]}: total {d.sum() / m.sum():.3f} | "
                          + " ".join(f"{e[i]:g}-{e[i + 1]:g}:{r[i]:.3f}±{err[i]:.3f}" for i in np.where(ok)[0]))
        ax.axhline(1, color="grey", ls="--", lw=1)
        ax.set_ylim(0.4, 1.5)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Data / MC")
        if var.endswith("pt"):
            ax.set_xscale("log")
            ax.set_xlim(e[0] * 0.9 if e[0] > 0 else 1.5, e[-1])
        ax.legend(fontsize=14, loc="lower left", title=CH_LABEL[ch], title_fontsize=16)
        hep.cms.label("Preliminary", data=True, ax=ax, fontsize=18,
                      rlabel=f"{LUMI[ch] / 1000:.2f} fb$^{{-1}}$ (13.6 TeV)")
    fig.tight_layout()
    fig.savefig(f"{plotdir}/stage_{var}.png", dpi=90)
    plt.close(fig)

with open(f"{indir}/stage_tables.txt", "w") as f:
    f.write(f"{camp} ({ERAS[camp]}): data/MC for Z events before / after the MET and jet cuts\n")
    f.write("\n".join(tables) + "\n")
    # cut efficiencies data vs MC (with all MC weights), per channel
    f.write("\ncut efficiencies on top of 'Z only' (data, MC, data/MC)\n")
    for ch in CHANNELS:
        tot = get("z_pt", ch, SELS["Z only"])
        for name in list(SELS)[1:]:
            s = get("z_pt", ch, SELS[name])
            ed, em = s[0].sum() / tot[0].sum(), s[1].sum() / tot[1].sum()
            f.write(f"  {ch} {PLAIN[name]}: {ed:.4f} {em:.4f} {ed / em:.3f}\n")
print(open(f"{indir}/stage_tables.txt").read())
