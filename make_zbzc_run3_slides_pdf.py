"""PDF slides for the first Run 3 data/MC look of Zb_Zc_ratio (AK4), same style as
make_zbzc_ak4_slides_pdf.py.

Pages: cover, what is new, data and lumi per campaign, MC samples, corrections and
weights, cutflow data vs MC per channel, yields by flavour and process, data/MC per
campaign, the data/MC plots of plot_zbzc_run3.py (all campaigns summed), per-campaign
grids (m(ll), jet eta, PNet B), the CvL-CvB map, and a summary page whose text comes
from --summary (a JSON file with "title", "body" and "next" written after looking at
the results). All numbers are read from the coffea outputs and lumi.json.

Usage:
    python make_zbzc_run3_slides_pdf.py all [--summary summary.json]
writes hists_zbzc_run3/<which>/slides_zbzc_run3_<which>.pdf
"""
import argparse
import datetime
import glob
import json
import os
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
from coffea.util import load
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch

parser = argparse.ArgumentParser()
parser.add_argument("which", help="campaign or 'all' (as for plot_zbzc_run3.py)")
parser.add_argument("--summary", default=None, help="JSON with the summary page text")
parser.add_argument("--date", default=None)
args = parser.parse_args()

CAMPAIGNS = ["Summer22", "Summer22EE", "Summer23", "Summer23BPix"]
ERAS = {"Summer22": "2022 C–D", "Summer22EE": "2022 E–G", "Summer23": "2023 C", "Summer23BPix": "2023 D"}
camps = CAMPAIGNS if args.which == "all" else [args.which]
indir = f"hists_zbzc_run3/{args.which}"
outfile = os.path.join(indir, f"slides_zbzc_run3_{args.which}.pdf")
DATE = args.date or datetime.date.today().strftime("%-d %B %Y")
XS = json.load(open("metadata/Zb_Zc_ratio_xsections_run3.json"))
CHS = {"Zee": "Z→ee", "Zmm": "Z→μμ"}

OUT, LUMI = {}, {}
for c in camps:
    OUT[c] = {}
    for f in sorted(glob.glob(f"hists_zbzc_run3/{c}/zbzc_run3/zbzc_run3_*.coffea")):
        OUT[c].update(load(f))
    LUMI[c] = json.load(open(f"hists_zbzc_run3/{c}/lumi.json"))
LTOT = {ch: sum(LUMI[c][ch] for c in camps) for ch in CHS}
VV_HAVE = sorted({ds.split("_")[0] for c in camps for ds in OUT[c] if ds.split("_")[0] in ("WW", "WZ", "ZZ")})
ERA_TXT = " + ".join(ERAS[c] for c in camps)
IS2023 = any("23" in c for c in camps)


def kind(ds):
    if ds.startswith("DYto2L"):
        return "DY"
    if ds.startswith("TTto2L2Nu"):
        return "tt"
    if ds.split("_")[0] in ("WW", "WZ", "ZZ"):
        return "VV"
    return "data_Zmm" if ds.startswith("Muon") else "data_Zee"


def scale(c, ds, ch):
    return XS[ds] * LUMI[c][ch] / OUT[c][ds]["sumw"]


def final_yields(c, ch):
    """Yields after the full selection: DY b/c/l, tt, VV (MC with all weights), data."""
    y = {k: 0.0 for k in ["b", "c", "l", "tt", "VV", "data"]}
    for ds, o in OUT[c].items():
        k = kind(ds)
        h = o["jet_pt"][{"channel": ch, "pflav": sum}]
        if k == "DY":
            for f in "bcl":
                y[f] += h[{"flav": f}].sum(flow=True).value * scale(c, ds, ch)
        elif k in ("tt", "VV"):
            y[k] += h[{"flav": sum}].sum(flow=True).value * scale(c, ds, ch)
        elif k == f"data_{ch}":
            y["data"] += h[{"flav": sum}].sum(flow=True).value
    y["MC"] = sum(y[k] for k in ["b", "c", "l", "tt", "VV"])
    return y


def summed(ch):
    tot = {}
    for c in camps:
        for k, v in final_yields(c, ch).items():
            tot[k] = tot.get(k, 0.0) + v
    return tot


Y = {ch: summed(ch) for ch in CHS}
STEPS = ["trigger", "leptons", "OS", "Zmass", "MET", "jet"]


