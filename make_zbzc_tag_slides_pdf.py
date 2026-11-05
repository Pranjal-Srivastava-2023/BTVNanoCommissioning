"""Deck for the advisor's request: Summer22 kinematics with all POG corrections and SFs, inclusive and
with a b-tagged or c-tagged leading AK4 jet (PNet Loose, Medium, Tight).
Run: ZBZC_RUN=zbzc_run3_tag (20 files per sample), plots from plot_zbzc_run3.py with ZBZC_TAG=<region>.
Numbers below are copied from hists_zbzc_run3_tag/Summer22/yields*.txt (see NOTES, 2026-11-05).

Usage:  python make_zbzc_tag_slides_pdf.py [--date "5 November 2026"]
Output: hists_zbzc_run3_tag/Summer22/slides_zbzc_tag_Summer22.pdf
"""
import argparse
import datetime
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch

parser = argparse.ArgumentParser()
parser.add_argument("--date", default=None)
args = parser.parse_args()
DATE = args.date or datetime.date.today().strftime("%-d %B %Y")
D = "hists_zbzc_run3_tag/Summer22"
OUT = f"{D}/slides_zbzc_tag_Summer22.pdf"

# ------------------------------------------------------------------ layout (as make_zbzc_run3_slides_pdf.py)
W, H = 1920, 1080
DARK, LIGHT, PANEL, ACCENT, BODY, MUTED = "#14213D", "#FBFBF8", "#EEF1F5", "#1F5FA8", "#4A5568", "#6A7179"
GOOD = ("#E8F3EA", "#2E7D32", "#1B5E20")
OPEN = ("#FDF1E4", "#E07B24", DARK)
PX = 72 / 100
plt.rcParams["font.family"] = "DejaVu Sans"
FOOT = "Summer22 (2022 C–D), 13.6 TeV · Z→ℓℓ + jets · 20 files per MC sample and per data channel · AK4 jets · stat. errors only"


def page(bg=LIGHT):
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    fig.patch.set_facecolor(bg)
    return fig


def text(fig, x, y, s, size, color=DARK, weight="normal", ha="left", width=None, ls=1.4):
    if width:
        s = "\n".join(textwrap.fill(p, max(1, int(width / (0.55 * size)))) for p in s.split("\n"))
    fig.text(x / W, 1 - y / H, s, fontsize=size * PX, color=color, weight=weight, ha=ha, va="top", linespacing=ls)
    return y + size * ls * (s.count("\n") + 1)


def box(fig, x, y, w, h, color):
    fig.add_artist(FancyBboxPatch((x / W, 1 - (y + h) / H), w / W, h / H, boxstyle="round,pad=0,rounding_size=0.008",
                                  transform=fig.transFigure, facecolor=color, edgecolor=color, lw=0))


def footer(fig, n):
    text(fig, 128, 1030, f"{FOOT} · {n}", 20, MUTED)


def heading(fig, s, sub=None):
    y = text(fig, 128, 70, s, 56, DARK, "bold", ls=1.15)
    if sub:
        y = text(fig, 128, y + 6, sub, 26, BODY, width=1664)
    return y


def note(fig, y, title, body, style=GOOD, h=150, x=128, w=1664):
    color, bar, tcolor = style
    box(fig, x, y, w, h, color)
    box(fig, x, y, 6, h, bar)
    yy = text(fig, x + 40, y + 20, title, 28, tcolor, "bold", ls=1.2) + 6
    if body:
        text(fig, x + 40, yy, body, 23, DARK, width=w - 80, ls=1.3)
    return y + h


def image(fig, path, y, x=128, w=1664, hmax=None):
    img = mpimg.imread(path)
    h = w * img.shape[0] / img.shape[1]
    if hmax and h > hmax:
        w2 = hmax * img.shape[1] / img.shape[0]
        x, w, h = x + (w - w2) / 2, w2, hmax
    ax = fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])
    ax.imshow(img)
    ax.axis("off")
    return y + h


def table(fig, x, y, cols, rows, size=26, colors=None):
    colors = colors or {}
    rh = size * 2.0
    for i, row in enumerate([[c[0] for c in cols]] + rows):
        cx = x
        for (hdr, w, al), val in zip(cols, row):
            tx = cx + (w - 12 if al == "right" else 12)
            col = colors.get(str(val), DARK)
            text(fig, tx, y + i * rh + size * 0.45, str(val), size, col,
                 "bold" if i == 0 or str(val) in colors else "normal", ha=al)
            cx += w
        fig.add_artist(plt.Line2D([x / W, (x + sum(c[1] for c in cols)) / W], [1 - (y + (i + 1) * rh) / H] * 2,
                                  color="#C9D3E3" if i else DARK, lw=1 if i else 2, transform=fig.transFigure))
    return y + (len(rows) + 1) * rh


