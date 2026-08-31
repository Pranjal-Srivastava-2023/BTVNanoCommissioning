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


def build_sel(h, region):
    sel = {"syst": "nominal"}
    axnames = [a.name for a in h.axes]
    if "region" in axnames and region is not None:
        sel["region"] = region
    if "flav" in axnames:
        sel["flav"] = sum
    return sel


def scaled_hist(histname, region=None):
    """Return {group_label: scaled hist (region-sliced if given)} plus the summed data hist."""
    any_sample = GROUPS["DY+jets"][0]
    sel = build_sel(out[any_sample][histname], region)

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


def make_plot(histname, region, xlabel, ax):
    group_hists, data_hist = scaled_hist(histname, region)
    order = ["Diboson", "ZH", "Single top", "ttbar", "DY+jets"]
    hep.histplot(
        [group_hists[g] for g in order],
        stack=True,
        histtype="fill",
        label=order,
        color=[COLORS[g] for g in order],
        ax=ax,
    )
    hep.histplot(data_hist, histtype="errorbar", color="black", label="Data", ax=ax)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(f"Events / bin")
    ax.set_title(region if region else histname, fontsize=14)
    ax.legend(fontsize=9, ncol=2)


fig, axes = plt.subplots(1, 2, figsize=(20, 8))
make_plot("cmp_mass_zcand", "Z_jet", r"$m_{\ell\ell}$ [GeV]", axes[0])
make_plot("cmp_mass_zcand", "Z_bjet", r"$m_{\ell\ell}$ [GeV]", axes[1])
hep.cms.label("Preliminary", data=True, lumi=LUMI_PB / 1000.0, year=2018, ax=axes[0])
hep.cms.label("Preliminary", data=True, lumi=LUMI_PB / 1000.0, year=2018, ax=axes[1])
plt.tight_layout()

outpath = f"{REPO}/qcd_sf_2018_sample_stack.png"
plt.savefig(outpath, dpi=130)
print("saved", outpath)

fig2, axes2 = plt.subplots(1, 2, figsize=(20, 8))
make_plot("cmp_pt_fj", "Z_jet", r"Leading AK8 jet $p_{T}$ [GeV]", axes2[0])
make_plot("jet0_particleNetMD_Xbb", None, "ParticleNetMD Xbb score", axes2[1])
plt.tight_layout()
outpath2 = f"{REPO}/qcd_sf_2018_sample_stack2.png"
plt.savefig(outpath2, dpi=130)
print("saved", outpath2)