def cutflow(ch):
    """Data events and MC sum(genWeight) x xsec x lumi / sumw (no SFs) per step, all campaigns."""
    mc, dat = np.zeros(len(STEPS)), np.zeros(len(STEPS))
    for c in camps:
        for ds, o in OUT[c].items():
            k = kind(ds)
            if k in ("DY", "tt", "VV"):
                mc += np.array([o["cutflow"][ch][s] for s in STEPS]) * scale(c, ds, ch)
            elif k == f"data_{ch}":
                dat += np.array([o["cutflow_raw"][ch][s] for s in STEPS])
    return mc, dat


# ------------------------------------------------------------------ layout helpers
W, H = 1920, 1080
DARK, LIGHT, PANEL, ACCENT, BODY, MUTED = "#14213D", "#FBFBF8", "#EEF1F5", "#1F5FA8", "#4A5568", "#6A7179"
PX = 72 / 100
plt.rcParams["font.family"] = "DejaVu Sans"
FOOT = (f"Run 3, 13.6 TeV · {', '.join(ERAS[c] for c in camps)} · 20 files per MC sample and per data channel "
        "· AK4 jets")


def page(bg=LIGHT):
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    fig.patch.set_facecolor(bg)
    return fig


def text(fig, x, y, s, size, color=DARK, weight="normal", ha="left", width=None, family=None, ls=1.4):
    if width:
        s = "\n".join(textwrap.fill(p, max(1, int(width / (0.55 * size)))) for p in s.split("\n"))
    fig.text(x / W, 1 - y / H, s, fontsize=size * PX, color=color, weight=weight, ha=ha, va="top",
             family=family or plt.rcParams["font.family"], linespacing=ls)
    return y + size * ls * (s.count("\n") + 1)


def box(fig, x, y, w, h, color):
    fig.add_artist(FancyBboxPatch((x / W, 1 - (y + h) / H), w / W, h / H, boxstyle="round,pad=0,rounding_size=0.008",
                                  transform=fig.transFigure, facecolor=color, edgecolor=color, lw=0))


def footer(fig, s, n):
    text(fig, 128, 1000, f"{s} · {n}", 22, MUTED)


def heading(fig, s, y=128):
    return text(fig, 128, y, s, 64, DARK, "bold", ls=1.15)


def table(fig, x, y, cols, rows, size=28, shade=()):
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


def note(fig, y, title, body, color="#FDF1E4", bar="#E07B24", tcolor=DARK, h=200):
    box(fig, 128, y, 1664, h, color)
    box(fig, 128, y, 6, h, bar)
    yy = text(fig, 168, y + 26, title, 32, tcolor, "bold", ls=1.2) + 10
    text(fig, 168, yy, body, 26, DARK, width=1584, ls=1.35)
    return y + h


def image(fig, path, y, x=128, w=1664, hmax=None):
    img = mpimg.imread(path)
    h = w * img.shape[0] / img.shape[1]
    if hmax and h > hmax:
        w, h = hmax * img.shape[1] / img.shape[0], hmax
        x = x + (1664 - w) / 2
    ax = fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])
    ax.imshow(img)
    ax.axis("off")


pdf = PdfPages(outfile)
n = 0


def save(fig):
    pdf.savefig(fig)
    plt.close(fig)


def num(v):
    return f"{v:,.0f}"


# ------------------------------------------------------------------ cover
fig = page(DARK)
text(fig, 128, 260, "BTVNANOCOMMISSIONING · ZB_ZC_RATIO WORKFLOW", 28, "#7FB3E6", "bold")
text(fig, 128, 340, "Z(→ℓℓ) + b/c jets in Run 3: first look at data", 88, LIGHT, "bold", width=1664, ls=1.1)
text(fig, 128, 570, (args.which if len(camps) == 1 else "All campaigns"), 44, "#7FB3E6", "bold")
text(fig, 128, 650, f"{ERA_TXT} data vs MC, a small sample ({LTOT['Zmm'] / 1000:.1f} fb⁻¹ in Z→μμ, "
     f"{LTOT['Zee'] / 1000:.1f} fb⁻¹ in Z→ee), AK4 jets", 44, "#C9D3E3", width=1664)
text(fig, 128, 800, DATE, 28, "#C9D3E3")
save(fig)
n = 2

# ------------------------------------------------------------------ what is new
fig = page()
y = heading(fig, "What is new since last time") + 40
cw = (1664 - 2 * 32) / 3
cards = [("DATA", ERA_TXT, "First look at data. Muon and EGamma, 22Sep2023 reprocessing."),
         ("CAMPAIGN", args.which if len(camps) == 1 else str(len(camps)),
          "One of four campaigns run (Summer22, Summer22EE, Summer23, Summer23BPix). Each has its own "
          "corrections and its own deck; they are not combined."),
         ("CORRECTIONS", "Full set", "Jet energy corrections, jet veto maps, lepton energy scale, "
                                      "lepton and trigger SFs. Electron SFs from Hsin-Wei's latest code.")]
