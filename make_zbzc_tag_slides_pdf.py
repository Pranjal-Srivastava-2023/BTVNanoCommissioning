"""Deck for the advisor's request: ALL Summer22 kinematic plots with all POG corrections and SFs,
Z + >= 1 jet, inclusive and with a b-tagged or c-tagged leading AK4 jet (PNet Loose, Medium, Tight).
Intro pages (corrections, cuts, yields, SFs), then one section per region with every plot
(hadron-flavour stacks) full size, one per page.
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
    ax.imshow(img, interpolation="none")  # embed the PNG pixels as they are (antialiasing bloats the PDF)
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


# (region, title, cut, {channel: (data/MC, DY+b, DY+c, DY+light, tt, tagged MC, tagged data)}) from yields*.txt
REGIONS = [
    ("incl", "No tag requirement", "Z + at least 1 jet (pT > 30 GeV, |η| < 2.5)",
     {"Z→ee": ("0.949 ± 0.012", "3.8%", "8.0%", "87.4%", "0.4%", "–", "–"),
      "Z→μμ": ("0.966 ± 0.009", "4.2%", "8.1%", "87.0%", "0.4%", "–", "–")}),
    ("btag_L", "b-tag Loose", "Leading jet PNet B > 0.047",
     {"Z→ee": ("0.947 ± 0.031", "20.7%", "23.0%", "54.1%", "1.7%", "16.9%", "16.9%"),
      "Z→μμ": ("0.951 ± 0.021", "21.5%", "20.9%", "55.6%", "1.6%", "17.9%", "17.6%")}),
    ("ctag_L", "c-tag Loose", "Leading jet PNet CvL > 0.054 and CvB > 0.181",
     {"Z→ee": ("0.932 ± 0.013", "1.1%", "8.7%", "89.7%", "0.2%", "89.4%", "87.7%"),
      "Z→μμ": ("0.951 ± 0.009", "1.3%", "8.7%", "89.6%", "0.2%", "89.5%", "88.2%")}),
    ("btag_M", "b-tag Medium", "Leading jet PNet B > 0.245",
     {"Z→ee": ("0.960 ± 0.053", "55.1%", "22.1%", "17.8%", "4.5%", "5.9%", "5.9%"),
      "Z→μμ": ("0.939 ± 0.036", "59.0%", "16.9%", "19.4%", "4.3%", "6.0%", "5.8%")}),
    ("ctag_M", "c-tag Medium", "Leading jet PNet CvL > 0.160 and CvB > 0.306",
     {"Z→ee": ("0.938 ± 0.023", "2.9%", "20.2%", "76.2%", "0.3%", "27.9%", "27.6%"),
      "Z→μμ": ("0.951 ± 0.017", "3.1%", "19.5%", "76.7%", "0.3%", "28.6%", "28.2%")}),
    ("btag_T", "b-tag Tight", "Leading jet PNet B > 0.673",
     {"Z→ee": ("1.004 ± 0.074", "82.9%", "5.4%", "4.5%", "6.8%", "3.2%", "3.4%"),
      "Z→μμ": ("0.902 ± 0.045", "82.0%", "4.8%", "6.7%", "6.1%", "3.5%", "3.3%")}),
    ("ctag_T", "c-tag Tight", "Leading jet PNet CvL > 0.492 and CvB > 0.259",
     {"Z→ee": ("0.916 ± 0.043", "8.2%", "49.4%", "41.1%", "0.7%", "7.6%", "7.3%"),
      "Z→μμ": ("0.928 ± 0.033", "9.6%", "50.2%", "38.9%", "0.7%", "7.3%", "7.0%")}),
]
TWOJ = "Events with at least 2 jets."
# (file, title, caption), in the order shown in every section
VARS = [
    ("z_mass", "Dilepton mass", "m(ℓℓ), 71–111 GeV window, linear scale."),
    ("z_pt", "Z pT", "pT of the lepton pair."),
    ("z_eta", "Z η", "η of the lepton pair."),
    ("lep0_pt", "Leading-lepton pT", "Leading lepton pT > 35 GeV (trigger plateau)."),
    ("lep0_eta", "Leading-lepton η", ""),
    ("lep0_phi", "Leading-lepton φ", ""),
    ("lep1_pt", "Second-lepton pT", "Second lepton pT > 25 GeV."),
    ("lep1_eta", "Second-lepton η", ""),
    ("lep1_phi", "Second-lepton φ", ""),
    ("dR_ll", "ΔR between the leptons", ""),
    ("dphi_ll", "Δφ between the leptons", ""),
    ("n_jet", "Number of jets", "AK4 jets with pT > 30 GeV, |η| < 2.5, away from the leptons. "
     "Untagged plot: Z events before the jet cut, so the 0-jet bin is filled."),
    ("jet_pt", "Leading-jet pT", "The tag (if any) is on this jet."),
    ("jet_eta", "Leading-jet η", ""),
    ("jet_phi", "Leading-jet φ", ""),
    ("jet1_pt", "Second-jet pT", TWOJ),
    ("jet1_eta", "Second-jet η", TWOJ),
    ("dR_jj", "ΔR between the two leading jets", TWOJ),
    ("dphi_jj", "Δφ between the two leading jets", TWOJ),
    ("m_jj", "Dijet mass", TWOJ),
    ("dphi_zj", "Δφ(Z, leading jet)", ""),
    ("dR_zj", "ΔR(Z, leading jet)", ""),
    ("dR_lj_min", "Smallest ΔR(lepton, leading jet)", ""),
    ("pt_balance", "pT balance: leading-jet pT / Z pT", ""),
    ("met_pt", "PUPPI MET", "Type-1 corrected; the selection cuts at 50 GeV."),
    ("npv", "Number of good primary vertices", "After pileup weights."),
    ("lhe_vpt", "Generator Z pT (LHE)", "MC only, no data."),
    ("jet_PNetB", "Leading-jet PNet B score", ""),
    ("jet_PNetCvL", "Leading-jet PNet CvL score", ""),
    ("jet_PNetCvB", "Leading-jet PNet CvB score", ""),
    ("jet_CvL_CvB", "PNet CvL vs CvB of the leading jet", "Each panel normalised to 1. Z→ee and Z→μμ added."),
    ("lep_eta_phi_ratio", "Lepton η–φ, data / MC", "Both Z leptons. MC normalised to data in each map. "
     "Colour scale stops at ±15%; in the tagged regions there are few events per cell, so read the numbers."),
]
N_INTRO = 5  # cover, contents, corrections, yields, SFs
SEC_LEN = 1 + len(VARS)
START = {r[0]: N_INTRO + 1 + i * SEC_LEN for i, r in enumerate(REGIONS)}


# ------------------------------------------------------------------ cover
fig = page(DARK)
text(fig, 128, 300, "Z + b-tagged and Z + c-tagged jet: kinematics in Summer22", 64, "white", "bold", width=1600, ls=1.15)
text(fig, 128, 520, "All POG corrections and SFs, plus BTV b- and c-tagging SFs on the leading jet", 32, "#C9D3E3", width=1600)
text(fig, 128, 640, "ParticleNet Loose (asked for), Medium and Tight, from one run", 26, "#C9D3E3", width=1600)
text(fig, 128, 860, DATE, 26, "#C9D3E3")
pdf.savefig(fig)
plt.close(fig)
n += 1

# ------------------------------------------------------------------ contents
fig = page()
y = heading(fig, "Contents", "Selection: Z→ee or Z→μμ + at least 1 jet. Every region has the same "
            f"{len(VARS)} plots in the same order.") + 30
rows = [["Corrections, tag cuts, yields, SFs", "3–5"]]
for region, title, cut, _ in REGIONS:
    rows.append([f"{title}  ({cut})", f"{START[region]}–{START[region] + SEC_LEN - 1}"])
rows.append(["Summary", str(N_INTRO + len(REGIONS) * SEC_LEN + 1)])
y = table(fig, 128, y, [("section", 1400, "left"), ("pages", 264, "right")], rows, 26)
save(fig)

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

# ------------------------------------------------------------------ all plots, one section per region
def plot_page(region, title, var, vtitle, caption):
    fig = page()
    text(fig, 128, 40, title, 26, ACCENT, "bold")
    y = text(fig, 128, 78, vtitle, 48, DARK, "bold", ls=1.15)
    if caption:
        y = text(fig, 128, y + 4, caption, 24, BODY, width=1664)
    folder = "plots" if region == "incl" else f"plots_{region}"
    path = f"{D}/{folder}/{var}.png"
    top = max(y + 14, 190)
    image(fig, path, top, x=128, w=1664, hmax=1010 - top)
    save(fig)


def section(region, title, cut, nums):
    fig = page(DARK)
    text(fig, 128, 200, title, 72, "white", "bold")
    text(fig, 128, 330, cut, 32, "#C9D3E3", width=1600)
    hdr = ["", "data/MC", "DY+b", "DY+c", "DY+light", "tt", "tagged MC", "tagged data"]
    xs = [128, 420, 700, 860, 1020, 1210, 1350, 1580]
    for x, h in zip(xs, hdr):
        text(fig, x, 470, h, 26, "#C9D3E3", "bold")
    for i, (ch, vals) in enumerate(nums.items()):
        for x, v in zip(xs, (ch,) + vals):
            text(fig, x, 530 + i * 60, v, 28, "white")
    text(fig, 128, 720, "Flavour shares are of all MC. 'Tagged' = fraction of Z + jet events passing the tag. "
         "Errors are statistical only.", 22, "#C9D3E3", width=1600)
    text(fig, 128, 800, f"{len(VARS)} plots follow: Z and leptons, jets, Z–jet, MET and vertices, tagger scores, "
         "2D maps. Left Z→ee, right Z→μμ.", 22, "#C9D3E3", width=1600)
    save(fig)
    for var, vtitle, caption in VARS:
        plot_page(region, title, var, vtitle, caption)


for region, title, cut, nums in REGIONS:
    section(region, title, cut, nums)

# ------------------------------------------------------------------ summary
fig = page()
y = heading(fig, "Summary") + 30
y = note(fig, y, "All kinematic plots now have every POG correction, plus b- and c-tagging SFs.",
         f"{len(VARS)} plots per region in this deck (hadron-flavour stacks); parton-flavour versions in "
         "hists_zbzc_run3_tag/Summer22/plots_<region>/. MET filters added; DY Z pT weights off.", h=140) + 30
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
