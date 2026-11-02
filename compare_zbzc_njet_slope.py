"""Does the data/MC slope in the pT spectra go away in Z + exactly 1 jet?

Compares two run_zbzc_run3.sh outputs of the same campaign with the same 10 GeV
pT binning: N_jet >= 1 (Zb_Zc_ratio, hists_zbzc_run3_ge1j) and N_jet = 1
(Zb_Zc_ratio_1jet, hists_zbzc_run3_1j). MC = DY + tt + VV scaled by
xsec * lumi / sumw; lumi from hists_zbzc_run3/<campaign>/lumi.json (same data files).

Per channel and variable: data/MC vs pT for both selections on one plot, plus a
straight-line fit of data/MC in the fit range (weighted by the expected stat. error,
sqrt(MC + MC var) / MC, so low-count bins that fluctuate down do not get a small
error and pull the line; empty data bins with MC > 0 enter as 0) ->
slope in % per 100 GeV. Ranges for the table as in hists_zbzc_run3/slope_check_run3.txt.

Usage: python compare_zbzc_njet_slope.py Summer22
Output: hists_zbzc_run3_1j/<campaign>/compare_ge1j/{<var>_ratio_ge1j_vs_1j.png, slope_ge1j_vs_1j.txt}
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

camp = sys.argv[1]
RUNS = {"ge1j": ("hists_zbzc_run3_ge1j", r"$N_{jet} \geq 1$", "black"),
        "1j": ("hists_zbzc_run3_1j", r"$N_{jet} = 1$", "#d62728")}
CHANNELS = ["Zee", "Zmm"]
CH_LABEL = {"Zee": r"Z$\to$ee", "Zmm": r"Z$\to\mu\mu$"}
# variable: (x range shown, fit range, table ranges)
VARS = {
    "lep0_pt": ((35, 400), (35, 300), [35, 100, 150, 200, 300, 1000]),
    "lep1_pt": ((25, 300), (25, 200), [25, 50, 100, 150, 200, 500]),
    "z_pt": ((0, 500), (0, 400), [0, 30, 60, 100, 200, 300, 1000]),
    "jet_pt": ((30, 400), (30, 300), [30, 50, 100, 150, 200, 300, 530]),
}
XS = json.load(open("metadata/Zb_Zc_ratio_xsections_run3.json"))
LUMI = json.load(open(f"hists_zbzc_run3/{camp}/lumi.json"))
outdir = os.path.join(RUNS["1j"][0], camp, "compare_ge1j")
os.makedirs(outdir, exist_ok=True)


def load_run(d):
    out = {}
    for f in sorted(glob.glob(f"{d}/{camp}/zbzc_run3/zbzc_run3_*.coffea")):
        out.update(load(f))
    return out


def data_mc(out, var, ch):
    """(edges, data values, MC values, MC variances) for one channel."""
    data = mc = None
    for ds, o in out.items():
        h = o[var][{"channel": ch, "flav": sum, "pflav": sum}]
        if not ds.startswith(("Muon", "EGamma")):
            h = h * (XS[ds] * LUMI[ch] / o["sumw"])
            mc = h if mc is None else mc + h
        elif ds.startswith("Muon" if ch == "Zmm" else "EGamma"):
            data = h if data is None else data + h
    return data.axes[0].edges, data.values(), mc.values(), mc.variances()


def ratio(d, m, mvar):
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where((m > 0) & (d > 0), d / m, np.nan)
        e = r * np.sqrt(1 / d + mvar / m**2)
    return r, e


OUT = {k: load_run(d) for k, (d, _, _) in RUNS.items()}
L = [f"{camp}: data/MC, N_jet >= 1 vs N_jet = 1, 10 GeV pT bins (MC absolute, not normalised)",
     "slope = straight-line fit of data/MC in the fit range, in % per 100 GeV (+- fit error)", ""]
for var, (xr, fr, ranges) in VARS.items():
    fig, axes = plt.subplots(1, 2, figsize=(22, 7.5))
    for ax, ch in zip(axes, CHANNELS):
        for key, (_, label, color) in RUNS.items():
            edges, d, m, mvar = data_mc(OUT[key], var, ch)
            cen = 0.5 * (edges[1:] + edges[:-1])
            r, e = ratio(d, m, mvar)
            # chi2 fit of r = a + b x with the expected (MC-based) error per bin
            with np.errstate(divide="ignore", invalid="ignore"):
                r_fit = np.where(m > 0, d / m, np.nan)
                e_fit = np.sqrt(m + mvar) / m
            sel = (cen > fr[0]) & (cen < fr[1]) & np.isfinite(r_fit) & (e_fit > 0)
            p, cov = np.polyfit(cen[sel], r_fit[sel], 1, w=1 / e_fit[sel], cov="unscaled")
            slope, slope_err = 100 * p[0] * 100, 100 * np.sqrt(cov[0, 0]) * 100
            tot = d.sum() / m.sum()
            ax.errorbar(cen, r, yerr=e, xerr=0.5 * np.diff(edges), fmt="o", ms=4,
                        color=color, label=f"{label}: data/MC {tot:.3f}, slope "
                        f"{slope:+.1f} $\\pm$ {slope_err:.1f} %/100 GeV")
            xx = np.array(fr, dtype=float)
            ax.plot(xx, p[1] + p[0] * xx, color=color, lw=1.5, ls="--")
            cells = []
            for lo, hi in zip(ranges[:-1], ranges[1:]):
                s = (cen > lo) & (cen < hi)
                dd, mm = d[s].sum(), m[s].sum()
                rr = dd / mm if mm > 0 else np.nan
                ee = rr * np.sqrt(1 / dd + mvar[s].sum() / mm**2) if dd > 0 else np.nan
                cells.append(f"{lo}-{hi}: {rr:.3f}+-{ee:.3f}")
            L.append(f"  {var:8s} {ch} {key:4s} total {tot:.3f} | slope {slope:+5.1f} +- "
                     f"{slope_err:.1f} %/100 GeV ({fr[0]}-{fr[1]}) | " + "  ".join(cells))
        ax.axhline(1, color="grey", lw=1)
        ax.set_xlim(*xr)
        ax.set_ylim(0.6, 1.4)
        ax.set_xlabel(OUT["1j"][next(iter(OUT["1j"]))][var].axes[-1].label)
        ax.set_ylabel("data / MC")
        ax.legend(fontsize=13, loc="upper left")
        ax.set_title(CH_LABEL[ch], fontsize=20, loc="center", pad=28)
        hep.cms.label("Preliminary", data=True, lumi=round(LUMI[ch] / 1000, 2), com=13.6,
                      ax=ax, fontsize=13)
    L.append("")
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, f"{var}_ratio_ge1j_vs_1j.png"), dpi=90)
    plt.close(fig)

open(os.path.join(outdir, "slope_ge1j_vs_1j.txt"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
