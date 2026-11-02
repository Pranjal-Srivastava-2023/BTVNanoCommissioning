"""Lepton eta-phi data/MC maps in 10 x 10 bins, split by AK4 jet multiplicity
(advisor's check: is the hot region in the electron eta-phi map still there in
the Z + 1 jet sub-sample?).

Reads lep_eta_phi_nj (both Z leptons per event) from a run_zbzc_run3.sh output
(ZBZC_RUN=zbzc_run3_ge1j -> hists_zbzc_run3_ge1j/<campaign>/zbzc_run3/) and the
lumi of hists_zbzc_run3/<campaign>/lumi.json (same data files). MC = DY + tt + VV,
scaled by xsec * lumi / sumw.

Per jet selection (>= 1, = 1, = 2, >= 3):
  lep_eta_phi_10x10_ratio_<sel>.png  data/MC per cell, MC normalised to data in
                                    each map (cell text: ratio and its stat. error)
  lep_eta_phi_10x10_pull_<sel>.png   (ratio - 1) / error per cell
  lep_eta_phi_10x10_occupancy_<ch>.png  data and MC entries, >= 1 jet
  etaphi_nj_summary.txt  yields, data/MC per selection, chi2 of each map vs flat,
                         cells more than 3 sigma off

Usage: python plot_zbzc_etaphi_nj.py Summer22 [run_dir]
"""
import glob
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplhep as hep
import hist
import numpy as np
from coffea.util import load

hep.style.use("CMS")

CHANNELS = ["Zee", "Zmm"]
CH_LABEL = {"Zee": r"Z$\to$ee", "Zmm": r"Z$\to\mu\mu$"}
SEL_LABEL = {"ge1": r"$N_{jet} \geq 1$", "eq1": r"$N_{jet} = 1$",
             "eq2": r"$N_{jet} = 2$", "ge3": r"$N_{jet} \geq 3$"}
XS = json.load(open("metadata/Zb_Zc_ratio_xsections_run3.json"))

camp = sys.argv[1]
rundir = sys.argv[2] if len(sys.argv) > 2 else "hists_zbzc_run3_ge1j"
outdir = os.path.join(rundir, camp)
plotdir = os.path.join(outdir, "plots")
os.makedirs(plotdir, exist_ok=True)

OUT = {}
for f in sorted(glob.glob(os.path.join(outdir, "zbzc_run3", "zbzc_run3_*.coffea"))):
    OUT.update(load(f))
LUMI = json.load(open(f"hists_zbzc_run3/{camp}/lumi.json"))


def is_mc(ds):
    return not ds.startswith(("Muon", "EGamma"))


def maps(ch):
    """{sel: (data hist, MC hist)} over (eta, phi) for one channel."""
    data = mc = None
    for ds, o in OUT.items():
        h = o["lep_eta_phi_nj"][{"channel": ch, "flav": sum, "pflav": sum}]
        if is_mc(ds):
            h = h * (XS[ds] * LUMI[ch] / o["sumw"])
            mc = h if mc is None else mc + h
        elif ds.startswith("Muon" if ch == "Zmm" else "EGamma"):
            data = h if data is None else data + h
    out = {}
    for name, h in (("data", data), ("mc", mc)):
        # nj bins: 1, 2 and the overflow (>= 3); sum includes the overflow
        out[name] = {"ge1": h[{"nj": sum}], "eq1": h[{"nj": 0}], "eq2": h[{"nj": 1}],
                     "ge3": h[{"nj": hist.overflow}]}
    return {s: (out["data"][s], out["mc"][s]) for s in SEL_LABEL}


def ratio(d, m):
    """data / (MC normalised to data) per cell, its stat. error, and the normalisation."""
    dv, mv, mvar = d.values(), m.values(), m.variances()
    norm = dv.sum() / mv.sum()
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(mv > 0, dv / (mv * norm), np.nan)
        err = r * np.sqrt(np.where(dv > 0, 1 / dv, np.nan) + mvar / mv**2)
    return r, err, norm


