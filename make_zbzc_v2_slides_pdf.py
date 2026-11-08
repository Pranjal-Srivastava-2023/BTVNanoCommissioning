"""Deck for the advisor's questions of 8 November 2026 (Summer22, run ZBZC_RUN=zbzc_run3_v2):
muon channel vs electrons (trigger SF, pT/eta cuts, scale/smearing, ...), other taggers with L/M/T,
ee vs mumu pileup, legend order, MET up to 200 GeV, zoomed plots. (Tau veto postponed.)

All numbers are read from the output files of the run:
  hists_zbzc_run3_v2/Summer22/muvar/muvar_table.txt      (compare_zbzc_muvar.py)
  hists_zbzc_run3_v2/Summer22/channels_summary.json      (compare_zbzc_v2_channels.py)
  hists_zbzc_run3_v2/Summer22/pu/pu_closure.txt, pu_profiles.json   (zbzc_pu_closure.py)
  hists_zbzc_run3_v2/Summer22/tagger_summary.txt         (summarize_zbzc_taggers.py)
  BTV working points from the Summer22 correctionlib files (as in the workflow)

Usage:  python make_zbzc_v2_slides_pdf.py [--date "8 November 2026"]
Output: hists_zbzc_run3_v2/Summer22/slides_zbzc_v2_Summer22.pdf
"""
import argparse
import datetime
import json
import re
import textwrap

import correctionlib
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
D = "hists_zbzc_run3_v2/Summer22"
OUT = f"{D}/slides_zbzc_v2_Summer22.pdf"

# ------------------------------------------------------------------ inputs
MUV = {}  # (stage, variant) -> dict
ETA_MU = {}  # (stage, variant) -> [(r, e)] for |eta| 0-0.8, 0.8-1.2, 1.2-2.0, 2.0-2.4
stage = None
eta_mode = False
row = re.compile(r"^(\w+)\s+.*?\s(\d+)\s+([\d.]+)\s+([\d.]+)\+-([\d.]+)\s+([+-][\d.]+)%\s+([+-][\d.]+)\+-\s*([\d.]+)\s+([+-][\d.]+)\+-\s*([\d.]+)")
for line in open(f"{D}/muvar/muvar_table.txt"):
    if line.startswith("== data/MC per leading-muon"):
        eta_mode = True
    m = re.match(r"(==|--) stage (\w+)", line)
    if m:
        stage = m.group(2)
        continue
    if not eta_mode:
        m = row.match(line)
        if m:
            g = m.groups()
            MUV[(stage, g[0])] = dict(data=int(g[1]), mc=float(g[2]), r=int(g[1]) / float(g[2]), re=float(g[4]), vsnom=float(g[5]),
                                      slope=float(g[6]), slope_err=float(g[7]), slope_lead=float(g[8]), slope_lead_err=float(g[9]))
    else:
        p = line.split()
        if p and stage and p[0] in ("nominal", "prev", "trigLead", "sub25", "lead26", "eta21", "trigMatch", "noSS",
                                    "noTrigSF", "noIDIsoSF", "noPU"):
            ETA_MU[(stage, p[0])] = [tuple(map(float, c.split("+-"))) for c in p[1:]]
assert len(MUV) == 22 and len(ETA_MU) == 22, (len(MUV), len(ETA_MU))
CH = json.load(open(f"{D}/channels_summary.json"))
PU = json.load(open(f"{D}/pu/pu_profiles.json"))
SHIFT = {}
for line in open(f"{D}/pu/pu_closure.txt"):
    m = re.match(r"== (\w+):", line)
    if m:
        ch = m.group(1)
    m = re.search(r"data - MC mean N\(PV\) = ([+-][\d.]+); expected .* = ([+-][\d.]+)$", line.strip())
    if m:
        SHIFT[ch] = (float(m.group(1)), float(m.group(2)))
