"""Plots for the MET / jet diagnostic runs (diag_zbzc_met.py) vs the nominal stage run.

For every campaign and variant in hists_zbzc_diag/<campaign>/ (same datasets on both
sides; MC-only variants such as nojer use the nominal data on both sides):
    diag_<variant>_met_eff.png   efficiency of MET < 50 vs Z pT, data and DY MC,
                                 nominal vs variant, and data/DY below
    diag_<variant>_jet_eff.png   same for the >= 1 jet cut
    diag_<variant>_met_pt.png    MET of all Z events (unit area), data/DY below
All Z events = trigger, two leptons, OS, Z mass, before the MET and jet cuts.
Errors: binomial from the raw data counts; MC from the sum of weights squared. MC bins
with < 20 effective events are not drawn (Summer22 has only DY incl. + PTLL-100 rerun).

Usage:  python plot_zbzc_diag.py
Output: hists_zbzc_diag/<campaign>/plots/
"""
import glob
import json
import os

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
VAR_LABEL = {"emef": "no EM jets in type-1 MET", "nojer": "no JER smearing"}
EDGES = [0, 5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100, 125, 150, 200, 300, 1000]
ALL = ["none", "MET", "jet", "MET+jet"]
PASS = {"met": ["MET", "MET+jet"], "jet": ["jet", "MET+jet"]}
CUT_LABEL = {"met": r"$p_T^{miss}$ < 50 GeV", "jet": r"$\geq$1 jet"}
XS = json.load(open("metadata/Zb_Zc_ratio_xsections_run3.json"))


def is_data(ds):
    return ds.startswith(("Muon", "EGamma"))


def rebin(v, e):
    idx = [int(np.where(np.isclose(e, x))[0][0]) for x in EDGES]
    return np.array([v[a:b].sum() for a, b in zip(idx[:-1], idx[1:])])


def collect(files, c, ch):
    """{data, DY}: Z pT sums/variances for all Z and each cut, and the MET histogram."""
    lumi = json.load(open(f"hists_zbzc_run3/{c}/lumi.json"))
    res = {}
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
            h = o["stage_z_pt"][{"channel": ch, "flav": sum, "pflav": sum}]
            e = h.axes[-1].edges
            m = o["stage_met_pt"][{"channel": ch, "flav": sum, "pflav": sum, "stage": sum}]
            r = res.setdefault(key, {})
            for sel, stages in [("all", ALL), *PASS.items()]:
                v = sum(h[{"stage": st}].values() for st in stages)
                w2 = sum(h[{"stage": st}].variances() for st in stages)
                r[sel] = r.get(sel, 0) + rebin(v, e) * s
                r[sel + "_w2"] = r.get(sel + "_w2", 0) + rebin(w2, e) * s * s
            r["metpt"] = r.get("metpt", 0) + m.values() * s
            r["metpt_w2"] = r.get("metpt_w2", 0) + m.variances() * s * s
            r["metpt_edges"] = m.axes[0].edges
    return res


def eff(r, cut):
    """Efficiency and error per Z pT bin (binomial with effective counts)."""
    with np.errstate(divide="ignore", invalid="ignore"):
        p = r[cut] / r["all"]
        neff = r["all"] ** 2 / r["all_w2"]
        return p, np.sqrt(p * (1 - p) / neff)


def label(ax, c):
    hep.cms.label("Preliminary", data=True, ax=ax, fontsize=18, rlabel=f"{ERAS[c]} (13.6 TeV)")