pdf = PdfPages(OUT)
n = 0


def save(fig):
    global n
    n += 1
    footer(fig, n)
    pdf.savefig(fig)
    plt.close(fig)


def plots_page(region, title, sub, vars4):
    """Four plots (Zee left, Zmm right in each) in a 2 x 2 grid."""
    fig = page()
    y = heading(fig, title, sub) + 16
    folder = "plots" if region == "incl" else f"plots_{region}"
    for i, var in enumerate(vars4):
        x = 190 + (i % 2) * 790
        yy = y + (i // 2) * 400
        image(fig, f"{D}/{folder}/{var}.png", yy, x=x, w=750)
    save(fig)


# ------------------------------------------------------------------ cover
fig = page(DARK)
text(fig, 128, 300, "Z + b-tagged and Z + c-tagged jet: kinematics in Summer22", 64, "white", "bold", width=1600, ls=1.15)
text(fig, 128, 520, "All POG corrections and SFs, plus BTV b- and c-tagging SFs on the leading jet", 32, "#C9D3E3", width=1600)
text(fig, 128, 640, "ParticleNet Loose (asked for), Medium and Tight, from one run", 26, "#C9D3E3", width=1600)
text(fig, 128, 860, DATE, 26, "#C9D3E3")
pdf.savefig(fig)
plt.close(fig)
n += 1

# ------------------------------------------------------------------ what is applied
fig = page()
y = heading(fig, "What goes into these plots") + 30
y = note(fig, y, "Corrections and SFs (POG recipes)",
         "Jets: JEC, JER, jet veto map, type-1 PUPPI MET. Leptons: muon and electron scale and smearing, "
         "ID, isolation and reco SFs, trigger SFs. Events: golden JSON, pileup weights, MET filters "
         "(new: they were missing before). The DY Z pT weights are now off.", h=200) + 30
cols = [("working point", 300, "left"), ("b-tag: PNet B >", 330, "right"), ("c-tag: CvL >", 300, "right"),
        ("and CvB >", 300, "right")]
y = table(fig, 128, y, cols, [["Loose", "0.047", "0.054", "0.181"], ["Medium", "0.245", "0.160", "0.306"],
                              ["Tight", "0.673", "0.492", "0.259"]], 26) + 30
note(fig, y, "Tagging is applied to the leading jet only",
     "In MC each tagged jet gets the BTV SF for its true flavour. b-tag: particleNet_comb (b and c jets), "
     "particleNet_light. c-tag: particleNet_wc (c jets), particleNet_tnp (b jets), particleNet_light. "
     "b-tag and c-tag are separate selections, so a jet can pass both.", h=200)
save(fig)

# ------------------------------------------------------------------ yields table
fig = page()
y = heading(fig, "Yields in each region",
            "Flavour shares are of all MC (DY + tt + VV). 'Tagged' is the fraction of Z + jet events that pass the tag.") + 24
cols = [("region", 270, "left"), ("data/MC  Z→ee", 280, "right"), ("data/MC  Z→μμ", 280, "right"),
        ("DY+b", 150, "right"), ("DY+c", 150, "right"), ("DY+light", 170, "right"),
        ("tagged MC", 190, "right"), ("tagged data", 190, "right")]
rows = [["inclusive", "0.95 ± 0.01", "0.97 ± 0.01", "4%", "8%", "87%", "–", "–"],
        ["b-tag Loose", "0.95 ± 0.03", "0.95 ± 0.02", "22%", "21%", "56%", "17.9%", "17.6%"],
        ["c-tag Loose", "0.93 ± 0.01", "0.95 ± 0.01", "1%", "9%", "90%", "89.5%", "88.2%"],
        ["b-tag Medium", "0.96 ± 0.05", "0.94 ± 0.04", "59%", "17%", "19%", "6.0%", "5.8%"],
        ["c-tag Medium", "0.94 ± 0.02", "0.95 ± 0.02", "3%", "20%", "77%", "28.6%", "28.2%"],
        ["b-tag Tight", "1.00 ± 0.07", "0.90 ± 0.05", "82%", "5%", "7%", "3.5%", "3.3%"],
        ["c-tag Tight", "0.92 ± 0.04", "0.93 ± 0.03", "10%", "50%", "39%", "7.3%", "7.0%"]]
y = table(fig, 128, y, cols, rows, 25) + 20
text(fig, 128, y, "Flavour shares and tagged fractions are for Z→μμ; Z→ee is within a few percent.", 22, MUTED)
note(fig, y + 50, "The tagging SFs work: data and MC tag the same fraction of jets (within 1–2%).",
     "Data/MC is about 0.95 in every region, the same as without tagging. The Loose c-tag keeps 89% of the "
     "events and they are 90% light, so it is not a charm selection. Medium (20% c) and Tight (50% c) are.",
     h=170)
save(fig)

# ------------------------------------------------------------------ SFs and overlap
fig = page()
y = heading(fig, "Tagging SFs and the overlap of the two tags",
            "Mean SF of the tagged leading jet in DY MC, per true flavour. Overlap: tagged jets that also pass "
            "the other tag at the same working point.") + 24
cols = [("region", 300, "left"), ("SF b jets", 220, "right"), ("SF c jets", 220, "right"),
        ("SF light jets", 260, "right"), ("overlap, DY MC", 300, "right"), ("overlap, data Z→μμ", 340, "right")]
rows = [["b-tag Loose", "0.95", "0.94", "1.21", "77%", "83%"],
        ["b-tag Medium", "0.94", "0.93", "1.29", "33%", "40%"],
        ["b-tag Tight", "0.92", "0.92", "1.27", "4%", "3%"],
        ["c-tag Loose", "0.78", "1.00", "1.06", "13%", "17%"],
        ["c-tag Medium", "0.77", "0.97", "1.09", "7%", "8%"],
        ["c-tag Tight", "0.79", "0.83", "1.16", "2%", "2%"]]
y = table(fig, 128, y, cols, rows, 26) + 40
note(fig, y, "Light jets are mistagged more in data than in MC (SF 1.06–1.29).",
     "At Loose most b-tagged jets also pass the c-tag. At Tight the two selections barely overlap.",
     style=OPEN, h=140)
save(fig)

# ------------------------------------------------------------------ plots per region
plots_page("incl", "No tag requirement",
           "Z + at least 1 jet. Data/MC 0.95 (Z→ee) and 0.97 (Z→μμ).",
           ["jet_pt", "z_pt", "jet_eta", "jet_PNetB"])
plots_page("btag_L", "b-tag Loose",
           "Leading jet PNet B > 0.047. 21–22% DY+b, 21–23% DY+c, 54–56% light. Data/MC 0.95.",
           ["jet_pt", "z_pt", "jet_eta", "jet_PNetB"])
plots_page("ctag_L", "c-tag Loose",
           "CvL > 0.054 and CvB > 0.181. 89% of the events pass; 9% DY+c, 90% light. Data/MC 0.93–0.95.",
           ["jet_pt", "z_pt", "jet_eta", "jet_PNetCvL"])
plots_page("btag_M", "b-tag Medium",
           "PNet B > 0.245. 55–59% DY+b, about 4% tt. Data/MC 0.94–0.96.",
           ["jet_pt", "z_pt", "jet_eta", "jet_PNetB"])
plots_page("ctag_M", "c-tag Medium",
           "CvL > 0.160 and CvB > 0.306. 20% DY+c, 77% light. Data/MC 0.94–0.95.",
           ["jet_pt", "z_pt", "jet_eta", "jet_PNetCvL"])
plots_page("btag_T", "b-tag Tight",
           "PNet B > 0.673. 82% DY+b, 6–7% tt. Data/MC 1.00 ± 0.07 (Z→ee), 0.90 ± 0.05 (Z→μμ).",
           ["jet_pt", "z_pt", "jet_eta", "jet_PNetB"])
plots_page("ctag_T", "c-tag Tight",
           "CvL > 0.492 and CvB > 0.259. 50% DY+c, 39% light, 10% DY+b. Data/MC 0.92–0.93.",
           ["jet_pt", "z_pt", "jet_eta", "jet_PNetCvL"])

# ------------------------------------------------------------------ summary
fig = page()
y = heading(fig, "Summary") + 30
y = note(fig, y, "All kinematic plots now have every POG correction, plus b- and c-tagging SFs.",
         "62 plots per region, in hists_zbzc_run3_tag/Summer22/plots_<region>/. MET filters added; "
         "DY Z pT weights off.", h=140) + 30
y = note(fig, y, "Data and MC tag the same fraction of jets, within 1–2%, at every working point.",
         "Data/MC is about 0.95 in all regions, as without tagging. Errors here are statistical only.", h=140) + 30
y = note(fig, y, "Loose c-tag is almost no selection (89% of events, 90% light).",
         "For a charm-enriched sample, Medium (20% c) or Tight (50% c) is better. b-tag Medium gives 55–59% b, Tight 82%.",
         style=OPEN, h=140) + 30
note(fig, y, "Next",
     "Add the SF up/down uncertainties as a band. Same plots for 2022 E–G and 2023.", style=OPEN, h=120)
save(fig)

pdf.close()
print("wrote", OUT, f"({n} pages)")
