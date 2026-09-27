"""Old (ZbAnalysis_boosted) vs new (QCD_sf) control plots, side by side, 2018.

Writes hists_run2018_mSD_SF/old_vs_new_2018.pdf:
  - title page with inputs and conventions
  - yield summary in the old framework's layout (DY, tt, Single t, VV, ZH, MC,
    Data, Data/MC; Electron/Muon), old | new | new/old
  - one page per (variable, region): for each channel, the old framework's PNG,
    the new result drawn in the old style, and the bin-by-bin new/old ratio of
    data and of total MC
  - list of old plots with no new counterpart
and hists_run2018_mSD_SF/old_vs_new_summary_2018.txt with the yield tables.

Old numbers are read from the old canvas macros (<var>_<region>_<channel>_18_amcnlo.C,
see old_framework_macro.py). New numbers come from the merged .coffea, with the
same conventions as compare_yields_old_new.py / qcd_sf_plot_common.py.

Binning: old and new histograms have different binnings. Where their bin edges
coincide on a grid with >= MIN_EXACT_BINS bins in the displayed range, both are
summed onto that grid (exact). Otherwise the new histogram is redistributed onto
the old binning assuming a flat distribution inside each new bin ("approx.").

Usage: python3 compare_plots_old_new.py [--input merged.coffea]
"""
import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

from old_framework_macro import read_macro
from qcd_sf_plot_common import REPO, EraOutput

OLD_DIR = (
    "/uscms/home/psrivast/nobackup/ZbExercize/CMSSW_14_0_6/src/Zb/CMSSW_14_0_6/src/"
    "ZbAnalysis_boosted/condor_output_mSD/2018"
)
RUN_DIR = f"{REPO}/hists_run2018_mSD_SF"
MIN_EXACT_BINS = 8
MIN_DATA_PER_RATIO_BIN = 50  # new/old panel: merge bins until each has this many old data events
CHANNELS = ["Zee", "Zmm"]
CH_LABEL = {"Zee": r"Z$\to$ee", "Zmm": r"Z$\to\mu\mu$"}
REGION_LABEL = {"Z_jet": r"$\geq$1 boosted jet (Z_jet)", "Z_bjet": r"$\geq$1 boosted b jet (Z_bjet)"}

