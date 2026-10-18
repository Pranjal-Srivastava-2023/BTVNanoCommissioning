"""PDF slides for the AK4 version of Zb_Zc_ratio, laid out like make_zbzc_slides_pdf.py (AK8)
so the two decks can be compared page by page.

Setup, samples, selection, cutflow per channel, yields by AK4 jet flavour, an AK8 vs AK4
comparison, the kinematic and PNet tagger plots from plot_zbzc.py, then a hadronFlavour vs
partonFlavour section (yields under both definitions, migration matrix, plots stacked by
partonFlavour). Cutflow and yield numbers are read from the coffea outputs (not typed in).

Usage:
    python make_zbzc_ak4_slides_pdf.py hists_zbzc_ak4_test/test_zbzc_ak4 [hists_zbzc_test/test_zbzc]
    python make_zbzc_ak4_slides_pdf.py hists_zbzc_ak4_20files/merged --nfiles 20
writes <dir>/slides_zbzc_ak4_summer22_test.pdf (1 file per sample) or
<dir>/slides_zbzc_ak4_summer22_<N>files.pdf (plots read from <dir>/plots/). The optional
second directory is the AK8 test output used for the AK8 vs AK4 slide; with --nfiles > 1 that
slide instead compares with the 1-file AK4 test (--ref), since AK8 only has the 1-file run.
"""
import argparse
import datetime
import glob
import json
import os
import sys
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from coffea.util import load
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch

parser = argparse.ArgumentParser()
parser.add_argument("indir")
parser.add_argument("ak8dir", nargs="?", default="hists_zbzc_test/test_zbzc")
parser.add_argument("--nfiles", type=int, default=1, help="files per sample in indir's run")
parser.add_argument("--ref", default="hists_zbzc_ak4_test/test_zbzc_ak4", help="1-file AK4 test (--nfiles > 1)")
parser.add_argument("--date", default=None, help="cover date (default: 11 October 2026 for the test, else today)")
args = parser.parse_args()
indir, ak8dir, NF = args.indir, args.ak8dir, args.nfiles
TEST = NF == 1
FILES = "1 file per sample" if TEST else f"{NF} files per sample"
outfile = os.path.join(indir, "slides_zbzc_ak4_summer22_" + ("test" if TEST else f"{NF}files") + ".pdf")
DATE = args.date or ("11 October 2026" if TEST else datetime.date.today().strftime("%-d %B %Y"))


def load_dir(d):
    return load(glob.glob(os.path.join(d, "*.coffea"))[0])


out = load_dir(indir)
out8 = load_dir(ak8dir) if TEST else None
ref = None if TEST else load_dir(args.ref)
xs = json.load(open("metadata/Zb_Zc_ratio_xsections_Summer22.json"))
LUMI = xs["lumi_pb"]
CHS = {"Zee": "Z→ee", "Zmm": "Z→μμ"}
STEPS = ["all", "trigger", "leptons", "OS", "Zmass", "MET", "jet"]
SHORT = {"DYto2L-2Jets_MLL-50_TuneCP5": "Inclusive", "_PTLL-100_": "PTLL-100", "_PTLL-200_": "PTLL-200",
         "_PTLL-400_": "PTLL-400", "_PTLL-600_": "PTLL-600"}
ORDER = list(SHORT.values())


def short(ds):
    return next(v for k, v in SHORT.items() if k in ds)


def yields(o, var, flavs, axis="flav"):
    """Scaled yield per channel and flavour (hadron "flav" or parton "pflav") after the full selection."""
    y = {ch: {f: 0.0 for f in flavs} for ch in CHS}
    for ds, od in o.items():
        sc = xs[ds] * LUMI / od["sumw"]
        for ch in CHS:
            for f in flavs:
                y[ch][f] += od[var][{"channel": ch, axis: f}].sum(flow=True).value * sc
    return y


def raw_selected(o, ch):
    return sum(od["cutflow_raw"][ch]["jet"] for od in o.values())


W, H = 1920, 1080
DARK, LIGHT, PANEL, ACCENT, BODY, MUTED = "#14213D", "#FBFBF8", "#EEF1F5", "#1F5FA8", "#4A5568", "#6A7179"
PX = 72 / 100  # px -> pt at dpi 100
plt.rcParams["font.family"] = "DejaVu Sans"

FOOT = f"Summer22 DY→ℓℓ MC · {FILES} · AK4 jets"
PLOT_FOOT = FOOT + " · stacked by leading-jet flavour; lower: fraction per bin · Z→ee left, Z→μμ right"


def page(bg=LIGHT):
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    fig.patch.set_facecolor(bg)
    return fig


def text(fig, x, y, s, size, color=DARK, weight="normal", ha="left", width=None, family=None, ls=1.4):
    """Text with its top-left at (x, y) px; wrapped to `width` px. Returns the bottom y."""
    if width:
        s = "\n".join(textwrap.fill(p, max(1, int(width / (0.55 * size)))) for p in s.split("\n"))
    fig.text(x / W, 1 - y / H, s, fontsize=size * PX, color=color, weight=weight, ha=ha, va="top",
             family=family or plt.rcParams["font.family"], linespacing=ls)
    return y + size * ls * (s.count("\n") + 1)