def draw(fig, ax, edges, z, text, cmap, vmin, vmax, label, title, fontsize=8):
    im = ax.pcolormesh(edges[0], edges[1], z.T, cmap=cmap, vmin=vmin, vmax=vmax)
    fig.colorbar(im, ax=ax, label=label)
    cx = 0.5 * (edges[0][1:] + edges[0][:-1])
    cy = 0.5 * (edges[1][1:] + edges[1][:-1])
    for i, x in enumerate(cx):
        for j, y in enumerate(cy):
            ax.text(x, y, text(i, j), ha="center", va="center", fontsize=fontsize)
    ax.set_xlabel(r"Lepton $\eta$")
    ax.set_ylabel(r"Lepton $\phi$")
    ax.set_title(title, fontsize=17, loc="center", pad=28)


M = {ch: maps(ch) for ch in CHANNELS}
edges = [ax.edges for ax in M["Zee"]["ge1"][0].axes]
L = [f"Lepton eta-phi, 10 x 10 bins, {camp}, split by N AK4 jets ({rundir})",
     "Each event enters twice (both Z leptons). data/MC per cell with MC normalised",
     "to data in each map; error = data + MC stat.", ""]

for sel, slabel in SEL_LABEL.items():
    fig, axes = plt.subplots(1, 2, figsize=(24, 9))
    figp, axesp = plt.subplots(1, 2, figsize=(24, 9))
    for ax, axp, ch in zip(axes, axesp, CHANNELS):
        d, m = M[ch][sel]
        r, err, norm = ratio(d, m)
        pull = (r - 1) / err
        ok = np.isfinite(pull)
        chi2, ndf = float(np.sum(pull[ok] ** 2)), int(ok.sum()) - 1
        title = f"{CH_LABEL[ch]}, {slabel}  (overall data/MC {1 / norm:.3f})"
        draw(fig, ax, edges, r, lambda i, j: f"{r[i, j]:.2f}\n$\\pm${err[i, j]:.2f}",
             "RdBu_r", 0.8, 1.2, "data / MC (MC normalised to data)", title)
        draw(figp, axp, edges, pull, lambda i, j: f"{pull[i, j]:.1f}",
             "RdBu_r", -4, 4, "(data/MC - 1) / stat. error", title, fontsize=10)
        hep.cms.label("Preliminary", data=True, lumi=round(LUMI[ch] / 1000, 2), com=13.6,
                      ax=ax, fontsize=13)
        hep.cms.label("Preliminary", data=True, lumi=round(LUMI[ch] / 1000, 2), com=13.6,
                      ax=axp, fontsize=13)
        L.append(f"{ch} {sel}: data {d.values().sum():.0f} lepton entries, MC "
                 f"{m.values().sum():.1f}, data/MC {1 / norm:.3f}; map vs flat "
                 f"chi2/ndf = {chi2:.1f}/{ndf}")
        for i, j in sorted(zip(*np.where(ok & (abs(pull) > 3))), key=lambda ij: -abs(pull[ij])):
            L.append(f"    cell eta [{edges[0][i]:+.1f},{edges[0][i + 1]:+.1f}] phi "
                     f"[{edges[1][j]:+.2f},{edges[1][j + 1]:+.2f}]: ratio {r[i, j]:.3f} "
                     f"+- {err[i, j]:.3f} ({pull[i, j]:+.1f} sigma), data {d.values()[i, j]:.0f}")
    L.append("")
    for f, name in ((fig, "ratio"), (figp, "pull")):
        f.tight_layout()
        f.savefig(os.path.join(plotdir, f"lep_eta_phi_10x10_{name}_{sel}.png"), dpi=90)
        plt.close(f)

# raw occupancy, >= 1 jet: is the hot region a data excess or an MC deficit?
for ch in CHANNELS:
    d, m = M[ch]["ge1"]
    mv = m.values() * d.values().sum() / m.values().sum()
    fig, axes = plt.subplots(1, 2, figsize=(24, 9))
    vmax = max(d.values().max(), mv.max())
    for ax, z, what in ((axes[0], d.values(), "data"), (axes[1], mv, "MC (normalised to data)")):
        draw(fig, ax, edges, z, lambda i, j: f"{z[i, j]:.0f}", "viridis", 0, vmax,
             "lepton entries", f"{CH_LABEL[ch]}, $N_{{jet}} \\geq 1$: {what}", fontsize=9)
        hep.cms.label("Preliminary", data=True, lumi=round(LUMI[ch] / 1000, 2), com=13.6,
                      ax=ax, fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(plotdir, f"lep_eta_phi_10x10_occupancy_{ch}.png"), dpi=90)
    plt.close(fig)

open(os.path.join(outdir, "etaphi_nj_summary.txt"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