# (old name, new histogram, regions, x label, old histogram actually holding this
#  quantity, offset added to new bin edges, note)
# EXTRA[var]: "floor" = selection cut below which the new histogram is empty (the
# new bin straddling it is taken to start at the cut when re-binning), "xrange" =
# x-range to use instead of the old plot's (the old subjet eta/phi plots only
# display 0..pi because config.ini's "-TMath::Pi()" is not evaluated).
# The old framework fills subjet eta into h_phi_sub* and phi into h_eta_sub*
# (src/Plots.cxx:338-339), so our eta_sub* is compared with its "phi_sub*" plot.
BOTH = ("Z_jet", "Z_bjet")
VARS = [
    ("ZMass", "cmp_mass_zcand", BOTH, r"$m_{\ell\ell}$ [GeV]", None, 0, ""),
    ("pt_dilepton", "cmp_pt_zcand", BOTH, r"Z $p_T$ [GeV]", None, 0, ""),
    ("pt_jet", "cmp_pt_fj", BOTH, r"AK8 jet $p_T$ [GeV]", None, 0, ""),
    ("eta_jet", "cmp_eta_fj", BOTH, r"AK8 jet $\eta$", None, 0, ""),
    ("Njet", "cmp_n_fj", BOTH, r"$N_{jet}$ (AK8)", None, -0.5,
     "Filled before the jet requirement, as in the old FillNjet."),
    ("pt_lep0", "cmp_pt_lep0", BOTH, r"Leading lepton $p_T$ [GeV]", None, 0, ""),
    ("pt_lep1", "cmp_pt_lep1", BOTH, r"Subleading lepton $p_T$ [GeV]", None, 0, ""),
    ("eta_lep0", "cmp_eta_lep0", BOTH, r"Leading lepton $\eta$", None, 0, ""),
    ("eta_lep1", "cmp_eta_lep1", BOTH, r"Subleading lepton $\eta$", None, 0, ""),
    ("pt_sub0", "cmp_pt_sub0", BOTH, r"Leading subjet $p_T$ [GeV]", None, 0, ""),
    ("pt_sub1", "cmp_pt_sub1", BOTH, r"Subleading subjet $p_T$ [GeV]", None, 0, ""),
    ("eta_sub0", "cmp_eta_sub0", BOTH, r"Leading subjet $\eta$", "phi_sub0", 0,
     "Old plot shown is its 'phi_sub0', which holds subjet eta (old eta/phi swap)."),
    ("eta_sub1", "cmp_eta_sub1", BOTH, r"Subleading subjet $\eta$", "phi_sub1", 0,
     "Old plot shown is its 'phi_sub1', which holds subjet eta (old eta/phi swap)."),
    ("phi_sub0", "cmp_phi_sub0", BOTH, r"Leading subjet $\phi$", "eta_sub0", 0,
     "Old plot shown is its 'eta_sub0', which holds subjet phi (old eta/phi swap); "
     "it overflows beyond |phi| > 3."),
    ("phi_sub1", "cmp_phi_sub1", BOTH, r"Subleading subjet $\phi$", "eta_sub1", 0,
     "Old plot shown is its 'eta_sub1', which holds subjet phi (old eta/phi swap); "
     "it overflows beyond |phi| > 3."),
    ("mass_sub0", "cmp_mass_sub0", BOTH, "Leading subjet mass [GeV]", None, 0, ""),
    ("mass_sub1", "cmp_mass_sub1", BOTH, "Subleading subjet mass [GeV]", None, 0, ""),
    ("deltaR_subjets", "cmp_dr_subjets", BOTH, r"$\Delta R$(subjet 1, subjet 2)", None, 0, ""),
    # jet0_* histograms: Z_jet only, no channel axis -> compared to old Zee + Zmm
    ("mSD", "jet0_msoftdrop", ("Z_jet",), r"Leading AK8 jet $m_{SD}$ [GeV]", None, 0, ""),
    ("mass_jet", "jet0_mass", ("Z_jet",), "Leading AK8 jet mass [GeV]", None, 0, ""),
    ("tau21_jet", "jet0_tau21", ("Z_jet",), r"$\tau_{21}$", None, 0, ""),
    ("tau32_jet", "jet0_tau32", ("Z_jet",), r"$\tau_{32}$", None, 0, ""),
]
EXTRA = {
    "mSD": {"floor": 40.0},
    "eta_sub0": {"xrange": (-3.0, 3.0)},
    "eta_sub1": {"xrange": (-3.0, 3.0)},
    "phi_sub0": {"xrange": (-3.0, 3.0)},
    "phi_sub1": {"xrange": (-3.0, 3.0)},
}
NOT_IN_NEW = ["dPhi_Z_jet", "deltaR_lep_lep", "deltaR_lep_jet", "deltaR_ZJet", "deltaR_lep_Z"]
SUBJET_BJET_NOTE = (
    "Z_bjet: the old framework fills subjet histograms from the leading jet's subjets, "
    "ours from the tagged jet's subjets; differences are expected."
)
SUMMARY_ROWS = [("DY", "DY+jets"), ("tt", "ttbar"), ("Single t", "Single top"), ("VV", "Diboson"), ("ZH", "ZH")]


# ---------------------------------------------------------------- binning
class Binned:
    """Histogram as (edges, values, variances) with under/overflow at [0] and [-1]."""

    def __init__(self, edges, values, variances):
        self.edges = np.asarray(edges, float)
        self.values = np.asarray(values, float)
        self.variances = np.asarray(variances, float)

    def __add__(self, other):
        return Binned(self.edges, self.values + other.values, self.variances + other.variances)

    def total(self):
        return self.values.sum()