for i, (lab, big, small) in enumerate(cards):
    cx = 128 + i * (cw + 32)
    box(fig, cx, y, cw, 330, PANEL)
    text(fig, cx + 36, y + 36, lab, 24, ACCENT, "bold")
    text(fig, cx + 36, y + 90, big, 48, DARK, "bold")
    text(fig, cx + 36, y + 180, small, 26, BODY, width=cw - 72)
y += 330 + 48
text(fig, 128, y, "This is a small, quick run: 20 files per MC sample and 20 data files per channel and campaign, "
     "run interactively. The aim is to see whether data and MC agree before we scale up. "
     "The selection is the same as in the MC-only study: two leptons on the Z peak and at least one AK4 jet "
     "with pT > 30 GeV. No b- or c-tag requirement yet.", 30, BODY, width=1664)
footer(fig, FOOT, n)
save(fig)
n += 1

# ------------------------------------------------------------------ data and lumi
fig = page()
y = heading(fig, "Data used and luminosity") + 40
rows = []
for c in camps:
    eras = ", ".join(sorted({ds.split("_")[1] for ds in OUT[c] if kind(ds).startswith("data")}))
    nfiles = {ch: sum(len(set(OUT[c][ds]["fname"])) for ds in OUT[c] if kind(ds) == f"data_{ch}") for ch in CHS}
    rows.append([c, eras.replace("Run", ""), nfiles["Zmm"], f"{LUMI[c]['Zmm']:.0f}", nfiles["Zee"],
                 f"{LUMI[c]['Zee']:.0f}"])
if len(camps) > 1:
    rows.append(["Total", "", "", f"{LTOT['Zmm']:.0f}", "", f"{LTOT['Zee']:.0f}"])
cols = [("Campaign", 300, "left"), ("Run eras", 260, "left"), ("Muon files", 220, "right"),
        ("Z→μμ lumi [pb⁻¹]", 310, "right"), ("EGamma files", 264, "right"), ("Z→ee lumi [pb⁻¹]", 310, "right")]
y = table(fig, 128, y, cols, rows, 28, shade=(len(rows) - 1,) if len(camps) > 1 else ()) + 40
y = text(fig, 128, y, "The luminosity is that of the lumisections we actually processed (golden JSON), from brilcalc. "
         "Muon and EGamma files cover different lumisections, so each channel has its own luminosity and the "
         "MC is scaled to it.", 28, BODY, width=1664) + 24
if IS2023:
    text(fig, 128, y, "In 2023 each PD is split in two halves (Muon0/Muon1, EGamma0/EGamma1) that share every "
         "lumisection, each half holding about 50% of the events. We use only the first half and count half of "
         "its luminosity.", 28, BODY, width=1664)
footer(fig, FOOT, n)
save(fig)
n += 1

# ------------------------------------------------------------------ MC samples
fig = page()
y = heading(fig, "MC samples") + 40
rows = [["DY→ℓℓ, inclusive (MLL > 50)", "amcatnloFXFX", "6346", "pT(ℓℓ) < 100 GeV"],
        ["DY→ℓℓ, pT(ℓℓ) binned", "amcatnloFXFX", "105 / 11.2 / 0.64 / 0.10", "pT(ℓℓ) > 100 GeV, 4 bins"],
        ["tt̄ → 2ℓ2ν", "powheg", "98.9", "NNLO"],
        [" / ".join(VV_HAVE), "pythia8", " / ".join({"WW": "75.9", "WZ": "27.6", "ZZ": "12.2"}[v] for v in VV_HAVE),
         "inclusive" + ("" if "WW" in VV_HAVE else "; WW not run (too slow to read)")]]
cols = [("Sample", 560, "left"), ("Generator", 260, "left"), ("σ [pb]", 400, "right"), ("Notes", 444, "left")]
y = table(fig, 128, y, rows=rows, cols=cols, size=28) + 40
text(fig, 128, y, "Same samples in all four campaigns (Run3Summer22/22EE/23/23BPix, NanoAODv12), 20 files each. "
     "The DY pT(ℓℓ) samples are stitched as before. DY events are split by the flavour of the leading jet "
     "(hadronFlavour: b, c or light). tt̄ and dibosons are not split.", 28, BODY, width=1664)
