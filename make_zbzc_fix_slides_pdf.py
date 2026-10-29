"""Short group-meeting deck: what the 2026-10-28 fixes changed, before vs after.

Fixes: electron smearing per electron (52b72bf), electrons' jets out of type-1 MET (1c3ce15),
DY Z pT weights from Z->mumu (8311570). Before = second small run (fb54afd), after = third
small run (b48a524), same 20 files per sample.
Inputs: hists_zbzc_compare/ (compare_zbzc_before_after.py), hists_zbzc_diag/ (diag_zbzc_met.py),
hists_zbzc_run3_smearfix/ (compare_zee_smearfix.py), slide-14 plots before (git fb54afd, path
given as argument) and after (hists_zbzc_run3/Summer23BPix/plots/lep0_pt.png).

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


# ------------------------------------------------------------------ 1 cover
fig = page(DARK)
text(fig, 128, 300, "Z + jets Run 3: data/MC before and after the fixes", 64, "white", "bold", width=1600, ls=1.15)
text(fig, 128, 520, "What changed, how we found it, and what is still open", 34, "#C9D3E3")
text(fig, 128, 640, "Small run: 20 files per sample, four campaigns (2022 C–D, 2022 E–G, 2023 C, 2023 D)",
     26, "#C9D3E3", width=1600)
text(fig, 128, 860, DATE, 26, "#C9D3E3")
pdf.savefig(fig)
plt.close(fig)
n += 1

# ------------------------------------------------------------------ 2 what we changed
fig = page()
y = heading(fig, "Three fixes", "Same files and same selection before and after. Only these changed.") + 40
cols = [("Fix", 470, "left"), ("What was wrong", 720, "left"), ("How we found it", 474, "left")]
rows = [["1. Electron smearing", "Both electrons got the same random", "Z→ee peak wider in MC"],
        ["", "number, so MC Z→ee was too wide", "than in data"],
        ["2. MET", "The electrons' own jets were counted", "High-pT Z→ee data lost"],
        ["", "in the MET (fake MET in Z→ee)", "at the MET < 50 cut"],
        ["3. Z pT weights", "The DY generator gets the Z pT", "Wiggle in Z pT before"],
        ["", "shape wrong", "any cut, both channels"]]
y = table(fig, 128, y, cols, rows, 26) + 40
note(fig, y, "Fixes 1 and 2 are bugs. Fix 3 is a correction we derive.",
     "Fix 1 and 2 change shared framework code, in our fork only. Fix 2 follows the JME type-1 MET recipe, "
     "which the framework applied only for 2024–25 samples. Fix 3 weights DY MC to Z→μμ data and is checked on Z→ee.",
     h=170)
save(fig)

# ------------------------------------------------------------------ 3 fix 1: Z mass width
fig = page()
y = heading(fig, "Fix 1: Z→ee mass width (2023 D shown)",
            "Red: MC before. Blue: MC after. Muons are not touched by this fix.") + 20
y = image(fig, "hists_zbzc_run3_smearfix/Summer23BPix/z_mass_smearfix.png", y, hmax=470) + 14
cols = [("Width data/MC (Z→ee)", 560, "left"), ("2022 C–D", 270, "right"), ("2022 E–G", 270, "right"),
        ("2023 C", 270, "right"), ("2023 D", 270, "right")]
y = table(fig, 128, y, cols, [["before", "0.95", "0.94", "0.94", "0.90"],
                              ["after", "0.99", "1.00", "1.00", "0.97"]], 24) + 14
note(fig, y, "Width fixed. The peak position did not move (this fix only changes the width).",
     "Data peak is 0.03–0.08 GeV (< 0.1%) above MC for electrons, same as before. That is inside the EGM "
     "energy-scale uncertainty (0.05–0.36%), so it is a systematic, not a bug.", style=OPEN, h=140)
save(fig)

# ------------------------------------------------------------------ 4 fix 2: why
fig = page()
y = heading(fig, "Fix 2: why high-pT electrons were lost (2023 D)",
            "Fraction of Z events passing MET < 50 GeV, before the jet cut. Filled: now. Open: electrons' jets "
            "left out of the MET.") + 16
y = image(fig, "hists_zbzc_diag/Summer23BPix/plots/diag_emef_met_eff.png", y, hmax=620) + 16
note(fig, y, "The electron's own jet made fake MET, more in data than in MC.",
     "Z→ee data/MC of the MET cut: 0.81 at Z pT 200–300 GeV, 0.64 above 300. Without those jets: 0.97 and 1.03, "
     "the same as Z→μμ. Muons do not change, as expected.", h=150)
save(fig)

# ------------------------------------------------------------------ 5 slide 14 before / after
fig = page()
y = heading(fig, "Leading-lepton pT in 2023 D: before and after",
            "Same plot as slide 14 of the main deck. Left: before. Right: after.") + 30
image(fig, f"{args.before_dir}/hists_zbzc_run3/Summer23BPix/plots/lep0_pt.png", y, x=128, w=820)
yb = image(fig, "hists_zbzc_run3/Summer23BPix/plots/lep0_pt.png", y, x=972, w=820)
text(fig, 128, y - 34, "Before", 28, MUTED, "bold")
text(fig, 972, y - 34, "After", 28, "#C0392B", "bold")
note(fig, yb + 30, "The Z→ee drop at high pT is gone.",
     "Z→ee data/MC at leading pT 200–300 GeV: 0.61 → 0.91. Above 300 GeV: 0.53 → 1.03. Z→μμ barely changes.",
     h=130)
save(fig)

# ------------------------------------------------------------------ 6-9 ratio before/after per campaign
VERDICT = {
    "Summer23BPix": ("2023 D: clear improvement in Z→ee", GOOD,
                     "Z→ee at Z pT 200–300 GeV: 0.72 → 0.94, above 300: 0.53 → 0.95. Z→μμ gets a little flatter. "
                     "Not fixed: the first bin (Z pT < 20 GeV) is still 1.08–1.11."),
    "Summer23": ("2023 C: better at high pT, within errors elsewhere", GOOD,
                 "Z pT above 200 GeV: 0.75–0.88 → 0.98–1.07 in both channels (each bin 1–2σ). "
                 "Not fixed: first bin still 1.07–1.10."),
    "Summer22": ("2022 C–D: level up 2%, shape not better", OPEN,
                 "Totals 0.948/0.967 → 0.973/0.987. Shape: low at 20–40 GeV (0.92–0.95), high at 100–140 GeV "
                 "(1.05), before and after. Likely the 2022 jet excess (page 11)."),
    "Summer22EE": ("2022 E–G: level up 2%, shape slightly worse", OPEN,
                   "Totals 0.969/0.985 → 0.995/1.006. Z→μμ at 60–300 GeV was 1.03–1.06, now 1.07–1.08. "
                   "Low at 20–40 GeV as before. Same 2022 jet issue (page 11)."),
}
for c, era in [("Summer23BPix", "2023 D"), ("Summer23", "2023 C"), ("Summer22", "2022 C–D"),
               ("Summer22EE", "2022 E–G")]:
    title, style, body = VERDICT[c]
    fig = page()
    y = heading(fig, f"Data/MC before and after: {era}",
                "Full selection. Top: Z pT. Bottom: leading-lepton pT. Grey: before. Red: after. Wide bins, "
                "errors = data + MC statistics.") + 10
    y = image(fig, f"hists_zbzc_compare/ratio_{c}.png", y, hmax=620) + 12
    note(fig, y, title, body, style=style, h=135)
    save(fig)

# ------------------------------------------------------------------ 10 fix 3 check
fig = page()
y = heading(fig, "Fix 3: Z pT weights, checked on Z→ee",
            "All Z events, before the MET and jet cuts. Weights come from Z→μμ (bottom row, flat by "
            "construction). Z→ee (top row) is the independent check.") + 16
y = image(fig, "hists_zbzc_compare/zpt_weights_closure.png", y, hmax=600) + 16
note(fig, y, "The weights remove the generator wiggle in Z→ee too.",
     "Bin-to-bin spread of Z→ee data/MC: 7–8% → 3–6%. Totals unchanged. After the jet cut the effect is "
     "smaller, and the first Z pT bin is still high (pages 6–7).", h=150)
save(fig)

# ------------------------------------------------------------------ 11 2022
fig = page()
y = heading(fig, "2022: extra MET and jets in MC (open)",
            "MET of all Z events, 2022 C–D. Filled: now. Open: MC without jet energy smearing (JER). "
            "Data is the same in both.") + 16
y = image(fig, "hists_zbzc_diag/Summer22/plots/diag_nojer_met_pt.png", y, hmax=600) + 16
note(fig, y, "Jet smearing makes most of the extra MET, but not the extra jets.",
     "Data/MC above 50 GeV: about 0.5 → 0.8 without JER. MC events with ≥1 jet: 5% too many → 3%. "
     "Turning JER off is only a test. Next: check the 2022 JER inputs (2023 uses newer ones and is fine).",
     style=OPEN, h=150)
save(fig)

# ------------------------------------------------------------------ 12 summary
fig = page()
y = heading(fig, "Summary") + 30
cols = [("Data/MC, Z→ee / Z→μμ", 560, "left"), ("before", 360, "right"), ("after", 360, "right"),
        ("shape", 384, "left")]
rows = [["2022 C–D", "0.948 / 0.967", "0.973 / 0.987", "not better"],
        ["2022 E–G", "0.969 / 0.985", "0.995 / 1.006", "slightly worse"],
        ["2023 C", "0.965 / 0.985", "0.985 / 0.999", "better at high pT"],
        ["2023 D", "0.941 / 0.988", "0.978 / 1.012", "much better (Z→ee)"]]
y = table(fig, 128, y, cols, rows, 28,
          colors={"not better": "#C0561B", "slightly worse": "#C0561B", "better at high pT": "#2E7D32",
                  "much better (Z→ee)": "#2E7D32"}) + 30
y = note(fig, y, "Done: two real bugs fixed, and the big 2023 D electron slope is gone.",
         "Z→ee width matches data. High-pT electrons are no longer lost to fake MET. All totals are now 0.97–1.01.",
         h=120) + 20
note(fig, y, "Open",
     "2022 jets and MET (JER inputs). First Z pT bin 7–11% high in 2023. 2023 D electrons 3% below muons "
     "(ask EGM). Z→ee peak offset < 0.1% (EGM scale systematic). 20 files are too few for few-% shapes: "
     "full condor run next.", style=OPEN, h=170)
save(fig)

pdf.close()
print("wrote", OUT, f"({n} pages)")