assert set(SHIFT) == {"Zee", "Zmm"}
TAGS = {}  # (channel, kind, tagger, wp) -> dict
for line in open(f"{D}/tagger_summary.txt"):
    m = re.match(r"== (\w+):", line)
    if m:
        ch = m.group(1)
    m = re.match(r"^(btag|ctag) (\w+) ([LMT])\s+(\d+)\s+([\d.]+)\s+([\d.]+)\+-([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\+-([\d.]+)", line)
    if m:
        g = m.groups()
        TAGS[(ch, g[0], g[1], g[2])] = dict(data=int(g[3]), mc=float(g[4]), r=float(g[5]), re=float(g[6]), bfrac=float(g[7]),
                                            cfrac=float(g[8]), effd=float(g[9]), effm=float(g[10]), er=float(g[11]), ere=float(g[12]))
assert len(TAGS) == 36, len(TAGS)
BTV = "/cvmfs/cms-griddata.cern.ch/cat/metadata/BTV/Run3-22CDSep23-Summer22-NanoAODv12/latest"
CB, CC = (correctionlib.CorrectionSet.from_file(f"{BTV}/{k}tagging.json.gz") for k in "bc")
TAGGER_CL = {"PNet": "particleNet", "DeepJet": "deepJet", "RobustParT": "robustParticleTransformer"}
WPV = {(t, wp): (CB[f"{c}_wp_values"].evaluate(wp), CC[f"{c}_wp_values"].evaluate(wp, "CvL"),
                 CC[f"{c}_wp_values"].evaluate(wp, "CvB")) for t, c in TAGGER_CL.items() for wp in "LMT"}

# ------------------------------------------------------------------ layout (as make_zbzc_tag_slides_pdf.py)
W, H = 1920, 1080
DARK, LIGHT, PANEL, ACCENT, BODY, MUTED = "#14213D", "#FBFBF8", "#EEF1F5", "#1F5FA8", "#4A5568", "#6A7179"
GOOD = ("#E8F3EA", "#2E7D32", "#1B5E20")
OPEN = ("#FDF1E4", "#E07B24", DARK)
PX = 72 / 100
plt.rcParams["font.family"] = "DejaVu Sans"
FOOT = "Summer22 (2022 C–D), 13.6 TeV · Z→ℓℓ + ≥1 jet · 20 files per MC sample and per data channel · stat. errors only"


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


def heading(fig, s, sub=None):
    y = text(fig, 128, 60, s, 52, DARK, "bold", ls=1.15)
    if sub:
        y = text(fig, 128, y + 6, sub, 25, BODY, width=1664)
    return y


def note(fig, y, title, body, style=GOOD, h=130, x=128, w=1664):
    color, bar, tcolor = style
    box(fig, x, y, w, h, color)
    box(fig, x, y, 6, h, bar)
    yy = text(fig, x + 40, y + 18, title, 27, tcolor, "bold", ls=1.2, width=w - 80) + 6
    if body:
        text(fig, x + 40, yy, body, 22, DARK, width=w - 80, ls=1.3)
    return y + h


def image(fig, path, y, x=128, w=1664, hmax=None):
    img = mpimg.imread(path)
    h = w * img.shape[0] / img.shape[1]
    if hmax and h > hmax:
        w2 = hmax * img.shape[1] / img.shape[0]
        x, w, h = x + (w - w2) / 2, w2, hmax
    ax = fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])
    ax.imshow(img, interpolation="none")
    ax.axis("off")
    return y + h


def table(fig, x, y, cols, rows, size=24, bold_rows=()):
    rh = size * 1.9
    for i, r in enumerate([[c[0] for c in cols]] + rows):
        cx = x
        for (hdr, w, al), val in zip(cols, r):
            tx = cx + (w - 12 if al == "right" else 12)
            text(fig, tx, y + i * rh + size * 0.45, str(val), size, DARK,
                 "bold" if i == 0 or (i - 1) in bold_rows else "normal", ha=al)
            cx += w
        fig.add_artist(plt.Line2D([x / W, (x + sum(c[1] for c in cols)) / W], [1 - (y + (i + 1) * rh) / H] * 2,
                                  color="#C9D3E3" if i else DARK, lw=1 if i else 2, transform=fig.transFigure))
    return y + (len(rows) + 1) * rh


