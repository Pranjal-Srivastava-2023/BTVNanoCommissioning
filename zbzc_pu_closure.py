"""Why do the Zee and Zmm N(PV) data/MC look different? (advisor, 2026-11-08)

The MC pileup weight (official LUM puWeights.json.gz) reweights MC to the pileup profile of
the FULL era (Summer22: 2022 C-D golden). The small runs process only 20 data files per
channel, and the EGamma and Muon files cover different runs, so the data each channel sees
can have a different pileup profile from the full era.

1. brilcalc --byls (normtag_PHYSICS, minBiasXsec 69200 ub) on the lumisections each channel
   processed (hists_zbzc_run3/<campaign>/lumi_<PD>.json) and on the full era golden JSON;
   pileup profile = luminosity-weighted histogram of the per-LS average pileup (avgpu),
   1-unit bins. (Per-LS average: the bunch-by-bunch spread is ignored; the minimum-bias
   cross section cancels to first order in the subset / full ratio.)
2. Closure: MC N(PV) from pu_ntrue_npv (selected events, all weights), reweighted per channel
   by r(nTrueInt) = profile(channel lumisections) / profile(full era), compared with data N(PV).
   If the Zee slope in data/MC vs N(PV) goes away, it is the data sampling, not the electrons.
   RESULT (2026-11-08, v2 run): this per-bin reweighting OVERSHOOTS in both channels (Zmm, flat before,
   gets a rising slope), most likely because per-LS average pileup profiles ignore the bunch-by-bunch
   spread, so their ratio is too steep in the tails. Not used as a closure.
3. Mean-shift check (no reweighting): data - MC mean N(PV) per channel vs (mean pileup of the channel's
   lumisections - mean of the full era) x dN(PV)/d(nTrueInt) from the MC (straight-line fit of the
   mean N(PV) per nTrueInt bin). Robust against the profile shape.

Usage: python zbzc_pu_closure.py [run dir, default hists_zbzc_run3_v2/Summer22]
Output: <run dir>/pu/{lumi_*.csv, golden.csv, pu_profiles.json, pu_profiles.png,
        npv_closure.png, pu_closure.txt}
"""
import glob
import json
import os
import subprocess
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
ERA_RUNS = {"Summer22": (355100, 357900)}  # 2022 C-D (puwei_2022_preEE / Summer22 LUM)
GOLDEN = "src/BTVNanoCommissioning/data/DC/Cert_Collisions2022_355100_362760_Golden.json"
IMG = "/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/cms-cloud/brilws-docker:latest"
NORMTAG = "/cvmfs/cms-bril.cern.ch/cms-lumi-pog/Normtags/normtag_PHYSICS.json"
PD = {"Zee": "EGamma", "Zmm": "Muon"}
pudir = os.path.join(rundir, "pu")
os.makedirs(pudir, exist_ok=True)
XS = json.load(open("metadata/Zb_Zc_ratio_xsections_run3.json"))
lumi_file = os.path.join(rundir, "lumi.json")
if not os.path.exists(lumi_file):
    lumi_file = f"hists_zbzc_run3/{camp}/lumi.json"
LUMI = json.load(open(lumi_file))


def brilcalc_byls(json_in, csv_out):
    if os.path.exists(csv_out) and os.path.getsize(csv_out) > 0:
        return
    env = dict(os.environ, APPTAINER_BINDPATH="/cvmfs,/uscms_data,/uscms/home,/tmp")
    res = subprocess.run(
        ["apptainer", "-s", "exec", "--env", "PYTHONPATH=/home/bril/.local/lib/python3.10/site-packages",
         IMG, "brilcalc", "lumi", "--byls", "--normtag", NORMTAG, "-c", "web", "-u", "/pb",
         "--minBiasXsec", "69200", "-i", os.path.abspath(json_in), "--output-style", "csv"],
        capture_output=True, text=True, env=env, check=True)
    open(csv_out, "w").write(res.stdout)


def profile(csvs):
    """Luminosity-weighted avgpu histogram, bins 0..100 (1 unit), normalised; total lumi."""
    pu, lumi = [], []
    for f in csvs:
        for line in open(f):
            if line.startswith("#"):
                continue
            p = line.strip().split(",")
            lumi.append(float(p[6]))
            pu.append(float(p[7]))
    h, _ = np.histogram(pu, np.arange(101), weights=lumi)
    return h / h.sum(), float(np.sum(lumi)), float(np.average(pu, weights=lumi))


