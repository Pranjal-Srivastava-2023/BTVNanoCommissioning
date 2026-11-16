"""MET > 50 study (2026-11-16), Summer22: compare MC with JER smearing (run zbzc_run3_metxy) and without
(zbzc_run3_metxy_nojer) against the same data; reference = zbzc_run3_zpt (no MET XY correction).
Both runs: zpt setup (8 Nov selection + DY Z pT weights) + JME PuppiMET XY correction.

Writes into hists_zbzc_run3_metxy/Summer22/met_compare/:
  met_compare.txt / met_compare.json  data/MC per MET bin (all cuts but MET), per Delta phi(MET, j1) region at
                                      MET 50-100, recoil response / resolution per pT(ll) bin, for zpt / JER / noJER
  met_nm1_jer_vs_nojer.png            MET (all cuts but MET): data vs MC with and without JER, data/MC for both
  dphi_j1_50-100_jer_vs_nojer.png     the same for Delta phi(MET, leading jet) at MET 50-100
  recoil_<Z|Zjet>.png                 <u_par + qT> and RMS(u_perp) vs pT(ll): data, MC JER, MC noJER
Usage: python plot_zbzc_met_compare.py
"""
import glob
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import mplhep as hep  # noqa: E402
import numpy as np  # noqa: E402
from coffea.util import load  # noqa: E402

hep.style.use("CMS")
C = "Summer22"
RUNS = {"zpt": "zbzc_run3_zpt", "JER": "zbzc_run3_metxy", "noJER": "zbzc_run3_metxy_nojer"}
# ZBZC_MET_TEST=<prefix>: read hists_<prefix>metxy and hists_<prefix>metxy_nojer instead (layout test)
if os.environ.get("ZBZC_MET_TEST"):
    RUNS.update(JER=os.environ["ZBZC_MET_TEST"] + "metxy", noJER=os.environ["ZBZC_MET_TEST"] + "metxy_nojer")
OUTDIR = f"hists_{RUNS['JER']}/{C}/met_compare"
os.makedirs(OUTDIR, exist_ok=True)
XS = json.load(open("metadata/Zb_Zc_ratio_xsections_run3.json"))
CHANNELS = {"Zee": r"Z$\to$ee", "Zmm": r"Z$\to\mu\mu$"}
COL = {"JER": "#1f77b4", "noJER": "#d62728", "zpt": "#7f7f7f"}
LAB = {"JER": "MC, JER smearing (nominal)", "noJER": "MC, no JER smearing", "zpt": "MC, no MET XY (zpt run)"}


def lumi_of(run):
    f = f"hists_{run}/{C}/lumi.json"
    return json.load(open(f if os.path.exists(f) else f"hists_zbzc_run3/{C}/lumi.json"))


def get(run, hname, ch, sl):
    """(data hist, MC hist) for one channel, all MC samples scaled and summed over flavours."""
    lumi = lumi_of(run)
    data = mc = None
    for f in sorted(glob.glob(f"hists_{run}/{C}/zbzc_run3/zbzc_run3_*.coffea")):
        for ds, o in load(f).items():
            if hname not in o:
                continue
            h = o[hname][{"channel": ch, "flav": sum, "pflav": sum, **sl}]
            if ds.startswith(("Muon", "EGamma")):
                if ds.startswith("Muon" if ch == "Zmm" else "EGamma"):
                    data = h if data is None else data + h
            else:
                h = h * (XS[ds] * lumi[ch] / o["sumw"])
                mc = h if mc is None else mc + h
    return data, mc


def ratio(d, m):
    D, M = d.values().sum(), m.values().sum()
    return D / M, D / M * np.sqrt(1 / D + m.variances().sum() / M ** 2)


res = {}
L = ["MET > 50 study, Summer22, 20 files per sample, statistical errors only",
     "zpt = 8 Nov setup + DY Z pT weights (no MET XY); JER / noJER = zpt + PuppiMET XY, MC with / without JER smearing",
     "Data: zpt run for zpt, metxy run for JER and noJER (data are the same events; only the XY correction differs).", ""]

# ---------------------------------------------------------------- data/MC per MET bin (all cuts but MET)
L.append("== data/MC, all cuts except MET, per MET bin")
L.append(f"{'':12s}{'run':8s}" + "".join(f"{b:>18s}" for b in ("0-50", "50-100", "100-200")))
for ch in CHANNELS:
    for key, run in RUNS.items():
        d, m = get(run, "met_pt_nm1", ch, {"tag": "incl"})
        e = d.axes[0].edges
        row = []
        for lo, hi in ((0, 50), (50, 100), (100, 200)):
            sel = (e[:-1] >= lo) & (e[1:] <= hi)
            D, M, MV = d.values()[sel].sum(), m.values()[sel].sum(), m.variances()[sel].sum()
            r = D / M
            row.append((r, r * np.sqrt(1 / D + MV / M ** 2), D, M))
        res[f"metbin_{ch}_{key}"] = row
        L.append(f"{ch:12s}{key:8s}" + "".join(f"{r:9.3f} ± {re:.3f} " for r, re, _, _ in row))
