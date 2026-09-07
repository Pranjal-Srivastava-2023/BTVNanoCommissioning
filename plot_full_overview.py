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
import numpy as np
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

# (histogram name, extra axis selections, axes to sum over, title, log-scale y-axis, xlim)
# xlim values are the actual populated range summed across all 16 datasets (checked directly
# against the merged .coffea output) -- crops the padding of zero-content bins left over from
# each histogram's wider default axis definition, without touching the underlying binning/data.
#
# region is always explicitly selected as "Z_jet" (the inclusive selection, no b-tag requirement)
# rather than summed over: "Z_bjet" is a strict *subset* of "Z_jet" (same events, plus the
# ParticleNetMD Xbb tag requirement -- see QCD_validation.py's fill_comparison_hists), so summing
# both together would double-count every b-tagged event.
PLOTS = [
    ("cmp_mass_zcand", {"channel": "Zee", "region": "Z_jet"}, [], "Zee candidate mass", True, (70, 110)),
    ("cmp_mass_zcand", {"channel": "Zmm", "region": "Z_jet"}, [], "Zmm candidate mass", True, (70, 110)),
    ("jet0_msoftdrop", {}, ["flav"], "Leading AK8 jet softdrop mass", True, None),
    ("jet0_pt", {}, ["flav"], "Leading AK8 jet pT", True, None),
    ("cmp_pt_zcand", {"region": "Z_jet"}, ["channel"], "Z candidate pT", True, None),
    ("cmp_pt_lep0", {"region": "Z_jet"}, ["channel"], "Leading lepton pT", True, (25, 700)),
    ("cmp_pt_lep1", {"region": "Z_jet"}, ["channel"], "Subleading lepton pT", True, (20, 350)),
    ("cmp_pt_sub0", {"region": "Z_jet"}, ["channel"], "Leading subjet pT", True, (45, 900)),
    ("cmp_pt_sub1", {"region": "Z_jet"}, ["channel"], "Subleading subjet pT", True, (5, 350)),
    ("jet0_tau21", {}, ["flav"], "tau21 = tau2/tau1", True, None),
    ("jet0_tau32", {}, ["flav"], "tau32 = tau3/tau2", True, None),
    ("jet0_n2b1", {}, ["flav"], "N2 (b1) subjettiness variable", True, (0, 0.45)),
    ("cmp_dr_subjets", {"region": "Z_jet"}, ["channel"], "Delta R between subjets", True, (0, 1.1)),
    ("jet0_eta", {}, ["flav"], "Leading AK8 jet eta", True, None),
    # njet has no "region" axis to select (its axes are just ["syst", "n"]) -- its Z_jet/Z_bjet
    # split happens differently in QCD_validation.py and isn't separable here; left as-is.
    ("njet", {}, [], "N selected AK8 jets", True, (0.5, 6.5)),
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


fig = plt.figure(figsize=(30, 21))
gs_outer = fig.add_gridspec(3, 5, wspace=0.32, hspace=0.35)

for i, (name, sel, sumaxes, title, logy, xlim) in enumerate(PLOTS):
    group_hists, data_hist = scaled_group_hists(name, sel, sumaxes)

    gs = gs_outer[i // 5, i % 5].subgridspec(2, 1, height_ratios=[3, 1], hspace=0.06)
    ax = fig.add_subplot(gs[0])
    ax_ratio = fig.add_subplot(gs[1], sharex=ax)

    hep.histplot(
        [group_hists[g] for g in ORDER],
        stack=True,
        histtype="fill",
        label=ORDER,
        color=[COLORS[g] for g in ORDER],
        ax=ax,
    )
    hep.histplot(data_hist, histtype="errorbar", color="black", label="Data", ax=ax)
    if logy:
        ax.set_yscale("log")
    if xlim:
        ax.set_xlim(*xlim)
    ax.set_title(title, fontsize=14)
    ax.set_xlabel("")
    plt.setp(ax.get_xticklabels(), visible=False)
    if i == 0:
        ax.legend(fontsize=8, ncol=2)

    mc_total = None
    for g in ORDER:
        mc_total = group_hists[g] if mc_total is None else mc_total + group_hists[g]
    ratio, ratio_err = data_mc_ratio(mc_total, data_hist)
    centers = mc_total.axes[0].centers
    ax_ratio.errorbar(centers, ratio, yerr=ratio_err, fmt="o", color="black", markersize=3)
    ax_ratio.axhline(1.0, color="gray", linestyle="--", linewidth=1)
    ax_ratio.set_ylim(0.4, 1.6)
    if xlim:
        ax_ratio.set_xlim(*xlim)
    ax_ratio.set_ylabel("Data/MC", fontsize=9)
    ax_ratio.tick_params(axis="both", labelsize=8)

outpath = f"{REPO}/qcd_sf_2018_full_overview.png"
plt.savefig(outpath, dpi=110)
print("saved", outpath)
