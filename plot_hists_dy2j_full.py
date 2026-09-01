import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplhep as hep
from coffea.util import load

hep.style.use("CMS")

out = load(
    "/uscms/home/psrivast/nobackup/BTVNanoCommissioning/hists_DY2J_condor/hists_QCD_sf_QCD_sf_run2018_DY2J/hists_QCD_sf_QCD_sf_run2018_DY2J.coffea"
)
h = out["DYJetsToLL_2J_TuneCP5_13TeV-amcatnloFXFX-pythia8"]

plots = [
    ("dilep_mass", None, "Z candidate mass"),
    ("jet0_msoftdrop", "flav", "Leading AK8 jet softdrop mass"),
    ("jet0_particleNetMD_Xbb", "flav", "ParticleNetMD Xbb score"),
    ("jet0_particleNetMD_QCD", "flav", "ParticleNetMD QCD score"),
    ("jet0_deepTagMD_ZbbvsQCD", "flav", "DeepTagMD Zbb vs QCD score"),
    ("jet0_tau21", "flav", "tau21 = tau2/tau1"),
    ("jet0_tau32", "flav", "tau32 = tau3/tau2"),
    ("btagDDBvLV2", "flav", "Double-b tagger (DDBvL V2)"),
    ("jet0_pt", "flav", "Leading AK8 jet pT"),
    ("njet", None, "N selected AK8 jets"),
]

fig, axes = plt.subplots(2, 5, figsize=(30, 10))
axes = axes.flatten()

for ax, (name, sumaxis, title) in zip(axes, plots):
    hh = h[name]
    axnames = [a.name for a in hh.axes]
    if "syst" in axnames:
        hh = hh[{"syst": "nominal"}]
    if sumaxis is not None and sumaxis in [a.name for a in hh.axes]:
        hh = hh[{sumaxis: sum}]
    hh.plot1d(ax=ax, histtype="fill")
    ax.set_title(title, fontsize=14)

plt.tight_layout()
outpath = "/uscms/home/psrivast/nobackup/BTVNanoCommissioning/dy2j_condor_full_overview.png"
plt.savefig(outpath, dpi=110)
print("saved", outpath)