def box(fig, x, y, w, h, color, edge=None):
    fig.add_artist(FancyBboxPatch((x / W, 1 - (y + h) / H), w / W, h / H, boxstyle="round,pad=0,rounding_size=0.008",
                                  transform=fig.transFigure, facecolor=color, edgecolor=edge or color, lw=0))


def footer(fig, s, n):
    text(fig, 128, 1000, f"{s} · {n}", 24, MUTED)


def heading(fig, s, y=128):
    return text(fig, 128, y, s, 64, DARK, "bold", ls=1.15)


def table(fig, x, y, cols, rows, size=28, shade=()):
    """cols: [(header, width px, align)]; rows: list of lists. Returns the bottom y."""
    rh = size * 2.1
    for i, row in enumerate([[c[0] for c in cols]] + rows):
        if i - 1 in shade:
            box(fig, x, y + i * rh, sum(c[1] for c in cols), rh, PANEL)
        cx = x
        for (hdr, w, al), val in zip(cols, row):
            tx = cx + (w - 12 if al == "right" else 12)
            text(fig, tx, y + i * rh + size * 0.5, str(val), size, DARK, "bold" if i == 0 else "normal", ha=al)
            cx += w
        fig.add_artist(plt.Line2D([x / W, (x + sum(c[1] for c in cols)) / W], [1 - (y + (i + 1) * rh) / H] * 2,
                                  color="#C9D3E3" if i else DARK, lw=1 if i else 2, transform=fig.transFigure))
    return y + (len(rows) + 1) * rh


def num(v):
    return f"{v:,.1f}".replace("-", "−")


pdf = PdfPages(outfile)


def save(fig):
    pdf.savefig(fig)
    plt.close(fig)


# cover
fig = page(DARK)
text(fig, 128, 260, "BTVNANOCOMMISSIONING · ZB_ZC_RATIO WORKFLOW", 28, "#7FB3E6", "bold")
text(fig, 128, 340, "Z(→ℓℓ) + b/c AK4 jets in Run 3", 88, LIGHT, "bold", width=1664, ls=1.1)
text(fig, 128, 580, "Summer22 DY→ℓℓ MC with AK4 jets: samples, cutflow, kinematics, and a comparison "
     "with the boosted AK8 selection" if TEST else
     f"Summer22 DY→ℓℓ MC with AK4 jets, {FILES}: samples, cutflow, kinematics, flavour and pileup checks",
     44, "#C9D3E3", width=1664)
text(fig, 128, 800, DATE, 28, "#C9D3E3")
save(fig)

# setup
fig = page()
y = heading(fig, "Campaign and setup") + 40
y = text(fig, 128, y, "Goal: measure σ(Z+b) / σ(Z+c) with an AK4 jet recoiling against Z→ee/μμ "
         "(switched from the boosted AK8 jet after the group meeting). First step: tune the selection "
         "on DY→ℓℓ MC.", 32, BODY, width=1664) + 40
cards = [("MC CAMPAIGN", "Summer22", "Run3Summer22 = 2022 eras C–D (pre-EE)"),
         ("FORMAT", "NanoAODv12", "130X MC conditions"),
         ("ENERGY (√s)", "13.6 TeV", "Run 3 pp collisions"),
         ("NORMALIZATION", "7.98 fb⁻¹", "2022 C–D golden JSON; brilcalc check pending")]
cw = (1664 - 3 * 32) / 4
for i, (lab, big, small) in enumerate(cards):
    cx = 128 + i * (cw + 32)
    box(fig, cx, y, cw, 280, PANEL)
    text(fig, cx + 36, y + 36, lab, 24, ACCENT, "bold")
    text(fig, cx + 36, y + 90, big, 44, DARK, "bold")
    text(fig, cx + 36, y + 170, small, 24, BODY, width=cw - 72)
y += 280 + 48
text(fig, 128, y, "MC only, no data yet. Processed: 1 file per sample (test run), the same files as the AK8 test. "
     "Code: BTVNanoCommissioning, branch coffea_machine, workflow Zb_Zc_ratio (AK4, commit f8748a6); "
     "the AK8 selection runs as Zb_Zc_ratio_AK8." if TEST else
     f"MC only, no data yet. Processed: {FILES} (the first {NF} files of each sample in the fileset, "
     f"{5 * NF} of 1887 DY files; run_zbzc_ak4_20files.sh). Code: BTVNanoCommissioning, branch coffea_machine, "
     "workflow Zb_Zc_ratio (AK4, commit 31ba6bc, with the GenJet-match counters).", 28, BODY, width=1664)
footer(fig, FOOT, 2)
save(fig)