def from_hist(h, offset=0.0, floor=None):
    ax = h.axes[0]
    v, w = h.values(flow=True), h.variances(flow=True)
    if len(v) == len(ax.edges) - 1:  # axis without flow bins
        v, w = np.r_[0, v, 0], np.r_[0, w, 0]
    edges = ax.edges + offset
    if floor is not None:
        i = np.searchsorted(edges, floor) - 1
        if 0 <= i < len(edges) - 1 and edges[i] < floor:
            edges = edges.copy()
            edges[i] = floor
    return Binned(edges, v, w)


def from_old(o):
    return Binned(o.edges, o.values, o.errors**2)


def common_edges(a, b, lo, hi):
    tol = 1e-6 * max(abs(a).max(), abs(b).max(), 1.0)
    return np.array([x for x in a if np.min(np.abs(b - x)) < tol and lo - tol <= x <= hi + tol])


def rebin_exact(h, target):
    """Sum h onto target edges (a subset of h.edges); outside content -> flow."""
    tol = 1e-6 * max(abs(h.edges).max(), 1.0)
    idx = np.array([np.argmin(np.abs(h.edges - t)) for t in target])
    assert np.all(np.abs(h.edges[idx] - target) < tol)
    out = []
    for arr in (h.values, h.variances):
        c = np.r_[0, np.cumsum(arr)]  # c[k] = sum of arr[:k]; bin j of h is arr[j+1]
        inner = c[idx[1:] + 1] - c[idx[:-1] + 1]
        under = c[idx[0] + 1]
        over = arr.sum() - c[idx[-1] + 1]
        out.append(np.r_[under, inner, over])
    return Binned(target, *out)


def rebin_flat(h, target):
    """Redistribute h onto arbitrary target edges assuming a flat density per bin."""
    e = h.edges
    out = []
    for arr in (h.values, h.variances):
        inner = arr[1:-1]
        cum = np.r_[0, np.cumsum(inner)]
        c_t = np.interp(target, e, cum)
        c_t_under = arr[0] + c_t
        body = np.diff(c_t)
        under = c_t_under[0]
        over = arr.sum() - c_t_under[-1]
        out.append(np.r_[under, body, over])
    return Binned(target, *out)


def merge_for_ratio(edges, data_values):
    """Subset of edges such that each merged bin holds >= MIN_DATA_PER_RATIO_BIN
    (data_values are per-bin contents, no flow). A short last bin joins its neighbour."""
    keep, acc = [edges[0]], 0.0
    for i, v in enumerate(data_values):
        acc += v
        if acc >= MIN_DATA_PER_RATIO_BIN:
            keep.append(edges[i + 1])
            acc = 0.0
    if keep[-1] != edges[-1]:
        if len(keep) > 1:
            keep[-1] = edges[-1]
        else:
            keep.append(edges[-1])
    return np.array(keep)


def choose_binning(old_edges, new_edges, xrange):
    """(target edges, exact?) for comparing old and new in the displayed range."""
    lo, hi = xrange
    common = common_edges(old_edges, new_edges, lo, hi)
    in_range = lambda e: e[(e >= lo - 1e-9) & (e <= hi + 1e-9)]
    nested = len(common) > 1 and (
        len(common) == len(in_range(old_edges)) or len(common) == len(in_range(new_edges))
    )
    if len(common) - 1 >= MIN_EXACT_BINS or nested:
        return common, True
    # merge old bins until at least as wide as the new ones, stay on the old grid
    ow = np.diff(old_edges).mean()
    nw = np.diff(new_edges).mean()
    step = max(1, int(np.ceil(nw / ow - 1e-9)))
    oe = old_edges[(old_edges >= lo - 1e-9) & (old_edges <= hi + 1e-9)]
    target = oe[::step]
    return target, False