def f3(r, e):
    return f"{r:.3f} ± {e:.3f}"


# ------------------------------------------------------------------ pages
PAGES = []


def P(key):
    def deco(fn):
        PAGES.append((key, fn))
        return fn
    return deco


def num(key):
    return [k for k, _ in PAGES].index(key) + 1


@P("cover")
def _(fig):
    fig.patch.set_facecolor(DARK)
    text(fig, 128, 300, "Z + jets in Summer22: answers to the questions of 8 November", 62, "white", "bold", width=1650, ls=1.15)
    text(fig, 128, 520, "Muon channel vs electrons, other b/c taggers, pileup in ee vs μμ, MET range, zoomed plots, legend order",
         32, "#C9D3E3", width=1600)
    text(fig, 128, 860, DATE, 26, "#C9D3E3")


@P("qa")
def _(fig):
    y = heading(fig, "The questions and short answers") + 24
    zee, zmm = CH["stages"]["final: MET<50, >=1 jet"]["Zee"], CH["stages"]["final: MET<50, >=1 jet"]["Zmm"]
    rows = [
        ["Small discrepancy in the muon channel", f"Muon trigger SF corrected. ee and μμ now agree: data/MC {zee['r']:.3f} and {zmm['r']:.3f}.", f"{num('mu_setup')}–{num('slope')}"],
        ["", "No muon choice (pT, η, SFs, scale/smearing) changes the pT shape.", ""],
        ["Other taggers, Loose/Medium/Tight", "DeepJet and RobustParT added, each with its own BTV SFs.", f"{num('wps')}–{num('scoreR')}"],
        ["Loose tau ID veto", "Not done yet (postponed, as agreed).", "–"],
        ["Why ee and μμ pileup look different", "The 20 test files of each channel cover different runs.", f"{num('pu_prof')}–{num('pu_rw')}"],
        ["MC colours ee vs μμ", "Legend order is now the same in both channels.", str(num("legend"))],
        ["MET up to ~200 GeV", "Done, without the MET cut.", str(num("met"))],
        ["Zoom into high-statistics bins", "Zoomed copies of 10 plots in every region (linear y, ratio 0.8–1.2).", f"{num('zoom_z_pt')}–{num('zoom_npv')}"],
    ]
    y = table(fig, 128, y, [("question", 560, "left"), ("answer", 960, "left"), ("pages", 144, "right")], rows, 23) + 30
    note(fig, y, "Same files and lumisections as the 237-page deck, so everything here compares directly.",
         f"Check: all 237 Z→ee histograms are identical to the deck, and the old muon setup reproduces the old "
         f"Z→μμ numbers exactly (data {MUV[('final', 'prev')]['data']}, MC {MUV[('final', 'prev')]['mc']:.1f}).", h=130)


@P("runcheck")
def _(fig):
    y = heading(fig, "How this was run and checked") + 30
    y = note(fig, y, "One run with everything in it",
             "Summer22, the same 20 files per MC sample and per data channel as the 237-page deck. Three taggers × "
             "L/M/T × b/c = 18 tagged regions, each with its own BTV SFs. For the muon study, 11 muon setups are "
             "filled side by side in the same run, each changing one thing.", h=170) + 30
    y = note(fig, y, "Checks before looking at the physics",
             "Z→ee: all 237 histograms bit-for-bit identical to the deck (nothing on the electron side changed). "
             "Old muon setup: reproduces the deck's Z→μμ yields exactly. Every sample read all its files.", h=150) + 30
    note(fig, y, "One file read through a different server",
             "One DY file could not be read from the FNAL disk pool (timeout every time), so it was read through the CMS "
             "redirector instead: same file, same events. One EGamma file had a one-off timeout and was rerun.",
             style=OPEN, h=150)


