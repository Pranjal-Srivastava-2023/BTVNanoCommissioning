"""Group-meeting deck, all four campaigns, before vs after:
  - Z mass with the old and the fixed electron smearing (52b72bf), from
    hists_zbzc_run3_smearfix/<campaign>/z_mass_smearfix.png (compare_zee_smearfix.py)
  - leading-lepton pT stack plot before (second small run, fb54afd) and after (third small
    run, b48a524: electrons' jets out of type-1 MET + DY Z pT weights), same 20 files.

Usage:  python make_zbzc_fix_slides_pdf.py <before_dir> [--date "29 October 2026"]
Output: hists_zbzc_compare/slides_zbzc_fixes_before_after.pdf
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
parser.add_argument("before_dir", help="git archive fb54afd hists_zbzc_run3 extracted here")
parser.add_argument("--date", default=None)
args = parser.parse_args()
DATE = args.date or datetime.date.today().strftime("%-d %B %Y")
OUT = "hists_zbzc_compare/slides_zbzc_fixes_before_after.pdf"

# ------------------------------------------------------------------ layout (as make_zbzc_run3_slides_pdf.py)
W, H = 1920, 1080
DARK, LIGHT, PANEL, ACCENT, BODY, MUTED = "#14213D", "#FBFBF8", "#EEF1F5", "#1F5FA8", "#4A5568", "#6A7179"
GOOD = ("#E8F3EA", "#2E7D32", "#1B5E20")
OPEN = ("#FDF1E4", "#E07B24", DARK)
PX = 72 / 100
plt.rcParams["font.family"] = "DejaVu Sans"
FOOT = "Run 3, 13.6 TeV · Z→ℓℓ + jets · 20 files per MC sample and per data channel · AK4 jets"


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
text(fig, 128, 300, "Z + jets Run 3: before and after, all campaigns", 64, "white", "bold", width=1600, ls=1.15)
text(fig, 128, 520, "Z mass (electron smearing fix) and leading-lepton pT (MET fix + Z pT weights)", 32, "#C9D3E3",
     width=1600)
text(fig, 128, 640, "Small run: 20 files per sample · 2022 C–D, 2022 E–G, 2023 C, 2023 D", 26, "#C9D3E3", width=1600)
text(fig, 128, 860, DATE, 26, "#C9D3E3")
pdf.savefig(fig)
plt.close(fig)
n += 1

CAMPS = [("Summer22", "2022 C–D"), ("Summer22EE", "2022 E–G"), ("Summer23", "2023 C"), ("Summer23BPix", "2023 D")]

# ------------------------------------------------------------------ Z mass, per campaign
# zee_smearfix_summary.txt: Z->ee width data/MC old -> new; data - MC peak (GeV) old -> new, Z->ee and Z->mumu
MASS = {
    "Summer22": ("0.95", "0.99", "+0.05", "+0.05", "+0.04"),
    "Summer22EE": ("0.94", "1.00", "+0.06", "+0.07", "−0.03"),
    "Summer23": ("0.94", "1.00", "+0.02", "+0.03", "+0.03"),
    "Summer23BPix": ("0.90", "0.97", "+0.08", "+0.08", "+0.03"),
}
for c, era in CAMPS:
    w0, w1, d0, d1, dm = MASS[c]
    fig = page()
    y = heading(fig, f"Z mass, {era}: electron smearing before and after",
                "Red dashed: MC with the old smearing. Blue: MC with the fix. Muons are not touched by this fix.") + 14
    y = image(fig, f"hists_zbzc_run3_smearfix/{c}/z_mass_smearfix.png", y, hmax=500) + 10
    cols = [("", 520, "left"), ("before", 380, "right"), ("after", 380, "right"), ("", 384, "left")]
    y = table(fig, 128, y, cols, [["Z→ee width, data/MC", w0, w1, ""],
                                  ["Z→ee peak, data − MC (GeV)", d0, d1, ""],
                                  ["Z→μμ peak, data − MC (GeV)", dm, dm, ""]], 22) + 10
    note(fig, y, f"Width: {w0} → {w1}. Peak position: unchanged.",
         "The fix only changes the width. The electron peak offset (< 0.1%) is inside the EGM energy-scale "
         "uncertainty (0.05–0.36%).", style=GOOD if float(w1) >= 0.97 else OPEN, h=110)
    save(fig)

# ------------------------------------------------------------------ leading-lepton pT stack, per campaign
LEP = {
    "Summer22": ("Level about 2% higher; shape not better", OPEN,
                 "Z→ee 60–200 GeV: 0.96–0.98 → 1.01–1.05. Z→μμ 200–300 GeV: 0.83 → 0.97. "
                 "Below 60 GeV still 0.94–0.96 in both channels."),
    "Summer22EE": ("Level about 2% higher; shape slightly worse", OPEN,
                   "Above 60 GeV MC is now 5–10% low: Z→μμ 1.00–1.07 → 1.05–1.10, Z→ee 0.99–1.02 → 1.05–1.07. "
                   "Below 60 GeV still 0.94–0.97."),
    "Summer23": ("Better at high pT", GOOD,
                 "Z→ee 140–300 GeV: 0.82–0.90 → 0.97–1.01. Z→μμ 140–300 GeV: 0.81–0.86 → 0.94–0.96. "
                 "Each bin moves by 1–2σ."),
    "Summer23BPix": ("The Z→ee drop at high pT is gone", GOOD,
                     "Z→ee 200–300 GeV: 0.61 → 0.91, above 300: 0.53 → 1.03. Z→μμ barely changes. "
                     "Electrons are still about 3% below muons overall."),
}
for c, era in CAMPS:
    title, style, body = LEP[c]
    fig = page()
    y = heading(fig, f"Leading-lepton pT, {era}: before and after",
                "Left: before. Right: after (electrons' jets out of the MET + DY Z pT weights). Same files.") + 44
    image(fig, f"{args.before_dir}/hists_zbzc_run3/{c}/plots/lep0_pt.png", y, x=30, w=920)
    yb = image(fig, f"hists_zbzc_run3/{c}/plots/lep0_pt.png", y, x=970, w=920)
    text(fig, 40, y - 36, "Before", 28, MUTED, "bold")
    text(fig, 980, y - 36, "After", 28, "#C0392B", "bold")
    note(fig, yb + 24, title, body, style=style, h=120)
    save(fig)

pdf.close()
print("wrote", OUT, f"({n} pages)")