# samples (same fileset as the AK8 deck)
fig = page()
y = heading(fig, "MC samples: DY→ℓℓ, stitched in pT(ℓℓ)") + 32
box(fig, 128, y, 1664, 110, PANEL)
text(fig, 160, y + 20, "/DYto2L-2Jets_MLL-50[_PTLL-X]_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/", 24, family="DejaVu Sans Mono")
text(fig, 160, y + 56, "  Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-vN/NANOAODSIM", 24, family="DejaVu Sans Mono")
y += 110 + 32
cols = [("Sample", 400, "left"), ("LHE pT(ℓℓ) used", 283, "left"), ("σ [pb]", 216, "right"),
        ("DAS files", 216, "right"), ("DAS events", 250, "right"), ("Test: events used" if TEST else f"{NF} files: events", 299, "right")]
used = {short(ds): od["cutflow_raw"]["Zmm"]["all"] for ds, od in out.items()}
incl = {ds: od for ds, od in out.items() if short(ds) == "Inclusive"}
incl_share = {ch: sum(yields(incl, "jet_pt", ["l", "c", "b"])[ch].values())
              / sum(yields(out, "jet_pt", ["l", "c", "b"])[ch].values()) for ch in CHS}
incl_raw = {ch: raw_selected(incl, ch) / raw_selected(out, ch) for ch in CHS}
rows = [["Inclusive (MLL-50)", "< 100 GeV", "6346", "525", "93.8 M", f"{used['Inclusive']:,}"],
        ["PTLL-100", "100–200 GeV", "105.0", "418", "56.4 M", f"{used['PTLL-100']:,}"],
        ["PTLL-200", "200–400 GeV", "11.24", "335", "44.7 M", f"{used['PTLL-200']:,}"],
        ["PTLL-400", "400–600 GeV", "0.643", "424", "41.6 M", f"{used['PTLL-400']:,}"],
        ["PTLL-600", "> 600 GeV", "0.0994", "185", "9.50 M", f"{used['PTLL-600']:,}"]]
y = table(fig, 128, y, cols, rows, 26) + 32
text(fig, 128, y, "PTLL-X samples are inclusive above X, so each is kept to its own LHE pT(ℓℓ) slice. "
     "σ(PTLL-X) = 6346 pb × fraction of inclusive events with pT(ℓℓ) > X (measured on 27.7 M inclusive events). "
     + ("\"Test: events used\" = events of 1 file" if TEST else f"\"{NF} files: events\" = events of {NF} files")
     + " inside the slice. With no boosted-jet requirement the "
     f"inclusive sample (pT(ℓℓ) < 100 GeV) gives {100 * incl_share['Zee']:.0f}% (Z→ee) / "
     f"{100 * incl_share['Zmm']:.0f}% (Z→μμ) of the scaled yield from only "
     f"{100 * min(incl_raw.values()):.0f}–{100 * max(incl_raw.values()):.0f}% of the raw selected events, "
     "so its large per-event weights limit the MC statistics.", 24, BODY, width=1664)
footer(fig, FOOT, 3)
save(fig)

# selection
fig = page()
y = heading(fig, "Event selection, per channel") + 40
cw = (1664 - 32) / 2
blocks = [
    [("Z→ee / Z→μμ (unchanged)", ["Trigger: HLT_Ele30_WPTight_Gsf / HLT_IsoMu24",
                                  "Leptons pT > 25 GeV, |η| < 2.4; leading pT > 35 GeV",
                                  "e: tight cut-based ID, IP cuts, EB–EE gap veto",
                                  "μ: tight ID, PF isolation < 0.15", "Opposite sign (OS)",
                                  "71 < mℓℓ < 111 GeV", "PuppiMET < 50 GeV"])],
    [("Leading AK4 jet (\"jet\" step)", ["AK4 PUPPI jets, ΔR > 0.4 from selected leptons",
                                         "Tight-lepton-veto jet ID (with NanoAODv12 jetId fix)",
                                         "pT > 30 GeV, |η| < 2.5; ≥ 1 such jet, leading one used",
                                         "No Z pT requirement"]),
     ("Weights and flavour", ["genWeight × pileup × lepton ID/iso/reco SFs", "No trigger SF yet",
                              "Jet flavour from hadronFlavour: b (5), c (4), light; no bb/cc split for AK4",
                              "Also labelled by |partonFlavour|: b, c, uds, g, none (pages 21+)",
                              "Tagger: PNet AK4 B, CvL, CvB"])],
]
for i, col in enumerate(blocks):
    cx = 128 + i * (cw + 32)
    box(fig, cx, y, cw, 730, PANEL)
    yy = y + 40
    for title, items in col:
        yy = text(fig, cx + 40, yy, title, 36, ACCENT, "bold", ls=1.2) + 16
        for it in items:
            yy = text(fig, cx + 40, yy, "• " + it, 26, DARK, width=cw - 80, ls=1.45) + 4
        yy += 24
footer(fig, FOOT, 4)
save(fig)

