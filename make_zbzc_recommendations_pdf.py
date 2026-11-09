"""One PDF with the advisor's recommendations of 8 November 2026, what was done for each and the outcome
(Summer22, run zbzc_run3_v2). Slide format like the other decks; every number is read from the output files
(same inputs as make_zbzc_v2_slides_pdf.py) plus the pT(ll) shape table computed from the coffea outputs of
hists_zbzc_run3_tag (237-page deck) and hists_zbzc_run3_v2.

Usage:  python make_zbzc_recommendations_pdf.py [--date "8 November 2026"]
Output: hists_zbzc_run3_v2/Summer22/advisor_recommendations_2026-11-08.pdf
"""
import argparse
import datetime
import glob
import json
import re
import textwrap

import correctionlib
import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
from coffea.util import load
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch

parser = argparse.ArgumentParser()
parser.add_argument("--date", default=None)
args = parser.parse_args()
DATE = args.date or datetime.date.today().strftime("%-d %B %Y")
D = "hists_zbzc_run3_v2/Summer22"
OUT = f"{D}/advisor_recommendations_2026-11-08.pdf"

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



# ------------------------------------------------------------------ pT(ll) shape: data/MC per range / overall data/MC
XS = json.load(open("metadata/Zb_Zc_ratio_xsections_run3.json"))
LUMI = json.load(open("hists_zbzc_run3/Summer22/lumi.json"))
RANGES = [(0, 30), (30, 60), (60, 100), (100, 150), (150, 200), (200, 300), (300, 400), (400, 1000)]


def shape(run, ch):
    out = {}
    for f in sorted(glob.glob(f"{run}/Summer22/zbzc_run3/zbzc_run3_*.coffea")):
        out.update(load(f))
    data = mc = None
    for ds, o in out.items():
        h = o["z_pt"][{"channel": ch, "flav": sum, "pflav": sum, "tag": "incl"}]
        if not ds.startswith(("Muon", "EGamma")):
            h = h * (XS[ds] * LUMI[ch] / o["sumw"])
            mc = h if mc is None else mc + h
        elif ds.startswith("Muon" if ch == "Zmm" else "EGamma"):
            data = h if data is None else data + h
    e = data.axes[0].edges
    c = 0.5 * (e[1:] + e[:-1])
    d, m = data.values(), mc.values()
    tot = d.sum() / m.sum()
    res = []
    for a, b in RANGES:
        s = (c > a) & (c < b)
        res.append((d[s].sum() / m[s].sum() / tot, int(d[s].sum())))
    return res


SHAPE = {"Z→μμ, 237-page deck": shape("hists_zbzc_run3_tag", "Zmm"), "Z→μμ, today": shape("hists_zbzc_run3_v2", "Zmm"),
         "Z→ee (unchanged)": shape("hists_zbzc_run3_v2", "Zee")}
FINAL = CH["stages"]["final: MET<50, >=1 jet"]
ALLZ = CH["stages"]["all Z events"]


def vs(v, st="final"):
    return f"{MUV[(st, v)]['vsnom']:+.2f}%"


pdf = PdfPages(OUT)
n = 0


def save(fig, foot=True):
    global n
    n += 1
    if foot:
        text(fig, 128, 1035, f"{FOOT} · {n}", 19, MUTED)
    pdf.savefig(fig)
    plt.close(fig)


# ------------------------------------------------------------------ 1 cover
fig = page(DARK)
text(fig, 128, 300, "Recommendations of 8 November:\nwhat was done and what came out", 62, "white", "bold", width=1650, ls=1.15)
text(fig, 128, 520, "Z + jets in Summer22 (2022 C–D), same files as the 237-page deck", 32, "#C9D3E3", width=1600)
text(fig, 128, 860, DATE, 26, "#C9D3E3")
save(fig, foot=False)