def plot_eff(nom, var, c, v, cut, out):
    fig, axes = plt.subplots(2, 2, figsize=(20, 12), sharex=True,
                             gridspec_kw={"height_ratios": [2, 1], "hspace": 0.05})
    x = 0.5 * (np.array(EDGES[:-1]) + np.array(EDGES[1:]))
    xerr = 0.5 * np.diff(EDGES)
    for col, ch in enumerate(CHANNELS):
        top, bot = axes[0, col], axes[1, col]
        if ch not in nom or "data" not in nom[ch] or "DY" not in nom[ch]:
            top.text(0.5, 0.5, "no data/DY for this channel", transform=top.transAxes, ha="center")
            continue
        styles = [("nominal", nom[ch], "o", "#222222", "#1f77b4"),
                  (VAR_LABEL.get(v, v), var[ch], "s", "#d62728", "#ff7f0e")]
        for i, (lab, r, mk, cd, cm) in enumerate(styles):
            pd, ed = eff(r["data"], cut)
            pm, em = eff(r["DY"], cut)
            ok = r["DY"]["all"] ** 2 / r["DY"]["all_w2"] >= 20  # hide MC bins with < 20 effective events
            shift = (-0.06 if i == 0 else 0.06) * xerr
            top.errorbar(x + shift, pd, yerr=ed, xerr=xerr, fmt=mk, color=cd, ms=7,
                         mfc=cd if i == 0 else "white", label=f"data, {lab}")
            top.stairs(np.where(ok, pm, np.nan), EDGES, color=cm, lw=2, baseline=None,
                       ls="-" if i == 0 else "--", label=f"DY MC, {lab}")
            rr = pd / pm
            re = np.abs(rr) * np.sqrt((ed / pd) ** 2 + (em / pm) ** 2)
            bot.errorbar(x + shift, np.where(ok, rr, np.nan), yerr=re, xerr=xerr, fmt=mk,
                         color=cd, ms=7, mfc=cd if i == 0 else "white", label=lab)
        top.set_ylabel(f"Efficiency of {CUT_LABEL[cut]}")
        top.set_ylim(0, 1.25 if cut == "met" else 1.0)
        top.legend(fontsize=13, loc="lower left" if cut == "met" else "upper left",
                   title=f"{CH_LABEL[ch]}, all Z events", title_fontsize=15, ncol=2)
        label(top, c)
        bot.axhline(1, color="grey", ls="--", lw=1)
        bot.set_ylim(0.5, 1.3)
        bot.set_ylabel("Data / DY")
        bot.set_xlabel(r"$p_T^{\ell\ell}$ [GeV]")
        bot.set_xscale("log")
        bot.set_xlim(1.5, EDGES[-1])
        bot.legend(fontsize=13, loc="lower left")
    fig.savefig(out, dpi=90, bbox_inches="tight")
    plt.close(fig)


def plot_met(nom, var, c, v, out):
    fig, axes = plt.subplots(2, 2, figsize=(20, 12), sharex=True,
                             gridspec_kw={"height_ratios": [2, 1], "hspace": 0.05})
    for col, ch in enumerate(CHANNELS):
        top, bot = axes[0, col], axes[1, col]
        if ch not in nom or "data" not in nom[ch] or "DY" not in nom[ch]:
            continue
        e = nom[ch]["DY"]["metpt_edges"]
        x = 0.5 * (e[1:] + e[:-1])
        for i, (lab, r, cd, cm) in enumerate([("nominal", nom[ch], "#222222", "#1f77b4"),
                                              (VAR_LABEL.get(v, v), var[ch], "#d62728", "#ff7f0e")]):
            d, m = r["data"]["metpt"], r["DY"]["metpt"]
            dn, mn = d / d.sum(), m / m.sum()
            de, me = np.sqrt(d) / d.sum(), np.sqrt(r["DY"]["metpt_w2"]) / abs(m.sum())
            top.errorbar(x, dn, yerr=de, fmt="o" if i == 0 else "s", color=cd, ms=6,
                         mfc=cd if i == 0 else "white", label=f"data, {lab}")
            top.stairs(mn, e, color=cm, lw=2, ls="-" if i == 0 else "--", label=f"DY MC, {lab}")
            with np.errstate(divide="ignore", invalid="ignore"):
                rr = dn / mn
                re = np.abs(rr) * np.sqrt((de / dn) ** 2 + (me / mn) ** 2)
            bot.errorbar(x, rr, yerr=re, fmt="o" if i == 0 else "s", color=cd, ms=6,
                         mfc=cd if i == 0 else "white", label=lab)
        top.axvline(50, color="grey", ls=":", lw=1.5)
        top.set_yscale("log")
        top.set_ylabel("Fraction of Z events")
        top.legend(fontsize=13, loc="upper right", title=f"{CH_LABEL[ch]}, all Z events",
                   title_fontsize=15)
        label(top, c)
        bot.axhline(1, color="grey", ls="--", lw=1)
        bot.axvline(50, color="grey", ls=":", lw=1.5)
        bot.set_ylim(0.3, 2.0)
        bot.set_ylabel("Data / DY")
        bot.set_xlabel(r"PUPPI $p_T^{miss}$ [GeV]")
        bot.legend(fontsize=13, loc="upper left")
    fig.savefig(out, dpi=90, bbox_inches="tight")
    plt.close(fig)


for cdir in sorted(glob.glob("hists_zbzc_diag/*/")):
    c = os.path.basename(cdir.rstrip("/"))
    plotdir = os.path.join(cdir, "plots")
    os.makedirs(plotdir, exist_ok=True)
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
        nom = {ch: collect(nfiles, c, ch) for ch in CHANNELS}
        var = {ch: collect(vfiles, c, ch) for ch in CHANNELS}
        for cut in PASS:
            plot_eff(nom, var, c, v, cut, f"{plotdir}/diag_{v}_{cut}_eff.png")
        plot_met(nom, var, c, v, f"{plotdir}/diag_{v}_met_pt.png")
        print("wrote", plotdir, v)