# cutflow per channel
cf_cols = [("Sample", 266, "left"), ("all", 183, "right"), ("trigger", 183, "right"), ("leptons", 183, "right"),
           ("OS", 166, "right"), ("Zmass", 166, "right"), ("MET", 166, "right"), ("jet", 150, "right"),
           ("jet / MET", 201, "right")]
page_no = 5
for ch, chname in CHS.items():
    cf = {short(ds): od["cutflow_raw"][ch] for ds, od in out.items()}
    rows = [[s] + [f"{cf[s][st]:,}" for st in STEPS] + [f"{100 * cf[s]['jet'] / cf[s]['MET']:.1f}%"]
            for s in ORDER]
    tot = sum(cf[s]["jet"] for s in ORDER)
    lead = max(ORDER, key=lambda s: cf[s]["jet"])
    hi_eff = min(cf[s]["jet"] / cf[s]["MET"] for s in ORDER[1:])
    fig = page()
    y = heading(fig, f"Cutflow, {chname}: raw MC events per step") + 40
    y = table(fig, 128, y, cf_cols, rows, 28) + 48
    text(fig, 128, y, f"{tot:,}", 44, ACCENT, "bold")
    text(fig, 340, y + 4, f"raw MC events pass the full {chname} selection; the most ({100 * cf[lead]['jet'] / tot:.0f}%) "
         f"come from {lead}. The AK4 jet step keeps {100 * cf['Inclusive']['jet'] / cf['Inclusive']['MET']:.0f}% of "
         f"inclusive (low-pT) Z events and ≥ {100 * hi_eff:.0f}% at pT(ℓℓ) > 100 GeV.", 28, BODY, width=1450)
    footer(fig, FOOT + " · \"all\" = events in the sample's LHE pT(ℓℓ) slice", page_no)
    save(fig)
    page_no += 1

# yields by flavour
fl4 = ["l", "c", "b"]
y4 = yields(out, "jet_pt", fl4)
fig = page()
y = heading(fig, "Yields by AK4 jet flavour (7.98 fb⁻¹)") + 40
y_cols = [("Channel", 300, "left")] + [(c, 300, "right") for c in ["light", "c", "b", "total"]]
y_rows = []
for ch, chname in CHS.items():
    v = [y4[ch][f] for f in fl4]
    y_rows.append([chname] + [num(x) for x in v] + [num(sum(v))])
    y_rows.append(["fraction"] + [f"{x / sum(v):.3f}" for x in v] + [""])
y = table(fig, 128, y, y_cols, y_rows, 28, shade=(1, 3)) + 40
box(fig, 128, y, 1664, 220, "#FDF1E4")
box(fig, 128, y, 6, 220, "#E07B24")
yy = text(fig, 168, y + 32, "Still 1 file per sample" if TEST else f"{FILES} ({5 * NF} of 1887 DY files)",
          32, DARK, "bold", ls=1.2) + 12
text(fig, 168, yy, f"No negative yields now: {raw_selected(out, 'Zee'):,} (Z→ee) and {raw_selected(out, 'Zmm'):,} "
     "(Z→μμ) raw events pass, vs ~1.4k / 2.1k with AK8. Single negative-weight amcatnlo events still leave "
     "jumps and empty bins in the tails of the plots. No b-tag requirement applied yet." if TEST else
     f"{raw_selected(out, 'Zee'):,} (Z→ee) and {raw_selected(out, 'Zmm'):,} (Z→μμ) raw events pass. The "
     "inclusive sample (pT(ℓℓ) < 100 GeV) still carries large per-event weights, so the far tails (e.g. "
     "N_jet ≥ 6) rest on a few events. No b-tag requirement applied yet.",
     26, BODY, width=1580, ls=1.45)
footer(fig, FOOT + " · weights: σ × L / Σw × genWeight × PU × lepton SFs", page_no)
save(fig)
page_no += 1

# AK8 vs AK4 comparison (1-file test), or AK4 at 1 file vs N files per sample


def frac(y, ch, fls):
    return f"{sum(y[ch][f] for f in fls) / sum(y[ch].values()):.3f}".replace("-", "−")