L.append("")

# ---------------------------------------------------------------- Delta phi(MET, j1) regions at MET 50-100
L.append("== data/MC at MET 50-100 (all cuts except MET) vs Delta phi(MET, leading jet)")
reg = [("<0.6", 0, 0.6), ("0.6-2.5", 0.6, 2.5), (">2.5", 2.5, np.pi + 1e-6)]
L.append(f"{'':12s}{'run':8s}" + "".join(f"{n:>18s}" for n, _, _ in reg) + f"{'MC share >2.5':>16s}")
for ch in CHANNELS:
    for key, run in RUNS.items():
        d, m = get(run, "dphi_met", ch, {"obj": "j1", "metbin": "50-100"})
        c = d.axes[0].centers
        row = []
        for _, lo, hi in reg:
            sel = (c > lo) & (c < hi)
            D, M, MV = d.values()[sel].sum(), m.values()[sel].sum(), m.variances()[sel].sum()
            row.append((D / M, D / M * np.sqrt(1 / D + MV / M ** 2), D, M))
        share = row[2][3] / sum(r[3] for r in row)
        res[f"dphi_{ch}_{key}"] = row + [share]
        L.append(f"{ch:12s}{key:8s}" + "".join(f"{r:9.3f} ± {re:.3f} " for r, re, _, _ in row) + f"{100 * share:15.0f}%")
L.append("")


# ---------------------------------------------------------------- overlays: data vs MC JER vs MC noJER
def overlay(hname, sl, fname, xlabel, logy):
    fig, axes = plt.subplots(2, 2, figsize=(20, 10.5), sharex="col",
                             gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05})
    for ax, rax, ch in zip(axes[0], axes[1], CHANNELS):
        d, _ = get(RUNS["JER"], hname, ch, sl)
        e = d.axes[0].edges
        dv = d.values()
        hep.histplot(dv, e, ax=ax, histtype="errorbar", color="black", yerr=np.sqrt(dv), label="Data")
        for key in ("JER", "noJER"):
            _, m = get(RUNS[key], hname, ch, sl)
            mv = m.values()
            hep.histplot(mv, e, ax=ax, color=COL[key], lw=2.5, label=f"{LAB[key]} (data/MC {dv.sum() / mv.sum():.3f})")
            with np.errstate(divide="ignore", invalid="ignore"):
                r = np.where(mv > 0, dv / mv, np.nan)
                hep.histplot(r, e, ax=rax, histtype="errorbar", color=COL[key],
                             yerr=np.where(mv > 0, np.sqrt(dv) / mv, np.nan), marker="o", markersize=6)
        if logy:
            ax.set_yscale("log")
            ax.set_ylim(max(dv[dv > 0].min() * 0.3, 0.1), dv.max() * 50)
        else:
            ax.set_ylim(0, dv.max() * 1.6)
        ax.set_ylabel("Events / bin")
        ax.text(0.04, 0.94, CHANNELS[ch], transform=ax.transAxes, fontsize=20, va="top")
        ax.legend(fontsize=14, loc="upper right")
        hep.cms.label("Preliminary", data=True, lumi=round(lumi_of(RUNS["JER"])[ch] / 1000, 2), com=13.6, ax=ax, fontsize=18)
        rax.axhline(1, color="black", lw=1, ls="--")
        rax.set_ylim(0.2, 1.6)
        rax.set_ylabel("Data / MC", fontsize=20)
        rax.set_xlabel(xlabel)
    fig.subplots_adjust(left=0.07, right=0.985, top=0.94, bottom=0.11, wspace=0.2)
    fig.savefig(os.path.join(OUTDIR, fname), dpi=90)
    plt.close(fig)


overlay("met_pt_nm1", {"tag": "incl"}, "met_nm1_jer_vs_nojer.png", r"PUPPI $p_T^{miss}$ [GeV] (all cuts except MET)", True)
overlay("dphi_met", {"obj": "j1", "metbin": "50-100"}, "dphi_j1_50-100_jer_vs_nojer.png",
        r"$\Delta\phi(p_T^{miss}, j_1)$, 50 < MET < 100 GeV", False)
