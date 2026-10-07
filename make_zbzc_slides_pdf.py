"""PDF version of the "Run 3 Z+b/c: first Summer22 MC look" slides (2026-10-07).

Same content as the online deck (https://claude.ai/artifact/FSDzBLV3qnBMVzSiQsscXE):
setup, samples, selection, cutflow per channel, yields by AK8 jet flavour and the
kinematic plots from plot_zbzc.py, drawn with matplotlib on 16:9 pages.

Usage:
    python make_zbzc_slides_pdf.py hists_zbzc_test/test_zbzc
writes <dir>/slides_zbzc_summer22_test.pdf (plots read from <dir>/plots/).
"""
import os
import sys
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch

indir = sys.argv[1]
outfile = os.path.join(indir, "slides_zbzc_summer22_test.pdf")

W, H = 1920, 1080
DARK, LIGHT, PANEL, ACCENT, BODY, MUTED = "#14213D", "#FBFBF8", "#EEF1F5", "#1F5FA8", "#4A5568", "#6A7179"
PX = 72 / 100  # px -> pt at dpi 100
plt.rcParams["font.family"] = "DejaVu Sans"

FOOT = "Summer22 DY→ℓℓ MC · 1 file per sample"
PLOT_FOOT = FOOT + " · stacked by AK8 jet flavour · Z→ee left, Z→μμ right"


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


pdf = PdfPages(outfile)

# 1 cover
fig = page(DARK)
text(fig, 128, 260, "BTVNANOCOMMISSIONING · ZB_ZC_RATIO WORKFLOW", 28, "#7FB3E6", "bold")
text(fig, 128, 340, "Z(→ℓℓ) + b/c boosted jets in Run 3", 88, LIGHT, "bold", width=1664, ls=1.1)
text(fig, 128, 580, "First look at Summer22 DY→ℓℓ MC: samples, cutflow and kinematics", 44, "#C9D3E3", width=1664)
text(fig, 128, 720, "7 October 2026", 28, "#C9D3E3")
pdf.savefig(fig); plt.close(fig)

# 2 setup
fig = page()
y = heading(fig, "Campaign and setup") + 40
y = text(fig, 128, y, "Goal: measure σ(Z+b) / σ(Z+c) with a boosted AK8 jet recoiling against Z→ee/μμ. "
         "First step: tune the selection on DY→ℓℓ MC.", 32, BODY, width=1664) + 40
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
text(fig, 128, y, "MC only, no data yet. Processed: 1 file per sample (test run). Code: BTVNanoCommissioning, "
     "branch coffea_machine, commit f8cd578.", 28, BODY, width=1664)
footer(fig, FOOT, 2)
pdf.savefig(fig); plt.close(fig)

# 3 samples
fig = page()
y = heading(fig, "MC samples: DY→ℓℓ, stitched in pT(ℓℓ)") + 32
box(fig, 128, y, 1664, 110, PANEL)
text(fig, 160, y + 20, "/DYto2L-2Jets_MLL-50[_PTLL-X]_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/", 24, family="DejaVu Sans Mono")
text(fig, 160, y + 56, "  Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-vN/NANOAODSIM", 24, family="DejaVu Sans Mono")
y += 110 + 32
cols = [("Sample", 400, "left"), ("LHE pT(ℓℓ) used", 283, "left"), ("σ [pb]", 216, "right"),
        ("DAS files", 216, "right"), ("DAS events", 250, "right"), ("Test: events used", 299, "right")]
rows = [["Inclusive (MLL-50)", "< 100 GeV", "6346", "525", "93.8 M", "197,672"],
        ["PTLL-100", "100–200 GeV", "105.0", "418", "56.4 M", "161,921"],
        ["PTLL-200", "200–400 GeV", "11.24", "335", "44.7 M", "91,186"],
        ["PTLL-400", "400–600 GeV", "0.643", "424", "41.6 M", "2,727"],
        ["PTLL-600", "> 600 GeV", "0.0994", "185", "9.50 M", "939"]]
