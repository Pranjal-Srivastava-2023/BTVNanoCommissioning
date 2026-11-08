"""Tagger comparison table from the yields_<region>.txt files of a Zb_Zc_ratio run
(PNet / DeepJet / RobustParT, b- and c-tag, WP L/M/T, each with its own BTV SFs).
Per region and channel: data, MC, data/MC, DY b and c fractions (purity of the tagged sample),
and the tagging fraction tagged/inclusive in data and MC with their ratio (the double ratio
cancels the overall normalisation, so it tests the tagging + SFs). Errors: stat. of data and MC.
usage: python summarize_zbzc_taggers.py [run dir, default hists_zbzc_run3_v2/Summer22]
output: <run dir>/tagger_summary.txt
"""
import os
import re
import sys

import numpy as np

rundir = sys.argv[1] if len(sys.argv) > 1 else "hists_zbzc_run3_v2/Summer22"


def read(fn):
    lines = open(fn).read().splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith("== hadronFlavour"))
    res = {}
    for k in range(i + 2, len(lines)):
        if lines[k].startswith("=="):
            break
        p = lines[k].split()
        if p and p[0] in ("Zee", "Zmm"):
            e = lines[k + 1].split()
            fr = re.findall(r"b frac ([\d.]+)\s+c frac ([\d.]+)", lines[k + 2])
            res[p[0]] = dict(mc=float(p[6]), mce=float(e[6]), data=float(p[7]), bfrac=float(fr[0][0]), cfrac=float(fr[0][1]))
    return res


incl = read(os.path.join(rundir, "yields.txt"))
L = [f"{rundir}: tagger comparison (leading jet tagged; each tagger with its own BTV SFs)",
     "eff = tagged / inclusive events; eff ratio = eff(data) / eff(MC) (normalisation cancels);",
     "b, c frac = DY b-jet and c-jet fractions of the tagged DY MC; errors: stat. (binomial for eff(data))", ""]
for ch in ("Zee", "Zmm"):
    I = incl[ch]
    L.append(f"== {ch}: inclusive data {I['data']:.0f}, MC {I['mc']:.1f}, data/MC {I['data'] / I['mc']:.3f}, "
             f"DY b frac {I['bfrac']:.3f}, c frac {I['cfrac']:.3f}")
    L.append(f"{'region':20s} {'data':>7s} {'MC':>9s} {'data/MC':>14s} {'b frac':>7s} {'c frac':>7s}"
             f" {'eff data':>9s} {'eff MC':>8s} {'eff ratio':>14s}")
    for kind in ("btag", "ctag"):
        for tg in ("", "DeepJet", "RobustParT"):
            for wp in "LMT":
                reg = f"{kind}{tg}_{wp}"
                fn = os.path.join(rundir, f"yields_{reg}.txt")
                if not os.path.exists(fn):
                    continue
                R = read(fn)[ch]
                r = R["data"] / R["mc"]
                re_ = r * np.hypot(R["data"] ** -0.5, R["mce"] / R["mc"])
                ed, em = R["data"] / I["data"], R["mc"] / I["mc"]
                ede = np.sqrt(ed * (1 - ed) / I["data"])
                eme = R["mce"] / I["mc"]  # tagged MC stat (dominant)
                er = ed / em
                ere = er * np.hypot(ede / ed, eme / em)
                name = f"{kind} {tg or 'PNet'} {wp}"
                L.append(f"{name:20s} {R['data']:7.0f} {R['mc']:9.1f} {r:7.3f}+-{re_:.3f} {R['bfrac']:7.3f} {R['cfrac']:7.3f}"
                         f" {ed:9.4f} {em:8.4f} {er:7.3f}+-{ere:.3f}")
        L.append("")
open(os.path.join(rundir, "tagger_summary.txt"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
