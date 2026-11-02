"""Short deck for the advisor's question: does the data/MC pT slope go away in Z + exactly 1 jet?
Summer22 only, two small runs with the same 20 files and 10 GeV pT bins:
  hists_zbzc_run3_ge1j (Zb_Zc_ratio, N_jet >= 1) and hists_zbzc_run3_1j (Zb_Zc_ratio_1jet, N_jet = 1).
Stack plots from plot_zbzc_run3.py, slope overlays from compare_zbzc_njet_slope.py, eta-phi maps from
plot_zbzc_etaphi_nj.py. Numbers below are copied from compare_ge1j/slope_ge1j_vs_1j.txt.

Usage:  python make_zbzc_njet_slides_pdf.py [--date "2 November 2026"]
Output: hists_zbzc_run3_1j/Summer22/slides_zbzc_njet_Summer22.pdf
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
GE, EQ = "hists_zbzc_run3_ge1j/Summer22", "hists_zbzc_run3_1j/Summer22"
OUT = f"{EQ}/slides_zbzc_njet_Summer22.pdf"

# ------------------------------------------------------------------ layout (as make_zbzc_run3_slides_pdf.py)
W, H = 1920, 1080
DARK, LIGHT, PANEL, ACCENT, BODY, MUTED = "#14213D", "#FBFBF8", "#EEF1F5", "#1F5FA8", "#4A5568", "#6A7179"
GOOD = ("#E8F3EA", "#2E7D32", "#1B5E20")
OPEN = ("#FDF1E4", "#E07B24", DARK)
PX = 72 / 100
plt.rcParams["font.family"] = "DejaVu Sans"
FOOT = "Summer22 (2022 C–D), 13.6 TeV · Z→ℓℓ + jets · 20 files per MC sample and per data channel · AK4 jets"


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


# ------------------------------------------------------------------ cover
fig = page(DARK)
text(fig, 128, 300, "Does the data/MC pT slope go away in Z + 1 jet?", 64, "white", "bold", width=1600, ls=1.15)
text(fig, 128, 520, "Summer22: Z + at least 1 jet compared with Z + exactly 1 jet", 32, "#C9D3E3", width=1600)
text(fig, 128, 640, "Same 20 files per sample, 10 GeV pT bins, DY Z pT weights still on", 26, "#C9D3E3", width=1600)
text(fig, 128, 860, DATE, 26, "#C9D3E3")
pdf.savefig(fig)
plt.close(fig)
n += 1

# ------------------------------------------------------------------ summary table
fig = page()
y = heading(fig, "Slope of data/MC, in % per 100 GeV",
            "Straight-line fit to data/MC in 10 GeV bins. The exactly-1-jet events are about 80% of the "
            "at-least-1-jet events, so the two columns are not independent.") + 30
cols = [("", 560, "left"), ("N jet ≥ 1", 360, "right"), ("N jet = 1", 360, "right"), ("", 384, "left")]
rows = [["Z→μμ, Z pT (0–400)", "+4.4 ± 1.3", "+0.7 ± 1.7", ""],
        ["Z→μμ, leading lepton (35–300)", "+6.2 ± 2.2", "+2.5 ± 3.0", ""],
        ["Z→μμ, second lepton (25–200)", "+20.5 ± 5.5", "+1.3 ± 7.6", ""],
        ["Z→μμ, leading jet (30–300)", "+2.0 ± 1.8", "−2.6 ± 2.1", ""],
        ["Z→ee, Z pT (0–400)", "+4.8 ± 2.0", "+3.0 ± 2.7", ""],
        ["Z→ee, leading lepton (35–300)", "+9.7 ± 3.5", "+9.1 ± 4.8", ""],
        ["Z→ee, second lepton (25–200)", "−0.9 ± 8.6", "−6.3 ± 11.9", ""],
        ["Z→ee, leading jet (30–300)", "+2.3 ± 2.6", "−0.4 ± 3.2", ""]]
y = table(fig, 128, y, cols, rows, 26) + 40
note(fig, y, "Muons: the slope is gone in Z + 1 jet. Electrons: no clear change.",
     "For muons the rise seems to come from events with 2 or more jets. For electrons the leading-lepton "
     "slope stays at about +9%, but the errors are large.", h=140)
save(fig)

# ------------------------------------------------------------------ stack plots, at least 1 jet | exactly 1 jet
STACK = [
    ("z_pt", "Z pT", ("Z→μμ: +4.4 ± 1.3 → +0.7 ± 1.7.  Z→ee: +4.8 ± 2.0 → +3.0 ± 2.7.",
                      "The Z→μμ rise above 100 GeV (1.04–1.06) drops to 0.99–1.03 with exactly 1 jet. "
                      "Below 30 GeV data/MC is 0.95 in both selections.")),
    ("lep0_pt", "Leading-lepton pT", ("Z→μμ: +6.2 ± 2.2 → +2.5 ± 3.0.  Z→ee: +9.7 ± 3.5 → +9.1 ± 4.8.",
                                      "Z→μμ 100–150 GeV: 1.06 → 1.01. Z→ee does not change much.")),
    ("lep1_pt", "Second-lepton pT", ("Z→μμ: +20.5 ± 5.5 → +1.3 ± 7.6.  Z→ee: −0.9 ± 8.6 → −6.3 ± 11.9.",
                                     "Z→μμ 50–150 GeV: 1.08–1.17 → 1.02–1.03. Electrons have too few events "
                                     "above 100 GeV to say anything.")),
    ("jet_pt", "Leading-jet pT", ("Z→μμ: +2.0 ± 1.8 → −2.6 ± 2.1.  Z→ee: +2.3 ± 2.6 → −0.4 ± 3.2.",
                                  "No real slope in either selection. With exactly 1 jet, MC is a bit high "
                                  "above 150 GeV.")),
]
for var, name, (title, body) in STACK:
    fig = page()
    y = heading(fig, f"{name}: ≥ 1 jet (left), exactly 1 jet (right)") + 50
    image(fig, f"{GE}/plots/{var}.png", y, x=30, w=920)
    yb = image(fig, f"{EQ}/plots/{var}.png", y, x=970, w=920)
    text(fig, 40, y - 36, "N jet ≥ 1", 28, MUTED, "bold")
    text(fig, 980, y - 36, "N jet = 1", 28, "#C0392B", "bold")
    note(fig, yb + 24, f"Slope: {title}", body, style=GOOD if var != "lep0_pt" else OPEN, h=130)
    save(fig)

# ------------------------------------------------------------------ slope overlays
fig = page()
y = heading(fig, "Data/MC with the fitted lines",
            "Black: at least 1 jet. Red: exactly 1 jet.") + 10
y = image(fig, f"{EQ}/compare_ge1j/z_pt_ratio_ge1j_vs_1j.png", y, x=340, w=1240) + 5
image(fig, f"{EQ}/compare_ge1j/lep0_pt_ratio_ge1j_vs_1j.png", y, x=340, w=1240)
save(fig)

# ------------------------------------------------------------------ eta-phi
fig = page()
y = heading(fig, "Lepton η–φ, data/MC, Z + exactly 1 jet",
            "MC normalised to data in each map. Each event enters twice (both leptons).") + 10
y = image(fig, f"{GE}/plots/lep_eta_phi_10x10_ratio_eq1.png", y, hmax=520) + 10
cols = [("cell", 560, "left"), ("N jet = 1", 300, "right"), ("N jet = 2", 300, "right"), ("N jet ≥ 1", 300, "right")]
y = table(fig, 128, y, cols, [["Z→ee, η 0–0.5, φ 1.3–1.9", "0.82 ± 0.07", "0.61 ± 0.10", "0.80 ± 0.06"],
                              ["Z→μμ, η 0.5–1.0, φ −3.1 to −2.5", "0.90 ± 0.06", "0.65 ± 0.08", "0.85 ± 0.05"]],
          22) + 14
note(fig, y, "Two cells are low with 1 jet and with 2 jets.",
     "These are separate events, so this is not one fluctuation. The rest of each map is flat "
     "(χ²/ndf 112 and 119 for 99 with exactly 1 jet).", style=OPEN, h=120)
save(fig)

# ------------------------------------------------------------------ summary
fig = page()
y = heading(fig, "Summary") + 30
y = note(fig, y, "Muons: the pT slope goes away in Z + exactly 1 jet.",
         "Z pT slope +4.4 ± 1.3 → +0.7 ± 1.7 %/100 GeV. The rise seems to come from events with 2 or more jets.",
         h=140) + 30
y = note(fig, y, "Electrons: no clear change.",
         "Leading-lepton slope +9.7 ± 3.5 → +9.1 ± 4.8 %/100 GeV. We need more files to say more.",
         style=OPEN, h=140) + 30
y = note(fig, y, "Two low η–φ cells, one per channel, low with 1 jet and with 2 jets.",
         "Z→ee η 0–0.5, φ 1.3–1.9: 0.82 and 0.61. Z→μμ η 0.5–1.0, φ −3.1 to −2.5: 0.90 and 0.65. "
         "MC is also about 20% high for N jet ≥ 3.", style=OPEN, h=140) + 30
note(fig, y, "Next",
     "Same check in 2022 E–G and 2023. Rerun without the DY Z pT weights (not decided yet).",
     style=OPEN, h=120)
save(fig)

pdf.close()
print("wrote", OUT, f"({n} pages)")