# ------------------------------------------------------------------ 2 overview
fig = page()
y = heading(fig, "Overview") + 24
rows = [
    ["1", "Muon discrepancy (trigger, η, SFs, Rochester)", "done", f"Trigger SF fixed: μμ {MUV[('final', 'prev')]['r']:.3f} → {FINAL['Zmm']['r']:.3f}, ee {FINAL['Zee']['r']:.3f}", "3–5"],
    ["", "", "", "pT shape: unchanged, same in ee (not muons)", ""],
    ["2", "Other b/c taggers, L/M/T", "done", "DeepJet, RobustParT added; similar purity", "6"],
    ["3", "Loose tau ID veto", "postponed", "–", "8"],
    ["4", "Why ee and μμ pileup differ", "done", "Test files cover different runs", "7"],
    ["5", "ee vs μμ MC colours (legend)", "done", "One stack and legend order for both", "8"],
    ["6", "MET up to ~200 GeV", "done", "MC excess 40–120 GeV (known)", "8"],
    ["7", "Zoom into high-statistics bins", "done", "10 zoomed plots in every region", "8"],
]
y = table(fig, 128, y, [("#", 60, "left"), ("recommendation", 600, "left"), ("status", 170, "left"),
                        ("outcome", 694, "left"), ("page", 140, "right")], rows, 22) + 26
note(fig, y, "Everything compares directly with the 237-page deck.",
     "Same files and lumisections. All 237 Z→ee histograms are bit-for-bit identical, and the old muon setup reproduces "
     f"the old Z→μμ yields exactly (data {MUV[('final', 'prev')]['data']}). Statistical errors only, 20 files per sample.", h=130)
save(fig)

# ------------------------------------------------------------------ 3 muons: what was checked
fig = page()
y = heading(fig, "1. Muons: what was checked",
            "Each line is a separate muon setup in the same run, changing one thing. Right: how much data/MC would change "
            "with that choice instead of the new default.") + 18
rows = [
    ["Trigger SF", "was: leading muon only (old choice)", vs("trigLead"), vs("trigLead", "Z")],
    ["", "other POG method: leading muon matched to trigger", vs("trigMatch"), vs("trigMatch", "Z")],
    ["Trigger turn-on", "second muon pT > 25 (old) instead of 26", vs("sub25"), vs("sub25", "Z")],
    ["", "leading muon pT > 26 instead of 35", vs("lead26"), vs("lead26", "Z")],
    ["η cut", "|η| < 2.1 instead of 2.4", vs("eta21"), vs("eta21", "Z")],
    ["Rochester", "no muon scale/smearing (Run 3 replacement)", vs("noSS"), vs("noSS", "Z")],
    ["SFs", "no ID + isolation SFs", vs("noIDIsoSF"), vs("noIDIsoSF", "Z")],
    ["", "no pileup weights", vs("noPU"), vs("noPU", "Z")],
]
y = table(fig, 128, y, [("suspect", 290, "left"), ("other choice", 820, "left"), ("after all cuts", 270, "right"),
                        ("before jet/MET cuts", 284, "right")], rows, 23) + 22
note(fig, y, "One real problem: the trigger SF. IsoMu24 fires if either muon fires, so the SF must use both muons.",
     "Now the POG two-muon formula with the data and MC efficiencies of muon_Z.json, and both muons pT > 26 GeV (where the "
     "SFs start). The trigger-matching method agrees within 1%. |η| < 2.4 and the scale/smearing were already in.", h=150)
save(fig)

# ------------------------------------------------------------------ 4 muons: outcome
fig = page()
y = heading(fig, "1. Muons: outcome", "data/MC per selection step, after the change.") + 18
rows = []
for lab, show in (("all Z events", "all Z events (no jet or MET cut)"), ("MET<50, 0 jets", "MET < 50, no jet"),
                  ("MET>50, >=1 jet", "MET > 50, ≥ 1 jet"), ("final: MET<50, >=1 jet", "final: MET < 50, ≥ 1 jet")):
    e, m = CH["stages"][lab]["Zee"], CH["stages"][lab]["Zmm"]
    rows.append([show, f3(e["r"], e["re"]), f3(m["r"], m["re"])])
y = table(fig, 128, y, [("step", 760, "left"), ("Z→ee", 450, "right"), ("Z→μμ", 454, "right")], rows, 24) + 26
y = note(fig, y, f"Z→μμ data/MC {MUV[('final', 'prev')]['r']:.3f} → {FINAL['Zmm']['r']:.3f}. It now matches Z→ee ({FINAL['Zee']['r']:.3f}) at every step.",
         "The remaining 5–6% deficit after the cuts is common to both channels: MC has too many events with jets and far too many "
         "with MET > 50 GeV.", h=130) + 22
