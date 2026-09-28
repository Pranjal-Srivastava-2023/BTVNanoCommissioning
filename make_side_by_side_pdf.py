"""
Old-vs-new side-by-side PDF for one era:
hists_run<ERA>_mSD_SF/old_vs_new_<ERA>_side_by_side.pdf

Page 1: leading-jet softdrop mass (new, Zee+Zmm combined) next to the old Zee and
Zmm plots. Then one new and one old plot per page for each overview variable
(Z_jet), both shown unmodified. Last two pages: the old event summary table
(condor_output_mSD/summary_eventCount_amcnlo.txt) and the new one in the same
layout (hists_run<ERA>_mSD_SF/compare_<ERA>.txt, "new" column).

Needs the per-channel panels from `plot_stack_sample.py --era <ERA>` and the
yield table from `compare_yields_old_new.py`.

Usage: python3 make_side_by_side_pdf.py --era 2017
"""

import argparse
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

OLD_BASE = (
    "/uscms/home/psrivast/nobackup/ZbExercize/CMSSW_14_0_6/src/Zb/CMSSW_14_0_6/src/"
    "ZbAnalysis_boosted/condor_output_mSD/"
)
# era -> (old plot subdirectory, old era label used in file names and tables)
ERAS = {
    "2016preVFP": ("20preVFP2016", "preVFP2016"),
    "2016postVFP": ("20postVFP2016", "postVFP2016"),
    "2017": ("2017", "17"),
    "2018": ("2018", "18"),
}
ROWS = [("DY", "DY"), ("tt", "tt"), ("Single t", "ST"), ("VV", "VV"), ("ZH", "ZH"),
        ("MC", "MC"), ("Data", "Data"), ("Data/MC", "Data/MC")]


def show(fig, rect, path):
    ax = fig.add_axes(rect)
    ax.imshow(plt.imread(path), interpolation="none")  # original pixels, only display size set
    ax.set_axis_off()


def headers(fig):
    fig.text(0.25, 0.96, "NEW", ha="center", fontsize=16, weight="bold")
    fig.text(0.75, 0.96, "OLD", ha="center", fontsize=16, weight="bold")


def parse_old_tables(path):
    """LaTeX tables in summary_eventCount_*.txt, keyed by caption (e.g. '18_Z_jet')."""
    tables, cur = {}, None
    for line in open(path):
        m = re.search(r"caption\{(.*)\}", line)
        if m:
            cur = m.group(1).replace("\\_", "_")
            tables[cur] = []
            continue
        m = re.match(r"\s*(DY|tt|Single t|VV|ZH|MC|Data|Data/MC)\s*&\s*(\S+)\s*&\s*(\S+?)\\\\", line)
        if m and cur:
            tables[cur].append(m.groups())
    return tables


def parse_new_table(path, label):
    """'new' column of compare_<ERA>.txt, keyed by (region, channel, row)."""
    vals, key = {}, None
    for line in open(path):
        if line.startswith(label + " "):
            key = tuple(line.split()[1:])
            continue
        parts = line.split()
        if key and len(parts) >= 3 and parts[0] in dict(ROWS).values():
            vals[key + (parts[0],)] = float(parts[2])
    return vals


def table_text(title, rowvals):
    lines = [title, "", f"{'':12s}{'Electron':>12s}{'Muon':>12s}", "-" * 36]
    for label, e, mu in rowvals:
        if label == "MC":
            lines.append("-" * 36)
        lines.append(f"{label:12s}{e:>12s}{mu:>12s}")
    return "\n".join(lines)


def fmt(label, v):
    return f"{v:.2f}" if label == "Data/MC" else f"{v:.0f}"


def main(era):
    old_dir, lab = ERAS[era]
    new_dir = f"hists_run{era}_mSD_SF/"
    P = f"{new_dir}plots/panels/qcd_sf_{era}_"
    OLD = OLD_BASE + old_dir + "/"
    o = lambda v, ch: f"{OLD}{v}_Z_jet_{ch}_{lab}_amcnlo.png"

    pairs = [(P + f"mass_zcand_{ch}.png", o("ZMass", ch)) for ch in ("Zee", "Zmm")]
    for new, old in [("pt_fj", "pt_jet"), ("pt_zcand", "pt_dilepton"), ("pt_lep0", "pt_lep0"),
                     ("pt_lep1", "pt_lep1"), ("pt_sub0", "pt_sub0"), ("pt_sub1", "pt_sub1")]:
        pairs += [(P + f"{new}_{ch}.png", o(old, ch)) for ch in ("Zee", "Zmm")]
    for new, old in [("tau21", "tau21_jet"), ("tau32", "tau32_jet")]:
        pairs += [(P + f"{new}_Zee+Zmm.png", o(old, ch)) for ch in ("Zee", "Zmm")]
    for new, old in [("dr_subjets", "deltaR_subjets"), ("eta_fj", "eta_jet")]:
        pairs += [(P + f"{new}_{ch}.png", o(old, ch)) for ch in ("Zee", "Zmm")]

    old_tables = parse_old_tables(OLD_BASE + "summary_eventCount_amcnlo.txt")
    new_vals = parse_new_table(f"{new_dir}compare_{era}.txt", lab)

    out = f"{new_dir}old_vs_new_{era}_side_by_side.pdf"
    with PdfPages(out) as pdf:
        # page 1: mSD, new combined vs old per channel
        fig = plt.figure(figsize=(22, 11))
        headers(fig)
        show(fig, [0.01, 0.03, 0.48, 0.88], f"{new_dir}plots/qcd_sf_{era}_msoftdrop.png")
        for i, ch in enumerate(("Zee", "Zmm")):
            show(fig, [0.51 + i * 0.24, 0.2, 0.235, 0.6], o("mSD", ch))
        pdf.savefig(fig)
        plt.close(fig)
        # one new + one old per page
        for new, old in pairs:
            fig = plt.figure(figsize=(22, 11))
            headers(fig)
            show(fig, [0.01, 0.03, 0.48, 0.88], new)
            show(fig, [0.51, 0.03, 0.48, 0.88], old)
            pdf.savefig(fig)
            plt.close(fig)
        # event summary: old, then new
        fig = plt.figure(figsize=(22, 11))
        fig.text(0.05, 0.93, "OLD", fontsize=18, weight="bold")
        for i, reg in enumerate(("Z_jet", "Z_bjet")):
            fig.text(0.05 + 0.45 * i, 0.82, table_text(f"{lab}_{reg}", old_tables[f"{lab}_{reg}"]),
                     fontsize=18, family="monospace", va="top")
        pdf.savefig(fig)
        plt.close(fig)
        fig = plt.figure(figsize=(22, 11))
        fig.text(0.05, 0.93, "NEW", fontsize=18, weight="bold")
        for i, reg in enumerate(("Z_jet", "Z_bjet")):
            vals = [(r, fmt(r, new_vals[(reg, "Zee", k)]), fmt(r, new_vals[(reg, "Zmm", k)])) for r, k in ROWS]
            fig.text(0.05 + 0.45 * i, 0.82, table_text(f"{lab}_{reg}", vals),
                     fontsize=18, family="monospace", va="top")
        pdf.savefig(fig)
        plt.close(fig)
    print("saved", out, 1 + len(pairs) + 2, "pages")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--era", required=True, choices=list(ERAS))
    main(parser.parse_args().era)