fig = page()
if TEST:
    fl8 = ["l", "c", "cc", "b", "bb"]
    y8 = yields(out8, "fj_pt", fl8)
    y = heading(fig, "AK8 vs AK4: same files, same Z selection") + 40
    c_cols = [("", 420, "left"), ("AK8 Z→ee", 310, "right"), ("AK4 Z→ee", 310, "right"),
              ("AK8 Z→μμ", 310, "right"), ("AK4 Z→μμ", 310, "right")]
    c_rows = [["Raw events selected"] + sum(([f"{raw_selected(out8, ch):,}", f"{raw_selected(out, ch):,}"] for ch in CHS), []),
              ["Scaled yield"] + sum(([num(sum(y8[ch].values())), num(sum(y4[ch].values()))] for ch in CHS), []),
              ["b fraction (b + bb)"] + sum(([frac(y8, ch, ['b', 'bb']), frac(y4, ch, ['b'])] for ch in CHS), []),
              ["c fraction (c + cc)"] + sum(([frac(y8, ch, ['c', 'cc']), frac(y4, ch, ['c'])] for ch in CHS), []),
              ["light fraction"] + sum(([frac(y8, ch, ['l']), frac(y4, ch, ['l'])] for ch in CHS), []),
              ["Jet requirement", "pT > 200, mSD > 40", "pT > 30", "pT > 200, mSD > 40", "pT > 30"]]
    y = table(fig, 128, y, c_cols, c_rows, 28, shade=(0, 2, 4)) + 40
    text(fig, 128, y, "AK8 flavour is from B/C hadron counts inside the jet (bb/b/cc/c); AK4 flavour is hadronFlavour. "
         "The AK4 selection keeps ~15× more events because it does not require a boosted Z. AK8 heavy-flavour "
         "fractions are unreliable at this statistics (negative Z→μμ b yield).", 26, BODY, width=1664)
    footer(fig, FOOT + " · AK8 numbers from the 7 Oct test output", page_no)
else:
    yr = yields(ref, "jet_pt", fl4)
    y = heading(fig, f"AK4: 1 file vs {NF} files per sample") + 40
    c_cols = [("", 420, "left"), ("1 file Z→ee", 310, "right"), (f"{NF} files Z→ee", 310, "right"),
              ("1 file Z→μμ", 310, "right"), (f"{NF} files Z→μμ", 310, "right")]
    c_rows = [["Raw events selected"] + sum(([f"{raw_selected(ref, ch):,}", f"{raw_selected(out, ch):,}"] for ch in CHS), []),
              ["Scaled yield"] + sum(([num(sum(yr[ch].values())), num(sum(y4[ch].values()))] for ch in CHS), []),
              ["b fraction"] + sum(([frac(yr, ch, ['b']), frac(y4, ch, ['b'])] for ch in CHS), []),
              ["c fraction"] + sum(([frac(yr, ch, ['c']), frac(y4, ch, ['c'])] for ch in CHS), []),
              ["light fraction"] + sum(([frac(yr, ch, ['l']), frac(y4, ch, ['l'])] for ch in CHS), [])]
    y = table(fig, 128, y, c_cols, c_rows, 28, shade=(0, 2, 4)) + 40
    def neff(o, ch):
        """Effective number of MC events (sum w)^2 / sum w^2 after the full selection."""
        v = var = 0.0
        for ds, od in o.items():
            sc = xs[ds] * LUMI / od["sumw"]
            h = od["jet_pt"][{"channel": ch}].sum(flow=True)
            v += h.value * sc
            var += h.variance * sc ** 2
        return v * v / var

    # largest flavour-fraction shift, in units of the 1-file binomial error sqrt(f(1-f)/N_eff)
    shifts = []
    for ch, lab in CHS.items():
        ne = neff(ref, ch)
        for f, fl in (("b", "b"), ("c", "c"), ("l", "light")):
            f1 = yr[ch][f] / sum(yr[ch].values())
            fn = y4[ch][f] / sum(y4[ch].values())
            shifts.append((abs(fn - f1) / (f1 * (1 - f1) / ne) ** 0.5, lab, fl, f1, fn))
    sig, lab, fl, f1, fn = max(shifts)
    text(fig, 128, y, f"Same selection and code; {NF}× more files per sample, about "
         f"{raw_selected(out, 'Zmm') / raw_selected(ref, 'Zmm'):.0f}× more raw events. The 1-file test had only "
         f"N_eff ≈ {neff(ref, 'Zee'):,.0f} (Z→ee) / {neff(ref, 'Zmm'):,.0f} (Z→μμ) effective events. The largest change "
         f"is the {lab} {fl} fraction, {f1:.3f} → {fn:.3f}, {sig:.1f}σ of the 1-file statistical error, so the "
         f"1-file numbers were a {'rough' if sig > 2 else 'fair'} estimate. The AK8 vs AK4 comparison "
         "(1-file test only) is in the test deck.", 26, BODY, width=1664)
    footer(fig, FOOT + " · 1-file numbers from the AK4 test output", page_no)
save(fig)
page_no += 1

