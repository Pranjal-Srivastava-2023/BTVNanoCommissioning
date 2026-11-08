"""Zmm muon-selection study (advisor, 2026-11-08: "small discrepancy in the muon channel: trigger
turn-on, eta cut, SFs, corrections, Rochester ...?").

Reads the muvar_* histograms of a Zb_Zc_ratio run with mu_variants=True (MU_VARIANTS in
workflows/Zb_Zc_ratio.py; each variant changes ONE thing w.r.t. the nominal):

    nominal    trigger SF from both muons (MUO IsoMu24 data/MC efficiencies), both muons pT > 26,
               leading > 35, |eta| < 2.4, muon scale/smearing, ID + iso + pileup SFs
    prev       the analysis until 2026-11-08: leading-muon-only trigger SF, muon pT > 25
    trigLead   leading-muon-only trigger SF
    sub25      muon pT > 25 (instead of 26)
    lead26     leading muon pT > 26 (instead of 35)
    eta21      both muons |eta| < 2.1
    trigMatch  leading muon matched to an IsoMu24 trigger object, its SF only (another POG-valid way)
    noSS       no muon scale/smearing correction (Run 3 replacement of Rochester), data and MC
    noTrigSF / noIDIsoSF / noPU   that weight switched off (MC)

at stage "Z" (trigger, 2 muons, OS, 71 < m < 111; no MET / jet cut) and "final" (+ MET < 50,
>= 1 jet). MC = DY + tt + VV scaled by xsec * lumi(Zmm) / sumw; data = Muon PDs.

Table per variant and stage: data, MC, data/MC (stat. error of data and MC), change w.r.t. the
nominal, and the slope of data/MC vs pT(mumu) and vs leading-muon pT (straight-line fit weighted
by the expected error sqrt(MC + MC var) / MC, as in compare_zbzc_njet_slope.py), in % per 100 GeV.
The variants share most events, so differences between variants are much more precise than the
quoted errors of each one.

Usage: python compare_zbzc_muvar.py [run dir, default hists_zbzc_run3_v2/Summer22]
Output: <run dir>/muvar/muvar_table.txt, muvar_<var>_<stage>.png
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

rundir = sys.argv[1] if len(sys.argv) > 1 else "hists_zbzc_run3_v2/Summer22"
camp = os.path.basename(os.path.normpath(rundir))
XS = json.load(open("metadata/Zb_Zc_ratio_xsections_run3.json"))
lumi_file = os.path.join(rundir, "lumi.json")
if not os.path.exists(lumi_file):
    lumi_file = f"hists_zbzc_run3/{camp}/lumi.json"
LUMI = json.load(open(lumi_file))["Zmm"]
outdir = os.path.join(rundir, "muvar")
os.makedirs(outdir, exist_ok=True)

OUT = {}
for f in sorted(glob.glob(f"{rundir}/zbzc_run3/zbzc_run3_*.coffea")):
    OUT.update(load(f))
VARIANTS = list(next(iter(OUT.values()))["muvar_z_pt"].axes["variant"])
STAGES = ["Z", "final"]
DESC = {
    "nominal": "trig SF both muons, pT > 26",
    "prev": "until 11-08: lead-muon trig SF, pT > 25",
    "trigLead": "leading-muon-only trigger SF",
    "sub25": "muon pT > 25",
    "lead26": "leading muon pT > 26 (not 35)",
    "eta21": "|eta| < 2.1",
    "trigMatch": "lead muon matched to IsoMu24, its SF",
    "noSS": "no muon scale/smearing",
    "noTrigSF": "no trigger SF",
    "noIDIsoSF": "no ID + iso SF",
    "noPU": "no pileup weight",
}


def data_mc(var, variant, stage):
    data = mc = None
    for ds, o in OUT.items():
        h = o[var][{"variant": variant, "stage": stage}]
        if ds.startswith("EGamma"):
            continue
        if ds.startswith("Muon"):
            data = h if data is None else data + h
        else:
            h = h * (XS[ds] * LUMI / o["sumw"])
            mc = h if mc is None else mc + h
    return data.axes[0].edges, data.values(flow=True)[1:-1], mc.values(flow=True)[1:-1], \
        mc.variances(flow=True)[1:-1], data.sum(flow=True).value, mc.sum(flow=True)


def slope(edges, d, m, mvar, fr):
    cen = 0.5 * (edges[1:] + edges[:-1])
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(m > 0, d / m, np.nan)
        e = np.sqrt(m + mvar) / m
    sel = (cen > fr[0]) & (cen < fr[1]) & np.isfinite(r) & (e > 0)
    p, cov = np.polyfit(cen[sel], r[sel], 1, w=1 / e[sel], cov="unscaled")
    return 1e4 * p[0], 1e4 * np.sqrt(cov[0, 0])


FITS = {"muvar_z_pt": (0, 400), "muvar_lep0_pt": (35, 300)}
L = [f"{camp} Zmm muon-selection variants (20 files per sample; lumi {LUMI:.1f}/pb; MC absolute)",
     "data/MC error = data + MC stat. (variants share events: differences are more precise)",
     "slopes: straight-line fit of data/MC, % per 100 GeV, pT(mumu) 0-400, leading-muon pT 35-300", ""]
summary = {}
for stage in STAGES:
    L.append(f"== stage {stage}" + (" (trigger, 2 muons, OS, Z mass)" if stage == "Z" else " (+ MET < 50, >= 1 jet)"))
    L.append(f"{'variant':10s} {'what':42s} {'data':>9s} {'MC':>11s} {'data/MC':>15s} {'vs nom':>8s}"
             f" {'slope pT(mumu)':>16s} {'slope lead pT':>16s}")
    nom = None
    for v in VARIANTS:
        _, _, _, _, dtot, mtot = data_mc("muvar_z_pt", v, stage)
        r = dtot / mtot.value
        err = r * np.hypot(1 / np.sqrt(dtot), np.sqrt(mtot.variance) / mtot.value)
        if v == "nominal":
            nom = r
        sl = {k: slope(*data_mc(k, v, stage)[:4], fr) for k, fr in FITS.items()}
        summary[(v, stage)] = (r, err, sl)
        L.append(f"{v:10s} {DESC.get(v, ''):42s} {dtot:9.0f} {mtot.value:11.1f} {r:8.4f}+-{err:.4f}"
                 f" {100 * (r / nom - 1):+7.2f}%"
                 + "".join(f" {s:+7.2f}+-{se:5.2f}  " for s, se in sl.values()))
    L.append("")

# data/MC per |eta| region of the leading muon; boundaries on the 0.2-wide bin edges
# (closest to the muon barrel / overlap / endcap / outer-endcap boundaries 0.9, 1.2, 2.1)
regions = [(0, 0.8), (0.8, 1.2), (1.2, 2.0), (2.0, 2.4)]
L.append("== data/MC per leading-muon |eta| region")
for stage in STAGES:
    L.append(f"-- stage {stage}")
    L.append(f"{'variant':10s}" + "".join(f"{f'{a}-{b}':>16s}" for a, b in regions))
    for v in VARIANTS:
        edges, d, m, mvar, _, _ = data_mc("muvar_lep0_eta", v, stage)
        cen = 0.5 * (edges[1:] + edges[:-1])
        cells = ""
        for a, b in regions:
            s = (abs(cen) > a) & (abs(cen) < b)
            dd, mm = d[s].sum(), m[s].sum()
            rr = dd / mm
            ee = rr * np.hypot(1 / np.sqrt(dd), np.sqrt(mvar[s].sum()) / mm)
            cells += f"{rr:9.3f}+-{ee:.3f}"
        L.append(f"{v:10s}{cells}")
    L.append("")

open(os.path.join(outdir, "muvar_table.txt"), "w").write("\n".join(L) + "\n")
print("\n".join(L))

# data/MC vs variable for selected variants
SHOW = {"prev": "black", "nominal": "#d62728", "trigMatch": "#1f77b4", "lead26": "#2ca02c",
        "eta21": "#9467bd", "noSS": "#ff7f0e"}
XR = {"muvar_z_pt": (0, 400), "muvar_lep0_pt": (26, 300), "muvar_lep1_pt": (25, 200),
      "muvar_lep0_eta": (-2.4, 2.4), "muvar_lep1_eta": (-2.4, 2.4), "muvar_z_mass": (71, 111),
      "muvar_n_jet": (0, 6)}
for var, xr in XR.items():
    for stage in STAGES:
        fig, ax = plt.subplots(figsize=(13, 8))
        for i, (v, col) in enumerate(SHOW.items()):
            if v not in VARIANTS:
                continue
            edges, d, m, mvar, dtot, mtot = data_mc(var, v, stage)
            cen = 0.5 * (edges[1:] + edges[:-1])
            w = np.diff(edges)
            with np.errstate(divide="ignore", invalid="ignore"):
                r = np.where((m > 0) & (d > 0), d / m, np.nan)
                e = r * np.sqrt(1 / d + mvar / m**2)
            # small x offsets so the error bars do not hide each other
            ax.errorbar(cen + (i - 2.5) * 0.04 * w, r, yerr=e, fmt="o", ms=4, color=col,
                        label=f"{v}: {DESC[v]} ({dtot / mtot.value:.3f})")
        ax.axhline(1, color="grey", lw=1)
        ax.set_xlim(*xr)
        ax.set_ylim(0.7, 1.3)
        ax.set_xlabel(OUT[next(iter(OUT))][var].axes[-1].label)
        ax.set_ylabel("data / MC")
        ax.legend(fontsize=12, loc="upper left", ncol=2)
        ax.text(0.98, 0.04, f"Z$\\to\\mu\\mu$, stage {stage}", transform=ax.transAxes, ha="right", fontsize=16)
        hep.cms.label("Preliminary", data=True, lumi=round(LUMI / 1000, 2), com=13.6, ax=ax, fontsize=14)
        fig.tight_layout()
        fig.savefig(os.path.join(outdir, f"{var.replace('muvar_', '')}_{stage}.png"), dpi=90)
        plt.close(fig)
print("plots in", outdir)
