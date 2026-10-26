"""Data/MC plots, cutflow and yield tables for the Zb_Zc_ratio Run 3 run (AK4).

Reads the per-dataset outputs in hists_zbzc_run3/<campaign>/ (run_zbzc_run3.sh) and
the processed lumi per channel (zbzc_lumi.py -> lumi.json). Each MC sample is scaled
by xsec * lumi[channel] / sumw (metadata/Zb_Zc_ratio_xsections_run3.json); data in
each channel come from its own PD only (Zmm: Muon/Muon0, Zee: EGamma/EGamma0).

Stack: DY split by leading-jet flavour (hadronFlavour b/c/light; *_parton.png:
partonFlavour), ttbar (TTto2L2Nu) and VV (WW+WZ+ZZ), smallest component at the
bottom of the log stack; hatched band = MC stat. uncertainty; lower panel data/MC.
N_jet >= 5 is merged into one bin. "all" sums the four campaigns.

Usage:
    python plot_zbzc_run3.py Summer22      # one campaign
    python plot_zbzc_run3.py all           # all four, summed
Output: hists_zbzc_run3/<campaign|all>/plots/*.png and yields.txt
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
ERAS = {"Summer22": "2022 C-D", "Summer22EE": "2022 E-G", "Summer23": "2023 C",
        "Summer23BPix": "2023 D", "all": "2022 + 2023"}
CHANNELS = ["Zee", "Zmm"]
CH_LABEL = {"Zee": r"Z$\to$ee", "Zmm": r"Z$\to\mu\mu$"}
XS = json.load(open("metadata/Zb_Zc_ratio_xsections_run3.json"))

which = sys.argv[1]
camps = CAMPAIGNS if which == "all" else [which]
outdir = f"hists_zbzc_run3/{which}"
plotdir = os.path.join(outdir, "plots")
os.makedirs(plotdir, exist_ok=True)

# per campaign: {dataset: output}, {channel: lumi in /pb}
OUT, LUMI = {}, {}
for c in camps:
    OUT[c] = {}
    for f in sorted(glob.glob(f"hists_zbzc_run3/{c}/zbzc_run3_*.coffea")):
        OUT[c].update(load(f))
    LUMI[c] = json.load(open(f"hists_zbzc_run3/{c}/lumi.json"))
LUMI_TOT = {ch: sum(LUMI[c][ch] for c in camps) for ch in CHANNELS}


def kind(ds):
    """Process group of a dataset."""
    if ds.startswith("DYto2L"):
        return "DY"
    if ds.startswith("TTto2L2Nu"):
        return "tt"
    if ds.split("_")[0] in ("WW", "WZ", "ZZ"):
        return "VV"
    if ds.startswith("Muon"):
        return "data_Zmm"
    if ds.startswith("EGamma"):
        return "data_Zee"
    raise KeyError(ds)


def scale(c, ds, ch):
    return XS[ds] * LUMI[c][ch] / OUT[c][ds]["sumw"]


HADRON = {"axis": "flav", "dy": ["l", "c", "b"],
          "label": {"l": "DY + light", "c": "DY + c", "b": "DY + b"},
          "color": {"l": "#9e9e9e", "c": "#7fb3e6", "b": "#f2a65a"}}
PARTON = {"axis": "pflav", "dy": ["none", "g", "uds", "c", "b"],
          "label": {"none": "DY + no parton", "g": "DY + g", "uds": "DY + uds",
                    "c": "DY + c (parton)", "b": "DY + b (parton)"},
          "color": {"none": "#d9d9d9", "g": "#6aa84f", "uds": "#9e9e9e",
                    "c": "#7fb3e6", "b": "#f2a65a"}}
BKG = {"tt": ("$t\\bar{t}$ (2L2Nu)", "#8e44ad"), "VV": ("VV (WW, WZ, ZZ)", "#16a085")}


def components(var, ch, flav):
    """{component: hist over the variable axes} for one channel: DY per flavour
    (flav = HADRON or PARTON), tt, VV (scaled MC) and data."""
    comp = {}

    def add(key, h):
        comp[key] = h if key not in comp else comp[key] + h

    other = "pflav" if flav["axis"] == "flav" else "flav"
    for c in camps:
        for ds, o in OUT[c].items():
            k = kind(ds)
            h = o[var][{"channel": ch}]
            if k == "DY":
                h = h[{other: sum}] * scale(c, ds, ch)
                for f in flav["dy"]:
                    add(f, h[{flav["axis"]: f}])
            elif k in BKG:
                add(k, h[{"flav": sum, "pflav": sum}] * scale(c, ds, ch))
            elif k == f"data_{ch}":
                add("data", h[{"flav": sum, "pflav": sum}])
    # empty histogram for any component without a sample (e.g. a partial run)
    zero = next(iter(comp.values())) * 0
    for k in flav["dy"] + list(BKG) + ["data"]:
        comp.setdefault(k, zero)
    return comp


def arrays(h, var):
    """values, variances, edges; N_jet >= 5 merged into the last bin."""
    v, w2, e = h.values(), h.variances(), h.axes[0].edges
    if var == "n_jet":
        v = np.append(v[:5], v[5:].sum())
        w2 = np.append(w2[:5], w2[5:].sum())
        e = e[:7]
    return v, w2, e


def cms_label(ax, ch=None, fontsize=18):
    lumi = LUMI_TOT[ch] if ch else sum(LUMI_TOT.values()) / 2
    hep.cms.label("Preliminary", data=True, lumi=round(lumi / 1000, 2), com=13.6,
                  ax=ax, fontsize=fontsize)


def stack(var, flav, suffix=""):
    fig, axes = plt.subplots(2, 2, figsize=(20, 10.5), sharex="col",
                             gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05})
    for ax, rax, ch in zip(axes[0], axes[1], CHANNELS):
        comp = components(var, ch, flav)
        mc = [k for k in list(BKG) + flav["dy"] if k in comp]
        mc = sorted(mc, key=lambda k: comp[k].values().sum())  # smallest at the bottom
        vals = [arrays(comp[k], var) for k in mc]
        edges = vals[0][2]
        tot = sum(v for v, _, _ in vals)
        totvar = sum(w for _, w, _ in vals)
        hep.histplot([v for v, _, _ in vals], edges, ax=ax, stack=True, histtype="fill",
                     color=[flav["color"].get(k, BKG.get(k, ("", ""))[1]) for k in mc],
                     label=[flav["label"].get(k, BKG.get(k, ("", ""))[0]) for k in mc])
        err = np.sqrt(totvar)
        ax.stairs(tot + err, edges, baseline=tot - err, fill=True, hatch="////",
                  facecolor="none", edgecolor="#555555", lw=0, label="MC stat. unc.")
        has_data = "data" in comp and var != "lhe_vpt"
        if has_data:
            d, _, _ = arrays(comp["data"], var)
            hep.histplot(d, edges, ax=ax, histtype="errorbar", color="black",
                         yerr=np.sqrt(d), label="Data")
        ax.set_ylabel("Events / bin")
        top = max(tot.max(), d.max() if has_data else 0, 1.0)
        if var == "z_mass":
            ax.set_ylim(0, top * 1.5)
        else:
            ax.set_yscale("log")
            ax.set_ylim(0.1, top * 80)
        ax.text(0.04, 0.94, CH_LABEL[ch], transform=ax.transAxes, fontsize=20, va="top")
        hdl, lab = ax.get_legend_handles_labels()
        ax.legend(hdl[::-1], lab[::-1], fontsize=13, loc="upper right", ncol=2)
        cms_label(ax, ch)
        xlabel = comp[mc[0]].axes[0].label
        ax.set_xlabel("")
        # data / MC, MC stat. band around 1
        with np.errstate(divide="ignore", invalid="ignore"):
            rel = np.where(tot > 0, err / tot, 0)
            rax.stairs(1 + rel, edges, baseline=1 - rel, fill=True, hatch="////",
                       facecolor="none", edgecolor="#555555", lw=0)
            if has_data:
                ratio = np.where(tot > 0, d / tot, np.nan)
                rerr = np.where(tot > 0, np.sqrt(d) / tot, np.nan)
                hep.histplot(ratio, edges, ax=rax, histtype="errorbar", color="black", yerr=rerr)
        rax.axhline(1, color="black", lw=1, ls="--")
        rax.set_ylim(0.5, 1.5)
        rax.set_ylabel("Data / MC", fontsize=20)
        if var == "n_jet":
            rax.set_xticks(np.arange(6) + 0.5, ["0", "1", "2", "3", "4", "≥5"])
        rax.set_xlabel(xlabel)
    fig.subplots_adjust(left=0.07, right=0.985, top=0.94, bottom=0.11, wspace=0.2)
    fig.savefig(os.path.join(plotdir, f"{var}{suffix}.png"), dpi=90)
    plt.close(fig)


VARS = ["z_mass", "z_pt", "lep0_pt", "lep1_pt", "jet_pt", "jet_eta", "jet_PNetB",
        "jet_PNetCvL", "jet_PNetCvB", "n_jet", "lhe_vpt"]
for var in VARS:
    stack(var, HADRON)
    stack(var, PARTON, "_parton")

# PNet CvL vs CvB per DY flavour and data, both channels summed, unit-normalized
fig, axes = plt.subplots(1, 4, figsize=(34, 8))
groups = {"DY + b": "b", "DY + c": "c", "DY + light": "l", "Data": "data"}
c2d = {ch: components("jet_CvL_CvB", ch, HADRON) for ch in CHANNELS}
for ax, (title, key) in zip(axes, groups.items()):
    hh = c2d["Zee"][key] + c2d["Zmm"][key]
    vals = hh.values()
    vals = vals / vals.sum() if vals.sum() > 0 else vals
    m = ax.pcolormesh(hh.axes[0].edges, hh.axes[1].edges, np.clip(vals.T, 1e-5, None),
                      norm=matplotlib.colors.LogNorm(1e-4, 1), cmap="viridis")
    fig.colorbar(m, ax=ax, label="fraction of jets")
    ax.set_xlabel("PNet CvL")
    ax.set_ylabel("PNet CvB")
    ax.text(0.04, 0.94, title, transform=ax.transAxes, fontsize=20, va="top", color="white")
    cms_label(ax, fontsize=13)
fig.tight_layout()
fig.savefig(os.path.join(plotdir, "jet_CvL_CvB.png"), dpi=90)
plt.close(fig)

# ---------------------------------------------------------------- tables
L = [f"Zb_Zc_ratio Run 3, AK4, {which} ({ERAS[which]}), 13.6 TeV, 20 files per MC sample "
     "and per data channel", ""]
L.append("== processed lumi [/pb] (brilcalc on the golden-JSON lumisections seen; 2023 x0.5 for the half PDs)")
L.append(f"{'campaign':14s}{'Zee':>10s}{'Zmm':>10s}")
for c in camps:
    L.append(f"{c:14s}{LUMI[c]['Zee']:10.2f}{LUMI[c]['Zmm']:10.2f}")
if len(camps) > 1:
    L.append(f"{'total':14s}{LUMI_TOT['Zee']:10.2f}{LUMI_TOT['Zmm']:10.2f}")
L.append("")

for c in camps:
    for ch in CHANNELS:
        steps = list(next(iter(OUT[c].values()))["cutflow_raw"][ch].keys())
        L.append(f"== {c} {ch}: raw events passing each step")
        L.append(f"{'dataset':22s}" + "".join(f"{s:>12s}" for s in steps))
        for ds, o in OUT[c].items():
            k = kind(ds)
            if k.startswith("data") and k != f"data_{ch}":
                continue
            short = ds.split("_TuneCP5")[0].replace("DYto2L-2Jets_MLL-50", "DY").replace("DY_", "DY")
            L.append(f"{short:22s}" + "".join(f"{o['cutflow_raw'][ch][s]:>12d}" for s in steps))
        L.append(f"-- {c} {ch}: MC sum(genWeight) scaled to lumi (no SFs) vs data, per step "
                 "(data PD is trigger-selected: data/MC means something from 'trigger' on)")
        mc = np.zeros(len(steps))
        dat = np.zeros(len(steps))
        for ds, o in OUT[c].items():
            k = kind(ds)
            if k in ("DY", "tt", "VV"):
                mc += np.array([o["cutflow"][ch][s] for s in steps]) * scale(c, ds, ch)
            elif k == f"data_{ch}":
                dat += np.array([o["cutflow_raw"][ch][s] for s in steps])
        L.append(f"{'MC':22s}" + "".join(f"{v:12.0f}" for v in mc))
        L.append(f"{'data':22s}" + "".join(f"{v:12.0f}" for v in dat))
        with np.errstate(divide="ignore", invalid="ignore"):
            L.append(f"{'data/MC':22s}" + "".join(f"{v:12.3f}" for v in dat / mc))
        L.append("")


def yield_table(flav, title):
    L.append(f"== {title}: yields after full selection (MC with all weights)")
    keys = flav["dy"] + list(BKG)
    L.append(f"{'':6s}" + "".join(f"{k:>10s}" for k in keys)
             + f"{'MC':>10s}{'data':>10s}{'data/MC':>10s}")
    for ch in CHANNELS:
        comp = components("jet_pt", ch, flav)
        y = [comp[k].sum(flow=True).value for k in keys]
        e2 = [comp[k].sum(flow=True).variance for k in keys]
        d = comp["data"].sum(flow=True).value if "data" in comp else 0
        mc = sum(y)
        L.append(f"{ch:6s}" + "".join(f"{v:10.1f}" for v in y)
                 + f"{mc:10.1f}{d:10.0f}{d / mc:10.3f}")
        L.append(f"{'  +-':6s}" + "".join(f"{np.sqrt(v):10.1f}" for v in e2)
                 + f"{np.sqrt(sum(e2)):10.1f}{np.sqrt(d):10.0f}"
                 + f"{d / mc * np.hypot(np.sqrt(d) / max(d, 1), np.sqrt(sum(e2)) / mc):10.3f}")
        if flav is HADRON:
            yb, yc = y[keys.index("b")], y[keys.index("c")]
            dy = sum(y[: len(flav["dy"])])
            L.append(f"{'  DY':6s} b frac {yb / dy:.3f}   c frac {yc / dy:.3f}   c/b {yc / yb:.2f}")
    L.append("")


yield_table(HADRON, "hadronFlavour")
yield_table(PARTON, "partonFlavour")
open(os.path.join(outdir, "yields.txt"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
print("plots in", plotdir)
