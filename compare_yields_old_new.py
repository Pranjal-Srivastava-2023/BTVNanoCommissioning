"""Compare QCD_sf event yields against the old ROOT-based ZbAnalysis_boosted tables.

New-framework yields are the integrals (incl. under/overflow) of cmp_pt_zcand per
region/channel, MC scaled by xsec * lumi / sumw. As in the old framework, Zee data
is taken only from the electron primary dataset (EGamma / SingleElectron) and Zmm
data only from SingleMuon, so events present in both are not double-counted.

Old yields are parsed from the old framework's event_counts_<region>_amcnlo.txt.

Usage:
    python3 compare_yields_old_new.py --new <merged.coffea> [--era 18]
"""
import argparse
import json

from coffea.util import load

OLD_DIR = (
    "/uscms/home/psrivast/nobackup/ZbExercize/CMSSW_14_0_6/src/Zb/CMSSW_14_0_6/src/"
    "ZbAnalysis_boosted/condor_output_mSD"
)
# era label in the old tables -> (lumi in /pb from old Configs/config.ini, xsec json)
ERAS = {
    "18": (59832.0, "metadata/QCD_sf_xsections_2018.json"),
}
GROUPS = {
    "DY": ["DYJetsToLL_0J", "DYJetsToLL_1J", "DYJetsToLL_2J"],
    "tt": ["TTTo2L2Nu", "TTToSemiLeptonic"],
    "ST": ["ST_"],
    "VV": ["WW_", "WZ_", "ZZ_"],
    "ZH": ["ZH_"],
}
DATA_PD = {"Zee": ("EGamma", "SingleElectron"), "Zmm": ("SingleMuon",)}


def parse_old(path):
    """event_counts_*.txt: '<era> <channel>' header lines followed by ' <proc>: <yield>'."""
    tables, key = {}, None
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            proc, val = line.split(":")
            tables[key][proc.strip()] = float(val)
        else:
            key = tuple(line.split())
            tables[key] = {}
    return tables


def yield_of(out, sample, region, channel):
    h = out[sample]["cmp_pt_zcand"][{"syst": "nominal", "region": region, "channel": channel}]
    return h.sum(flow=True).value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--new", required=True, help="merged new-framework .coffea output")
    parser.add_argument("--era", default="18", choices=list(ERAS))
    parser.add_argument("--old-dir", default=OLD_DIR)
    args = parser.parse_args()

    out = load(args.new)
    lumi, xsec_json = ERAS[args.era]
    xsecs = json.load(open(xsec_json))["cross_sections_pb"]

    for region in ["Z_jet", "Z_bjet"]:
        old = parse_old(f"{args.old_dir}/event_counts_{region}_amcnlo.txt")
        for channel in ["Zee", "Zmm"]:
            o = old[(args.era, channel)]
            print(f"\n{args.era} {region} {channel}")
            print(f"  {'':8s}{'old':>11s}{'new':>11s}{'new/old':>9s}")
            mc_old = mc_new = 0.0
            for proc, prefixes in GROUPS.items():
                samples = [s for s in out if s in xsecs and s.startswith(tuple(prefixes))]
                y = sum(
                    yield_of(out, s, region, channel) * xsecs[s] * lumi / out[s]["sumw"]
                    for s in samples
                )
                mc_old += o[proc]
                mc_new += y
                print(f"  {proc:8s}{o[proc]:11.1f}{y:11.1f}{y / o[proc] if o[proc] else float('nan'):9.3f}")
            print(f"  {'MC':8s}{mc_old:11.1f}{mc_new:11.1f}{mc_new / mc_old:9.3f}")
            data = sum(
                yield_of(out, s, region, channel)
                for s in out
                if s not in xsecs and s.startswith(DATA_PD[channel])
            )
            print(f"  {'Data':8s}{o['Data']:11.0f}{data:11.0f}{data / o['Data']:9.3f}")
            print(f"  {'Data/MC':8s}{o['Data'] / mc_old:11.3f}{data / mc_new:11.3f}")
