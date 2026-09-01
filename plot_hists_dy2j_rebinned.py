import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplhep as hep
from coffea.util import load

hep.style.use("CMS")

out = load(
    "/uscms/home/psrivast/nobackup/BTVNanoCommissioning/hists_DY2J_condor_rebin/hists_QCD_sf_QCD_sf_run2018_DY2J/hists_QCD_sf_QCD_sf_run2018_DY2J.coffea"
)
h = out["DYJetsToLL_2J_TuneCP5_13TeV-amcatnloFXFX-pythia8"]

# (histogram name, selection dict for non-plotted axes, sumaxis, title)
plots = [
    ("cmp_mass_zcand", {"channel": "Zee"}, "region", "Zee candidate mass"),
    ("cmp_mass_zcand", {"channel": "Zmm"}, "region", "Zmm candidate mass"),
    ("jet0_msoftdrop", {}, "flav", "Leading AK8 jet softdrop mass"),
    ("jet0_pt", {}, "flav", "Leading AK8 jet pT"),
    ("cmp_pt_zcand", {}, ["region", "channel"], "Z candidate pT"),
    ("cmp_pt_lep0", {}, ["region", "channel"], "Leading lepton pT"),
    ("cmp_pt_lep1", {}, ["region", "channel"], "Subleading lepton pT"),
    ("cmp_pt_sub0", {}, ["region", "channel"], "Leading subjet pT"),
    ("cmp_pt_sub1", {}, ["region", "channel"], "Subleading subjet pT"),
    ("jet0_tau21", {}, "flav", "tau21 = tau2/tau1"),
    ("jet0_tau32", {}, "flav", "tau32 = tau3/tau2"),
    ("jet0_n2b1", {}, "flav", "N2 (b1) subjettiness variable"),
    ("cmp_dr_subjets", {}, ["region", "channel"], "Delta R between subjets"),
    ("jet0_eta", {}, "flav", "Leading AK8 jet eta"),
    ("njet", {}, None, "N selected AK8 jets"),
]

fig, axes = plt.subplots(3, 5, figsize=(30, 18))
axes = axes.flatten()

for ax, (name, sel, sumaxis, title) in zip(axes, plots):
    hh = h[name]
    axnames = [a.name for a in hh.axes]
    if "syst" in axnames:
        hh = hh[{"syst": "nominal"}]
    for k, v in sel.items():
        if k in [a.name for a in hh.axes]:
            hh = hh[{k: v}]
    if sumaxis is not None:
        sumaxes = sumaxis if isinstance(sumaxis, list) else [sumaxis]
        for sa in sumaxes:
            if sa in [a.name for a in hh.axes]:
                hh = hh[{sa: sum}]
    hh.plot1d(ax=ax, histtype="fill")
    ax.set_title(title, fontsize=14)

plt.tight_layout()
outpath = "/uscms/home/psrivast/nobackup/BTVNanoCommissioning/dy2j_condor_overview_rebinned.png"
plt.savefig(outpath, dpi=110)
print("saved", outpath)