# 1. profiles
lo, hi = ERA_RUNS[camp]
g = {r: v for r, v in json.load(open(GOLDEN)).items() if lo <= int(r) <= hi}
json.dump(g, open(os.path.join(pudir, "golden_era.json"), "w"))
brilcalc_byls(os.path.join(pudir, "golden_era.json"), os.path.join(pudir, "golden.csv"))
prof = {"full": profile([os.path.join(pudir, "golden.csv")])}
for ch, pd in PD.items():
    csvs = []
    for js in sorted(glob.glob(f"hists_zbzc_run3/{camp}/lumi_{pd}_*.json")):
        out = os.path.join(pudir, os.path.basename(js).replace(".json", ".csv"))
        brilcalc_byls(js, out)
        csvs.append(out)
    prof[ch] = profile(csvs)
json.dump({k: {"fraction": v[0].tolist(), "lumi_pb": v[1], "mean_pu": v[2]} for k, v in prof.items()},
          open(os.path.join(pudir, "pu_profiles.json"), "w"), indent=1)

fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True, gridspec_kw={"height_ratios": [3, 1.3]})
cols = {"full": "black", "Zee": "#d62728", "Zmm": "#1f77b4"}
lab = {"full": f"2022 C-D golden (MC target)", "Zee": "EGamma lumisections (Zee)", "Zmm": "Muon lumisections (Zmm)"}
for k, (h, L, m) in prof.items():
    axes[0].stairs(h, np.arange(101), color=cols[k], lw=2, label=f"{lab[k]}: {L:.0f}/pb, mean {m:.1f}")
for k in ("Zee", "Zmm"):
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(prof["full"][0] > 1e-3, prof[k][0] / prof["full"][0], np.nan)
    axes[1].stairs(r, np.arange(101), color=cols[k], lw=2)
axes[1].axhline(1, color="grey")
axes[1].set_ylim(0, 2)
axes[1].set_ylabel("subset / full")
axes[1].set_xlabel("average pileup per lumisection (69.2 mb)")
axes[0].set_ylabel("fraction of luminosity")
axes[0].legend(fontsize=13)
axes[1].set_xlim(10, 65)
hep.cms.label("Preliminary", data=True, com=13.6, ax=axes[0], fontsize=14)
fig.tight_layout()
fig.savefig(os.path.join(pudir, "pu_profiles.png"), dpi=90)
plt.close(fig)

# 2. closure on N(PV)
OUT = {}
for f in sorted(glob.glob(f"{rundir}/zbzc_run3/zbzc_run3_*.coffea")):
    OUT.update(load(f))
T = [f"{camp}: N(PV) data/MC with the MC reweighted to each channel's own data pileup profile",
     "r(nTrueInt) = profile(channel lumisections) / profile(full era), bins of 1; MC with all weights", ""]