# kinematic and tagger plots
plots = [
    ("z_mass", "Dilepton mass", "m(ℓℓ) after the full selection (71–111 GeV window): peaks at the Z mass in both channels."),
    ("z_pt", "Dilepton pT", "pT(ℓℓ) of the Z candidate after the full selection. No Z pT cut: dominated by low pT, unlike the boosted AK8 selection."),
    ("lep0_pt", "Leading-lepton pT", "Leading lepton of the Z candidate, after the full selection (pT > 35 GeV required)."),
    ("lep1_pt", "Subleading-lepton pT", "Subleading lepton of the Z candidate, after the full selection (pT > 25 GeV required)."),
    ("jet_pt", "Leading AK4 jet pT", "Leading lepton-cleaned AK4 jet with tight-lepton-veto ID (pT > 30 GeV required)."),
    ("jet_eta", "Leading AK4 jet η", "Pseudorapidity of the selected AK4 jet (|η| < 2.5 required)."),
    ("n_jet", "AK4 jet multiplicity", "Number of selected AK4 jets (pT > 30 GeV, |η| < 2.5, ID, lepton-cleaned) in events passing the full selection."),
    ("lhe_vpt", "LHE pT(ℓℓ)", "Generator-level pT(ℓℓ) after the full selection: checks the sample stitching (slices at 100/200/400/600 GeV)."),
    ("jet_PNetB", "Leading AK4 jet: PNet B", "ParticleNet b-tag score of the selected jet; b jets pile up near 1, light jets near 0."),
    ("jet_PNetCvL", "Leading AK4 jet: PNet CvL", "ParticleNet charm-vs-light score of the selected jet."),
    ("jet_PNetCvB", "Leading AK4 jet: PNet CvB", "ParticleNet charm-vs-b score of the selected jet."),
]
for name, title, caption in plots:
    fig = page()
    y = heading(fig, title, y=96) + 20
    y = text(fig, 128, y, caption, 28, BODY, width=1664) + 20
    hpx = 1000 - 12 - y  # plot fills the page down to the footer
    ax = fig.add_axes([128 / W, 1 - (y + hpx) / H, 1664 / W, hpx / H])
    ax.imshow(mpimg.imread(os.path.join(indir, "plots", f"{name}.png")))
    ax.axis("off")
    footer(fig, PLOT_FOOT, page_no)
    save(fig)
    page_no += 1

# CvL vs CvB map
fig = page()
y = heading(fig, "PNet charm-tagging plane: CvL vs CvB", y=96) + 20
y = text(fig, 128, y, "Selected AK4 jets per flavour, both channels summed, normalized to unit area. b jets sit at "
         "high CvL and low CvB, light jets at low CvL and high CvB. c jets are at high CvB, but a large "
         "part of them overlaps the light-jet corner (low CvL), with the rest at high CvL.", 28, BODY, width=1664) + 20
img = mpimg.imread(os.path.join(indir, "plots", "jet_CvL_CvB.png"))
hpx = 1664 * img.shape[0] / img.shape[1]
ax = fig.add_axes([128 / W, 1 - (y + hpx) / H, 1664 / W, hpx / H])
ax.imshow(img)
ax.axis("off")
footer(fig, FOOT + " · Z→ee + Z→μμ", page_no)
save(fig)
page_no += 1

# hadronFlavour vs partonFlavour: definitions and yields under both
pfl = ["b", "c", "uds", "g", "none"]
yp = yields(out, "jet_pt", pfl, axis="pflav")
fig = page()
y = heading(fig, "hadronFlavour vs partonFlavour") + 40
cw = (1664 - 32) / 2
defs = [("hadronFlavour (default)", ["Ghost-matched B / C hadrons clustered into the jet",
                                     "b (5) if any B hadron, else c (4) if any C hadron, else 0",
                                     "BTV standard; b/c-tag SFs are measured for it"]),
        ("partonFlavour", ["Ghost-matched partons (last before hadronization) in the jet",
                           "Hardest heavy parton wins: b (5), c (4), else hardest light parton",
                           "Splits light jets into uds (1–3) and gluon (21); 0 = no parton matched"])]
for i, (title, items) in enumerate(defs):
    cx = 128 + i * (cw + 32)
    box(fig, cx, y, cw, 290, PANEL)
    yy = text(fig, cx + 36, y + 30, title, 32, ACCENT, "bold", ls=1.2) + 10
    for it in items:
        yy = text(fig, cx + 36, yy, "• " + it, 24, DARK, width=cw - 72, ls=1.4) + 2
y += 290 + 36
d_cols = [("Fraction of scaled yield", 520, "left"), ("hadron Z→ee", 286, "right"), ("parton Z→ee", 286, "right"),
          ("hadron Z→μμ", 286, "right"), ("parton Z→μμ", 286, "right")]
d_rows = [["b"] + sum(([frac(y4, ch, ["b"]), frac(yp, ch, ["b"])] for ch in CHS), []),
          ["c"] + sum(([frac(y4, ch, ["c"]), frac(yp, ch, ["c"])] for ch in CHS), []),
          ["light (hadron) / uds + g + none (parton)"] + sum(([frac(y4, ch, ["l"]), frac(yp, ch, ["uds", "g", "none"])]
                                                              for ch in CHS), []),
          ["   of which g / none (parton)"] + sum((["", f"{frac(yp, ch, ['g'])} / {frac(yp, ch, ['none'])}"]
                                                   for ch in CHS), [])]
table(fig, 128, y, d_cols, d_rows, 26, shade=(0, 2))
footer(fig, FOOT + " · leading AK4 jet, scaled to 7.98 fb⁻¹", page_no)
save(fig)
page_no += 1

