"""MET > 50 study Phase 2 (2026-11-22), Summer22: data/MC for each MET version of run zbzc_run3_metvar.

Run zbzc_run3_metvar = run A (zpt setup + PuppiMET XY, MC with JER smearing) with the MET filled in several versions
side by side (MET_VARIANTS in workflows/Zb_Zc_ratio.py): in each version the JER factor of one class of jets in the
type-1 MET sum is set to 1. The analysis jets are always smeared as nominal, so only the MET changes.
Data have no JER, so every version has the same data: run A's data (met_pt_nm1, recoil).
Reference: run B (zbzc_run3_metxy_nojer) = no JER anywhere (jets AND MET).

Writes into hists_zbzc_run3_metvar/Summer22/metvar/:
  metvar.txt / metvar.json   data/MC per MET bin per version, final selection (MET < 50 + jet) per tag region,
                             MC b-tag / c-tag yield ratios per version, recoil response / width, checks
  met_nm1_versions.png       MET (all cuts except MET): data vs MC versions, data/MC panel
  datamc_metbins.png         data/MC at MET 0-50, 50-100, 100-200 per version (both channels)
  recoil_<Z|Zjet>.png        <u_par + qT> and RMS(u_perp) vs pT(ll): data and MC versions
Usage: python plot_zbzc_metvar.py
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
RV, RA, RB = os.environ.get("ZBZC_METVAR_RUN", "zbzc_run3_metvar"), "zbzc_run3_metxy", "zbzc_run3_metxy_nojer"
OUTDIR = f"hists_{RV}/{C}/metvar"
os.makedirs(OUTDIR, exist_ok=True)
XS = json.load(open("metadata/Zb_Zc_ratio_xsections_run3.json"))
LUMI = json.load(open(f"hists_{RA}/{C}/lumi.json"))
CHANNELS = {"Zee": r"Z$\to$ee", "Zmm": r"Z$\to\mu\mu$"}
VERS = ["all", "noJERhighSF", "noJERfwd", "noJERsoftfwd", "noJERsoft", "noJERcorrT1", "noJER"]
LAB = {"all": "JER in MET for all jets (nominal = run A)",
       "noJERhighSF": "no JER in MET, 2.65 < |η| < 2.964",
       "noJERfwd": "no JER in MET, 2.5 < |η| < 3.139",
       "noJERsoftfwd": "no JER in MET, pT < 30 and 2.5 < |η| < 3.139",
       "noJERsoft": "no JER in MET, pT < 30",
       "noJERcorrT1": "no JER in MET for CorrT1METJet",
       "noJER": "no JER in MET at all",
       "B": "run B: no JER anywhere (jets and MET)"}
COL = {"all": "#1f77b4", "noJERhighSF": "#9467bd", "noJERfwd": "#2ca02c", "noJERsoftfwd": "#17becf",
       "noJERsoft": "#ff7f0e", "noJERcorrT1": "#8c564b", "noJER": "#d62728", "B": "#7f7f7f"}
TAGS = ["incl", "btag_L", "ctag_L", "btag_M", "ctag_M", "btag_T", "ctag_T"]
_cache = {}


def files(run):
    return sorted(glob.glob(f"hists_{run}/{C}/zbzc_run3/zbzc_run3_*.coffea"))


def loadf(f):
    if f not in _cache:
        _cache[f] = load(f)
    return _cache[f]


def get(run, hname, ch, sl, want="mc"):
    """Sum of MC samples (scaled to the data lumi) or data, one channel, flavours summed."""
    out = None
    for f in files(run):
        for ds, o in loadf(f).items():
            if hname not in o:
                continue
            isdata = ds.startswith(("Muon", "EGamma"))
            if (want == "data") != isdata:
                continue
            if isdata and not ds.startswith("Muon" if ch == "Zmm" else "EGamma"):
                continue
            h = o[hname][{"channel": ch, "flav": sum, "pflav": sum, **sl}]
            if not isdata:
                h = h * (XS[ds] * LUMI[ch] / o["sumw"])
            out = h if out is None else out + h
    return out


def mc_hist(key, hname, ch, sl):
    """MC for a version (metvar hists of run V) or 'B' (run B, nominal hists)."""
    if key == "B":
        name = {"metvar_nm1": "met_pt_nm1", "metvar_recoil": "recoil"}[hname]
        return get(RB, name, ch, sl)
    return get(RV, hname, ch, {**sl, "metvar": key})


def data_hist(hname, ch, sl):
    name = {"metvar_nm1": "met_pt_nm1", "metvar_recoil": "recoil"}[hname]
    return get(RA, name, ch, sl, want="data")


def ratio_in(d, m, lo, hi):
    e = d.axes[0].edges
    sel = (e[:-1] >= lo) & (e[1:] <= hi)
    D, M, MV = d.values()[sel].sum(), m.values()[sel].sum(), m.variances()[sel].sum()
    r = D / M
    return r, r * np.sqrt(1 / max(D, 1) + MV / M ** 2), D, M, MV


KEYS = VERS + ["B"]
res = {"checks": {}}
L = ["MET > 50 study Phase 2, Summer22, 20 files per sample, statistical errors only.",
     "MC: run zbzc_run3_metvar (= run A with the MET filled in several versions; analysis jets always nominal).",
     "Data: run A (data have no JER: the same for every version). B = run B (no JER for jets and MET).", ""]

# ------------------------------------------------------------------ checks
L.append("== checks")
for ch in CHANNELS:
    a = mc_hist("all", "metvar_nm1", ch, {"tag": "incl"}).values(flow=True)
    ra = get(RA, "met_pt_nm1", ch, {"tag": "incl"}).values(flow=True)
    rel = float(np.max(np.abs(a - ra)) / ra.sum())
    res["checks"][f"all_vs_runA_{ch}"] = rel
    L.append(f"   {ch}: version 'all' vs run A met_pt_nm1 (MC): max |diff| / total = {rel:.2e}")
for f in files(RV):
    for ds, o in loadf(f).items():
        if "metvar_check" in o:
            for ch, c in o["metvar_check"].items():
                n, nb = c.get("n", 0), c.get("n_diff_gt_0p01", 0)
                res["checks"].setdefault("framework_MET_vs_all", {})[f"{ds}|{ch}"] = [n, nb, c.get("sum_absdiff", 0)]
                if nb:
                    L.append(f"   WARNING {ds} {ch}: {nb} of {n} events with |MET_all - MET_framework| > 0.01 GeV")
bad = sum(v[1] for v in res["checks"].get("framework_MET_vs_all", {}).values())
ntot = sum(v[0] for v in res["checks"].get("framework_MET_vs_all", {}).values())
L.append(f"   type-1 MET 'all' recomputed vs framework MET: {bad} of {ntot:.0f} Z events differ by > 0.01 GeV")
L.append("")

# ------------------------------------------------------------------ data/MC per MET bin
BINS = [(0, 50), (50, 100), (100, 200)]
L.append("== data/MC, all cuts except MET, per MET bin (tag incl)")
L.append(f"{'':6s}{'version':16s}" + "".join(f"{f'{lo}-{hi}':>18s}" for lo, hi in BINS) + f"{'MC 50-100 / nominal':>22s}")
for ch in CHANNELS:
    d = data_hist("metvar_nm1", ch, {"tag": "incl"})
    m_all = mc_hist("all", "metvar_nm1", ch, {"tag": "incl"})
    for key in KEYS:
        m = mc_hist(key, "metvar_nm1", ch, {"tag": "incl"})
        row = [ratio_in(d, m, lo, hi) for lo, hi in BINS]
        mcfrac = row[1][3] / ratio_in(d, m_all, 50, 100)[3]
        res[f"metbin_{ch}_{key}"] = row
        L.append(f"{ch:6s}{key:16s}" + "".join(f"{r:9.3f} ± {e:.3f} " for r, e, _, _, _ in row) + f"{mcfrac:22.3f}")
L.append("")

# ------------------------------------------------------------------ final selection per tag region
L.append("== final selection (MET < 50 + jet, all weights): data/MC per tag region (ParticleNet)")
L.append(f"{'':6s}{'version':16s}" + "".join(f"{t:>17s}" for t in TAGS))
for ch in CHANNELS:
    for key in KEYS:
        row = []
        for t in TAGS:
            d = data_hist("metvar_nm1", ch, {"tag": t})
            m = mc_hist(key, "metvar_nm1", ch, {"tag": t})
            row.append(ratio_in(d, m, 0, 50))
        res[f"final_{ch}_{key}"] = row
        L.append(f"{ch:6s}{key:16s}" + "".join(f"{r:8.3f}±{e:.3f} " for r, e, _, _, _ in row))
L.append("")
L.append("== MC b-tag / c-tag yield ratio at the final selection (ParticleNet), and its change w.r.t. nominal")
L.append("   (error of the change, approximate: the versions share the events; only the events that cross the MET cut")
L.append("    count, with variance |sum w^2 (version) - sum w^2 (nominal)| for the b-tag and the c-tag yield; run B uses")
L.append("    other jets, so for B the full MC stat errors are used)")
for ch in CHANNELS:
    for wp in "LMT":
        ib, ic = TAGS.index(f"btag_{wp}"), TAGS.index(f"ctag_{wp}")
        b0, c0 = res[f"final_{ch}_all"][ib], res[f"final_{ch}_all"][ic]
        base = b0[3] / c0[3]
        parts = []
        for key in KEYS:
            bv, cv = res[f"final_{ch}_{key}"][ib], res[f"final_{ch}_{key}"][ic]
            r = bv[3] / cv[3]
            if key == "B":
                err = np.sqrt(bv[4] / bv[3] ** 2 + cv[4] / cv[3] ** 2 + b0[4] / b0[3] ** 2 + c0[4] / c0[3] ** 2)
            else:
                err = np.sqrt(abs(bv[4] - b0[4]) / bv[3] ** 2 + abs(cv[4] - c0[4]) / cv[3] ** 2)
            res[f"bc_{ch}_{wp}_{key}"] = [r, r / base - 1, err]
            parts.append(f"{key} {r:.4f} ({100 * (r / base - 1):+.2f} ± {100 * err:.2f}%)")
        L.append(f"   {ch} {wp}: " + ", ".join(parts))
    # data
    for wp in "LMT":
        fb = res[f"final_{ch}_all"][TAGS.index(f"btag_{wp}")][2]
        fc = res[f"final_{ch}_all"][TAGS.index(f"ctag_{wp}")][2]
        res[f"bc_{ch}_{wp}_data"] = fb / fc
        L.append(f"   {ch} {wp} data: {fb / fc:.4f} (± {fb / fc * np.sqrt(1 / fb + 1 / fc):.4f} stat)")
L.append("")


# ------------------------------------------------------------------ plots: MET overlay
SHOW = ["all", "noJERfwd", "noJERsoft", "noJER", "B"]


def overlay():
    fig, axes = plt.subplots(2, 2, figsize=(20, 11), sharex="col", gridspec_kw={"height_ratios": [3, 1.3], "hspace": 0.05})
    for ax, rax, ch in zip(axes[0], axes[1], CHANNELS):
        d = data_hist("metvar_nm1", ch, {"tag": "incl"})
        e, dv = d.axes[0].edges, d.values()
        hep.histplot(dv, e, ax=ax, histtype="errorbar", color="black", yerr=np.sqrt(dv), label="Data")
        for key in SHOW:
            mv = mc_hist(key, "metvar_nm1", ch, {"tag": "incl"}).values()
            r5 = res[f"metbin_{ch}_{key}"][1][0]
            hep.histplot(mv, e, ax=ax, color=COL[key], lw=2.5, ls="--" if key == "B" else "-",
                         label=f"{LAB[key]} (data/MC 50–100: {r5:.2f})")
            with np.errstate(divide="ignore", invalid="ignore"):
                hep.histplot(np.where(mv > 0, dv / mv, np.nan), e, ax=rax, histtype="errorbar", color=COL[key],
                             yerr=np.where(mv > 0, np.sqrt(dv) / mv, np.nan), marker="o", markersize=5)
        ax.set_yscale("log")
        ax.set_ylim(max(dv[dv > 0].min() * 0.3, 0.1), dv.max() * 3000)
        ax.set_ylabel("Events / 5 GeV")
        ax.axvline(50, color="grey", lw=1, ls=":")
        ax.text(0.04, 0.62, CHANNELS[ch] + ", all cuts except MET", transform=ax.transAxes, fontsize=19, va="top")
        ax.legend(fontsize=12.5, loc="upper right")
        hep.cms.label("Preliminary", data=True, lumi=round(LUMI[ch] / 1000, 2), com=13.6, ax=ax, fontsize=18)
        rax.axhline(1, color="black", lw=1, ls="--")
        rax.axvline(50, color="grey", lw=1, ls=":")
        rax.set_ylim(0.3, 1.5)
        rax.set_ylabel("Data / MC", fontsize=20)
        rax.set_xlabel(r"PUPPI $p_T^{miss}$ [GeV]")
    fig.subplots_adjust(left=0.07, right=0.985, top=0.94, bottom=0.1, wspace=0.2)
    fig.savefig(os.path.join(OUTDIR, "met_nm1_versions.png"), dpi=90)
    plt.close(fig)


def summary_points():
    fig, axes = plt.subplots(1, 3, figsize=(21, 8.5), sharey=True)
    y = np.arange(len(KEYS))
    for ax, (lo, hi), i in zip(axes, BINS, range(3)):
        for j, ch in enumerate(CHANNELS):
            vals = [res[f"metbin_{ch}_{k}"][i] for k in KEYS]
            ax.errorbar([v[0] for v in vals], y + (0.15 if j else -0.15), xerr=[v[1] for v in vals], fmt="o" if j else "s",
                        color=["#3b75af", "#d1495b"][j], ms=9, capsize=3, label=CHANNELS[ch])
        ax.axvline(1, color="black", lw=1, ls="--")
        ax.set_title(f"{lo} < MET < {hi} GeV", fontsize=20)
        ax.set_xlabel("data / MC (all cuts except MET)", fontsize=17)
        ax.grid(axis="x", alpha=0.3)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels([LAB[k] for k in KEYS], fontsize=14)
    axes[0].invert_yaxis()
    axes[1].legend(fontsize=16, loc="upper right")
    fig.subplots_adjust(left=0.3, right=0.985, top=0.9, bottom=0.12, wspace=0.08)
    fig.suptitle("Summer22: data/MC per MET bin for each MET version (MC); data are the same in every row", fontsize=19)
    fig.savefig(os.path.join(OUTDIR, "datamc_metbins.png"), dpi=90)
    plt.close(fig)


def moments(h):
    c, v = h.axes[0].centers, h.values()
    n = v.sum()
    mu = (v * c).sum() / n
    rms = np.sqrt(max((v * (c - mu) ** 2).sum() / n, 0))
    neff = n ** 2 / max(h.variances().sum(), 1e-12)
    return mu, rms, rms / np.sqrt(neff), rms / np.sqrt(2 * neff)


RSHOW = ["all", "noJERfwd", "noJERsoft", "noJER"]


def recoil():
    L.append("== recoil u = -(MET + pT(ll)): <u_par + qT> and RMS(u_perp) [GeV], |u| < 100; columns data / " + " / ".join(RSHOW))
    for sel in ("Z", "Z+jet"):
        fig, axes = plt.subplots(2, 2, figsize=(20, 11), sharex=True, gridspec_kw={"hspace": 0.05})
        for j, ch in enumerate(CHANNELS):
            d0 = data_hist("metvar_recoil", ch, {"sel": sel, "comp": "uperp"})
            zb = d0.axes["zpt"].edges
            x = 0.5 * (zb[:-1] + np.minimum(zb[1:], 250))
            pts = {k: ([], []) for k in ["data"] + RSHOW}
            L.append(f"-- {sel}, {ch}")
            for i in range(len(zb) - 1):
                out = {}
                for comp in ("upar_qt", "uperp"):
                    out[("data", comp)] = moments(data_hist("metvar_recoil", ch, {"sel": sel, "comp": comp, "zpt": i}))
                    for k in RSHOW:
                        out[(k, comp)] = moments(mc_hist(k, "metvar_recoil", ch, {"sel": sel, "comp": comp, "zpt": i}))
                for k in pts:
                    pts[k][0].append(out[(k, "upar_qt")])
                    pts[k][1].append(out[(k, "uperp")])
                res[f"recoil_{sel}_{ch}_{i}"] = {k: [out[(k, 'upar_qt')][0], out[(k, 'uperp')][1]] for k in pts}
                L.append(f"   qT {zb[i]:4.0f}-{zb[i + 1]:<5.0f}| " + " / ".join(f"{out[(k, 'upar_qt')][0]:6.2f}" for k in pts)
                         + " | " + " / ".join(f"{out[(k, 'uperp')][1]:6.2f}" for k in pts))
            for k, col in [("data", "black")] + [(k, COL[k]) for k in RSHOW]:
                lab = "Data" if k == "data" else LAB[k]
                axes[0, j].errorbar(x, [p[0] for p in pts[k][0]], yerr=[p[2] for p in pts[k][0]], fmt="o-", color=col, label=lab)
                axes[1, j].errorbar(x, [p[1] for p in pts[k][1]], yerr=[p[3] for p in pts[k][1]], fmt="o-", color=col, label=lab)
            axes[0, j].axhline(0, color="black", lw=1, ls="--")
            axes[0, j].set_ylabel(r"$\langle u_\parallel + q_T \rangle$ [GeV]")
            axes[1, j].set_ylabel(r"RMS($u_\perp$) [GeV]")
            axes[1, j].set_xlabel(r"$q_T = p_T(\ell\ell)$ [GeV] (last bin 150+)")
            axes[0, j].text(0.04, 0.94, f"{CHANNELS[ch]}, {'Z events (no MET / jet cut)' if sel == 'Z' else 'all cuts except MET'}",
                            transform=axes[0, j].transAxes, fontsize=18, va="top")
            axes[1, j].legend(fontsize=13, loc="best")
            hep.cms.label("Preliminary", data=True, lumi=round(LUMI[ch] / 1000, 2), com=13.6, ax=axes[0, j], fontsize=16)
        fig.subplots_adjust(left=0.08, right=0.985, top=0.94, bottom=0.09, wspace=0.22)
        fig.savefig(os.path.join(OUTDIR, f"recoil_{sel.replace('+', '')}.png"), dpi=90)
        plt.close(fig)


overlay()
summary_points()
recoil()
open(os.path.join(OUTDIR, "metvar.txt"), "w").write("\n".join(L) + "\n")
json.dump(res, open(os.path.join(OUTDIR, "metvar.json"), "w"), indent=1, default=float)
print("\n".join(L))
print("plots in", OUTDIR)
