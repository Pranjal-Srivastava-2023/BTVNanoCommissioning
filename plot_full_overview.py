"""Full-statistics, stacked/scaled 15-histogram overview of the 16-dataset
QCD_sf run -- same histogram set as plot_hists_dy2j_rebinned.py's single-sample
overview, but properly xsec-scaled, grouped by physics process, and with a
data overlay, matching plot_stack_sample.py's treatment.
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplhep as hep
from coffea.util import load

hep.style.use("CMS")

LUMI_PB = 59832.0  # 2018, Configs/config.ini [General] lumi_18

REPO = "/uscms/home/psrivast/nobackup/BTVNanoCommissioning"
out = load(f"{REPO}/hists_QCD_sf_QCD_sf_run2018_all/hists_QCD_sf_QCD_sf_run2018_all.coffea")
xsecs = json.load(open(f"{REPO}/metadata/QCD_sf_xsections_2018.json"))["cross_sections_pb"]

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
DATA_SAMPLES = ["EGamma_Run2018", "SingleMuon_Run2018"]
COLORS = {"DY+jets": "#5790fc", "ttbar": "#f89c20", "Single top": "#e42536", "Diboson": "#964a8b", "ZH": "#9c9ca1"}
ORDER = ["Diboson", "ZH", "Single top", "ttbar", "DY+jets"]

# (histogram name, extra axis selections, axes to sum over, title)
PLOTS = [
    ("cmp_mass_zcand", {"channel": "Zee"}, ["region"], "Zee candidate mass"),
    ("cmp_mass_zcand", {"channel": "Zmm"}, ["region"], "Zmm candidate mass"),
    ("jet0_msoftdrop", {}, ["flav"], "Leading AK8 jet softdrop mass"),
    ("jet0_pt", {}, ["flav"], "Leading AK8 jet pT"),
    ("cmp_pt_zcand", {}, ["region", "channel"], "Z candidate pT"),
    ("cmp_pt_lep0", {}, ["region", "channel"], "Leading lepton pT"),
    ("cmp_pt_lep1", {}, ["region", "channel"], "Subleading lepton pT"),
    ("cmp_pt_sub0", {}, ["region", "channel"], "Leading subjet pT"),
    ("cmp_pt_sub1", {}, ["region", "channel"], "Subleading subjet pT"),
    ("jet0_tau21", {}, ["flav"], "tau21 = tau2/tau1"),
    ("jet0_tau32", {}, ["flav"], "tau32 = tau3/tau2"),
    ("jet0_n2b1", {}, ["flav"], "N2 (b1) subjettiness variable"),
    ("cmp_dr_subjets", {}, ["region", "channel"], "Delta R between subjets"),
    ("jet0_eta", {}, ["flav"], "Leading AK8 jet eta"),
    ("njet", {}, [], "N selected AK8 jets"),
]


def reduce_hist(h, sel, sumaxes):
    axnames = [a.name for a in h.axes]
    if "syst" in axnames:
        h = h[{"syst": "nominal"}]
    for k, v in sel.items():
        if k in [a.name for a in h.axes]:
            h = h[{k: v}]
    for sa in sumaxes:
        if sa in [a.name for a in h.axes]:
            h = h[{sa: sum}]
    return h


def scaled_group_hists(histname, sel, sumaxes):
    group_hists = {}
    for label, samples in GROUPS.items():
        total = None
        for sample in samples:
            raw = out[sample][histname]
            if "nominal" not in list(raw.axes["syst"]):
                continue
            h = reduce_hist(raw, sel, sumaxes)
            sumw = out[sample]["sumw"]
            scale = xsecs[sample] * LUMI_PB / sumw
            h = h * scale
            total = h if total is None else total + h
        if total is None:
            any_sample = samples[0]
            total = reduce_hist(out[any_sample][histname], sel, sumaxes) * 0
        group_hists[label] = total

    data_total = None
    for sample in DATA_SAMPLES:
        h = reduce_hist(out[sample][histname], sel, sumaxes)
        data_total = h if data_total is None else data_total + h
    return group_hists, data_total


fig, axes = plt.subplots(3, 5, figsize=(30, 18))
axes = axes.flatten()

for ax, (name, sel, sumaxes, title) in zip(axes, PLOTS):
    group_hists, data_hist = scaled_group_hists(name, sel, sumaxes)
    hep.histplot(
        [group_hists[g] for g in ORDER],
        stack=True,
        histtype="fill",
        label=ORDER,
        color=[COLORS[g] for g in ORDER],
        ax=ax,
    )
    hep.histplot(data_hist, histtype="errorbar", color="black", label="Data", ax=ax)
    ax.set_title(title, fontsize=14)

axes[0].legend(fontsize=8, ncol=2)
plt.tight_layout()

outpath = f"{REPO}/qcd_sf_2018_full_overview.png"
plt.savefig(outpath, dpi=110)
print("saved", outpath)