# ---------------------------------------------------------------- drawing
def draw_stack(ax, rax, groups, data, colors, order, edges, xrange, xlabel, title):
    """Old-style stacked plot with hatched MC stat band and Data/MC ratio."""
    centers = 0.5 * (edges[1:] + edges[:-1])
    bottom = np.zeros(len(edges) - 1)
    for g in order:
        vals = groups[g].values[1:-1]
        ax.stairs(bottom + vals, edges, baseline=bottom, fill=True, color=colors[g], label=legend_name(g))
        bottom = bottom + vals
    mc = sum((groups[g] for g in order[1:]), groups[order[0]])
    mcv, mce = mc.values[1:-1], np.sqrt(mc.variances[1:-1])
    ax.stairs(mcv + mce, edges, baseline=mcv - mce, fill=False, hatch="xxxx", color="gray", lw=0, label="MC unc. (stat.)")
    dv, de = data.values[1:-1], np.sqrt(data.variances[1:-1])
    m = dv > 0
    ax.errorbar(centers[m], dv[m], yerr=de[m], fmt="o", color="black", ms=3.5, label="Data")
    ax.set_yscale("log")
    top = max(mcv.max(), dv.max(), 1)
    ax.set_ylim(1e-2, top * 500)  # old plots: st->SetMinimum(0.01)
    ax.set_xlim(*xrange)
    ax.set_ylabel(f"Events/{np.diff(edges).mean():.3g}", fontsize=9)
    ax.text(0.04, 0.95, title, transform=ax.transAxes, va="top", fontsize=9)
    ax.legend(fontsize=6.5, ncol=2, loc="upper right", frameon=False)
    ax.tick_params(labelbottom=False, labelsize=8)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(mcv > 0, dv / mcv, np.nan)
        re_ = np.where(mcv > 0, de / mcv, np.nan)
        band = np.where(mcv > 0, mce / mcv, np.nan)
    rax.stairs(1 + np.nan_to_num(band), edges, baseline=1 - np.nan_to_num(band), fill=False, hatch="xxxx", color="gray", lw=0)
    rax.errorbar(centers[m], r[m], yerr=re_[m], fmt="o", color="black", ms=3)
    rax.axhline(1, color="black", lw=0.8)
    rax.set_ylim(0.4, 1.6)
    rax.set_xlim(*xrange)
    rax.set_ylabel("Data/MC", fontsize=8)
    rax.set_xlabel(xlabel, fontsize=9)
    rax.tick_params(labelsize=8)


def legend_name(g):
    return {"DY+jets": "Z+jets", "ttbar": r"t$\bar{t}$"}.get(g, g)


def draw_ratio(ax, old_mc, new_mc, old_data, new_data, edges, xrange, xlabel, exact):
    """new/old per bin for data and total MC, with integrals."""
    centers = 0.5 * (edges[1:] + edges[:-1])
    for old, new, color, label, dx in [
        (old_data, new_data, "black", "Data", -0.15),
        (old_mc, new_mc, "#cc0000", "MC", 0.15),
    ]:
        ov, nv = old.values[1:-1], new.values[1:-1]
        with np.errstate(divide="ignore", invalid="ignore"):
            r = np.where(ov > 0, nv / ov, np.nan)
            err = np.abs(r) * np.sqrt(
                np.where(nv > 0, new.variances[1:-1] / nv**2, 0) + np.where(ov > 0, old.variances[1:-1] / ov**2, 0)
            )
        m = np.isfinite(r)
        w = np.diff(edges)
        ax.errorbar(centers[m] + dx * w[m], r[m], yerr=err[m], fmt="o", color=color, ms=3, label=label)
    ax.axhline(1, color="gray", ls="--", lw=0.8)
    ax.set_ylim(0.7, 1.3)
    ax.set_xlim(*xrange)
    ax.set_ylabel("new / old (per bin)", fontsize=9)
    ax.set_xlabel(xlabel, fontsize=9)
    ax.tick_params(labelsize=8)
    ax.legend(fontsize=8, loc="upper right")
    tag = "exact common binning" if exact else "approx.: new re-binned assuming flat bins"
    tag += f"; bins merged to >= {MIN_DATA_PER_RATIO_BIN} old data events"
    txt = (
        f"Integrals (incl. under/overflow)\n"
        f"Data  old {old_data.total():9.1f}  new {new_data.total():9.1f}  ({new_data.total() / old_data.total():.3f})\n"
        f"MC    old {old_mc.total():9.1f}  new {new_mc.total():9.1f}  ({new_mc.total() / old_mc.total():.3f})\n"
        f"Binning: {tag}"
    )
    ax.text(0.03, 0.04, txt, transform=ax.transAxes, fontsize=7, family="monospace", va="bottom",
            bbox=dict(facecolor="white", alpha=0.85, edgecolor="lightgray"))