eta = ETA_MU[("Z", "nominal")]
note(fig, y, f"Open: muons with |η| > 2.0 are low before the jet/MET cuts ({eta[3][0]:.3f} ± {eta[3][1]:.3f} vs {eta[0][0]:.3f} in the barrel).",
     f"Both POG trigger SF methods see it (trigger matching: {ETA_MU[('Z', 'trigMatch')][3][0]:.3f}). Cutting at |η| < 2.1 "
     f"changes the total by only {vs('eta21', 'Z')}.", style=OPEN, h=130)
save(fig)

# ------------------------------------------------------------------ 5 pT shape
fig = page()
y = heading(fig, "1. Muons: the pT(ℓℓ) slope",
            "data/MC per pT(ℓℓ) range divided by the overall data/MC (shape only), full selection.") + 18
rows = [[k] + [f"{r:.3f}" for r, _ in v] for k, v in SHAPE.items()]
rows.append(["events, Z→μμ today"] + [str(nn) for _, nn in SHAPE["Z→μμ, today"]])
y = table(fig, 128, y, [("pT(ℓℓ) [GeV]", 384, "left")] + [(f"{a}–{b}", 160, "right") for a, b in RANGES], rows, 22) + 22
y = note(fig, y, "The visual slope is still there, unchanged. No muon setup changes it, and Z→ee has the same pattern.",
         "data/MC peaks at 100–150 GeV and falls above 200 GeV. Before the jet and MET cuts both channels already fall at high "
         f"pT(ℓℓ) (Z→ee {ALLZ['Zee']['slope']:+.1f} ± {ALLZ['Zee']['slope_err']:.1f}, Z→μμ {ALLZ['Zmm']['slope']:+.1f} ± "
         f"{ALLZ['Zmm']['slope_err']:.1f} % per 100 GeV): DY modelling, not muons.", style=OPEN, h=160) + 22
R = CH["runs"]
note(fig, y, "The fitted slope of +4.4% per 100 GeV came from the run with the DY Z pT weights on.",
     f"Same fit, same files: weights on {R['hists_zbzc_run3_ge1j']['Zmm']['z_pt'][0]:+.1f} ± {R['hists_zbzc_run3_ge1j']['Zmm']['z_pt'][1]:.1f}; "
     f"237-page deck (weights off) {R['hists_zbzc_run3_tag']['Zmm']['z_pt'][0]:+.1f} ± {R['hists_zbzc_run3_tag']['Zmm']['z_pt'][1]:.1f}; "
     f"today {R['hists_zbzc_run3_v2']['Zmm']['z_pt'][0]:+.1f} ± {R['hists_zbzc_run3_v2']['Zmm']['z_pt'][1]:.1f}. "
     "A straight line misses the up-and-down pattern, so the fit is near zero.", h=150)
save(fig)

# ------------------------------------------------------------------ 6 taggers
fig = page()
y = heading(fig, "2. Other taggers: DeepJet and RobustParT next to PNet",
            "Leading jet, POG working points, each tagger with its own BTV SFs. Purity = share of real b (c) jets in the tagged DY MC "
            "(Z→μμ). Tag ratio = tagged fraction in data / in MC, Z→ee and Z→μμ.") + 16
rows = []
for t in TAGGER_CL:
    for wp in "LMT":
        b = (TAGS[("Zee", "btag", t, wp)], TAGS[("Zmm", "btag", t, wp)])
        c = (TAGS[("Zee", "ctag", t, wp)], TAGS[("Zmm", "ctag", t, wp)])
        rows.append([t if wp == "L" else "", wp, f"{100 * b[1]['bfrac']:.0f}%", f"{b[0]['er']:.3f} / {b[1]['er']:.3f}",
                     f"{100 * c[1]['cfrac']:.0f}%", f"{c[0]['er']:.3f} / {c[1]['er']:.3f}"])
y = table(fig, 128, y, [("tagger", 280, "left"), ("WP", 90, "left"), ("b-tag purity", 250, "right"),
                        ("b-tag ratio ee / μμ", 380, "right"), ("c-tag purity", 250, "right"),
                        ("c-tag ratio ee / μμ", 414, "right")], rows, 21) + 18
bp = [abs(x["er"] - 1) / x["ere"] for k, x in TAGS.items() if k[1] == "btag"]
cav = {t: np.mean([TAGS[(c, "ctag", t, wp)]["er"] for c in ("Zee", "Zmm") for wp in "LMT"]) for t in TAGGER_CL}
cp = max(abs(x["er"] - 1) / x["ere"] for k, x in TAGS.items() if k[1] == "ctag")
note(fig, y, f"Similar purity at the same WP. b-tag: data and MC agree for all three (largest {max(bp):.1f}σ).",
     "c-tag: average tag ratio " + ", ".join(f"{t} {v:.3f}" for t, v in cav.items()) +
     f" (largest {cp:.1f}σ), so the taggers differ by a few percent there. Stat. errors 1–8%; no SF uncertainties yet.",
     h=130)
