"""Z peak in data vs MC before and after the electron smearing fix.

Old MC: hists_zbzc_run3/<campaign>/ (EGM_shifts drew one random number per event, so both
electrons of a Z->ee pair were smeared together). New MC: hists_zbzc_run3_smearfix/<campaign>/
(run_zbzc_run3_smearfix.sh, one random number per electron). Only DY and ttbar were rerun;
data, VV and the lumi are unchanged by the fix and come from the old directory.

For each campaign and channel: Gaussian fit to the peak core (86-96 GeV) of data, old MC and
new MC (peak position and width), median in 81-101 GeV, data/MC yield in 71-111 GeV, and a
plot of m(ll) with data/MC for both MC versions. Z->mumu is the control (should not move).

Usage:  python compare_zee_smearfix.py [campaign ...]    (default: all four)
Output: hists_zbzc_run3_smearfix/<campaign>/z_mass_smearfix.png,
        hists_zbzc_run3_smearfix/zee_smearfix_summary.txt
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
from scipy.optimize import curve_fit

hep.style.use("CMS")

CAMPAIGNS = sys.argv[1:] or ["Summer22", "Summer22EE", "Summer23", "Summer23BPix"]
ERAS = {"Summer22": "2022 C-D", "Summer22EE": "2022 E-G", "Summer23": "2023 C",
        "Summer23BPix": "2023 D"}
CH_LABEL = {"Zee": r"Z$\to$ee", "Zmm": r"Z$\to\mu\mu$"}
XS = json.load(open("metadata/Zb_Zc_ratio_xsections_run3.json"))
RERUN = ("DYto2L", "TTto2L2Nu")


def load_dir(d):
    out = {}
    for f in sorted(glob.glob(f"{d}/zbzc_run3/zbzc_run3_*.coffea")):
        out.update(load(f))
    return out


def gaus(x, n, m, s):
    return n * np.exp(-0.5 * ((x - m) / s) ** 2)


def peak(h):
    """Gaussian core fit (86-96 GeV): mean, its error, sigma; median in 81-101 GeV."""
    v, w2, c = h.values(), h.variances(), h.axes[0].centers
    sel = (c > 86) & (c < 96)
    p, cov = curve_fit(gaus, c[sel], v[sel], p0=[v[sel].max(), 91, 2.5],
                       sigma=np.sqrt(np.maximum(w2[sel], 1e-9)), absolute_sigma=True)
    win = (c > 81) & (c < 101)
    cdf = np.cumsum(v[win]) / v[win].sum()
    return p[1], np.sqrt(cov[1, 1]), abs(p[2]), np.interp(0.5, cdf, c[win])


lines = ["Z peak, data vs MC, before (old) and after (new) the electron smearing fix",
         "Gaussian fit to 86-96 GeV; dm = data - MC peak; sigma in GeV; yield = data/MC in 71-111 GeV",
         ""]
for camp in CAMPAIGNS:
    old = load_dir(f"hists_zbzc_run3/{camp}")
    new = load_dir(f"hists_zbzc_run3_smearfix/{camp}")
    missing = [ds for ds in old if ds.startswith(RERUN) and ds not in new]
    if missing:
        print(f"{camp}: not all reruns done yet ({len(missing)} missing), skipped")
        continue
    lumi = json.load(open(f"hists_zbzc_run3/{camp}/lumi.json"))
    fig, axes = plt.subplots(2, 2, figsize=(20, 10.5), sharex="col",
                             gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05})
    lines.append(f"{camp} ({ERAS[camp]})")
    for ax, rax, ch in zip(axes[0], axes[1], ["Zee", "Zmm"]):
        hists = {}
        for label, src in [("old", old), ("new", {**old, **new})]:
            mc = None
            for ds, o in src.items():
                if ds.startswith(("Muon", "EGamma")):
                    continue
                h = o["z_mass"][{"channel": ch, "flav": sum, "pflav": sum}]
                h = h * (XS[ds] * lumi[ch] / o["sumw"])
                mc = h if mc is None else mc + h
            hists[label] = mc
        data = None
        for ds, o in old.items():
            if ds.startswith("Muon" if ch == "Zmm" else "EGamma"):
                h = o["z_mass"][{"channel": ch, "flav": sum, "pflav": sum}]
                data = h if data is None else data + h
        fd = peak(data)
        lines.append(f"  {ch}: data peak {fd[0]:.3f} +- {fd[1]:.3f}  sigma {fd[2]:.2f}  median {fd[3]:.3f}")
        for label in ["old", "new"]:
            f = peak(hists[label])
            yld = data.values().sum() / hists[label].values().sum()
            lines.append(f"       {label} MC  peak {f[0]:.3f} +- {f[1]:.3f}  sigma {f[2]:.2f}  "
                         f"median {f[3]:.3f} | dm {fd[0] - f[0]:+.3f} GeV ({(fd[0] / f[0] - 1) * 100:+.2f}%)  "
                         f"dmedian {fd[3] - f[3]:+.3f}  sigma data/MC {fd[2] / f[2]:.3f}  yield {yld:.3f}")
        edges = data.axes[0].edges
        d = data.values()
        hep.histplot(hists["old"].values(), edges, ax=ax, color="#c0392b", ls="--", lw=2,
                     label="MC, old smearing (per event)")
        hep.histplot(hists["new"].values(), edges, ax=ax, color="#2471a3", lw=2,
                     label="MC, fixed smearing (per electron)")
        hep.histplot(d, edges, ax=ax, histtype="errorbar", color="black", yerr=np.sqrt(d), label="Data")
        ax.set_ylim(0, max(d.max(), hists["old"].values().max()) * 1.45)
        ax.set_ylabel("Events / GeV")
        ax.set_xlabel("")
        ax.text(0.04, 0.94, CH_LABEL[ch], transform=ax.transAxes, fontsize=20, va="top")
        ax.legend(fontsize=14, loc="upper right")
        hep.cms.label("Preliminary", data=True, lumi=round(lumi[ch] / 1000, 2), com=13.6,
                      ax=ax, fontsize=18)
        with np.errstate(divide="ignore", invalid="ignore"):
            for label, col, mk in [("old", "#c0392b", "s"), ("new", "#2471a3", "o")]:
                m = hists[label].values()
                rax.errorbar(data.axes[0].centers + (0.12 if label == "new" else -0.12),
                             d / m, yerr=np.sqrt(d) / m, fmt=mk, color=col, ms=5)
        rax.axhline(1, color="black", lw=1, ls="--")
        rax.set_ylim(0.7, 1.3)
        rax.set_ylabel("Data / MC", fontsize=20)
        rax.set_xlabel(data.axes[0].label)
    fig.subplots_adjust(left=0.07, right=0.985, top=0.94, bottom=0.11, wspace=0.2)
    os.makedirs(f"hists_zbzc_run3_smearfix/{camp}", exist_ok=True)
    fig.savefig(f"hists_zbzc_run3_smearfix/{camp}/z_mass_smearfix.png", dpi=90)
    plt.close(fig)
    lines.append("")

print("\n".join(lines))
if len(CAMPAIGNS) == 4:
    open("hists_zbzc_run3_smearfix/zee_smearfix_summary.txt", "w").write("\n".join(lines) + "\n")