def show_png(ax, path, caption):
    ax.imshow(plt.imread(path))
    ax.set_axis_off()
    ax.set_title(caption, fontsize=9)


# ---------------------------------------------------------------- pages
def old_path(var, region, channel, ext):
    return f"{OLD_DIR}/{var}_{region}_{channel}_18_amcnlo.{ext}"


def new_binned(era, hist, sel, offset, floor=None):
    groups = {g: from_hist(h, offset, floor) for g, h in era.mc_groups(hist, sel).items()}
    return groups, from_hist(era.data(hist, sel), offset, floor)


def comparison_row(fig, cell, old, new, xlabel, xrange, title, colors, order):
    """One row: [old png | new plot] + [new/old ratio]. old/new are (groups, data)."""
    (og, od), (ng, nd) = old, new
    any_old = next(iter(og.values()))
    any_new = next(iter(ng.values()))
    target, exact = choose_binning(any_old.edges, any_new.edges, xrange)
    rb_new = (lambda h: rebin_exact(h, target)) if exact else (lambda h: rebin_flat(h, target))
    rb_old = lambda h: rebin_exact(h, target)
    ng_t = {g: rb_new(h) for g, h in ng.items()}
    nd_t = rb_new(nd)
    og_t = {g: rb_old(h) for g, h in og.items()}
    od_t = rb_old(od)

    sub = cell.subgridspec(2, 2, height_ratios=[3, 1], hspace=0.05, wspace=0.3)
    ax, rax = fig.add_subplot(sub[0, 0]), fig.add_subplot(sub[1, 0])
    # middle panel: common binning when exact, otherwise the new native binning
    if exact:
        draw_stack(ax, rax, ng_t, nd_t, colors, order, target, xrange, xlabel, title + "\nNEW (QCD_sf)")
    else:
        draw_stack(ax, rax, ng, nd, colors, order, any_new.edges, xrange, xlabel, title + "\nNEW (QCD_sf)")
    tax = fig.add_subplot(sub[:, 1])
    old_mc = sum((og_t[g] for g in order[1:]), og_t[order[0]])
    new_mc = sum((ng_t[g] for g in order[1:]), ng_t[order[0]])
    merged = merge_for_ratio(target, od_t.values[1:-1])
    m = lambda h: rebin_exact(h, merged)
    draw_ratio(tax, m(old_mc), m(new_mc), m(od_t), m(nd_t), merged, xrange, xlabel, exact)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", default=f"{RUN_DIR}/merged_run2018.coffea")
    args = parser.parse_args()
    era = EraOutput("2018", args.input)
    pdf_path = f"{RUN_DIR}/old_vs_new_2018.pdf"
    txt_path = f"{RUN_DIR}/old_vs_new_summary_2018.txt"

    # ---- yield summary (old layout), from the ZMass macros / cmp_mass_zcand
    summary = {}
    for region in BOTH:
        for ch in CHANNELS:
            og, od, _ = read_macro(old_path("ZMass", region, ch, "C"))
            ng, nd = new_binned(era, "cmp_mass_zcand", {"region": region, "channel": ch}, 0)
            summary[(region, ch)] = (
                {g: h.integral() for g, h in og.items()}, od.integral(),
                {g: h.total() for g, h in ng.items()}, nd.total(),
            )
    lines = [f"Old (ZbAnalysis_boosted, condor_output_mSD) vs new (QCD_sf) yields, 2018, "
             f"{era.lumi / 1000:.1f} fb^-1", "Layout of the old summary_eventCount_amcnlo.txt tables.", ""]
    for region in BOTH:
        lines.append(f"{region}")
        lines.append(f"  {'':10s}{'Electron':>10s}{'':>21s}   {'Muon':>10s}")
        lines.append(f"  {'':10s}{'old':>10s}{'new':>10s}{'new/old':>9s}   {'old':>10s}{'new':>10s}{'new/old':>9s}")
        rows = SUMMARY_ROWS + [("MC", None), ("Data", None), ("Data/MC", None)]
        for label, g in rows:
            cells = []
            for ch in CHANNELS:
                og, od, ng, nd = summary[(region, ch)]
                if g:
                    o, n = og[g], ng[g]
                elif label == "MC":
                    o, n = sum(og.values()), sum(ng.values())
                elif label == "Data":
                    o, n = od, nd
                else:
                    o, n = od / sum(og.values()), nd / sum(ng.values())
                fmt = "{:10.3f}" if label == "Data/MC" else "{:10.1f}"
                ratio = f"{n / o:9.3f}" if o and label != "Data/MC" else " " * 9
                cells.append(fmt.format(o) + fmt.format(n) + ratio)
            lines.append(f"  {label:10s}{cells[0]}   {cells[1]}")
        lines.append("")
    summary_text = "\n".join(lines)
    with open(txt_path, "w") as f:
        f.write(summary_text + "\n")

    colors = order = None
    with PdfPages(pdf_path) as pdf:
        # ---- title page
        fig = plt.figure(figsize=(16.5, 11.7))
        fig.text(0.05, 0.93, f"Old (ZbAnalysis_boosted) vs new (QCD_sf) control plots, 2018",
                 fontsize=22, weight="bold")
        intro = [
            f"Old: {OLD_DIR}  (*_amcnlo.png / .C, amc@NLO DY)",
            f"New: {args.input}",
            f"Luminosity {era.lumi:.0f} /pb. Same selection, lepton SFs, cross sections and lumi mask in both (see SESSION_NOTES.md reference table).",
            "",
            "Each variable page: per channel, left = old framework's plot as produced; middle = new result in the same style",
            "(same processes, colours, stacking order, x-range, log scale, hatched MC stat. band); right = new/old per bin for",
            "data (black) and total MC (red), with integrals. Old numbers are read from the old canvas macros (.C), so the",
            "right-hand panel compares the exact plotted histograms.",
            "",
            f"Binning: when old and new bin edges coincide on >= {MIN_EXACT_BINS} bins in range, both are summed onto that",
            "common grid (exact). Otherwise the new histogram is redistributed onto the old bins assuming a flat distribution",
            "inside each new bin; those pages say 'approx.' and the middle panel shows the new native binning.",
            f"In the new/old panel, neighbouring bins are merged until each holds >= {MIN_DATA_PER_RATIO_BIN} old data events.",
            "Its error bars combine old and new statistical errors as if independent; since both frameworks select mostly the",
            "same events, they overstate the real old/new scatter.",
            "",
            "Data: Zee from EGamma only, Zmm from SingleMuon only (as in the old framework).",
            "Leading-jet mSD, jet mass, tau21, tau32 exist in the new output only for Z_jet and without a Zee/Zmm split:",
            "they are compared with the SUM of the old Zee and Zmm plots, and their new data sums both primary datasets",
            "(~2% of events are in both), so expect new/old data ~1.02 there.",
            "",
            "Known differences (not bugs in the new code):",
            "  - old applies Rochester muon corrections (-0.2% at the two-muon step); old jet ID reads the AK4 branch with the",
            "    AK8 index (likely the ~+1-1.5% new/old at the jet step, in data and MC alike).",
            "  - old swaps subjet eta and phi (src/Plots.cxx:338-339): our eta_sub* is paired with its 'phi_sub*' plot and vice versa.",
            f"  - {SUBJET_BJET_NOTE}",
            f"  - Not filled in the new framework (no comparison): {', '.join(NOT_IN_NEW)}.",
        ]
        fig.text(0.05, 0.88, "\n".join(intro), fontsize=13, va="top", family="sans-serif")
        pdf.savefig(fig)
        plt.close(fig)

        # ---- summary table page
        fig = plt.figure(figsize=(16.5, 11.7))
        fig.text(0.05, 0.95, "Yield summary (same layout as old summary_eventCount_amcnlo.txt)", fontsize=18, weight="bold")
        fig.text(0.05, 0.9, summary_text, fontsize=15, family="monospace", va="top")
        pdf.savefig(fig)
        plt.close(fig)

        # ---- variable pages
        for var, hist, regions, xlabel, old_var, offset, note in VARS:
            for region in regions:
                old_name = old_var or var
                combined = hist.startswith("jet0_")
                extra = EXTRA.get(var, {})
                fig = plt.figure(figsize=(16.5, 11.7))
                fig.suptitle(f"{var}  |  {region}  |  2018", fontsize=16, weight="bold")
                notes = [n for n in [note, SUBJET_BJET_NOTE if (region == "Z_bjet" and "sub" in var) else ""] if n]
                if notes:
                    fig.text(0.5, 0.935, "  ".join(notes), ha="center", fontsize=9, color="darkred")
                outer = fig.add_gridspec(2, 2, width_ratios=[1, 2.1], left=0.02, right=0.98, top=0.9, bottom=0.06,
                                         hspace=0.18, wspace=0.05)
                if not combined:
                    for row, ch in enumerate(CHANNELS):
                        og, od, xr = read_macro(old_path(old_name, region, ch, "C"))
                        colors = {g: h.fill for g, h in og.items()}
                        order = list(og)
                        show_png(fig.add_subplot(outer[row, 0]), old_path(old_name, region, ch, "png"),
                                 f"OLD: {old_name}_{region}_{ch}")
                        og_b = {g: from_old(h) for g, h in og.items()}
                        new = new_binned(era, hist, {"region": region, "channel": ch}, offset, extra.get("floor"))
                        comparison_row(fig, outer[row, 1], (og_b, from_old(od)), new, xlabel, extra.get("xrange", xr),
                                       f"{CH_LABEL[ch]} + {REGION_LABEL[region]}", colors, order)
                else:
                    olds = [read_macro(old_path(old_name, region, ch, "C")) for ch in CHANNELS]
                    colors = {g: h.fill for g, h in olds[0][0].items()}
                    order = list(olds[0][0])
                    left = outer[:, 0].subgridspec(2, 1, hspace=0.1)
                    for row, ch in enumerate(CHANNELS):
                        show_png(fig.add_subplot(left[row]), old_path(old_name, region, ch, "png"),
                                 f"OLD: {old_name}_{region}_{ch}")
                    og_b = {g: from_old(olds[0][0][g]) + from_old(olds[1][0][g]) for g in order}
                    od_b = from_old(olds[0][1]) + from_old(olds[1][1])
                    new = new_binned(era, hist, {}, offset, extra.get("floor"))
                    comparison_row(fig, outer[0, 1], (og_b, od_b), new, xlabel, extra.get("xrange", olds[0][2]),
                                   f"Zee + Zmm, {REGION_LABEL[region]}\n(compared with old Zee + Zmm)", colors, order)
                pdf.savefig(fig)
                plt.close(fig)

        # ---- not compared
        fig = plt.figure(figsize=(16.5, 11.7))
        fig.text(0.05, 0.93, "Old plots without a new counterpart", fontsize=18, weight="bold")
        fig.text(0.05, 0.88, "These variables are not filled by the new QCD_sf workflow yet:\n\n  "
                 + "\n  ".join(f"{v}_Z_jet (Zee, Zmm)" for v in NOT_IN_NEW), fontsize=12, va="top")
        pdf.savefig(fig)
        plt.close(fig)

    print(summary_text)
    print("saved", pdf_path)
    print("saved", txt_path)


if __name__ == "__main__":
    main()