overlay("stage_dphi_met", {"obj": "jany", "metbin": "50-100", "stage": sum}, "stage_dphi_jany_50-100_jer_vs_nojer.png",
        r"$\Delta\phi(p_T^{miss}, j_{15}^{any\,\eta})$, Z events, 50 < MET < 100", False)


# ---------------------------------------------------------------- recoil response and resolution vs pT(ll)
def moments(h):
    c, v = h.axes[0].centers, h.values()
    n = v.sum()
    mu = (v * c).sum() / n
    rms = np.sqrt(max((v * (c - mu) ** 2).sum() / n, 0))
    neff = n ** 2 / max(h.variances().sum(), 1e-12)
    return mu, rms, rms / np.sqrt(neff), rms / np.sqrt(2 * neff)


L.append("== hadronic recoil u = -(MET + pT(ll)): mean of u_par + qT (0 = balanced) and RMS of u_perp [GeV], |u| < 100")
for sel in ("Z", "Z+jet"):
    fig, axes = plt.subplots(2, 2, figsize=(20, 11), sharex=True, gridspec_kw={"hspace": 0.05})
    for j, ch in enumerate(CHANNELS):
        L.append(f"-- {sel}, {ch}: qT bin | <u_par+qT> data / JER / noJER | RMS(u_perp) data / JER / noJER")
        d0, _ = get(RUNS["JER"], "recoil", ch, {"sel": sel, "comp": "uperp"})
        zb = d0.axes["zpt"].edges
        x = 0.5 * (zb[:-1] + np.minimum(zb[1:], 250))
        pts = {k: ([], []) for k in ("data", "JER", "noJER")}
        for i in range(len(zb) - 1):
            out = {}
            for key in ("JER", "noJER"):
                for comp, idx in (("upar_qt", 0), ("uperp", 1)):
                    d, m = get(RUNS[key], "recoil", ch, {"sel": sel, "comp": comp, "zpt": i})
                    if key == "JER":
                        out[("data", comp)] = moments(d)
                    out[(key, comp)] = moments(m)
            for k in pts:
                pts[k][0].append(out[(k, "upar_qt")])
                pts[k][1].append(out[(k, "uperp")])
            L.append(f"   {zb[i]:4.0f}-{zb[i + 1]:<5.0f}| " + " / ".join(f"{out[(k, 'upar_qt')][0]:6.2f}" for k in pts)
                     + " | " + " / ".join(f"{out[(k, 'uperp')][1]:6.2f}" for k in pts))
            res[f"recoil_{sel}_{ch}_{i}"] = {k: [out[(k, 'upar_qt')][0], out[(k, 'uperp')][1]] for k in pts}
        for k, col in (("data", "black"), ("JER", COL["JER"]), ("noJER", COL["noJER"])):
            lab = "Data" if k == "data" else LAB[k]
            axes[0, j].errorbar(x, [p[0] for p in pts[k][0]], yerr=[p[2] for p in pts[k][0]], fmt="o-", color=col, label=lab)
            axes[1, j].errorbar(x, [p[1] for p in pts[k][1]], yerr=[p[3] for p in pts[k][1]], fmt="o-", color=col, label=lab)
        axes[0, j].axhline(0, color="black", lw=1, ls="--")
        axes[0, j].set_ylabel(r"$\langle u_\parallel + q_T \rangle$ [GeV]")
        axes[1, j].set_ylabel(r"RMS($u_\perp$) [GeV]")
        axes[1, j].set_xlabel(r"$q_T = p_T(\ell\ell)$ [GeV] (last bin 150+)")
        axes[0, j].text(0.04, 0.94, f"{CHANNELS[ch]}, {'Z events (no MET / jet cut)' if sel == 'Z' else 'all cuts except MET'}",
                        transform=axes[0, j].transAxes, fontsize=18, va="top")
        axes[0, j].legend(fontsize=14, loc="best")
        hep.cms.label("Preliminary", data=True, lumi=round(lumi_of(RUNS["JER"])[ch] / 1000, 2), com=13.6, ax=axes[0, j],
                      fontsize=16)
    fig.subplots_adjust(left=0.08, right=0.985, top=0.94, bottom=0.09, wspace=0.22)
    fig.savefig(os.path.join(OUTDIR, f"recoil_{sel.replace('+', '')}.png"), dpi=90)
    plt.close(fig)

open(os.path.join(OUTDIR, "met_compare.txt"), "w").write("\n".join(L) + "\n")
json.dump(res, open(os.path.join(OUTDIR, "met_compare.json"), "w"), indent=1, default=float)
print("\n".join(L))
print("plots in", OUTDIR)
