"""Read the per-process histograms out of an old ZbAnalysis_boosted canvas macro.

The old framework's Scripts/plot_dataMC_v4.py saves every control plot as
<var>_<region>_<channel>_<era>_amcnlo.C next to the .png. The macro contains
the stacked MC histograms (one TH1D per process, already xsec*lumi-scaled and
rebinned for the plot) and the data histogram, with every bin written out as
SetBinContent/SetBinError. The stack histograms are unnamed by process, so each
is identified by its fill colour, matched to the legend entries.
"""
import re

import numpy as np

# legend label in the old plots -> our process group name
LEGEND_TO_GROUP = {
    "Z+jets": "DY+jets",
    "t#bar{t}": "ttbar",
    "ZH": "ZH",
    "Diboson": "Diboson",
    "Single top": "Single top",
}

_NEW_TH1 = re.compile(r'(\w+) = new TH1[DF]\("(\w+)","[^"]*",(\d+),([-\d.e+]+),([-\d.e+]+)\)')
_COLOR = re.compile(r'ci = (?:TColor::GetColor\("(#\w+)"\)|(\d+));')
_ENTRY = re.compile(r'AddEntry\("[^"]*","([^"]+)","(\w+)"\)')


class OldHist:
    def __init__(self, nbins, lo, hi):
        self.edges = np.linspace(lo, hi, nbins + 1)
        self.values = np.zeros(nbins + 2)  # ROOT convention: 0 = underflow, nbins+1 = overflow
        self.errors = np.zeros(nbins + 2)
        self.fill = None

    def integral(self, flow=True):
        return self.values.sum() if flow else self.values[1:-1].sum()


def read_macro(path):
    """Return ({group: OldHist}, data OldHist, (xlo, xhi)) from an old canvas macro.

    groups are in stack order (bottom first); each OldHist.fill is its colour.
    (xlo, xhi) is the x-range the old plot displays (frame SetRange).
    """
    hists, stack, data_name, frame = {}, [], None, None
    last_color = None
    legend = []  # (label, colour) in legend order
    for line in open(path):
        m = _NEW_TH1.search(line)
        if m:
            var, name, n, lo, hi = m.groups()
            hists[var] = OldHist(int(n), float(lo), float(hi))
            continue
        m = _COLOR.search(line)
        if m:
            last_color = m.group(1) or m.group(2)
            continue
        m = re.search(r"(\w+)->SetBinContent\((\d+),([-\d.e+]+)\)", line)
        if m and m.group(1) in hists:
            hists[m.group(1)].values[int(m.group(2))] = float(m.group(3))
            continue
        m = re.search(r"(\w+)->SetBinError\((\d+),([-\d.e+]+)\)", line)
        if m and m.group(1) in hists:
            hists[m.group(1)].errors[int(m.group(2))] = float(m.group(3))
            continue
        m = re.search(r"(\w+)->SetFillColor\((ci|\d+)\)", line)
        if m and m.group(1) in hists:
            hists[m.group(1)].fill = last_color if m.group(2) == "ci" else m.group(2)
            continue
        m = re.search(r"(st_stack_\d+)->GetXaxis\(\)->SetRange\((\d+),(\d+)\)", line)
        if m:
            frame = (m.group(1), int(m.group(2)), int(m.group(3)))
            continue
        m = re.search(r"st->Add\((\w+),", line)
        if m:
            stack.append(m.group(1))
            continue
        m = re.search(r'(\w+)->Draw\("same E"\)', line)
        if m and data_name is None:
            data_name = m.group(1)
            continue
        m = _ENTRY.search(line)
        if m:
            legend.append([m.group(1).strip(), None])
            continue
        m = re.search(r"entry->SetFillColor\((ci|\d+)\)", line)
        if m and legend:
            legend[-1][1] = last_color if m.group(1) == "ci" else m.group(1)

    colour_to_group = {c: LEGEND_TO_GROUP[l] for l, c in legend if l in LEGEND_TO_GROUP}
    groups = {}
    for var in stack:
        g = colour_to_group[hists[var].fill]
        if g in groups:
            raise ValueError(f"{path}: two stack histograms map to {g}")
        groups[g] = hists[var]
    missing = set(LEGEND_TO_GROUP.values()) - set(groups)
    if missing:
        raise ValueError(f"{path}: no stack histogram for {missing}")
    fedges = hists[frame[0]].edges
    xrange = (fedges[frame[1] - 1], fedges[min(frame[2], len(fedges) - 1)])
    return groups, hists[data_name], xrange