footer(fig, FOOT, n)
save(fig)
n += 1

# ------------------------------------------------------------------ corrections
fig = page()
y = heading(fig, "Corrections and weights") + 40
cw = (1664 - 32) / 2
blocks = [("Applied to data and MC", [
              "Jet energy corrections (and resolution smearing in MC), propagated to the MET",
              "Jet veto maps: events with a jet in a vetoed detector region are dropped",
              "Muon and electron energy scale and smearing",
              "Golden JSON for data"]),
          ("MC weights", [
              "Pileup",
              "Lepton ID, isolation and reconstruction SFs",
              "Trigger SF of the leading lepton (IsoMu24, Ele30 tight)",
              "Not yet: b- and c-tag SFs. We do not cut on the tagger yet, so they would not change anything."])]
for i, (title, items) in enumerate(blocks):
    cx = 128 + i * (cw + 32)
    box(fig, cx, y, cw, 520, PANEL)
    yy = text(fig, cx + 40, y + 40, title, 36, ACCENT, "bold", ls=1.2) + 16
    for it in items:
        yy = text(fig, cx + 40, yy, "• " + it, 28, DARK, width=cw - 80, ls=1.4) + 8
y += 520 + 32
text(fig, 128, y, "All corrections come from the official POG files for each campaign. "
     + ("In 2022EE the electron ID SFs are lower (about 0.90–0.94 per electron), as expected after the ECAL endcap issue."
        if "Summer22EE" in camps else ""),
     26, BODY, width=1664)
footer(fig, FOOT, n)
save(fig)
n += 1

# ------------------------------------------------------------------ cutflow data vs MC
fig = page()
y = heading(fig, "Cutflow: data vs MC") + 30
cols = [("", 240, "left")] + [(s, 236, "right") for s in STEPS]
rows, shade = [], []
for ch, chname in CHS.items():
    mc, dat = cutflow(ch)
    rows += [[f"{chname} data"] + [num(v) for v in dat],
             ["MC"] + [num(v) for v in mc],
             ["data / MC"] + [f"{d / m:.2f}" if m else "–" for d, m in zip(dat, mc)]]
    shade.append(len(rows) - 1)
y = table(fig, 128, y, cols, rows, 26, shade=tuple(shade)) + 36
text(fig, 128, y, "MC here is before SFs (generator weight × σ × L / Σw only), so data/MC is expected a few % "
     "below 1 at the lepton steps. The first step only makes sense from the trigger on, since each data PD "
     "is already trigger-selected.", 26, BODY, width=1664)
footer(fig, FOOT + " · events after each step" + (", all campaigns summed" if len(camps) > 1 else ""), n)
save(fig)
n += 1

# ------------------------------------------------------------------ yields
fig = page()
y = heading(fig, "Yields after the full selection") + 40
cols = [("", 180, "left"), ("DY + light", 220, "right"), ("DY + c", 180, "right"), ("DY + b", 180, "right"),
        ("tt̄", 160, "right"), ("VV", 160, "right"), ("MC", 200, "right"), ("Data", 180, "right"),
        ("Data/MC", 204, "right")]
rows = []
for ch, chname in CHS.items():
    v = Y[ch]
    rows.append([chname, num(v["l"]), num(v["c"]), num(v["b"]), num(v["tt"]), num(v["VV"]), num(v["MC"]),
                 num(v["data"]), f"{v['data'] / v['MC']:.3f}"])
y = table(fig, 128, y, cols, rows, 30) + 40
dy = {ch: Y[ch]["l"] + Y[ch]["c"] + Y[ch]["b"] for ch in CHS}
for ch, chname in CHS.items():
    y = text(fig, 128, y, f"{chname}: DY + b is {100 * Y[ch]['b'] / dy[ch]:.1f}% and DY + c is "
             f"{100 * Y[ch]['c'] / dy[ch]:.1f}% of DY (c/b = {Y[ch]['c'] / Y[ch]['b']:.2f}); tt̄ + VV is "
             f"{100 * (Y[ch]['tt'] + Y[ch]['VV']) / Y[ch]['MC']:.1f}% of the MC.", 28, BODY, width=1664) + 12
footer(fig, FOOT + " · MC with all weights" + (" · all campaigns summed" if len(camps) > 1 else ""), n)
save(fig)
n += 1