# migration matrix
def migration(o, f, p):
    """Scaled fraction of hadron-flavour-f jets with parton flavour p, both channels summed."""
    num_, den = 0.0, 0.0
    for ds, od in o.items():
        sc = xs[ds] * LUMI / od["sumw"]
        for ch in CHS:
            h = od["jet_pt"][{"channel": ch, "flav": f}]
            num_ += h[{"pflav": p}].sum(flow=True).value * sc
            den += h.sum(flow=True).value * sc
    return 100 * num_ / den


MIGRATION_CAPTION = (
    f"Each row shows where the jets of one hadronFlavour land in partonFlavour. {migration(out, 'b', 'b'):.0f}% of "
    f"hadron-b and {migration(out, 'c', 'c'):.0f}% of hadron-c jets also have partonFlavour b / c (both channels). "
    f"Hadron-light jets split into uds ({migration(out, 'l', 'uds'):.0f}%) and gluon ({migration(out, 'l', 'g'):.0f}%); "
    f"{migration(out, 'l', 'c') + migration(out, 'l', 'b'):.1f}% carry a c or b parton without a matching hadron."
)
fig = page()
y = heading(fig, "Hadron vs parton flavour migration", y=96) + 20
y = text(fig, 128, y, MIGRATION_CAPTION, 28, BODY, width=1664) + 20
img = mpimg.imread(os.path.join(indir, "plots", "flav_migration.png"))
hpx = min(1664 * img.shape[0] / img.shape[1], 620)
wpx = hpx * img.shape[1] / img.shape[0]
ax = fig.add_axes([(W - wpx) / 2 / W, 1 - (y + hpx) / H, wpx / W, hpx / H])
ax.imshow(img)
ax.axis("off")
footer(fig, FOOT + " · rows: hadronFlavour, each sums to 100% (scaled) · small negative entries = NLO negative weights", page_no)
save(fig)
page_no += 1

# plots stacked by partonFlavour
pplots = [
    ("jet_pt", "Leading AK4 jet pT, by partonFlavour", "Same as page 13, stacked by |partonFlavour| of the leading jet."),
    ("jet_eta", "Leading AK4 jet η, by partonFlavour", "Same as page 14, stacked by |partonFlavour| of the leading jet."),
    ("n_jet", "AK4 jet multiplicity, by partonFlavour", "Same as page 15, stacked by |partonFlavour| of the leading jet."),
    ("jet_PNetB", "PNet B, by partonFlavour", "Same as page 17, stacked by |partonFlavour| of the leading jet."),
    ("jet_PNetCvL", "PNet CvL, by partonFlavour", "Same as page 18, stacked by |partonFlavour| of the leading jet."),
    ("jet_PNetCvB", "PNet CvB, by partonFlavour", "Same as page 19, stacked by |partonFlavour| of the leading jet."),
]
for name, title, caption in pplots:
    fig = page()
    y = heading(fig, title, y=96) + 20
    y = text(fig, 128, y, caption, 28, BODY, width=1664) + 20
    hpx = 1000 - 12 - y  # plot fills the page down to the footer
    ax = fig.add_axes([128 / W, 1 - (y + hpx) / H, 1664 / W, hpx / H])
    ax.imshow(mpimg.imread(os.path.join(indir, "plots", f"{name}_parton.png")))
    ax.axis("off")
    footer(fig, FOOT + " · by leading-jet partonFlavour; lower: fraction per bin · Z→ee left, Z→μμ right", page_no)
    save(fig)
    page_no += 1


# GenJet match of the leading jet: partonFlavour 0 = pileup?
def genmatch(o, ch, pf=None, hf=None, scaled=False):
    """(matched, nomatch) leading-jet counts; raw, or scaled to the lumi when `scaled`."""
    n = {"matched": 0.0, "nomatch": 0.0}
    for ds, od in o.items():
        sc = xs[ds] * LUMI / od["sumw"] if scaled else 1.0
        src = od["sumw_genmatch" if scaled else "nevt_genmatch"][ch]
        for k, v in src.items():
            h, p, g = k.split("|")
            if pf in (None, p) and hf in (None, h):
                n[g] += v * sc
    return n["matched"], n["nomatch"]


fig = page()
y = heading(fig, "Leading jets with partonFlavour 0 are pileup", y=96) + 20
none_ee, none_mm = (genmatch(out, ch, "none") for ch in CHS)
y = text(fig, 128, y, "A jet with no GenJet (pT > 10 GeV) within ΔR < 0.4 (Jet_genJetIdx = −1) is a pileup jet. "
         + (f"All {int(none_ee[1] + none_mm[1])}" if none_ee[0] + none_mm[0] == 0 else
            f"{int(none_ee[1] + none_mm[1])} of {int(sum(none_ee) + sum(none_mm))} "
            f"({100 * (none_ee[1] + none_mm[1]) / (sum(none_ee) + sum(none_mm)):.0f}%)")
         + f" leading jets with partonFlavour 0 have no GenJet match "
         f"({int(none_ee[1])} Z→ee, {int(none_mm[1])} Z→μμ).", 28, BODY, width=1664) + 24
