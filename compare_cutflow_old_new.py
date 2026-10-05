"""Old (ZbAnalysis_boosted, aligned ZbSelection.cxx) vs new (BTVNanoCommissioning QCD_sf) data cutflow.

usage: python cmp_cutflow_old_new.py ERA OLD_SAMPLE NEW_DATASET [OLD_DIR] [OUTDIR]
  e.g. python cmp_cutflow_old_new.py 2017 SingleElectron_DATA_2017 SingleElectron_Run2017
"""
import sys
import numpy as np
import uproot
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from coffea.util import load

ERA, OLD_SAMPLE, DS = sys.argv[1:4]
OLD_BASE = ("/uscms/home/psrivast/nobackup/ZbExercize/CMSSW_14_0_6/src/Zb/CMSSW_14_0_6/src/"
            "ZbAnalysis_boosted/")
OLD_DIR = sys.argv[4] if len(sys.argv) > 4 else "condor_output_mSD_evt"
NEW_BASE = "/uscms/home/psrivast/nobackup/BTVNanoCommissioning/"
OUTDIR = sys.argv[5] if len(sys.argv) > 5 else f"{NEW_BASE}hists_run{ERA}_mSD_SF/"
OLD_FILE = f"{OLD_BASE}{OLD_DIR}/{OLD_SAMPLE}.root"
NEW_FILE = f"{NEW_BASE}hists_run{ERA}_mSD_SF/merged_run{ERA}.coffea"
PD = DS.split("_Run")[0]
TAG = f"{PD}{ERA}"

# (section, label, old hist, old bin, new dict, new key)
ROWS = [("Events", "all events", "Nevt", 0, "cutflow", "Total Events")]
ROWS += [("Electrons", l, "ele_cutflow", i + 1, "cutflow", k) for i, (l, k) in enumerate(
    [("all", "ele_all"), ("IP", "ele_ip"), ("pT, eta", "ele_kin"), ("EB-EE gap", "ele_EE_EB"), ("tight ID", "ele_ID")])]
ROWS += [("Muons", l, "muon_cutflow", i + 1, "cutflow", k) for i, (l, k) in enumerate(
    [("all", "mu_all"), ("pT, eta", "mu_kin"), ("medium ID", "mu_ID"), ("iso", "mu_iso")])]
ROWS += [("AK8 jets", l, "Jet_cutflow", i + 1, "cutflow", k) for i, (l, k) in enumerate(
    [("all", "jet_all"), ("ele removal", "jet_ele_removed"), ("mu removal", "jet_mu_removed"),
     ("jet ID", "jet_ID"), ("2 subjets", "subjet_req")])]
for sec, h, dct, lep in [("Zee events", "zee_cutflow", "cutflow_Zee", "electron"),
                         ("Zmm events", "zmm_cutflow", "cutflow_Zmm", "muon")]:
    ROWS += [(sec, l, h, i + 2, dct, k) for i, (l, k) in enumerate(
        [("trigger", "trigger"), (f"2 {lep}s", lep), ("Z mass", "Zmass"), ("MET", "MET"),
         ("jet (Z_jet)", "jet"), ("b-jet (Z_bjet)", "bjet")])]

old_f = uproot.open(OLD_FILE)
new = load(NEW_FILE)[DS]
old = np.array([old_f[h].values()[b] for _, _, h, b, _, _ in ROWS], dtype=float)
nw = np.array([new[d][k] for _, _, _, _, d, k in ROWS], dtype=float)

# ---- table ----
head = f"Cutflow {PD} {ERA}: "
lines = [f"{head}OLD = {OLD_FILE}", f"{' ' * len(head)}NEW = {NEW_FILE} [{DS}]",
         "Object sections count objects; Events/Zee/Zmm sections count events.", "",
         f"{'section':11s} {'step':16s} {'old':>14s} {'new':>14s} {'new-old':>9s} {'new/old':>10s}"]
prev = None
for (sec, lab, *_), o, n in zip(ROWS, old, nw):
    if sec != prev and prev is not None:
        lines.append("")
    lines.append(f"{sec if sec != prev else '':11s} {lab:16s} {o:14,.0f} {n:14,.0f} {n - o:+9,.0f} {n / o:10.6f}")
    prev = sec
table = "\n".join(lines)
print(table)
open(f"{OUTDIR}cutflow_{TAG}_old_vs_new.txt", "w").write(table + "\n")

# ---- plot ----
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
C_OLD, C_NEW = "#2a78d6", "#eb6834"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "text.color": INK})

x = np.arange(len(ROWS))
w = 0.38
fig, (ax, rx) = plt.subplots(2, 1, figsize=(15, 8), sharex=True, facecolor=SURF,
                             gridspec_kw={"height_ratios": [3, 1.2], "hspace": 0.06})
for a in (ax, rx):
    a.set_facecolor(SURF)
    for s in ("top", "right"):
        a.spines[s].set_visible(False)

ax.bar(x - w / 2 - 0.01, old, w, color=C_OLD, label="old framework (rerun)", zorder=3)
ax.bar(x + w / 2 + 0.01, nw, w, color=C_NEW, label="new framework", zorder=3)
ax.set_yscale("log")
ax.set_ylim(10, 2e10)
ax.set_ylabel("count (objects or events)")
ax.grid(axis="y", color=GRID, lw=0.8, zorder=0)
ax.legend(loc="lower right", bbox_to_anchor=(1.0, 1.07), ncol=2, frameon=False, handlelength=1.2)
ax.set_title(f"Cutflow, {PD} {ERA} data: old vs new framework", loc="left", fontsize=13, pad=30)

secs = [r[0] for r in ROWS]
starts = [i for i in range(len(secs)) if i == 0 or secs[i] != secs[i - 1]]
for j, s in enumerate(starts):
    e = starts[j + 1] if j + 1 < len(starts) else len(secs)
    if s > 0:
        for a in (ax, rx):
            a.axvline(s - 0.5, color=INK2, lw=0.8, ls=(0, (3, 3)), zorder=1)
    ax.text((s + e - 1) / 2, 1.01, secs[s], transform=ax.get_xaxis_transform(),
            ha="center", va="bottom", fontsize=10, color=INK2)

# ratio panel: new/old - 1 in parts per million keeps the tiny residuals readable
dev = (nw / old - 1) * 1e6
rx.axhline(0, color=INK2, lw=1, zorder=1)
rx.plot(x, dev, "o", ms=6, color=INK, zorder=3)
rx.set_ylabel("new/old − 1  [ppm]")
rx.grid(axis="y", color=GRID, lw=0.8, zorder=0)
lim = max(50, np.abs(dev).max() * 1.35)
rx.set_ylim(-lim, lim)
i_big = int(np.argmax(np.abs(dev)))
rx.annotate(f"{old[i_big]:,.0f} → {nw[i_big]:,.0f}  ({nw[i_big] - old[i_big]:+.0f})",
            (x[i_big], dev[i_big]), xytext=(-12, -4), textcoords="offset points",
            ha="right", va="center", fontsize=9, color=INK2)

rx.set_xticks(x)
rx.set_xticklabels([r[1] for r in ROWS], rotation=55, ha="right")
rx.set_xlim(-0.6, len(ROWS) - 0.4)
png = f"{OUTDIR}plots/cutflow_{TAG}_old_vs_new.png" if len(sys.argv) <= 5 else f"{OUTDIR}cutflow_{TAG}_old_vs_new.png"
fig.savefig(png, dpi=150, bbox_inches="tight", facecolor=SURF)
print("\nwrote", png)
