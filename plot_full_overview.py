"""Full-statistics, stacked/scaled 15-histogram overview of the 16-dataset
QCD_sf run -- same histogram set as plot_hists_dy2j_rebinned.py's single-sample
overview, but properly xsec-scaled, grouped by physics process, and with a
data overlay, matching plot_stack_sample.py's treatment.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplhep as hep

from qcd_sf_plot_common import COLORS, ORDER, EraOutput, data_mc_ratio, parse_args

hep.style.use("CMS")

args = parse_args("15-panel stacked/scaled overview with Data/MC ratios for one era.")
era = EraOutput(args.era, args.input)
os.makedirs(args.outdir, exist_ok=True)

# (histogram name, axis selections, title, log-scale y-axis, xlim)
# xlim values crop the zero-content padding of each histogram's wider default
# axis (measured on the 2018 output), without touching the binning.
#
# cmp_* histograms are selected at region "Z_jet" (leading AK8 jet, msoftdrop > 40).
# Z_bjet is a separate selection (first PNet-tagged jet, no msoftdrop cut), not a
# subset of Z_jet, so the two are never summed. jet0_* histograms are filled for
# Z_jet events only and have no channel axis, so their data sums both primary
# datasets (~2% overlap, see qcd_sf_plot_common.py) -- marked "(*)" in the title.
PLOTS = [
    ("cmp_mass_zcand", {"channel": "Zee", "region": "Z_jet"}, "Zee candidate mass", True, (70, 110)),
    ("cmp_mass_zcand", {"channel": "Zmm", "region": "Z_jet"}, "Zmm candidate mass", True, (70, 110)),
    ("jet0_msoftdrop", {}, "Leading AK8 jet softdrop mass (*)", True, None),
    ("cmp_pt_fj", {"region": "Z_jet"}, "Leading AK8 jet pT", True, (195, 900)),
    ("cmp_pt_zcand", {"region": "Z_jet"}, "Z candidate pT", True, None),
    ("cmp_pt_lep0", {"region": "Z_jet"}, "Leading lepton pT", True, (25, 700)),
    ("cmp_pt_lep1", {"region": "Z_jet"}, "Subleading lepton pT", True, (20, 350)),
    ("cmp_pt_sub0", {"region": "Z_jet"}, "Leading subjet pT", True, (45, 900)),
    ("cmp_pt_sub1", {"region": "Z_jet"}, "Subleading subjet pT", True, (5, 350)),
    ("jet0_tau21", {}, "tau21 = tau2/tau1 (*)", True, None),
    ("jet0_tau32", {}, "tau32 = tau3/tau2 (*)", True, None),
    ("jet0_n2b1", {}, "N2 (b1) (*)", True, (0, 0.45)),
    ("cmp_dr_subjets", {"region": "Z_jet"}, "Delta R between subjets", True, (0, 1.1)),
    ("cmp_eta_fj", {"region": "Z_jet"}, "Leading AK8 jet eta", True, None),
    ("jet0_particleNetMD_Xbb", {}, "ParticleNetMD Xbb score (*)", True, None),
]


fig = plt.figure(figsize=(30, 21))
gs_outer = fig.add_gridspec(3, 5, wspace=0.32, hspace=0.35)

for i, (name, sel, title, logy, xlim) in enumerate(PLOTS):
    group_hists = era.mc_groups(name, sel)
    data_hist = era.data(name, sel)

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

fig.suptitle(f"QCD_sf {era.cfg['year']}, {era.lumi / 1000:.1f} fb$^{{-1}}$", fontsize=20)
outpath = f"{args.outdir}/qcd_sf_{args.era}_full_overview.png"
plt.savefig(outpath, dpi=110)
print("saved", outpath)
