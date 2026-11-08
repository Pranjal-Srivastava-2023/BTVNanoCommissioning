"""Regression check of the 2026-11-08 Summer22 run (hists_zbzc_run3_v2) against the run behind the
237-page b/c-tag deck (hists_zbzc_run3_tag, commit 397eacb). Same 20 files per sample, same lumisections.
1. Zee: every histogram that exists in both runs, Zee channel, the old tag regions (incl + PNet L/M/T),
   all bins incl. flow, must be identical (nothing on the electron side changed). sumw identical.
2. Zmm: muvar 'prev' variant (old muon setup: leading-muon trigger SF, pT > 25) at stage final must
   reproduce the old Zmm z_pt (incl) per dataset; 'nominal' must equal the new main Zmm z_pt.
usage: python check_zbzc_v2_regression.py
"""
import glob
import os

import hist
import numpy as np
from coffea.util import load

OLD, NEW = "hists_zbzc_run3_tag/Summer22/zbzc_run3", "hists_zbzc_run3_v2/Summer22/zbzc_run3"
nbad = 0
tot = {}
for fo in sorted(glob.glob(f"{OLD}/*.coffea")):
    fn = os.path.join(NEW, os.path.basename(fo))
    o, n = load(fo), load(fn)
    ds = next(iter(o))
    o, n = o[ds], n[ds]
    isdata = ds.startswith(("Muon", "EGamma"))
    nh = ndiff = 0
    if not isdata and not np.isclose(o["sumw"], n["sumw"], rtol=1e-12):
        print(f"  {ds}: sumw differs {o['sumw']} {n['sumw']}"); ndiff += 1
    for k in sorted(set(o) & set(n)):
        ho, hn = o[k], n[k]
        if not isinstance(ho, hist.Hist) or "channel" not in [a.name for a in ho.axes]:
            continue
        sel = {"channel": "Zee"}
        if "tag" in [a.name for a in ho.axes]:
            for t in ho.axes["tag"]:
                a = ho[{**sel, "tag": t}].values(flow=True)
                b = hn[{**sel, "tag": t}].values(flow=True)
                nh += 1
                if a.shape != b.shape or not np.allclose(a, b, rtol=1e-9, atol=1e-12):
                    ndiff += 1; print(f"  {ds} {k} Zee {t}: DIFF sums {a.sum():.6g} {b.sum():.6g}")
        else:
            a, b = ho[sel].values(flow=True), hn[sel].values(flow=True)
            nh += 1
            if a.shape != b.shape or not np.allclose(a, b, rtol=1e-9, atol=1e-12):
                ndiff += 1; print(f"  {ds} {k} Zee: DIFF sums {a.sum():.6g} {b.sum():.6g}")
    # Zmm
    if not ds.startswith("EGamma"):
        old_mm = o["z_pt"][{"channel": "Zmm", "tag": "incl", "flav": sum, "pflav": sum}].sum(flow=True).value
        prev = n["muvar_z_pt"][{"variant": "prev", "stage": "final"}].sum(flow=True).value
        nom = n["muvar_z_pt"][{"variant": "nominal", "stage": "final"}].sum(flow=True).value
        new_mm = n["z_pt"][{"channel": "Zmm", "tag": "incl", "flav": sum, "pflav": sum}].sum(flow=True).value
        ok1, ok2 = np.isclose(prev, old_mm, rtol=1e-9), np.isclose(nom, new_mm, rtol=1e-9)
        ndiff += (not ok1) + (not ok2)
        mm = f"Zmm old {old_mm:.6g} prev {prev:.6g} [{'OK' if ok1 else 'DIFF'}]  new {new_mm:.6g} nominal {nom:.6g} [{'OK' if ok2 else 'DIFF'}]"
        tot[ds] = (old_mm, prev, new_mm, nom, n["sumw"] if not isdata else None)
    else:
        mm = ""
    nbad += ndiff
    print(f"{ds[:40]:40s} Zee hists compared {nh:4d}, differing {ndiff}  {mm}")
print("REGRESSION", "PASSED" if nbad == 0 else f"FAILED ({nbad})")