save(fig)

# ------------------------------------------------------------------ 7 pileup
fig = page()
y = heading(fig, "4. Why the ee and μμ pileup plots differ",
            "Pileup of the lumisections our 20 data files cover (brilcalc, normtag, 69.2 mb), vs the full 2022 C–D profile "
            "the MC is weighted to.") + 22
rows = [[c, f"{PU[k]['mean_pu']:.1f}", f"{PU['full']['mean_pu']:.1f}", f"{SHIFT[k][0]:+.2f}", f"{SHIFT[k][1]:+.2f}"]
        for c, k in (("Z→ee (EGamma files)", "Zee"), ("Z→μμ (Muon files)", "Zmm"))]
y = table(fig, 128, y, [("", 420, "left"), ("mean pileup, files", 300, "right"), ("full era", 220, "right"),
                        ("data − MC, mean N(PV)", 360, "right"), ("expected", 364, "right")], rows, 24) + 10
y = text(fig, 128, y, "Expected = pileup difference × N(PV) per pileup interaction from the MC (0.69).", 21, MUTED) + 26
y = note(fig, y, "The test files cover different runs, and that predicts each channel's N(PV) offset.",
         "The EGamma files have less high pileup than the Muon files and the full era.", h=110) + 22
note(fig, y, "Caveat: reweighting the MC bin by bin to each subset over-corrected, so it is not used.",
     "The clean test is the full-dataset run, where both channels see the same runs.", style=OPEN, h=110)
save(fig)

# ------------------------------------------------------------------ 8 items 3, 5, 6, 7
fig = page()
y = heading(fig, "3, 5, 6, 7: the other items") + 26
y = note(fig, y, "5. ee vs μμ MC colours: fixed.",
         "The plot script sorted the stack by each channel's own yields, so DY+b and DY+c swapped places in Z→ee. Now one fixed "
         "order for both channels. The 237-page deck's plots were remade too.", h=130) + 22
y = note(fig, y, "6. MET up to 200 GeV: done (new plot without the MET cut, in every region).",
         "MC is well above data from 40 to 120 GeV in both channels (data/MC down to about 0.6): the 2022 jet/MET issue traced in "
         "October. Not fixed.", h=130) + 22
y = note(fig, y, "7. Zoom: done.",
         "Zoomed copies (linear scale, ratio 0.8–1.2) of Z pT, both lepton pTs, leading and second jet pT, generator Z pT, MET, "
         "N(PV), dijet mass and pT balance, in every region.", h=130) + 22
note(fig, y, "3. Loose tau ID veto: postponed, as agreed.", "", style=OPEN, h=70)
save(fig)

# ------------------------------------------------------------------ 9 open, decisions, files
fig = page()
y = heading(fig, "Still open, to decide, and where everything is") + 26
y = note(fig, y, "Still open",
         "• Common 5–6% deficit after the jet and MET cuts (MC excess with jets and with MET > 50 GeV).\n"
         "• pT(ℓℓ) shape (dip at 30–60 GeV, fall above 200 GeV) in both channels.\n"
         "• Muons with |η| > 2.0 about 3% low. • Tau veto. • SF uncertainties. • Only 20 files per sample.", style=OPEN, h=175) + 22
y = note(fig, y, "To decide",
         "Keep the new muon setup (two-muon trigger SF, pT > 26) as the default? Which tagger and working point? "
         "Then run the full Summer22 dataset.", style=OPEN, h=120) + 22
note(fig, y, "Files (in hists_zbzc_run3_v2/Summer22/)",
     "slides_zbzc_v2_Summer22.pdf: answers deck with plots (25 pages).\n"
     "slides_zbzc_btagL_3taggers_Summer22.pdf: Loose b-tag, three taggers, key plots (65 pages).\n"
     "plots_<region>/: all 49 plots for each of the 19 regions. Tables: muvar/, pu/, tagger_summary.txt, channels_summary.txt.",
     h=190)
save(fig)

pdf.close()
print("wrote", OUT, f"({n} pages)")