y = table(fig, 128, y, cols, rows, 26) + 32
text(fig, 128, y, "PTLL-X samples are inclusive above X, so each is kept to its own LHE pT(ℓℓ) slice. "
     "σ(PTLL-X) = 6346 pb × fraction of inclusive events with pT(ℓℓ) > X (measured on 27.7 M inclusive events). "
     "\"Test: events used\" = events of 1 file inside the slice.", 24, BODY, width=1664)
footer(fig, FOOT, 3)
pdf.savefig(fig); plt.close(fig)

# 4 selection
fig = page()
y = heading(fig, "Event selection, per channel") + 40
cw = (1664 - 32) / 2
blocks = [
    [("Z→ee / Z→μμ", ["Trigger: HLT_Ele30_WPTight_Gsf / HLT_IsoMu24",
                      "Leptons pT > 25 GeV, |η| < 2.4; leading pT > 35 GeV",
                      "e: tight cut-based ID, IP cuts, EB–EE gap veto",
                      "μ: tight ID, PF isolation < 0.15", "Opposite sign (OS)",
                      "71 < mℓℓ < 111 GeV", "PuppiMET < 50 GeV"])],
    [("Leading AK8 jet (\"jet\" step)", ["ΔR > 0.8 from selected leptons", "Tight jet ID, two soft-drop subjets",
                                         "pT > 200 GeV, |η| < 2.5, mSD > 40 GeV"]),
     ("Weights and flavour", ["genWeight × pileup × lepton ID/iso/reco SFs", "No trigger SF yet",
                              "Jet flavour from B/C hadron counts: bb, b, cc, c, light"])],
]
for i, col in enumerate(blocks):
    cx = 128 + i * (cw + 32)
    box(fig, cx, y, cw, 640, PANEL)
    yy = y + 40
    for title, items in col:
        yy = text(fig, cx + 40, yy, title, 36, ACCENT, "bold", ls=1.2) + 16
        for it in items:
            yy = text(fig, cx + 40, yy, "• " + it, 26, DARK, width=cw - 80, ls=1.45) + 4
        yy += 24
footer(fig, FOOT, 4)
pdf.savefig(fig); plt.close(fig)

# 5-6 cutflow
cf_cols = [("Sample", 266, "left"), ("all", 183, "right"), ("trigger", 183, "right"), ("leptons", 183, "right"),
           ("OS", 166, "right"), ("Zmass", 166, "right"), ("MET", 166, "right"), ("jet", 150, "right"),
           ("jet / MET", 201, "right")]
cutflows = {
    "Z→ee": ([["Inclusive", "197,672", "32,660", "9,802", "9,745", "9,396", "8,872", "1", "0.01%"],
              ["PTLL-100", "161,921", "46,448", "13,156", "13,037", "12,032", "10,642", "139", "1.3%"],
              ["PTLL-200", "91,186", "31,202", "11,594", "11,431", "10,398", "8,584", "1,211", "14.1%"],
              ["PTLL-400", "2,727", "1,013", "458", "447", "396", "287", "77", "26.8%"],
              ["PTLL-600", "939", "229", "101", "100", "82", "54", "12", "22.2%"]],
             "1,440", "raw MC events pass the full Z→ee selection; 84% of them come from PTLL-200. "
                      "The boosted-jet step keeps 1.3% (PTLL-100) to 14% (PTLL-200) of Z events."),
    "Z→μμ": ([["Inclusive", "197,672", "42,062", "17,685", "17,685", "17,054", "16,139", "8", "0.05%"],
              ["PTLL-100", "161,921", "48,592", "20,606", "20,604", "19,043", "16,788", "225", "1.3%"],
              ["PTLL-200", "91,186", "31,717", "16,868", "16,865", "15,258", "12,453", "1,753", "14.1%"],
              ["PTLL-400", "2,727", "1,048", "659", "659", "592", "407", "104", "25.6%"],
              ["PTLL-600", "939", "319", "199", "199", "178", "102", "31", "30.4%"]],
             "2,121", "raw MC events pass the full Z→μμ selection; 83% of them come from PTLL-200. "
                      "Jet-step efficiencies similar to Z→ee."),
}
for n, (ch, (rows, big, msg)) in enumerate(cutflows.items(), start=5):
    fig = page()
    y = heading(fig, f"Cutflow, {ch}: raw MC events per step") + 40
    y = table(fig, 128, y, cf_cols, rows, 28) + 48
    text(fig, 128, y, big, 44, ACCENT, "bold")
    text(fig, 300, y + 4, msg, 28, BODY, width=1490)
    footer(fig, FOOT + " · \"all\" = events in the sample's LHE pT(ℓℓ) slice", n)
    pdf.savefig(fig); plt.close(fig)

