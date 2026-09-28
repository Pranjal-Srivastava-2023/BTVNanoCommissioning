import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplhep as hep

from qcd_sf_plot_common import COLORS, ORDER, EraOutput, data_mc_ratio, parse_args

hep.style.use("CMS")

args = parse_args("Stacked Z-candidate mass / jet plots with Data/MC ratio for one era.")
era = EraOutput(args.era, args.input)
os.makedirs(args.outdir, exist_ok=True)


def make_plot(histname, region, xlabel, fig, subplot_spec, channel=None, logy=True, xlim=None):
    """Draws a main stacked-histogram panel plus a Data/MC ratio panel below it
    (70/30 height split, matching the old ROOT-based ZbAnalysis_boosted convention),
    into the given figure at the given outer GridSpec cell. Returns the main axes
    (for e.g. hep.cms.label placement)."""
    sel = {"region": region if region is not None else sum, "channel": channel if channel is not None else sum}
    group_hists = era.mc_groups(histname, sel)
    data_hist = era.data(histname, sel)

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


lumi_fb = round(era.lumi / 1000.0, 1)  # one decimal, as in the old plots; keeps the 2016 labels from overlapping "Preliminary"
tag = f"qcd_sf_{args.era}"

fig = plt.figure(figsize=(20, 9))
gs_outer = fig.add_gridspec(1, 2, wspace=0.28)
ax0 = make_plot("cmp_mass_zcand", "Z_jet", r"$m_{\ell\ell}$ [GeV]", fig, gs_outer[0], xlim=(70, 110))
ax1 = make_plot("cmp_mass_zcand", "Z_bjet", r"$m_{\ell\ell}$ [GeV]", fig, gs_outer[1], xlim=(70, 110))
hep.cms.label("Preliminary", data=True, lumi=lumi_fb, year=era.cfg["year"], ax=ax0)
hep.cms.label("Preliminary", data=True, lumi=lumi_fb, year=era.cfg["year"], ax=ax1)
outpath = f"{args.outdir}/{tag}_sample_stack.png"
plt.savefig(outpath, dpi=130)
print("saved", outpath)

fig2 = plt.figure(figsize=(20, 9))
gs_outer2 = fig2.add_gridspec(1, 2, wspace=0.28)
make_plot("cmp_pt_fj", "Z_jet", r"Leading AK8 jet $p_{T}$ [GeV]", fig2, gs_outer2[0], logy=True, xlim=(195, 900))
make_plot("cmp_pt_fj", "Z_bjet", r"Tagged AK8 jet $p_{T}$ [GeV]", fig2, gs_outer2[1], logy=True, xlim=(195, 900))
outpath2 = f"{args.outdir}/{tag}_sample_stack2.png"
plt.savefig(outpath2, dpi=130)
print("saved", outpath2)

# Zee vs Zmm split -- matches the old workflow keeping these as separate plots
for region in ["Z_jet", "Z_bjet"]:
    fig3 = plt.figure(figsize=(20, 9))
    gs_outer3 = fig3.add_gridspec(1, 2, wspace=0.28)
    make_plot("cmp_mass_zcand", region, r"$m_{\ell\ell}$ [GeV]", fig3, gs_outer3[0], channel="Zee", xlim=(70, 110))
    make_plot("cmp_mass_zcand", region, r"$m_{\ell\ell}$ [GeV]", fig3, gs_outer3[1], channel="Zmm", xlim=(70, 110))
    outpath3 = f"{args.outdir}/{tag}_sample_stack_by_channel_{region}.png"
    plt.savefig(outpath3, dpi=130)
    print("saved", outpath3)

# Leading AK8 jet softdrop mass in Z_jet (msoftdrop > 40 cut). jet0_* histograms
# have no channel axis, so this is Zee + Zmm combined and the data sums both
# primary datasets (~2% overlap, see qcd_sf_plot_common.py).
fig4 = plt.figure(figsize=(10, 9))
ax4 = make_plot("jet0_msoftdrop", None, r"Leading AK8 jet $m_{SD}$ [GeV]", fig4, fig4.add_gridspec(1, 1)[0], xlim=(40, 250))
ax4.texts[0].set_text("Z_jet (Zee + Zmm)")
ax4.set_ylim(top=ax4.get_ylim()[1] * 30)  # headroom for label and legend
hep.cms.label("Preliminary", data=True, lumi=lumi_fb, year=era.cfg["year"], ax=ax4, fontsize=22)  # smaller: 2016 labels are long
outpath4 = f"{args.outdir}/{tag}_msoftdrop.png"
plt.savefig(outpath4, dpi=130)
print("saved", outpath4)

# The 15-panel overview's variables as single plots, one per channel (Z_jet), for
# the side-by-side comparison with the old framework's per-channel plots. N2 and
# the Xbb score have no old counterpart and are not made here; mSD is above.
# tau21/tau32 are jet0_* histograms without a channel axis: Zee + Zmm combined.
PANELS = [
    ("cmp_mass_zcand", r"$m_{\ell\ell}$ [GeV]", (70, 110), "mass_zcand"),
    ("cmp_pt_fj", r"Leading AK8 jet $p_{T}$ [GeV]", (195, 900), "pt_fj"),
    ("cmp_pt_zcand", r"Z candidate $p_{T}$ [GeV]", None, "pt_zcand"),
    ("cmp_pt_lep0", r"Leading lepton $p_{T}$ [GeV]", (25, 700), "pt_lep0"),
    ("cmp_pt_lep1", r"Subleading lepton $p_{T}$ [GeV]", (20, 350), "pt_lep1"),
    ("cmp_pt_sub0", r"Leading subjet $p_{T}$ [GeV]", (45, 900), "pt_sub0"),
    ("cmp_pt_sub1", r"Subleading subjet $p_{T}$ [GeV]", (5, 350), "pt_sub1"),
    ("cmp_dr_subjets", r"$\Delta R$ between subjets", (0, 1.1), "dr_subjets"),
    ("cmp_eta_fj", r"Leading AK8 jet $\eta$", None, "eta_fj"),
    ("jet0_tau21", r"$\tau_{21} = \tau_2/\tau_1$", None, "tau21"),
    ("jet0_tau32", r"$\tau_{32} = \tau_3/\tau_2$", None, "tau32"),
]
panel_dir = f"{args.outdir}/panels"
os.makedirs(panel_dir, exist_ok=True)
for hist, xlabel, xlim, name in PANELS:
    channels = [None] if hist.startswith("jet0_") else ["Zee", "Zmm"]
    for channel in channels:
        figp = plt.figure(figsize=(10, 9))
        region = None if channel is None else "Z_jet"
        axp = make_plot(hist, region, xlabel, figp, figp.add_gridspec(1, 1)[0], channel=channel, xlim=xlim)
        axp.texts[0].set_text("Z_jet (Zee + Zmm)" if channel is None else f"Z_jet ({channel})")
        axp.set_ylim(top=axp.get_ylim()[1] * 30)  # headroom for label and legend
        hep.cms.label("Preliminary", data=True, lumi=lumi_fb, year=era.cfg["year"], ax=axp, fontsize=22)
        outp = f"{panel_dir}/{tag}_{name}_{channel or 'Zee+Zmm'}.png"
        plt.savefig(outp, dpi=130)
        plt.close(figp)
        print("saved", outp)