g_cols = [("Leading-jet partonFlavour", 520, "left"), ("Z→ee no GenJet / all", 380, "right"), ("Z→ee %", 192, "right"),
          ("Z→μμ no GenJet / all", 380, "right"), ("Z→μμ %", 192, "right")]
g_rows = []
for p in pfl + [None]:
    row = [p or "all"]
    for ch in CHS:
        m, u = genmatch(out, ch, p)
        row += [f"{int(u):,} / {int(m + u):,}", f"{100 * u / (m + u):.2f}" if m + u else "–"]
    g_rows.append(row)
y = table(fig, 128, y, g_cols, g_rows, 26, shade=(4, 5)) + 30
nob, alb = (sum(v) for v in zip(*(genmatch(out, ch, hf="b")[::-1] for ch in CHS)))
noc, alc = (sum(v) for v in zip(*(genmatch(out, ch, hf="c")[::-1] for ch in CHS)))
scl = " and ".join(f"{100 * u / (m + u):.1f}% ({lab})" for ch, lab in CHS.items()
                   for m, u in [genmatch(out, ch, scaled=True)])
for s in [f"Not every pileup jet has partonFlavour 0: most unmatched leading jets carry a gluon label "
          f"(a soft ISR/UE gluon is ghost-matched, but there is no GenJet).",
          f"Pileup barely reaches the heavy-flavour yields: {int(nob)} of {int(nob + alb):,} hadron-b and {int(noc)} of "
          f"{int(noc + alc):,} hadron-c leading jets are unmatched. Scaled, {scl} of leading jets are unmatched. "
          + ("This is above the raw fraction because the events come from the high-weight inclusive sample, "
             "so it waits for the full MC run." if TEST else
             "This is above the raw fraction because the unmatched jets sit in the high-weight inclusive sample, "
             "but it is close to the 1-file value, so it is not a statistical fluke.")]:
    y = text(fig, 128, y, "• " + s, 26, DARK, width=1664) + 8
footer(fig, FOOT + " · raw (unweighted) leading-jet counts · counters nevt_genmatch / sumw_genmatch", page_no)
save(fig)
page_no += 1

# N_jet bumps vs MC statistics: 1 file vs 20 files per sample (compare_njet_zbzc.py)
dir20 = "hists_zbzc_ak4_20files/merged"
if os.path.exists(os.path.join(dir20, "plots", "n_jet_stats_compare.png")):
    out20 = load_dir(dir20)

    def njet(o, ch, n):
        """Scaled yield and N_eff in N_jet bin n, all flavours."""
        v = var = 0.0
        for ds, od in o.items():
            sc = xs[ds] * LUMI / od["sumw"]
            h = od["n_jet"][{"channel": ch, "flav": sum, "pflav": sum, "n": n}]
            v += h.value * sc
            var += h.variance * sc ** 2
        return v, (v * v / var if var > 0 else 0.0)

    def nj(o, ch, n):
        v, ne = njet(o, ch, n)
        return f"{num(v)} (N_eff {ne:.1f})"

    fig = page()
    y = heading(fig, "N_jet bumps go away with more MC", y=96) + 20
    y = text(fig, 128, y, f"20 files per sample instead of 1. Z→ee N_jet = 6: {nj(out, 'Zee', 6)} → {nj(out20, 'Zee', 6)}; "
             f"Z→μμ N_jet = 6: {nj(out, 'Zmm', 6)} → {nj(out20, 'Zmm', 6)}, N_jet = 8: {nj(out, 'Zmm', 8)} → "
             f"{nj(out20, 'Zmm', 8)}. Both spectra now fall smoothly up to N_jet = 7. The new Z→ee N_jet = 8 "
             f"point, {nj(out20, 'Zee', 8)}, is again a single inclusive-sample event: N_jet ≥ 6 still needs the full run.",
             26, BODY, width=1664) + 16
    img = mpimg.imread(os.path.join(dir20, "plots", "n_jet_stats_compare.png"))
    hpx = min(1664 * img.shape[0] / img.shape[1], 1000 - 24 - y)
    wpx = hpx * img.shape[1] / img.shape[0]
    ax = fig.add_axes([(W - wpx) / 2 / W, 1 - (y + hpx) / H, wpx / W, hpx / H])
    ax.imshow(img)
    ax.axis("off")
    footer(fig, "Summer22 DY→ℓℓ MC · AK4 jets · all flavours, scaled to 7.98 fb⁻¹ · error bars: MC stat · "
           f"20-file plots in {dir20}/plots", page_no)
    save(fig)
    page_no += 1
page_no -= 1

pdf.close()
print("wrote", outfile, f"({page_no} pages)")