@P("mu_setup")
def _(fig):
    y = heading(fig, "Muons: what changed, following the MUO recommendations") + 30
    y = note(fig, y, "Trigger SF now uses both muons",
             "IsoMu24 fires if either muon fires, so the event SF is [1 − (1−ε¹data)(1−ε²data)] / [1 − (1−ε¹MC)(1−ε²MC)], "
             "with the MUO IsoMu24 efficiencies (muon_Z.json). Before, we used the SF of the leading muon only. That is "
             "only right if we require the leading muon to match the trigger object, which we did not.", h=200) + 25
    y = note(fig, y, "Both muons pT > 26 GeV (was 25 for the second muon)",
             "The MUO trigger efficiencies start at 26 GeV. |η| < 2.4 was already used. Leading muon stays > 35 GeV.",
             h=130) + 25
    y = note(fig, y, "Already in, unchanged",
             "Muon scale and smearing (the Run 3 replacement of Rochester), Tight ID and Tight PF isolation SFs, pileup "
             "weights, golden JSON, MET filters.", h=130) + 25
    a, b = MUV[("final", "prev")], MUV[("final", "nominal")]
    note(fig, y, f"Effect on Z→μμ: data/MC {a['r']:.3f} → {b['r']:.3f}. Z→ee ({CH['stages']['final: MET<50, >=1 jet']['Zee']['r']:.3f}) is unchanged.",
         "Most of it is the trigger SF formula. The 26 GeV cut alone changes data/MC by "
         f"{-MUV[('final', 'sub25')]['vsnom']:+.1f}%.", h=110)


DESC = {"nominal": "new default", "prev": "old setup (deck of 5 Nov)", "trigLead": "trigger SF of leading muon only",
        "sub25": "muon pT > 25 instead of 26", "lead26": "leading muon pT > 26 (not 35)", "eta21": "|η| < 2.1",
        "trigMatch": "lead muon matched to trigger, its SF", "noSS": "no muon scale/smearing",
        "noTrigSF": "no trigger SF", "noIDIsoSF": "no ID + iso SFs", "noPU": "no pileup weights"}
ORDER = list(DESC)


def variant_page(st, title, sub):
    def f(fig):
        y = heading(fig, title, sub) + 18
        rows = []
        for v in ORDER:
            m = MUV[(st, v)]
            rows.append([v, DESC[v], f"{m['data']}", f"{m['mc']:.0f}", f3(m["r"], m["re"]),
                         "–" if v == "nominal" else f"{m['vsnom']:+.2f}%", f"{m['slope']:+.1f} ± {m['slope_err']:.1f}"])
        y = table(fig, 128, y, [("setup", 170, "left"), ("what changes", 520, "left"), ("data", 140, "right"),
                                ("MC", 150, "right"), ("data/MC", 230, "right"), ("vs new", 150, "right"),
                                ("slope pT(μμ)", 304, "right")], rows, 22, bold_rows=(0,)) + 18
        sl = [MUV[(st, v)]["slope"] for v in ORDER]
        tm = MUV[(st, "trigMatch")]["vsnom"]
        note(fig, y, "Only the SFs move the normalisation. No choice changes the pT shape.",
             f"Slopes (% per 100 GeV, pT(μμ) 0–400 GeV) range from {min(sl):+.1f} to {max(sl):+.1f}; the setups share "
             f"most events, so differences are much smaller than the quoted errors. The two POG trigger SF methods "
             f"(both muons, or trigger-matched leading muon) agree within {abs(tm):.1f}%.", h=150)
    return f


P("mu_final")(variant_page("final", "Muon setups after the full selection",
                           "MET < 50 GeV and ≥ 1 jet. Each setup changes one thing w.r.t. the new default."))
P("mu_Z")(variant_page("Z", "Muon setups before the jet and MET cuts",
                       "Trigger, two muons, opposite charge, 71 < m(μμ) < 111 GeV."))


@P("mu_zpt")
def _(fig):
    y = heading(fig, "Muon setups: data/MC vs pT(μμ), Z selection", "Before the jet and MET cuts.") + 10
    y = image(fig, f"{D}/muvar/z_pt_Z.png", y, hmax=720) + 8
    note(fig, y, "All setups give the same shape; they only shift up or down together.",
         "The fall at high pT(μμ) is there in Z→ee too (next pages), so it is not a muon effect.", h=110)


