"""
Print the MC scale factors of the Zb_Zc_ratio workflow for a small sample.

Runs the workflow itself (same selection, same corrections) on the first
--nevents events of one inclusive DY file per campaign, and records inside
NanoProcessor.mc_sf every factor separately: pileup weight, each lepton's
ID / iso / reco SFs and the trigger SF. The product of the printed factors is
checked against the weight the workflow uses.

Output (per campaign, both channels): a per-event table of the first --nprint
events passing the full selection, and the average of every factor over all
selected events in the sample (Z selection, and full selection = + MET < 50,
>= 1 jet). The Z pT weight (zpt_reweight, workflow default) is printed as its
own column; it is not a scale factor.

usage: python print_zbzc_sfs.py [--campaigns Summer22 ...] [--nevents 50000]
                                [--nprint 10] [--out hists_zbzc_sfprint/sf_printout.txt]
"""
import argparse
import json
import os

import awkward as ak
import numpy as np
from coffea.analysis_tools import Weights
from coffea.nanoevents import NanoEventsFactory, PFNanoAODSchema

from BTVNanoCommissioning.utils.correction import eleSFs, muSFs, puwei
from BTVNanoCommissioning.workflows.Zb_Zc_ratio import NanoProcessor

YEAR = {"Summer22": "2022", "Summer22EE": "2022", "Summer23": "2023", "Summer23BPix": "2023"}
LABEL = {
    "Summer22": "2022 C-D",
    "Summer22EE": "2022 E-G",
    "Summer23": "2023 C",
    "Summer23BPix": "2023 D",
}
DY = "DYto2L-2Jets_MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8"


