import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplhep as hep
from coffea.util import load

hep.style.use("CMS")

out = load(
    "/uscms/home/psrivast/nobackup/BTVNanoCommissioning/hists_QCD_sf_test_Zb/hists_QCD_sf_test_Zb.coffea"
)
h = out["DY_2J_amcnlo"]

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
    hh = h[name][{"syst": "nominal"}]
    if sumaxis is not None and sumaxis in [a.name for a in hh.axes]:
        hh = hh[{sumaxis: sum}]
    hh.plot1d(ax=ax, histtype="fill")
    ax.set_title(title, fontsize=14)

plt.tight_layout()
outpath = "/tmp/claude-10024/-uscms-homes-p-psrivast/4674d058-2547-47f6-95fe-1d9b07f098df/scratchpad/qcd_hists_overview.png"
plt.savefig(outpath, dpi=110)
print("saved", outpath)
