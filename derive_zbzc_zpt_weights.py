"""Z pT weights for the DY MC of the Zb_Zc_ratio Run 3 run, from Z->mumu.

Per campaign: w(pT(ll)) = [(data - non-DY MC) / DY MC] in bins of reco pT(ll), for
all Z events before the MET and jet cuts (stage_z_pt, all stages, from
hists_zbzc_run3_stage/<campaign>/), divided by the same ratio over all bins, so the
weights change the DY shape only, not its total. Bins above 200 GeV are merged
for statistics. Z->ee is not used and serves as the check.

Output: src/BTVNanoCommissioning/data/ZbZc/zpt_weights_run3.json
    {campaign: {"edges": [...], "weights": [...], "errors": [...], "norm": R_tot}}
and a printed Z->ee check: data/MC per bin before and after the weights.
"""
import glob
import json

import numpy as np
from coffea.util import load

CAMPAIGNS = ["Summer22", "Summer22EE", "Summer23", "Summer23BPix"]
STAGES = ["none", "MET", "jet", "MET+jet"]
EDGES = [0, 5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100, 125, 150, 200, 300, 1000]
XS = json.load(open("metadata/Zb_Zc_ratio_xsections_run3.json"))


def rebin(values, edges):
    """Sum the stage_z_pt bins into EDGES (EDGES is a subset of the stage edges)."""
    idx = [int(np.where(np.isclose(edges, e))[0][0]) for e in EDGES]
    return np.array([values[a:b].sum() for a, b in zip(idx[:-1], idx[1:])])


def components(c, ch):
    """data, DY, other MC, DY variance in EDGES bins (Z only = all stages)."""
    out = {}
    for f in sorted(glob.glob(f"hists_zbzc_run3_stage/{c}/zbzc_run3/zbzc_run3_*.coffea")):
        out.update(load(f))
    lumi = json.load(open(f"hists_zbzc_run3/{c}/lumi.json"))
    d = dy = bkg = dyw2 = 0
    for ds, o in out.items():
        h = o["stage_z_pt"][{"channel": ch, "flav": sum, "pflav": sum, "stage": sum}]
        e = h.axes[0].edges
        if ds.startswith("Muon" if ch == "Zmm" else "EGamma"):
            d = d + rebin(h.values(), e)
        elif ds.startswith(("Muon", "EGamma")):
            continue
        else:
            s = XS[ds] * lumi[ch] / o["sumw"]
            if ds.startswith("DYto2L"):
                dy = dy + rebin(h.values(), e) * s
                dyw2 = dyw2 + rebin(h.variances(), e) * s * s
            else:
                bkg = bkg + rebin(h.values(), e) * s
    return d, dy, bkg, dyw2


result = {}
for c in CAMPAIGNS:
    d, dy, bkg, dyw2 = components(c, "Zmm")
    norm = (d.sum() - bkg.sum()) / dy.sum()
    r = (d - bkg) / dy
    err = np.sqrt(d + dyw2 * r**2) / dy
    result[c] = {"edges": EDGES, "weights": list(np.round(r / norm, 4)),
                 "errors": list(np.round(err / norm, 4)), "norm": round(float(norm), 4)}

    # Z->ee check with the Z->mumu weights
    de, dye, bkge, _ = components(c, "Zee")
    w = r / norm
    before = de / (dye + bkge)
    after = de / (dye * w + bkge)
    lab = [f"{a:g}-{b:g}" for a, b in zip(EDGES[:-1], EDGES[1:])]
    print(f"\n{c}: Zmm norm (data-bkg)/DY = {norm:.3f}")
    print("  bin       w(Zmm)         Zee data/MC before -> after")
    for i, l in enumerate(lab):
        print(f"  {l:9s} {w[i]:.3f}±{err[i] / norm:.3f}   {before[i]:.3f} -> {after[i]:.3f}")
    tot_b = de.sum() / (dye + bkge).sum()
    tot_a = de.sum() / (dye * w + bkge).sum()
    print(f"  Zee total {tot_b:.3f} -> {tot_a:.3f};  spread of Zee data/MC over bins (rms) "
          f"{np.std(before / tot_b):.3f} -> {np.std(after / tot_a):.3f}")

json.dump(result, open("src/BTVNanoCommissioning/data/ZbZc/zpt_weights_run3.json", "w"), indent=1)
print("\nwrote src/BTVNanoCommissioning/data/ZbZc/zpt_weights_run3.json")
