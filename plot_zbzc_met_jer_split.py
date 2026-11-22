"""Plots for the MET > 50 Phase 1 study (study_zbzc_met_jer_split.py): share of the JER-induced increase of
the MC MET 50-100 fraction coming from each jet class, per channel, Z+jet stage (all cuts except MET).
Usage: python plot_zbzc_met_jer_split.py hists_zbzc_run3_metsplit/Summer22
"""
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

d = sys.argv[1]
js = json.load(open(os.path.join(d, "met_jer_split.json")))
outd = os.path.join(d, "plots")
os.makedirs(outd, exist_ok=True)

GROUPS = [
    ("Jet collection", ["JER: Jet collection only", "JER: CorrT1METJet only"]),
    ("gen matching", ["JER: gen-matched Jet only (= run C)", "JER: unmatched Jet only", "JER: CorrT1METJet only"]),
    ("jet pT (JEC)", ["JER: JEC pT 0-20 only", "JER: JEC pT 20-30 only", "JER: JEC pT 30-50 only", "JER: JEC pT 50-inf only"]),
    ("jet |eta|", ["JER: |eta| 0-1.3 only", "JER: |eta| 1.3-2.5 only", "JER: |eta| 2.5-3.0 only", "JER: |eta| 3.0-5.2 only"]),
    ("|eta| 2.5-3.139 in JER SF bins", ["JER: |eta| 2.5-2.65 only", "JER: |eta| 2.65-2.853 only",
                                       "JER: |eta| 2.853-2.964 only", "JER: |eta| 2.964-3.139 only"]),
    ("removing the high-SF region", ["JER: all (= run A)", "JER: all except |eta| 2.65-2.964",
                                     "JER: all except |eta| 2.5-3.139", "no JER in MET (= run B MET)"]),
]


def short(k):
    return k.replace("JER: ", "").replace(" only", "")


for stage in ["Z+jet (all cuts except MET)", "Z (no jet cut)"]:
    fig, axes = plt.subplots(len(GROUPS), 1, figsize=(9, 2.2 * len(GROUPS) + 1))
    for ax, (title, keys) in zip(axes, GROUPS):
        y = np.arange(len(keys))
        for i, ch in enumerate(["Zee", "Zmm"]):
            r = js[f"{ch} | {stage}"]
            vals = [100 * (r[k]["ratio_noJER"] - 1) for k in keys]
            ax.barh(y + (0.2 if i else -0.2), vals, height=0.38, color=["#3b75af", "#d1495b"][i],
                    label=ch.replace("Zee", "Z→ee").replace("Zmm", "Z→μμ"))
            for yy, v in zip(y + (0.2 if i else -0.2), vals):
                ax.text(v + 0.5, yy, f"{v:+.1f}%", va="center", fontsize=7)
        ax.set_yticks(y)
        ax.set_yticklabels([short(k) for k in keys], fontsize=8)
        ax.invert_yaxis()
        ax.set_title(title, fontsize=9, loc="left")
        ax.axvline(0, color="k", lw=0.6)
    xmax = max(100 * (js[f"{ch} | {stage}"][k]["ratio_noJER"] - 1) for ch in ("Zee", "Zmm") for _, ks in GROUPS for k in ks)
    for ax in axes:
        ax.set_xlim(0, 1.15 * xmax)
    axes[0].legend(fontsize=8, loc="lower right")
    axes[-1].set_xlabel("Increase of the MC fraction of events with 50 < MET < 100 GeV\n"
                        "when only these jets are JER-smeared in the type-1 MET (vs no JER in the MET) [%]", fontsize=9)
    fig.suptitle(f"Summer22 DY MC, {stage}: which jets make the MET grow under JER smearing", fontsize=10)
    fig.tight_layout()
    tag = "zjet" if "jet (all" in stage else "z"
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(outd, f"met_jer_split_{tag}.{ext}"), dpi=130)
    plt.close(fig)
print("plots in", outd)
