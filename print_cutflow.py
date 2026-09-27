"""Cutflow tables for one era's merged QCD_sf output.

1. Object-level cutflow (`cutflow`): per dataset, "Total Events" is an event count
   but every later step counts objects (electrons, muons, AK8 jets) passing it.
2. Zee and Zmm event cutflows (`cutflow_Zee`, `cutflow_Zmm`): raw event counts per
   dataset. Data rows are only meaningful for the channel's own primary dataset
   (Zee: EGamma/SingleElectron, Zmm: SingleMuon); the other PD is shown in
   brackets for reference.
3. Final yields per process group in Z_jet / Z_bjet, MC scaled by xsec*lumi/sumw
   (integral of cmp_pt_zcand incl. flow, the same numbers as compare_yields_old_new.py).

Usage: python3 print_cutflow.py [--era 2018] [--input merged.coffea] [--outdir dir]
Writes <outdir>/../cutflow_<era>.txt and prints it.
"""
import os

from qcd_sf_plot_common import GROUPS, EraOutput, parse_args


def short(name):
    return name.split("_TuneCP5")[0]


def table(era, key, datasets, bracket=()):
    steps = list(era.out[datasets[0]][key].keys())
    w = max(len(short(d)) for d in datasets) + 2
    cw = [max(14, len(s) + 2) for s in steps]
    lines = [f"{'dataset':{w}s}" + "".join(f"{s:>{c}s}" for s, c in zip(steps, cw))]
    for d in datasets:
        row = [era.out[d][key].get(s, 0) for s in steps]
        cells = "".join(f"{('[%d]' % v) if d in bracket else v:>{c}}" for v, c in zip(row, cw))
        lines.append(f"{short(d):{w}s}" + cells)
    return lines


def yields(era):
    lines = []
    for region in ["Z_jet", "Z_bjet"]:
        for channel in ["Zee", "Zmm"]:
            sel = {"region": region, "channel": channel}
            mc = {g: h.sum(flow=True) for g, h in era.mc_groups("cmp_pt_zcand", sel).items()}
            data = era.data("cmp_pt_zcand", sel).sum(flow=True).value
            tot = sum(v.value for v in mc.values())
            lines.append(f"\n{region} {channel}")
            for g in GROUPS:
                lines.append(f"  {g:12s}{mc[g].value:12.1f} +- {mc[g].variance ** 0.5:7.1f}  ({mc[g].value / tot:6.1%})")
            lines.append(f"  {'MC total':12s}{tot:12.1f}")
            lines.append(f"  {'Data':12s}{data:12.0f}")
            lines.append(f"  {'Data/MC':12s}{data / tot:12.3f}")
    return lines


if __name__ == "__main__":
    args = parse_args(__doc__)
    era = EraOutput(args.era, args.input)
    mc = [s for g in GROUPS.values() for s in g]
    ele_pd, mu_pd = era.cfg["ele_pd"], era.cfg["mu_pd"]

    out = [f"QCD_sf cutflow, {args.era}, lumi {era.lumi:.0f} /pb, input {args.input}", ""]
    out += ["== Object-level cutflow (Total Events = events; other columns = object counts) =="] + table(era, "cutflow", mc + [ele_pd, mu_pd])
    out += ["", "== Zee cutflow (raw events; [..] = not the Zee primary dataset) =="]
    out += table(era, "cutflow_Zee", mc + [ele_pd, mu_pd], bracket=(mu_pd,))
    out += ["", "== Zmm cutflow (raw events; [..] = not the Zmm primary dataset) =="]
    out += table(era, "cutflow_Zmm", mc + [ele_pd, mu_pd], bracket=(ele_pd,))
    out += ["", "== Final yields (MC xsec*lumi/sumw-scaled, stat. unc.) =="] + yields(era)

    text = "\n".join(out)
    print(text)
    path = os.path.join(os.path.dirname(args.outdir.rstrip("/")), f"cutflow_{args.era}.txt")
    with open(path, "w") as f:
        f.write(text + "\n")
    print("\nsaved", path)