fig, axes = plt.subplots(2, 2, figsize=(22, 11), sharex=True, gridspec_kw={"height_ratios": [3, 1.3]})
for j, ch in enumerate(("Zee", "Zmm")):
    with np.errstate(divide="ignore", invalid="ignore"):
        rw = np.where(prof["full"][0] > 0, prof[ch][0] / prof["full"][0], 0.0)
    mc2d, data = None, None
    for ds, o in OUT.items():
        if ds.startswith(("Muon", "EGamma")):
            if ds.startswith(PD[ch]):
                h = o["npv"][{"channel": ch, "tag": "incl", "flav": sum, "pflav": sum}]
                data = h if data is None else data + h
            continue
        h = o["pu_ntrue_npv"][{"channel": ch}] * (XS[ds] * LUMI[ch] / o["sumw"])
        mc2d = h if mc2d is None else mc2d + h
    v2 = mc2d.values()  # ntrue (100) x npv (80)
    w2 = mc2d.variances()
    mc_nom, mc_rw = v2.sum(axis=0), (v2 * rw[:, None]).sum(axis=0)
    var_nom, var_rw = w2.sum(axis=0), (w2 * rw[:, None] ** 2).sum(axis=0)
    d = data.values()
    edges = data.axes[0].edges  # Integer(0, 80): N(PV) = n in [n, n + 1)
    cen = 0.5 * (edges[1:] + edges[:-1])
    ax, rax = axes[0, j], axes[1, j]
    ax.stairs(mc_nom, edges, color="grey", lw=2, label=f"MC, full-era PU weight ({mc_nom.sum():.0f})")
    ax.stairs(mc_rw, edges, color=cols[ch], lw=2, label=f"MC, reweighted to {PD[ch]} lumisections ({mc_rw.sum():.0f})")
    ax.errorbar(cen, d, yerr=np.sqrt(d), fmt="o", color="black", ms=4, label=f"Data ({d.sum():.0f})")
    ax.set_yscale("log")
    ax.set_ylim(0.5, d.max() * 30)
    ax.legend(fontsize=13)
    ax.set_ylabel("Events")
    ax.text(0.04, 0.94, {"Zee": r"Z$\to$ee", "Zmm": r"Z$\to\mu\mu$"}[ch], transform=ax.transAxes, fontsize=20, va="top")
    hep.cms.label("Preliminary", data=True, lumi=round(LUMI[ch] / 1000, 2), com=13.6, ax=ax, fontsize=14)
    T.append(f"== {ch}: data {d.sum():.0f}, MC {mc_nom.sum():.1f} (data/MC {d.sum() / mc_nom.sum():.4f}), "
             f"MC reweighted {mc_rw.sum():.1f} (data/MC {d.sum() / mc_rw.sum():.4f})")
    T.append(f"   mean N(PV): data {np.average(cen, weights=d):.2f}  MC {np.average(cen, weights=mc_nom):.2f}"
             f"  MC reweighted {np.average(cen, weights=mc_rw):.2f}")
    T.append(f"   {'N(PV)':>10s} {'data/MC':>16s} {'reweighted':>16s}   (MC normalised to data)")
    for name, mm, vv, col in (("full-era PU weight", mc_nom, var_nom, "grey"), ("reweighted", mc_rw, var_rw, cols[ch])):
        norm = d.sum() / mm.sum()
        with np.errstate(divide="ignore", invalid="ignore"):
            r = np.where((mm > 0) & (d > 0), d / (mm * norm), np.nan)
            e = r * np.sqrt(1 / d + vv / mm**2)
        rax.errorbar(cen, r, yerr=e, fmt="o", ms=4, color=col, label=name)
    for a, b in ((5, 15), (15, 20), (20, 25), (25, 30), (30, 35), (35, 40), (40, 45), (45, 55)):
        s = (cen >= a) & (cen < b)
        cells = []
        for mm, vv in ((mc_nom, var_nom), (mc_rw, var_rw)):
            norm = d.sum() / mm.sum()
            rr = d[s].sum() / (mm[s].sum() * norm)
            ee = rr * np.hypot(1 / np.sqrt(max(d[s].sum(), 1)), np.sqrt(vv[s].sum()) / mm[s].sum())
            cells.append(f"{rr:8.3f}+-{ee:.3f}")
        T.append(f"   {f'{a}-{b}':>10s} {cells[0]:>16s} {cells[1]:>16s}")
    # 3. mean-shift check
    v2w = v2.sum(axis=1)
    nt = np.arange(v2.shape[0]) + 0.5
    mean_npv = (v2 * edges[:-1]).sum(axis=1) / np.where(v2w > 0, v2w, 1)
    s3 = v2w > 0.02 * v2w.max()
    k = np.polyfit(nt[s3], mean_npv[s3], 1, w=np.sqrt(v2w[s3]))[0]
    dpu = prof[ch][2] - prof["full"][2]
    dnpv = np.average(edges[:-1], weights=d) - np.average(edges[:-1], weights=mc_nom)
    T.append(f"   mean-shift check: data - MC mean N(PV) = {dnpv:+.2f}; expected (mean pileup {prof[ch][2]:.2f} - "
             f"{prof['full'][2]:.2f} = {dpu:+.2f}) x dN(PV)/dnTrueInt {k:.3f} = {dpu * k:+.2f}")
    T.append("")
    rax.axhline(1, color="grey")
    rax.set_ylim(0.5, 1.5)
    rax.set_xlim(0, 65)
    rax.set_ylabel("Data / MC (shape)")
    rax.set_xlabel("N good primary vertices")
    rax.legend(fontsize=12, loc="upper left")
fig.tight_layout()
fig.savefig(os.path.join(pudir, "npv_closure.png"), dpi=90)
plt.close(fig)
open(os.path.join(pudir, "pu_closure.txt"), "w").write("\n".join(T) + "\n")
print("\n".join(T))
print("output in", pudir)