@P("mu_eta")
def _(fig):
    y = heading(fig, "Muon setups: data/MC vs leading-muon η", "Z selection, before the jet and MET cuts.") + 10
    y = image(fig, f"{D}/muvar/lep0_eta_Z.png", y, hmax=700) + 8
    n, t = ETA_MU[("Z", "nominal")], ETA_MU[("Z", "trigMatch")]
    note(fig, y, f"Muons with |η| > 2.0 are low: data/MC {n[3][0]:.3f} ± {n[3][1]:.3f} vs {n[0][0]:.3f} in the barrel.",
         f"The trigger-matching method gives {t[3][0]:.3f} there, so both POG methods see it. Cutting at |η| < 2.1 "
         f"changes data/MC by only {MUV[('Z', 'eta21')]['vsnom']:+.2f}% (same selection). Not understood yet.", style=OPEN, h=130)


@P("channels")
def _(fig):
    y = heading(fig, "Muons vs electrons, step by step",
                "data/MC per selection step; slope = straight-line fit of data/MC vs pT(ℓℓ), 0–400 GeV, % per 100 GeV.") + 18
    rows = []
    for lab, show in (("all Z events", "all Z events (no jet or MET cut)"), ("MET<50, 0 jets", "MET < 50, no jet"),
                      ("MET>50, 0 jets", "MET > 50, no jet"), ("MET>50, >=1 jet", "MET > 50, ≥ 1 jet"),
                      ("final: MET<50, >=1 jet", "final: MET < 50, ≥ 1 jet")):
        e, m = CH["stages"][lab]["Zee"], CH["stages"][lab]["Zmm"]
        rows.append([show, f3(e["r"], e["re"]), f3(m["r"], m["re"]),
                     f"{e['slope']:+.1f} ± {e['slope_err']:.1f}", f"{m['slope']:+.1f} ± {m['slope_err']:.1f}"])
    y = table(fig, 128, y, [("step", 520, "left"), ("data/MC  Z→ee", 290, "right"), ("data/MC  Z→μμ", 290, "right"),
                            ("slope Z→ee", 280, "right"), ("slope Z→μμ", 284, "right")], rows, 23, bold_rows=(4,)) + 22
    rows = [[ch.replace("Zee", "Z→ee").replace("Zmm", "Z→μμ")] + [f3(r, e) for _, r, e in CH["eta"][ch]] for ch in ("Zee", "Zmm")]
    y = text(fig, 128, y, "Final selection, data/MC per leading-lepton |η|:", 23, BODY) + 4
    y = table(fig, 128, y, [("", 200, "left"), ("0–0.8", 360, "right"), ("0.8–1.2", 360, "right"), ("1.2–2.0", 360, "right"),
                            ("2.0–2.5", 384, "right")], rows, 23) + 18
    note(fig, y, "The two channels now behave the same at every step.",
         "The 5–6% deficit after the selection is common: MC has too many events with jets and far too many with MET > 50 GeV.",
         h=110)