# ------------------------------------------------------------------ data/MC per campaign
if len(camps) > 1:
    fig = page()
    y = heading(fig, "Data / MC per campaign") + 40
    cols = [("Campaign", 360, "left"), ("Z→μμ data", 260, "right"), ("Z→μμ MC", 260, "right"),
            ("data/MC", 200, "right"), ("Z→ee data", 260, "right"), ("Z→ee MC", 260, "right"),
            ("data/MC", 200, "right")]
    rows = []
    for c in camps:
        m, e = final_yields(c, "Zmm"), final_yields(c, "Zee")
        rows.append([f"{c} ({ERAS[c]})", num(m["data"]), num(m["MC"]), f"{m['data'] / m['MC']:.3f}",
                     num(e["data"]), num(e["MC"]), f"{e['data'] / e['MC']:.3f}"])
    y = table(fig, 128, y, cols, rows, 28) + 40
    text(fig, 128, y, "After the full selection, MC with all weights. Statistical uncertainty on data/MC is about "
         f"{100 / np.sqrt(min(Y['Zee']['data'], Y['Zmm']['data']) / len(camps)):.0f}% or less per entry.",
         28, BODY, width=1664)
    footer(fig, FOOT, n)
    save(fig)
    n += 1

# ------------------------------------------------------------------ plots
PLOTS = [
    ("z_mass", "Dilepton mass", "The Z peak in data and MC. Linear y-axis."),
    ("z_pt", "Dilepton pT", "pT of the Z candidate. No cut on it."),
    ("lep0_pt", "Leading-lepton pT", "Leading lepton, pT > 35 GeV required."),
    ("lep1_pt", "Subleading-lepton pT", "Subleading lepton, pT > 25 GeV required."),
    ("jet_pt", "Leading AK4 jet pT", "Leading lepton-cleaned AK4 jet, pT > 30 GeV required."),
    ("jet_eta", "Leading AK4 jet η", "Pseudorapidity of the leading jet, |η| < 2.5."),
    ("n_jet", "Number of AK4 jets", "Jets with pT > 30 GeV and |η| < 2.5. The last bin holds 5 or more jets."),
    ("jet_PNetB", "PNet b-tag score", "Leading jet. b jets sit near 1, light jets near 0."),
    ("jet_PNetCvL", "PNet charm vs light", "Leading jet."),
    ("jet_PNetCvB", "PNet charm vs b", "Leading jet."),
]
PLOT_FOOT = FOOT + " · Z→ee left, Z→μμ right · band: MC stat. uncertainty"
for name, title, caption in PLOTS:
    fig = page()
    y = heading(fig, title, y=96) + 16
    y = text(fig, 128, y, caption, 28, BODY, width=1664) + 16
    image(fig, os.path.join(indir, "plots", f"{name}.png"), y, hmax=1000 - 12 - y)
    footer(fig, PLOT_FOOT, n)
    save(fig)
    n += 1

# per-campaign grids
if len(camps) > 1:
    for name, title in [("z_mass", "Dilepton mass per campaign"), ("jet_eta", "Leading-jet η per campaign"),
                        ("jet_PNetB", "PNet b-tag score per campaign")]:
        fig = page()
        heading(fig, title, y=72)
        for i, c in enumerate(camps):
            x0, y0 = 128 + (i % 2) * 840, 170 + (i // 2) * 410
            text(fig, x0, y0, f"{c} ({ERAS[c]})", 24, ACCENT, "bold")
            image(fig, f"hists_zbzc_run3/{c}/plots/{name}.png", y0 + 34, x=x0, w=812)
        footer(fig, PLOT_FOOT, n)
        save(fig)
        n += 1

# CvL vs CvB
fig = page()
y = heading(fig, "PNet charm-tagging plane: CvL vs CvB", y=96) + 16
y = text(fig, 128, y, "Leading jets, both channels summed, each panel normalized to unit area. "
         "Data is a mix of all flavours, mostly light.", 28, BODY, width=1664) + 24
image(fig, os.path.join(indir, "plots", "jet_CvL_CvB.png"), y)
footer(fig, FOOT, n)
save(fig)
n += 1

# summary
summ = json.load(open(args.summary)) if args.summary else {
    "title": "Summary (to be written after looking at the results)", "body": "", "next": []}
fig = page()
y = heading(fig, "Summary and next steps") + 40
y = note(fig, y, summ["title"], summ["body"], color="#E8F3EA", bar="#2E7D32", tcolor="#1B5E20", h=300) + 40
for it in summ["next"]:
    y = text(fig, 128, y, "• " + it, 30, DARK, width=1664, ls=1.35) + 12
footer(fig, FOOT, n)
save(fig)

pdf.close()
print("wrote", outfile, f"({n} pages)")
