"""Z->mumu cut study (2026-11-15): one selection cut changed at a time, effect on data/MC and on
the data/MC slope versus pT; plus Delta phi(MET, X) for the MET > 50 GeV data/MC deficit.

Reads the muvar_* histograms (MU_VARIANTS in workflows/Zb_Zc_ratio.py, Zmm only, axes variant x
stage) and dphi_met / stage_dphi_met of a Zb_Zc_ratio run. Each cut variant differs from the
nominal in ONE cut; values stay inside the POG SF ranges. Electron cuts are not changed.

MC = DY + tt + VV, each scaled by xsec * lumi(Zmm) / sumw; data = Muon PDs (Zmm) / EGamma (Zee).

Output in <run dir>/cutvar/:
  cutvar_table.txt / .json   per variant and stage: data, MC, data/MC, change w.r.t. nominal,
                             chi2/ndf and slope of data/MC vs pT(mumu), leading-muon pT, jet pT
  var_<variant>_<var>.png    nominal (left) and variant (right), stack + data/MC, statistics box
  ovl_<group>_<var>.png      data/MC of the nominal and the variants of one cut group
  dphi_<obj>.png             Delta phi(MET, obj), every cut except MET, per MET bin, Zee | Zmm
  stage_dphi_<obj>.png       Delta phi(MET, Z / any-eta jet) for Z events with 0 jets / >= 1 jet

Statistics box: data and MC yields, data/MC (stat.), mean and RMS of data and MC, chi2/ndf of
data vs MC (data + MC stat. errors) and, for pT variables, the slope of a straight-line fit to
data/MC (weighted by the expected error sqrt(MC + MC var)/MC) in % per 100 GeV.

Usage: python plot_zbzc_cutvar.py [run dir, default hists_zbzc_run3_cutvar/Summer22]
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

rundir = sys.argv[1] if len(sys.argv) > 1 else "hists_zbzc_run3_cutvar/Summer22"
camp = os.path.basename(os.path.normpath(rundir))
XS = json.load(open("metadata/Zb_Zc_ratio_xsections_run3.json"))
lumi_file = os.path.join(rundir, "lumi.json")
if not os.path.exists(lumi_file):
    lumi_file = f"hists_zbzc_run3/{camp}/lumi.json"
LUMIS = json.load(open(lumi_file))
outdir = os.path.join(rundir, "cutvar")
os.makedirs(outdir, exist_ok=True)

OUT = {}
for f in sorted(glob.glob(f"{rundir}/zbzc_run3/zbzc_run3_*.coffea")):
    OUT.update(load(f))
VARIANTS = list(next(iter(OUT.values()))["muvar_z_pt"].axes["variant"])

from zbzc_cutvar_defs import DESC, FIT_LO, GROUPS, VARS  # noqa: E402

CUTVARS = [v for g in GROUPS.values() for v in g[1] if v in VARIANTS]
COLORS = {"DY": "#9e9e9e", "tt": "#8e44ad", "VV": "#16a085"}
LABELS = {"DY": "DY", "tt": r"$t\bar{t}$ (2L2Nu)", "VV": "VV"}


def kind(ds):
    if ds.startswith("DYto2L"):
        return "DY"
    if ds.startswith("TTto2L2Nu"):
        return "tt"
    if ds.split("_")[0] in ("WW", "WZ", "ZZ"):
        return "VV"
    return "data_Zmm" if ds.startswith("Muon") else "data_Zee"


def comps(var, variant, stage):
    """{DY, tt, VV, data}: (values, variances) incl. flow folded into the edge bins; edges."""
    c = {}
    for ds, o in OUT.items():
        k = kind(ds)
        if k == "data_Zee":
            continue
        h = o[var][{"variant": variant, "stage": stage}]
        if k != "data_Zmm":
            h = h * (XS[ds] * LUMIS["Zmm"] / o["sumw"])
        k = "data" if k == "data_Zmm" else k
        c[k] = h if k not in c else c[k] + h
    edges = next(iter(c.values())).axes[0].edges
    res = {}
    for k, h in c.items():
        v, w2 = h.values(flow=True).copy(), h.variances(flow=True).copy()
        v[1] += v[0]; v[-2] += v[-1]; w2[1] += w2[0]; w2[-2] += w2[-1]
        res[k] = (v[1:-1], w2[1:-1])
    for k in ("DY", "tt", "VV", "data"):
        res.setdefault(k, (np.zeros(len(edges) - 1), np.zeros(len(edges) - 1)))
    return edges, res


def slope(edges, d, m, mvar, fr):
    cen = 0.5 * (edges[1:] + edges[:-1])
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(m > 0, d / m, np.nan)
        e = np.sqrt(m + mvar) / m
    sel = (cen > fr[0]) & (cen < fr[1]) & np.isfinite(r) & np.isfinite(e) & (e > 0)
    if sel.sum() < 3:
        return np.nan, np.nan
    p, cov = np.polyfit(cen[sel], r[sel], 1, w=1 / e[sel], cov="unscaled")
    return 1e4 * p[0], 1e4 * np.sqrt(cov[0, 0])


def stats(var, variant, stage):
    edges, c = comps(var, variant, stage)
    d, dv = c["data"]
    m = sum(c[k][0] for k in ("DY", "tt", "VV"))
    mv = sum(c[k][1] for k in ("DY", "tt", "VV"))
    cen = 0.5 * (edges[1:] + edges[:-1])
    if var == "muvar_n_jet":
        cen = edges[:-1]

    def mom(v):
        n = v.sum()
        mu = (v * cen).sum() / n if n > 0 else np.nan
        return mu, np.sqrt(max((v * (cen - mu) ** 2).sum() / n, 0)) if n > 0 else np.nan

    D, M = d.sum(), m.sum()
    ok = (d + mv) > 0
    chi2 = float(((d - m) ** 2 / np.where(ok, d + mv, 1))[ok].sum())
    s = dict(data=float(D), mc=float(M), ratio=D / M if M > 0 else np.nan,
             ratio_err=(D / M) * np.sqrt(1 / D + mv.sum() / M ** 2) if D > 0 and M > 0 else np.nan,
             mean_d=mom(d)[0], mean_m=mom(m)[0], rms_d=mom(d)[1], rms_m=mom(m)[1],
             chi2=chi2, ndf=int(ok.sum()))
    fr, is_pt = VARS[var]
    if is_pt:
        fr = (FIT_LO.get((var, variant), fr[0]), fr[1])
        s["slope"], s["slope_err"] = slope(edges, d, m, mv, fr)
        s["fit_range"] = fr
    return edges, c, d, m, mv, s


def stat_box(ax, s, var):
    unit = "" if var in ("muvar_n_jet",) or "eta" in var else " GeV"
    lines = [f"Data {s['data']:.0f}   MC {s['mc']:.0f}",
             f"data/MC {s['ratio']:.3f} ± {s['ratio_err']:.3f}",
             f"mean  data {s['mean_d']:.2f}  MC {s['mean_m']:.2f}{unit}",
             f"RMS   data {s['rms_d']:.2f}  MC {s['rms_m']:.2f}{unit}",
             f"χ²/ndf {s['chi2']:.1f}/{s['ndf']}"]
    if "slope" in s and np.isfinite(s["slope"]):
        lines.append(f"slope {s['slope']:+.1f} ± {s['slope_err']:.1f} %/100 GeV "
                     f"({s['fit_range'][0]:.0f}-{s['fit_range'][1]:.0f})")
    ax.text(0.03, 0.97, "\n".join(lines), transform=ax.transAxes, va="top", ha="left", fontsize=12,
            family="DejaVu Sans Mono",
            bbox=dict(boxstyle="round", facecolor="white", edgecolor="#888888", alpha=0.9))


def panel(ax, rax, var, variant, stage, title):
    edges, c, d, m, mv, s = stats(var, variant, stage)
    order = ["VV", "tt", "DY"]
    hep.histplot([c[k][0] for k in order], edges, ax=ax, stack=True, histtype="fill",
                 color=[COLORS[k] for k in order], label=[LABELS[k] for k in order])
    hep.histplot(d, edges, ax=ax, histtype="errorbar", color="black", yerr=np.sqrt(d), label="Data")
    ax.stairs(m + np.sqrt(mv), edges, baseline=m - np.sqrt(mv), fill=True, hatch="////",
              facecolor="none", edgecolor="#555555", lw=0, label="MC stat. unc.")
    ax.set_yscale("log")
    top = max(d.max(), m.max(), 1)
    ax.set_ylim(max(0.1, 1e-4 * top), top * 300)
    ax.set_ylabel("Events / bin")
    ax.legend(loc="upper right", fontsize=13, ncol=2)
    stat_box(ax, s, var)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(m > 0, d / m, np.nan)
        re = np.where(m > 0, np.sqrt(d) / m, np.nan)
        band = np.where(m > 0, np.sqrt(mv) / m, 0)
    rax.stairs(1 + band, edges, baseline=1 - band, fill=True, hatch="////", facecolor="none",
               edgecolor="#555555", lw=0)
    hep.histplot(r, edges, ax=rax, histtype="errorbar", color="black", yerr=re)
    if "slope" in s and np.isfinite(s["slope"]):
        x = np.linspace(*s["fit_range"], 50)
        # line through the fitted points: refit for the intercept
        cen = 0.5 * (edges[1:] + edges[:-1])
        e = np.sqrt(m + mv) / np.where(m > 0, m, 1)
        sel = (cen > s["fit_range"][0]) & (cen < s["fit_range"][1]) & np.isfinite(r) & (e > 0)
        p = np.polyfit(cen[sel], r[sel], 1, w=1 / e[sel])
        rax.plot(x, np.polyval(p, x), color="#d62728", lw=2)
    rax.axhline(1, color="black", ls="--", lw=1)
    rax.set_ylim(0.7, 1.3)
    rax.set_ylabel("Data / MC", fontsize=16)
    label = next(iter(OUT.values()))[var].axes[-1].label
    rax.set_xlabel(label.replace("muon", "muon").replace("$p_T$", "$p_T$"))
    if var == "muvar_n_jet":
        rax.set_xticks(edges[:-1] + 0.5, [str(int(x)) for x in edges[:-1]])
    if var in ("muvar_z_pt", "muvar_lep0_pt", "muvar_lep1_pt", "muvar_jet_pt"):
        ax.set_xscale("log"); rax.set_xscale("log")
    return s


def compare_fig(variant, var, stage="final"):
    fig, axs = plt.subplots(2, 2, figsize=(20, 10), gridspec_kw=dict(height_ratios=[3, 1], hspace=0.05),
                            sharex="col")
    s0 = panel(axs[0, 0], axs[1, 0], var, "nominal", stage, "Nominal selection")
    s1 = panel(axs[0, 1], axs[1, 1], var, variant, stage, f"Variant (not applied): {DESC[variant]}")
    for ax in axs[0]:
        hep.cms.label("Preliminary", data=True, lumi=round(LUMIS["Zmm"] / 1000, 2), com=13.6, ax=ax, fontsize=16)
    fig.text(0.07, 0.975, "Z→μμ, nominal selection", fontsize=17, weight="bold", va="top")
    fig.text(0.545, 0.975, f"Z→μμ, variant (not applied): {DESC[variant]}", fontsize=17, weight="bold",
             va="top", color="#b03a00")
    fig.subplots_adjust(left=0.07, right=0.985, top=0.9, bottom=0.1, wspace=0.18)
    fig.savefig(os.path.join(outdir, f"var_{variant}_{var[6:]}.png"), dpi=80)
    plt.close(fig)
    return s0, s1


def overlay(group, var, stage="final"):
    name, members = GROUPS[group]
    members = [v for v in members if v in VARIANTS]
    fig, ax = plt.subplots(figsize=(12, 7))
    cols = ["black", "#d62728", "#1f77b4", "#2ca02c", "#ff7f0e"]
    for i, v in enumerate(["nominal"] + members):
        edges, c, d, m, mv, s = stats(var, v, stage)
        cen = 0.5 * (edges[1:] + edges[:-1])
        with np.errstate(divide="ignore", invalid="ignore"):
            r = np.where(m > 0, d / m, np.nan)
            re = np.where(m > 0, np.sqrt(d) / m, np.nan)
        off = (i - len(members) / 2) * 0.12 * np.diff(edges)
        lab = DESC[v] if v != "nominal" else "nominal"
        if "slope" in s and np.isfinite(s["slope"]):
            lab += f"  (slope {s['slope']:+.1f}±{s['slope_err']:.1f} %/100 GeV)"
        ax.errorbar(cen + off, r, yerr=re, fmt="o", ms=4, color=cols[i % len(cols)], label=lab)
    ax.axhline(1, color="black", ls="--", lw=1)
    ax.set_ylim(0.7, 1.3)
    ax.set_ylabel("Data / MC")
    ax.set_xlabel(next(iter(OUT.values()))[var].axes[-1].label)
    if var in ("muvar_z_pt", "muvar_lep0_pt", "muvar_lep1_pt", "muvar_jet_pt"):
        ax.set_xscale("log")
    ax.legend(fontsize=11, loc="lower left")
    ax.set_title(f"Z→μμ, full selection: {name}", fontsize=15, loc="left")
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, f"ovl_{group}_{var[6:]}.png"), dpi=80)
    plt.close(fig)


# ---------------------------------------------------------------- table
table = {}
for v in ["nominal"] + CUTVARS:
    for stage in ("Z", "final"):
        row = {}
        for var in ("muvar_z_pt", "muvar_lep0_pt", "muvar_lep1_pt", "muvar_jet_pt"):
            if stage == "Z" and var == "muvar_jet_pt":
                continue
            row[var] = stats(var, v, stage)[-1]
        table[f"{v}|{stage}"] = row
json.dump(table, open(os.path.join(outdir, "cutvar_table.json"), "w"), indent=1, default=float)

L = [f"{camp} Z->mumu cut study: one cut changed at a time (20 files per sample, lumi {LUMIS['Zmm']:.1f}/pb, "
     "stat. errors only). Stage Z = trigger, 2 muons, OS, m window; final = + MET + >= 1 jet.",
     "slope = data/MC straight-line fit in %/100 GeV (pT(mumu) 0-400, lead mu 35-300 (lead30: 30-300), "
     "jet 30-300 (jpt25/40: from the cut)).", ""]
hdr = f"{'variant':10s} {'stage':6s} {'data':>8s} {'MC':>10s} {'data/MC':>14s} {'d(ratio)':>9s} " \
      f"{'slope pT(mumu)':>16s} {'slope lead mu':>15s} {'slope jet pT':>15s}  description"
L.append(hdr)
for stage in ("Z", "final"):
    nom = table[f"nominal|{stage}"]["muvar_z_pt"]
    for v in ["nominal"] + CUTVARS:
        r = table[f"{v}|{stage}"]
        z = r["muvar_z_pt"]
        sl = lambda k: f"{r[k]['slope']:+6.1f}+-{r[k]['slope_err']:4.1f}" if k in r and np.isfinite(r[k]["slope"]) else "-"
        L.append(f"{v:10s} {stage:6s} {z['data']:8.0f} {z['mc']:10.1f} {z['ratio']:7.3f}+-{z['ratio_err']:.3f} "
                 f"{z['ratio'] - nom['ratio']:+9.3f} {sl('muvar_z_pt'):>16s} {sl('muvar_lep0_pt'):>15s} "
                 f"{sl('muvar_jet_pt'):>15s}  {DESC[v]}")
    L.append("")
open(os.path.join(outdir, "cutvar_table.txt"), "w").write("\n".join(L) + "\n")
print("\n".join(L))

# ---------------------------------------------------------------- plots
for v in CUTVARS:
    for var in VARS:
        compare_fig(v, var)
for g in GROUPS:
    if any(v in VARIANTS for v in GROUPS[g][1]):
        for var in ("muvar_z_pt", "muvar_lep0_pt", "muvar_lep1_pt", "muvar_jet_pt", "muvar_lep0_eta",
                    "muvar_jet_eta"):
            overlay(g, var)


# ---------------------------------------------------------------- Delta phi(MET, X)
DPHI_LABEL = {"j1": "leading jet", "jmin": "closest selected jet", "z": "Z", "lep0": "leading lepton",
              "lep1": "subleading lepton", "jany": "leading jet (pT > 15, any |η|)"}
FL = {"l": ("DY + light", "#9e9e9e"), "c": ("DY + c", "#7fb3e6"), "b": ("DY + b", "#f2a65a")}


def dphi_comps(name, ch, sel):
    c = {}
    for ds, o in OUT.items():
        k = kind(ds)
        if k.startswith("data") and k != f"data_{ch}":
            continue
        lists = {a: v for a, v in sel.items() if isinstance(v, list)}
        h = o[name][{"channel": ch, "pflav": sum, **{a: v for a, v in sel.items() if a not in lists}}]
        for a, v in lists.items():
            h = sum(h[{a: x}] for x in v)
        if k == "DY":
            h = h * (XS[ds] * LUMIS[ch] / o["sumw"])
            for f in "lcb":
                c[f] = c.get(f, 0) + h[{"flav": f}].values()
        elif k in ("tt", "VV"):
            c[k] = c.get(k, 0) + (h[{"flav": sum}] * (XS[ds] * LUMIS[ch] / o["sumw"])).values()
        else:
            c["data"] = c.get("data", 0) + h[{"flav": sum}].values()
    edges = next(iter(OUT.values()))[name].axes["dphi"].edges
    return edges, c


def dphi_fig(name, obj, cols, fname, title):
    """cols: list of (column label, selection dict) (MET bins); rows Zee, Zmm; ratio under each."""
    fig = plt.figure(figsize=(7 * len(cols), 13))
    outer = fig.add_gridspec(2, len(cols), hspace=0.32, wspace=0.22, top=0.9, bottom=0.07, left=0.06, right=0.98)
    lab = {"VV": "VV", "tt": r"$t\bar{t}$", **{f: FL[f][0] for f in FL}}
    col = {"VV": COLORS["VV"], "tt": COLORS["tt"], **{f: FL[f][1] for f in FL}}
    for i, ch in enumerate(("Zee", "Zmm")):
        for j, (cl, sel) in enumerate(cols):
            inner = outer[i, j].subgridspec(2, 1, height_ratios=[3, 1], hspace=0.05)
            ax, rax = fig.add_subplot(inner[0]), fig.add_subplot(inner[1])
            edges, c = dphi_comps(name, ch, dict(obj=obj, **sel))
            order = [k for k in ("VV", "tt", "b", "c", "l") if k in c]
            hep.histplot([c[k] for k in order], edges, ax=ax, stack=True, histtype="fill",
                         color=[col[k] for k in order], label=[lab[k] for k in order])
            d = c.get("data", np.zeros(len(edges) - 1))
            m = sum(c[k] for k in order)
            hep.histplot(d, edges, ax=ax, histtype="errorbar", color="black", yerr=np.sqrt(d), label="Data")
            ax.set_ylim(0, max(d.max(), m.max(), 1) * 1.7)
            ax.set_title(f"{'Z→ee' if ch == 'Zee' else 'Z→μμ'}, {cl}", fontsize=15, loc="left")
            ax.legend(fontsize=10, ncol=3, loc="upper right")
            ratio = d.sum() / m.sum() if m.sum() > 0 else np.nan
            ax.text(0.03, 0.95, f"Data {d.sum():.0f}\nMC   {m.sum():.0f}\ndata/MC {ratio:.3f}",
                    transform=ax.transAxes, va="top", fontsize=11, family="DejaVu Sans Mono",
                    bbox=dict(boxstyle="round", facecolor="white", edgecolor="#888888"))
            ax.set_xlim(0, np.pi); ax.set_xticklabels([]); ax.set_xlabel("")
            with np.errstate(divide="ignore", invalid="ignore"):
                hep.histplot(np.where(m > 0, d / m, np.nan), edges, ax=rax, histtype="errorbar",
                             color="black", yerr=np.where(m > 0, np.sqrt(d) / m, np.nan))
            rax.axhline(1, color="black", ls="--", lw=1)
            rax.set_xlim(0, np.pi); rax.set_ylim(0.2, 1.6)
            rax.set_ylabel("Data/MC", fontsize=13)
            rax.set_xlabel(rf"$\Delta\phi$(MET, {DPHI_LABEL[obj]})", fontsize=15)
    fig.suptitle(title, fontsize=19, weight="bold")
    fig.savefig(os.path.join(outdir, fname), dpi=70)
    plt.close(fig)


o0 = next(iter(OUT.values()))
if "dphi_met" in o0:
    for obj in o0["dphi_met"].axes["obj"]:
        dphi_fig("dphi_met", obj, [(f"MET {b} GeV", dict(metbin=b)) for b in o0["dphi_met"].axes["metbin"]],
                 f"dphi_{obj}.png", f"Δφ(MET, {DPHI_LABEL[obj]}): every cut except MET < 50")
    for obj in o0["stage_dphi_met"].axes["obj"]:
        for jl, stages in (("0 jets", ["none", "MET"]), ("≥1 jet", ["jet", "MET+jet"])):
            rows = [(f"{jl}, MET {b} GeV", dict(metbin=b, stage=stages)) for b in o0["stage_dphi_met"].axes["metbin"]]
            dphi_fig("stage_dphi_met", obj, rows, f"stage_dphi_{obj}_{'0j' if jl == '0 jets' else 'ge1j'}.png",
                     f"Δφ(MET, {DPHI_LABEL[obj]}): Z events, {jl} (no MET cut)")
print("plots in", outdir)