# 7 yields
fig = page()
y = heading(fig, "Yields by AK8 jet flavour (7.98 fb⁻¹)") + 40
y_cols = [("Channel", 266, "left")] + [(c, 233, "right") for c in ["light", "c", "cc", "b", "bb", "total"]]
y_rows = [["Z→ee", "1897.8", "137.0", "128.7", "65.1", "31.1", "2259.7"],
          ["fraction", "0.840", "0.061", "0.057", "0.029", "0.014", ""],
          ["Z→μμ", "2228.6", "265.0", "415.5", "−191.8", "67.3", "2784.7"],
          ["fraction", "0.800", "0.095", "0.149", "−0.069", "0.024", ""]]
y = table(fig, 128, y, y_cols, y_rows, 28, shade=(1, 3)) + 40
box(fig, 128, y, 1664, 220, "#FDF1E4")
box(fig, 128, y, 6, 220, "#E07B24")
yy = text(fig, 168, y + 32, "Heavy-flavour numbers are not reliable yet", 32, DARK, "bold", ls=1.2) + 12
text(fig, 168, yy, "With 1 file per sample each inclusive-sample event weighs about 250, and amcatnlo events can "
     "have negative weights: one or two such events give the negative b yield in Z→μμ. "
     "The b and c fractions need the full samples.", 26, BODY, width=1580, ls=1.45)
footer(fig, FOOT + " · weights: σ × L / Σw × genWeight × PU × lepton SFs", 7)
pdf.savefig(fig); plt.close(fig)

# 8-15 kinematic plots
plots = [
    ("z_mass", "Dilepton mass", "m(ℓℓ) after the full selection (71–111 GeV window): peaks at the Z mass in both channels."),
    ("z_pt", "Dilepton pT", "pT(ℓℓ) of the Z candidate after the full selection; the Z recoils against the boosted AK8 jet."),
    ("lep0_pt", "Leading-lepton pT", "Leading lepton of the Z candidate, after the full selection (pT > 35 GeV required)."),
    ("lep1_pt", "Subleading-lepton pT", "Subleading lepton of the Z candidate, after the full selection (pT > 25 GeV required)."),
    ("fj_pt", "Leading AK8 jet pT", "Leading lepton-cleaned AK8 jet with tight ID and two subjets (pT > 200 GeV required)."),
    ("fj_eta", "Leading AK8 jet η", "Pseudorapidity of the selected AK8 jet (|η| < 2.5 required)."),
    ("fj_msd", "Leading AK8 jet soft-drop mass", "mSD of the selected AK8 jet (mSD > 40 GeV required)."),
    ("n_fj", "AK8 jet multiplicity", "Number of lepton-cleaned AK8 jets with tight ID and two subjets, in events passing the full selection."),
]
for n, (name, title, caption) in enumerate(plots, start=8):
    fig = page()
    y = heading(fig, title, y=96) + 20
    y = text(fig, 128, y, caption, 28, BODY, width=1664) + 20
    ax = fig.add_axes([128 / W, 1 - (y + 666) / H, 1664 / W, 666 / H])
    ax.imshow(mpimg.imread(os.path.join(indir, "plots", f"{name}.png")))
    ax.axis("off")
    foot = PLOT_FOOT.replace("by AK8", "by leading AK8") if name == "n_fj" else PLOT_FOOT
    footer(fig, foot, n)
    pdf.savefig(fig); plt.close(fig)

pdf.close()
print("wrote", outfile)