@P("slope")
def _(fig):
    y = heading(fig, "The pT slope we discussed",
                "Same fit as before (10 GeV bins, final selection, % per 100 GeV) on three runs with the same files.") + 20
    rows = []
    for run, lab in (("hists_zbzc_run3_ge1j", "29 Oct run, DY Z pT weights ON"), ("hists_zbzc_run3_tag", "237-page deck, weights off"),
                     ("hists_zbzc_run3_v2", "this run (new muon setup)")):
        R = CH["runs"][run]
        rows.append([lab, f"{R['Zee']['z_pt'][0]:+.1f} ± {R['Zee']['z_pt'][1]:.1f}", f"{R['Zmm']['z_pt'][0]:+.1f} ± {R['Zmm']['z_pt'][1]:.1f}",
                     f"{R['Zmm']['lep0_pt'][0]:+.1f} ± {R['Zmm']['lep0_pt'][1]:.1f}", f"{R['Zmm']['jet_pt'][0]:+.1f} ± {R['Zmm']['jet_pt'][1]:.1f}"])
    y = table(fig, 128, y, [("run", 560, "left"), ("pT(ee)", 260, "right"), ("pT(μμ)", 260, "right"),
                            ("lead μ pT", 280, "right"), ("jet pT (μμ)", 304, "right")], rows, 24) + 30
    R = CH["runs"]["hists_zbzc_run3_ge1j"]["Zmm"]["z_pt"]
    y = note(fig, y, f"The +{R[0]:.1f} ± {R[1]:.1f}% per 100 GeV came from the run with the DY Z pT weights on.",
             "With the weights off (the 237-page deck and now) neither channel has a significant slope after the full selection.",
             h=120) + 25
    z = CH["stages"]["all Z events"]
    note(fig, y, "Before the jet and MET cuts both channels fall at high pT(ℓℓ) in the same way.",
         f"Z→ee {z['Zee']['slope']:+.1f} ± {z['Zee']['slope_err']:.1f}, Z→μμ {z['Zmm']['slope']:+.1f} ± {z['Zmm']['slope_err']:.1f} "
         "(% per 100 GeV): the DY generator Z pT, seen before. Still open: a dip at pT(ℓℓ) 30–60 GeV (≈ 0.92) in both channels.",
         style=OPEN, h=150)


@P("pu_prof")
def _(fig):
    y = heading(fig, "Pileup: which lumisections the test files cover",
                "Luminosity-weighted average pileup per lumisection (brilcalc, normtag, 69.2 mb).") + 10
    y = image(fig, f"{D}/pu/pu_profiles.png", y, hmax=680) + 8
    note(fig, y, f"Mean pileup: EGamma files {PU['Zee']['mean_pu']:.1f}, Muon files {PU['Zmm']['mean_pu']:.1f}, "
                 f"full 2022 C–D {PU['full']['mean_pu']:.1f}.",
         "The MC is weighted to the full 2022 C–D profile, so Z→ee data sit lower in N(PV) than its MC.", h=110)


@P("pu_shift")
def _(fig):
    y = heading(fig, "Pileup: the ee vs μμ difference is the data sampling") + 18
    rows = [[c, f"{SHIFT[k][0]:+.2f}", f"{PU[k]['mean_pu'] - PU['full']['mean_pu']:+.2f}", f"{SHIFT[k][1]:+.2f}"]
            for c, k in (("Z→ee", "Zee"), ("Z→μμ", "Zmm"))]
    y = table(fig, 128, y, [("", 200, "left"), ("data − MC, mean N(PV)", 460, "right"),
                            ("pileup of files − full era", 500, "right"), ("expected shift in N(PV)", 504, "right")], rows, 24) + 8
    y = text(fig, 128, y, "Expected = pileup difference × N(PV) per pileup interaction from the MC (0.69).", 21, MUTED) + 10
    y = image(fig, f"{D}/plots/npv.png", y, hmax=560) + 6
    note(fig, y, "The N(PV) offset of each channel is what its lumisections predict.",
         "With the full dataset both channels see the same runs, so this should go away.", h=105)


@P("pu_rw")
def _(fig):
    y = heading(fig, "Pileup: a bin-by-bin reweighting overshoots, so it is not used") + 10
    y = image(fig, f"{D}/pu/npv_closure.png", y, hmax=700) + 8
    note(fig, y, "Reweighting the MC to each channel's own profile over-corrects (Z→μμ, flat before, gets a slope).",
         "Probably because the per-lumisection average ignores the bunch-to-bunch spread. The mean check on the previous page "
         "does not depend on that. The clean test is the full-dataset run.", style=OPEN, h=140)


@P("legend")
def _(fig):
    y = heading(fig, "Legend order is now the same in both channels") + 10
    y = image(fig, f"{D}/plots/z_pt.png", y, hmax=760) + 8
    note(fig, y, "Before, each channel sorted the stack by its own yields, so DY+b and DY+c swapped places in Z→ee.",
         "Now one order for both: DY+b, DY+c, DY+light, tt, VV. Colours unchanged.", h=110)


