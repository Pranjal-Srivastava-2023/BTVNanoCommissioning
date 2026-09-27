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


lumi_fb = era.lumi / 1000.0
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
