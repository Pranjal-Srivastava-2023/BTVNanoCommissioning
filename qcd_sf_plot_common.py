"""Shared era configuration and histogram helpers for the QCD_sf plotting and
cutflow scripts (plot_stack_sample.py, plot_full_overview.py, print_cutflow.py).

Data convention (same as compare_yields_old_new.py and the old ZbAnalysis_boosted
framework): Zee data comes only from the electron primary dataset (EGamma /
SingleElectron) and Zmm data only from SingleMuon, so events recorded in both
are not counted twice. Histograms without a channel axis (jet0_*, dilep_*,
njet) cannot be split this way and sum both primary datasets; in 2018 that
overcounts data by ~2% (events in both PDs).
"""
import argparse
import json

import numpy as np
from coffea.util import load

REPO = "/uscms/home/psrivast/nobackup/BTVNanoCommissioning"

# era -> lumi in /pb (old Configs/config.ini [General]), year label, primary datasets
ERAS = {
    "2016preVFP": dict(lumi=19648.0, year="2016preVFP", ele_pd="SingleElectron_Run2016preVFP", mu_pd="SingleMuon_Run2016preVFP"),
    "2016postVFP": dict(lumi=16978.0, year="2016postVFP", ele_pd="SingleElectron_Run2016postVFP", mu_pd="SingleMuon_Run2016postVFP"),
    "2017": dict(lumi=41480.0, year="2017", ele_pd="SingleElectron_Run2017", mu_pd="SingleMuon_Run2017"),
    "2018": dict(lumi=59832.0, year="2018", ele_pd="EGamma_Run2018", mu_pd="SingleMuon_Run2018"),
}

GROUPS = {
    "DY+jets": [
        "DYJetsToLL_0J_TuneCP5_13TeV-amcatnloFXFX-pythia8",
        "DYJetsToLL_1J_TuneCP5_13TeV-amcatnloFXFX-pythia8",
        "DYJetsToLL_2J_TuneCP5_13TeV-amcatnloFXFX-pythia8",
    ],
    "ttbar": [
        "TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8",
        "TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8",
    ],
    "Single top": [
        "ST_t-channel_top_4f_InclusiveDecays_TuneCP5_13TeV-powheg-madspin-pythia8",
        "ST_t-channel_antitop_4f_InclusiveDecays_TuneCP5_13TeV-powheg-madspin-pythia8",
        "ST_s-channel_4f_leptonDecays_TuneCP5_13TeV-amcatnlo-pythia8",
        "ST_tW_top_5f_inclusiveDecays_TuneCP5_13TeV-powheg-pythia8",
        "ST_tW_antitop_5f_inclusiveDecays_TuneCP5_13TeV-powheg-pythia8",
    ],
    "Diboson": [
        "WW_TuneCP5_13TeV-pythia8",
        "WZ_TuneCP5_13TeV-pythia8",
        "ZZ_TuneCP5_13TeV-pythia8",
    ],
    "ZH": ["ZH_HToBB_ZToLL_M-125_TuneCP5_13TeV-powheg-pythia8"],
}
COLORS = {"DY+jets": "#5790fc", "ttbar": "#f89c20", "Single top": "#e42536", "Diboson": "#964a8b", "ZH": "#9c9ca1"}
ORDER = ["Diboson", "ZH", "Single top", "ttbar", "DY+jets"]


def parse_args(description):
    """--era / --input / --outdir, defaulting to the per-era merged run output."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--era", default="2018", choices=list(ERAS))
    parser.add_argument("--input", help="merged .coffea (default: hists_run<era>_mSD_SF/merged_run<era>.coffea)")
    parser.add_argument("--outdir", help="output directory (default: hists_run<era>_mSD_SF/plots)")
    args = parser.parse_args()
    run_dir = f"{REPO}/hists_run{args.era}_mSD_SF"
    args.input = args.input or f"{run_dir}/merged_run{args.era}.coffea"
    args.outdir = args.outdir or f"{run_dir}/plots"
    return args


class EraOutput:
    """A merged QCD_sf output plus the era's lumi, cross sections and data PDs."""

    def __init__(self, era, path):
        self.era = era
        self.cfg = ERAS[era]
        self.lumi = self.cfg["lumi"]
        self.out = load(path)
        self.xsecs = json.load(open(f"{REPO}/metadata/QCD_sf_xsections_{era}.json"))["cross_sections_pb"]

    def scale(self, sample):
        return self.xsecs[sample] * self.lumi / self.out[sample]["sumw"]

    def _reduce(self, sample, histname, sel):
        h = self.out[sample][histname]
        axnames = [a.name for a in h.axes]
        if "nominal" not in list(h.axes["syst"]):
            return None  # no events passed the selection for this sample
        s = {"syst": "nominal"}
        for k, v in sel.items():
            if k in axnames:
                s[k] = v
        for ax in ("flav", "channel", "region"):
            if ax in axnames and ax not in s:
                s[ax] = sum
        return h[s]

    def mc_groups(self, histname, sel):
        """{group label: xsec*lumi/sumw-scaled hist}, sel maps axis -> value (or sum)."""
        groups = {}
        for label, samples in GROUPS.items():
            total = None
            for sample in samples:
                h = self._reduce(sample, histname, sel)
                if h is None:
                    continue
                h = h * self.scale(sample)
                total = h if total is None else total + h
            if total is None:
                total = self._reduce(self.cfg["mu_pd"], histname, sel) * 0
            groups[label] = total
        return groups

    def data(self, histname, sel):
        """Data hist with each channel taken from its own primary dataset."""
        axnames = [a.name for a in self.out[self.cfg["mu_pd"]][histname].axes]
        if "channel" not in axnames:
            return self._reduce(self.cfg["ele_pd"], histname, sel) + self._reduce(self.cfg["mu_pd"], histname, sel)
        pd = {"Zee": self.cfg["ele_pd"], "Zmm": self.cfg["mu_pd"]}
        channels = [sel["channel"]] if sel.get("channel", sum) is not sum else ["Zee", "Zmm"]
        total = None
        for ch in channels:
            h = self._reduce(pd[ch], histname, {**sel, "channel": ch})
            total = h if total is None else total + h
        return total


def data_mc_ratio(mc_total, data_hist):
    """Data/MC ratio with data+MC statistical uncertainty combined in quadrature."""
    mc_vals, mc_vars = mc_total.values(), mc_total.variances()
    data_vals, data_vars = data_hist.values(), data_hist.variances()
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(mc_vals > 0, data_vals / mc_vals, np.nan)
        rel_err2 = np.where(data_vals > 0, data_vars / data_vals**2, 0.0) + np.where(
            mc_vals > 0, mc_vars / mc_vals**2, 0.0
        )
        ratio_err = np.abs(ratio) * np.sqrt(rel_err2)
    return ratio, ratio_err
