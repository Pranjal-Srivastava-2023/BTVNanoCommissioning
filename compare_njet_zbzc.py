"""
Compare the scaled AK4 jet multiplicity (all flavours summed) between two Zb_Zc_ratio
AK4 outputs with different MC statistics, e.g. the 1-file and the 20-file-per-sample runs:

    python compare_njet_zbzc.py hists_zbzc_ak4_test/test_zbzc_ak4/test_zbzc_ak4.coffea "1 file / sample" \
        hists_zbzc_ak4_20files/merged/zbzc_ak4_20files.coffea "20 files / sample" <outdir>

writes <outdir>/n_jet_stats_compare.png and n_jet_stats_compare.txt (per-bin yield, MC stat
error and N_eff = (sum w)^2 / sum w^2). Both inputs are scaled to xsec * lumi / sumw.
"""
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
from coffea.util import load

plt.style.use(hep.style.CMS)
xs = json.load(open("metadata/Zb_Zc_ratio_xsections_Summer22.json"))
LUMI = xs["lumi_pb"]
CHS = {"Zee": r"Z$\to$ee", "Zmm": r"Z$\to\mu\mu$"}
inputs = [(sys.argv[1], sys.argv[2]), (sys.argv[3], sys.argv[4])]
outdir = sys.argv[5]
os.makedirs(outdir, exist_ok=True)
STYLE = [dict(color="#9e9e9e", marker="o", mfc="white", ms=9, mew=2),
         dict(color="#1f5fa8", marker="o", ms=8)]


def njet(infile):
    """Scaled n_jet per channel, all flavours summed: (edges, {ch: (values, variances)})."""
    tot = None
    for ds, o in load(infile).items():
        h = o["n_jet"] * (xs[ds] * LUMI / o["sumw"])
        tot = h if tot is None else tot + h
    tot = tot[{"flav": sum, "pflav": sum}]
    return tot.axes["n"].edges, {ch: (tot[{"channel": ch}].values(), tot[{"channel": ch}].variances())
                                 for ch in CHS}


res = [(lab, *njet(f)) for f, lab in inputs]
fig, axes = plt.subplots(1, 2, figsize=(20, 8))
lines = [f"scaled to {LUMI / 1000:.2f} /fb; value +- MC stat error (N_eff)"]
for ax, ch in zip(axes, CHS):
    lines.append(f"-- {ch}")
    lines.append(f"{'N_jet':>6s}" + "".join(f"{lab:>34s}" for lab, *_ in res))
    for i, (lab, edges, d) in enumerate(res):
        v, var = d[ch]
        x = edges[:-1] + 0.5 * np.diff(edges) + (i - 0.5) * 0.12
        ok = v > 0
        ax.errorbar(x[ok], v[ok], yerr=np.sqrt(var[ok]), ls="none", label=lab, elinewidth=2, capsize=0, **STYLE[i])
    for b in range(len(res[0][1]) - 1):
        cells = []
        for lab, edges, d in res:
            v, var = d[ch]
            neff = v[b] ** 2 / var[b] if var[b] > 0 else 0
            cells.append(f"{v[b]:12.1f} +- {np.sqrt(var[b]):8.1f} ({neff:7.1f})")
        lines.append(f"{int(res[0][1][b]):6d}" + "".join(f"{c:>34s}" for c in cells))
    ax.set_yscale("log")
    ax.set_xlabel("N AK4 jets")
    ax.set_ylabel("Events (scaled)")
    ax.set_xticks(range(0, 10))
    ax.grid(axis="y", color="#e0e0e0", lw=1)
    ax.set_axisbelow(True)
    ax.legend(title=CHS[ch], loc="upper right", fontsize=18, title_fontsize=20)
    hep.cms.label("Preliminary", data=False, lumi=round(LUMI / 1000, 2), com=13.6, ax=ax, fontsize=18)
fig.tight_layout()
fig.savefig(os.path.join(outdir, "n_jet_stats_compare.png"), dpi=90)
open(os.path.join(outdir, "n_jet_stats_compare.txt"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