class SFPrinter(NanoProcessor):
    """Zb_Zc_ratio processor that keeps a record of every MC SF it applies."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = {"Zee": [], "Zmm": []}
        self._pending = None

    def mc_sf(self, ev, l0, l1, channel):
        sf, sf_lead = super().mc_sf(ev, l0, l1, channel)
        cols = {}
        w = Weights(len(ev))
        puwei(ev.Pileup.nTrueInt, self.SF_map, w, False)
        cols["PU"] = w.weight()
        for i, lep in enumerate((l0, l1)):
            wl = Weights(len(ev), storeIndividual=True)
            if channel == "Zee":
                eleSFs(lep, self.SF_map, wl, False, False)
            else:
                muSFs(lep, self.SF_map, wl, False, False)
            for name, arr in wl._weights.items():
                cols[f"l{i}:{name}"] = np.asarray(arr)
        rest = np.prod([v for v in cols.values()], axis=0)
        cols["trig"] = sf / rest
        cols["total_SF"] = sf
        rec = {
            "event": ak.to_numpy(ev.event),
            "l0_pt": ak.to_numpy(l0.pt),
            "l0_eta": ak.to_numpy(l0.eta),
            "l1_pt": ak.to_numpy(l1.pt),
            "l1_eta": ak.to_numpy(l1.eta),
            **cols,
        }
        self._pending = (channel, rec)
        return sf, sf_lead

    def fill_stage(self, output, channel, isRealData, ev, lead, z, l0, l1, met, jet, weight):
        if not isRealData and self._pending is not None:
            ch, rec = self._pending
            sf = rec["total_SF"]
            zw = np.ones(len(sf))
            if self.zpt_weights is not None and ev.metadata["dataset"].startswith("DYto2L"):
                zw = self.zpt_weight(ak.to_numpy(z.pt))
            rec["zpt_w"] = zw
            rec["full_sel"] = np.asarray(met) & np.asarray(jet)
            self.records[ch].append(rec)
            self._pending = None
        return super().fill_stage(
            output, channel, isRealData, ev, lead, z, l0, l1, met, jet, weight
        )


def merge(recs):
    keys = recs[0].keys()
    return {k: np.concatenate([r[k] for r in recs]) for k in keys}


def short(name):
    # strip correctionlib key noise for the table header
    for a, b in (
        ("NUM_", ""), ("_DEN_TrackerMuons", ""), ("_DEN_TightID", ""),
        ("ele_", ""), ("mu_", ""),
    ):
        name = name.replace(a, b)
    return name


def report(campaign, rec, channel, nprint):
    lines = []
    sel = rec["full_sel"]
    sfcols = [k for k in rec if k.startswith(("PU", "l0:", "l1:", "trig"))]
    prod = np.prod([rec[k] for k in sfcols], axis=0)
    closure = np.max(np.abs(prod / rec["total_SF"] - 1))
    lines.append(f"--- {channel}: {int(sel.sum())} events pass the full selection "
                 f"({len(sel)} pass the Z selection)")
    hdr = ["event", "lep1 pT", "eta", "lep2 pT", "eta"] + [short(k) for k in sfcols] + ["total SF", "Z pT w"]
    lines.append(" | ".join(f"{h:>11}" for h in hdr))
    for i in np.flatnonzero(sel)[:nprint]:
        row = [f"{rec['event'][i]:>11d}"]
        row += [f"{rec[k][i]:>11.1f}" if "pt" in k else f"{rec[k][i]:>11.2f}"
                for k in ("l0_pt", "l0_eta", "l1_pt", "l1_eta")]
        row += [f"{rec[k][i]:>11.3f}" for k in sfcols + ["total_SF", "zpt_w"]]
        lines.append(" | ".join(row))
    for lab, m in (("Z selection", np.ones(len(sel), bool)), ("full selection", sel)):
        if not m.any():
            continue
        avg = [f"{short(k)} {rec[k][m].mean():.3f}" for k in sfcols + ["total_SF"]]
        lines.append(f"mean over {lab} ({int(m.sum())} ev): " + ", ".join(avg))
        lines.append(f"    total SF min {rec['total_SF'][m].min():.3f} max {rec['total_SF'][m].max():.3f}; "
                     f"non-finite: {int((~np.isfinite(rec['total_SF'][m])).sum())}; "
                     f"Z pT weight mean {rec['zpt_w'][m].mean():.3f}")
    lines.append(f"check: product of printed factors = workflow SF to {closure:.1e}")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaigns", nargs="+", default=list(YEAR))
    ap.add_argument("--nevents", type=int, default=50000)
    ap.add_argument("--nprint", type=int, default=10)
    ap.add_argument("--out", default="hists_zbzc_sfprint/sf_printout.txt")
    args = ap.parse_args()

    out = [
        "MC scale factors applied by the Zb_Zc_ratio workflow, small-sample printout",
        f"Sample: first {args.nevents} events of the first file of {DY} (inclusive DY,",
        "LHE pT(ll) < 100 slice kept by the stitching), per campaign.",
        "Columns: PU = pileup weight; l0:/l1: = leading/subleading lepton SFs (muon: ID, iso;",
        "electron: reco, ID); trig = trigger SF (Zee: both electrons, Zmm: leading muon);",
        "total SF = product (= what the workflow multiplies genWeight by, apart from the Z pT weight).",
        "No b-/c-tag SFs are applied in the workflow.",
        "",
    ]
    for c in args.campaigns:
        files = json.load(open(f"metadata/Zb_Zc_ratio_run3_{c}.json"))[DY]
        print(f"[{c}] {files[0]}", flush=True)
        events = NanoEventsFactory.from_root(
            files[0],
            schemaclass=PFNanoAODSchema,
            entry_stop=args.nevents,
            metadata={"dataset": DY, "filename": files[0]},
        ).events()
        proc = SFPrinter(year=YEAR[c], campaign=c)
        proc.process(events)
        out.append(f"===== {c} ({LABEL[c]}) =====")
        for ch in ("Zee", "Zmm"):
            if proc.records[ch]:
                out += report(c, merge(proc.records[ch]), ch, args.nprint)
            else:
                out.append(f"--- {ch}: no selected events")
        out.append("")
        print("\n".join(out[-40:]), flush=True)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        f.write("\n".join(out) + "\n")
    print(f"written {args.out}")


if __name__ == "__main__":
    main()