@P("met")
def _(fig):
    y = heading(fig, "MET up to 200 GeV, without the MET cut") + 10
    y = image(fig, f"{D}/plots/met_pt_nm1.png", y, hmax=760) + 8
    note(fig, y, "MC is well above data from 40 to 120 GeV in both channels (data/MC down to about 0.6).",
         "This is the 2022 jet/MET issue we traced in October (jets in the type-1 MET). Above ~120 GeV tt dominates.",
         style=OPEN, h=110)


for var, title in (("z_pt", "Z pT, 0–200 GeV"), ("lep0_pt", "Leading-lepton pT, 30–200 GeV"),
                   ("jet_pt", "Leading-jet pT, 30–200 GeV"), ("npv", "N primary vertices, 10–50")):
    def mk(var=var, title=title):
        def f(fig):
            y = heading(fig, f"Zoom: {title}", "Linear scale, ratio 0.8–1.2. Every region has zoomed copies of z_pt, lep0_pt, lep1_pt, "
                        "jet_pt, jet1_pt, lhe_vpt, met_pt_nm1, npv, m_jj, pt_balance (*_zoom.png).") + 10
            image(fig, f"{D}/plots/{var}_zoom.png", y, hmax=1000 - y)
        return f
    P(f"zoom_{var}")(mk())


@P("wps")
def _(fig):
    y = heading(fig, "Three taggers, Loose / Medium / Tight",
                "Cut on the leading jet. Working points and SFs from the BTV Summer22 files; each tagger uses its own SFs.") + 20
    rows = []
    for t in TAGGER_CL:
        for wp in "LMT":
            b, cvl, cvb = WPV[(t, wp)]
            rows.append([t if wp == "L" else "", {"L": "Loose", "M": "Medium", "T": "Tight"}[wp], f"{b:.4g}", f"{cvl:.4g}", f"{cvb:.4g}"])
    y = table(fig, 128, y, [("tagger", 360, "left"), ("WP", 240, "left"), ("b-tag: B >", 340, "right"),
                            ("c-tag: CvL >", 340, "right"), ("and CvB >", 384, "right")], rows, 23) + 20
    note(fig, y, "SFs: _comb (b, c) and _light for b-tag; _wc (c), _tnp (b) and _light for c-tag.",
         "Same SF validity range for all three taggers. b-tag and c-tag are separate regions.", h=110)


def tag_page(kind):
    def f(fig):
        fl = "bfrac" if kind == "btag" else "cfrac"
        y = heading(fig, f"{'b' if kind == 'btag' else 'c'}-tag: purity and data vs MC per tagger",
                    "Purity = DY " + ("b" if kind == "btag" else "c") + "-jet share of the tagged DY MC. Tag ratio = tagged "
                    "fraction in data / in MC: the overall 5% normalisation cancels, so it tests the tagging and its SFs.") + 18
        rows, pulls = [], []
        for t in TAGGER_CL:
            for wp in "LMT":
                e, m = TAGS[("Zee", kind, t, wp)], TAGS[("Zmm", kind, t, wp)]
                pulls += [((x["er"] - 1) / x["ere"], ch, t, wp, x) for ch, x in (("Z→ee", e), ("Z→μμ", m))]
                rows.append([t if wp == "L" else "", wp, f"{100 * e[fl]:.0f}%", f"{100 * m[fl]:.0f}%",
                             f"{100 * m['effd']:.1f}%", f3(e["er"], e["ere"]), f3(m["er"], m["ere"])])
        y = table(fig, 128, y, [("tagger", 300, "left"), ("WP", 90, "left"), ("purity ee", 210, "right"),
                                ("purity μμ", 210, "right"), ("tagged, μμ data", 270, "right"),
                                ("tag ratio  Z→ee", 290, "right"), ("tag ratio  Z→μμ", 294, "right")], rows, 22) + 18
        worst = max(pulls, key=lambda p: abs(p[0]))
        avg = {t: sum(TAGS[(c, kind, t, wp)]["er"] for c in ("Zee", "Zmm") for wp in "LMT") / 6 for t in TAGGER_CL}
        dev = max(abs(x[4]["er"] - 1) for x in pulls)
        title = ("Data and MC tag the same fraction of jets within the stat. errors, for all three taggers."
                 if abs(worst[0]) < 2 else
                 f"Data and MC tag fractions agree within {100 * dev:.0f}%, but not all within the stat. errors.")
        note(fig, y, title,
             f"Largest deviation: {worst[2]} {worst[3]}, {worst[1]}: {worst[4]['er']:.3f} ± {worst[4]['ere']:.3f} "
             f"({abs(worst[0]):.1f}σ, stat. only). Mean tag ratio over the 6 numbers: "
             + ", ".join(f"{t} {v:.3f}" for t, v in avg.items()) + ". SF uncertainties not included yet.",
             style=GOOD if abs(worst[0]) < 2 else OPEN, h=130)
    return f


