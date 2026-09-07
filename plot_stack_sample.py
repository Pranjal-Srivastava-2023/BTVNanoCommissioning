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

# Physics-process grouping for the legend/stack
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


def build_sel(h, region, channel):
    sel = {"syst": "nominal"}
    axnames = [a.name for a in h.axes]
    if "region" in axnames and region is not None:
        sel["region"] = region
    if "channel" in axnames:
        sel["channel"] = channel if channel is not None else sum
    if "flav" in axnames:
        sel["flav"] = sum
    return sel


def scaled_hist(histname, region=None, channel=None):
    """Return {group_label: scaled hist (region/channel-sliced if given)} plus the summed data hist."""
    any_sample = GROUPS["DY+jets"][0]
    sel = build_sel(out[any_sample][histname], region, channel)

    group_hists = {}
    for label, samples in GROUPS.items():
        total = None
        for sample in samples:
            raw = out[sample][histname]
            if "nominal" not in list(raw.axes["syst"]):
                continue  # no events passed selection for this sample (small --limit test)
            h = raw[sel]
            sumw = out[sample]["sumw"]
            scale = xsecs[sample] * LUMI_PB / sumw
            h = h * scale
            total = h if total is None else total + h
        if total is None:
            total = out[GROUPS["DY+jets"][0]][histname][sel] * 0  # empty placeholder, same axes
        group_hists[label] = total

    data_total = None
    for sample in DATA_SAMPLES:
        h = out[sample][histname][sel]
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


def make_plot(histname, region, xlabel, fig, subplot_spec, channel=None, logy=True, xlim=None):
    """Draws a main stacked-histogram panel plus a Data/MC ratio panel below it
    (70/30 height split, matching the old ROOT-based ZbAnalysis_boosted convention),
    into the given figure at the given outer GridSpec cell. Returns the main axes
    (for e.g. hep.cms.label placement)."""
    group_hists, data_hist = scaled_hist(histname, region, channel)

    gs = subplot_spec.subgridspec(2, 1, height_ratios=[3, 1], hspace=0.06)
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
    ax.set_ylabel("Events / bin")
    title = region or histname
    if channel:
        title = f"{title} ({channel})"
    ax.text(0.03, 0.95, title, transform=ax.transAxes, fontsize=13, va="top", ha="left")
    ax.legend(fontsize=9, ncol=2)
    ax.set_xlabel("")
    plt.setp(ax.get_xticklabels(), visible=False)

    mc_total = None
    for g in ORDER:
        mc_total = group_hists[g] if mc_total is None else mc_total + group_hists[g]
    ratio, ratio_err = data_mc_ratio(mc_total, data_hist)
    centers = mc_total.axes[0].centers
    ax_ratio.errorbar(centers, ratio, yerr=ratio_err, fmt="o", color="black", markersize=4)
    ax_ratio.axhline(1.0, color="gray", linestyle="--", linewidth=1)
    ax_ratio.set_ylim(0.4, 1.6)
    if xlim:
        ax_ratio.set_xlim(*xlim)
    ax_ratio.set_ylabel("Data/MC", fontsize=11)
    ax_ratio.set_xlabel(xlabel)
    return ax


fig = plt.figure(figsize=(20, 9))
gs_outer = fig.add_gridspec(1, 2, wspace=0.28)
ax0 = make_plot("cmp_mass_zcand", "Z_jet", r"$m_{\ell\ell}$ [GeV]", fig, gs_outer[0], xlim=(70, 110))
ax1 = make_plot("cmp_mass_zcand", "Z_bjet", r"$m_{\ell\ell}$ [GeV]", fig, gs_outer[1], xlim=(70, 110))
hep.cms.label("Preliminary", data=True, lumi=LUMI_PB / 1000.0, year=2018, ax=ax0)
hep.cms.label("Preliminary", data=True, lumi=LUMI_PB / 1000.0, year=2018, ax=ax1)

outpath = f"{REPO}/qcd_sf_2018_sample_stack.png"
plt.savefig(outpath, dpi=130)
print("saved", outpath)

fig2 = plt.figure(figsize=(20, 9))
gs_outer2 = fig2.add_gridspec(1, 2, wspace=0.28)
make_plot("cmp_pt_fj", "Z_jet", r"Leading AK8 jet $p_{T}$ [GeV]", fig2, gs_outer2[0], logy=True, xlim=(195, 900))
make_plot("jet0_particleNetMD_Xbb", None, "ParticleNetMD Xbb score", fig2, gs_outer2[1])
outpath2 = f"{REPO}/qcd_sf_2018_sample_stack2.png"
plt.savefig(outpath2, dpi=130)
print("saved", outpath2)

# Zee vs Zmm split -- matches the old workflow keeping these as separate plots
fig3 = plt.figure(figsize=(20, 9))
gs_outer3 = fig3.add_gridspec(1, 2, wspace=0.28)
make_plot("cmp_mass_zcand", "Z_jet", r"$m_{\ell\ell}$ [GeV]", fig3, gs_outer3[0], channel="Zee", xlim=(70, 110))
make_plot("cmp_mass_zcand", "Z_jet", r"$m_{\ell\ell}$ [GeV]", fig3, gs_outer3[1], channel="Zmm", xlim=(70, 110))
outpath3 = f"{REPO}/qcd_sf_2018_sample_stack_by_channel.png"
plt.savefig(outpath3, dpi=130)
print("saved", outpath3)