P("btag")(tag_page("btag"))
P("ctag")(tag_page("ctag"))


@P("scoreD")
def _(fig):
    y = heading(fig, "DeepJet B score of the leading jet", "No tag cut, so no tagging SF here (SFs apply to tagged jets only).") + 10
    image(fig, f"{D}/plots/jet_DeepJetB.png", y, hmax=1000 - y)


@P("scoreR")
def _(fig):
    y = heading(fig, "RobustParT B score of the leading jet", "No tag cut, so no tagging SF here. CvL, CvB plots and all 18 "
                "tagged regions: hists_zbzc_run3_v2/Summer22/plots_<region>/.") + 10
    image(fig, f"{D}/plots/jet_RobustParTB.png", y, hmax=1000 - y)


@P("summary")
def _(fig):
    y = heading(fig, "Summary") + 24
    zee, zmm = CH["stages"]["final: MET<50, >=1 jet"]["Zee"], CH["stages"]["final: MET<50, >=1 jet"]["Zmm"]
    y = note(fig, y, f"Muon channel: trigger SF now follows MUO for two muons. Z→ee {zee['r']:.3f}, Z→μμ {zmm['r']:.3f}.",
             "The channels agree at every step. No muon choice changes the pT shape; there is no significant pT slope after "
             "the selection in either channel.", h=125) + 18
    y = note(fig, y, "Pileup ee vs μμ: explained by the runs the 20 test files cover.",
             "Legend order fixed, MET up to 200 GeV, zoomed plots in every region.", h=105) + 18
    cav = {t: sum(TAGS[(c, "ctag", t, wp)]["er"] for c in ("Zee", "Zmm") for wp in "LMT") / 6 for t in TAGGER_CL}
    y = note(fig, y, "DeepJet and RobustParT added at L/M/T, with their own SFs. Purity is similar to PNet.",
             "b-tag: data/MC tag ratios consistent with 1 for all three. c-tag: mean tag ratio "
             + ", ".join(f"{t} {v:.3f}" for t, v in cav.items()) + " (stat. only, no SF uncertainties yet).", h=105) + 18
    y = note(fig, y, "Not fixed / still open",
             "• Common 5–6% deficit after the jet and MET cuts: MC has too many events with jets and with MET > 50 GeV.\n"
             "• Dip at pT(ℓℓ) 30–60 GeV in both channels. • Muons with |η| > 2.0 about 3% low before the jet cut.\n"
             "• Loose tau veto not done. • No SF uncertainties yet. • 20 files per sample: stat. errors of 1–8%.",
             style=OPEN, h=175) + 18
    note(fig, y, "To decide",
         "Keep the new muon setup (pair trigger SF, pT > 26) as the default? Which tagger and WP for b and for c? "
         "Then: run the full Summer22 dataset.", style=OPEN, h=115)


# ------------------------------------------------------------------ render
pdf = PdfPages(OUT)
for i, (key, fn) in enumerate(PAGES, 1):
    fig = page()
    fn(fig)
    if key != "cover":
        text(fig, 128, 1035, f"{FOOT} · {i}", 19, MUTED)
    pdf.savefig(fig)
    plt.close(fig)
pdf.close()
print("wrote", OUT, f"({len(PAGES)} pages)")
