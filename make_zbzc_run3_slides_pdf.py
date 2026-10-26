"""PDF slides for the first Run 3 data/MC look of Zb_Zc_ratio (AK4), same style as
make_zbzc_ak4_slides_pdf.py.

Pages: cover, what is new, data datasets, golden JSON and luminosity, MC samples,
corrections and SFs (files and keys), POG recommendations vs what we do, what
Hsin-Wei's merge brought, cutflow data vs MC per channel, yields by flavour and
process, data/MC per campaign, the data/MC plots of plot_zbzc_run3.py, per-campaign
grids (m(ll), jet eta, PNet B), the CvL-CvB map, and a summary page whose text comes
from --summary (a JSON file with "title", "body" and "next" written after looking at
the results, or a dict of those keyed by campaign). All numbers are read from the
coffea outputs, lumi.json, the fileset JSONs, the run logs and the cvmfs golden JSONs.

Usage:
    python make_zbzc_run3_slides_pdf.py all [--summary summary.json]
writes hists_zbzc_run3/<which>/slides_zbzc_run3_<which>.pdf
"""
import argparse
import datetime
import glob
import json
import os
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

from BTVNanoCommissioning.utils.AK4_parameters import correction_config
from BTVNanoCommissioning.utils.correction import _cvmfs_dir

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
CVMFS = "/cvmfs/cms-griddata.cern.ch/cat/metadata"


def das(c, ds):
    """(primary dataset, processed dataset, tier) from the first file of the fileset JSON."""
    f = FILESET[c][ds][0]
    m = re.search(r"/store/(?:mc|data)/([^/]+)/([^/]+)/([^/]+)/([^/]+)/", f)
    return m.group(2), f"{m.group(1)}-{m.group(4)}", m.group(3)


def lumisections(path):
    d = json.load(open(path))
    return {(int(r), ls) for r, rngs in d.items() for a, b in rngs for ls in range(a, b + 1)}


FILESET, NFAIL, GOLDEN = {}, {}, {}
for c in camps:
    FILESET[c] = json.load(open(f"metadata/Zb_Zc_ratio_run3_{c}.json"))
    # files skipped by the runner (XRootD timeout at validation), from the final per-sample logs
    NFAIL[c] = {}
    for log in glob.glob(f"logs_zbzc_run3/{c}/*.log"):
        tag = os.path.basename(log)[:-4]
        bad = set(re.findall(r"ERROR validating file: (\S+),", open(log, errors="ignore").read()))
        for ds in OUT[c]:
            if ds == tag or ds.startswith(tag + "_TuneCP5"):
                NFAIL[c][ds] = len(bad)
    # golden JSON: load_lumi takes cvmfs Collisions<campaign[-2:]>/latest, else the repo copy
    dc = correction_config[c]["default"]["DC"]
    year = c[6:8]
    latest = f"{CVMFS}/DC/Collisions{year}/latest/{dc}"
    used = f"{CVMFS}/DC/Collisions{c[-2:]}/latest/{dc}"
    if not os.path.exists(used):
        used = f"src/BTVNanoCommissioning/data/DC/{dc}"
    processed = set()
    for ds, o in OUT[c].items():
        if "_Run20" in ds:
            processed |= {(int(r), int(ls)) for r, ls in zip(o["run"].value, o["lumi"].value)}
    GOLDEN[c] = {"file": dc, "cvmfs": used.startswith(CVMFS), "latest": latest,
                 "same_as_latest": lumisections(used) == lumisections(latest),
                 "outside_latest": len(processed - lumisections(latest)), "processed": len(processed)}


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


def wtable(fig, x, y, cols, rows, size=24, colors=None):
    """Table whose cells wrap to the column width; colors maps a cell text to its colour."""
    colors = colors or {}
    lh = size * 1.3
    for i, row in enumerate([[c[0] for c in cols]] + rows):
        cells = [textwrap.fill(str(v), max(1, int((w - 24) / (0.55 * size)))) for (_, w, _a), v in zip(cols, row)]
        nl = max(s.count("\n") + 1 for s in cells)
        cx = x
        for (_, w, _a), s in zip(cols, cells):
            bold = i == 0 or s in colors
            text(fig, cx + 12, y + size * 0.45, s, size, colors.get(s, DARK), "bold" if bold else "normal", ls=1.3)
            cx += w
        y += nl * lh + size * 0.9
        fig.add_artist(plt.Line2D([x / W, (x + sum(c[1] for c in cols)) / W], [1 - y / H] * 2,
                                  color="#C9D3E3" if i else DARK, lw=1 if i else 2, transform=fig.transFigure))
    return y


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
                                      "lepton and trigger SFs, all from the official POG files. "
                                      "Hsin-Wei's latest code merged in.")]
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

# ------------------------------------------------------------------ data
fig = page()
y = heading(fig, "Data used") + 30
rows, skipped = [], []
for c in camps:
    for ds in sorted(d for d in OUT[c] if kind(d).startswith("data")):
        pd_, proc, tier = das(c, ds)
        info = LUMI[c]["datasets"][ds]
        nf = len(set(OUT[c][ds]["fname"]))
        rows.append([f"/{pd_}/{proc}/{tier}", nf, f"{info['nls']:,}", f"{info['brilcalc_pb']:.0f}",
                     f"{info['factor']:g}", f"{info['brilcalc_pb'] * info['factor']:.0f}"])
        if NFAIL[c].get(ds):
            skipped.append(f"{pd_} {proc.split('-')[0]}")
cols = [("Dataset (DAS)", 680, "left"), ("Files", 130, "right"), ("Lumisections", 230, "right"),
        ("brilcalc [pb⁻¹]", 250, "right"), ("Factor", 130, "right"), ("Used [pb⁻¹]", 244, "right")]
y = table(fig, 128, y, cols, rows, 24 if len(rows) <= 6 else 22) + 30
for c in camps:
    y = text(fig, 128, y, f"{c}: Z→μμ {LUMI[c]['Zmm']:.0f} pb⁻¹, Z→ee {LUMI[c]['Zee']:.0f} pb⁻¹", 30, DARK, "bold") + 16
y = text(fig, 128, y, "The 22Sep2023 re-reconstruction in NanoAODv12, 20 files per channel spread over the eras. "
         "Z→μμ comes from the Muon PD (IsoMu24), Z→ee from the EGamma PD (Ele30_WPTight). "
         "Muon and EGamma files cover different lumisections, so each channel has its own luminosity and the "
         "MC is scaled to it.", 26, BODY, width=1664) + 12
if IS2023:
    y = text(fig, 128, y, "In 2023 each PD is split in two halves (Muon0/Muon1, EGamma0/EGamma1) that share every "
             "lumisection, each half holding about 50% of the events. We use only the first half and count half of "
             "its luminosity (factor 0.5).", 26, BODY, width=1664) + 12
if skipped:
    text(fig, 128, y, f"{', '.join(skipped)}: one file timed out when opened and was skipped. Its lumisections are "
         "not counted either, so the luminosity stays consistent.", 26, BODY, width=1664)
footer(fig, FOOT, n)
save(fig)
n += 1

# ------------------------------------------------------------------ golden JSON and lumi
fig = page()
y = heading(fig, "Golden JSON and luminosity") + 40
cw = (1664 - 32) / 2
for c in camps:
    g = GOLDEN[c]
    yr = "20" + c[6:8]
    if g["cvmfs"]:
        where = (f"The official {yr} golden JSON, read from the CMS central area on cvmfs "
                 f"(cms-griddata …/DC/Collisions{c[6:8]}/latest). This is the newest version, after the 2026 "
                 "tracker re-review.")
    else:
        where = ("The framework read its own copy in the repo, not the cvmfs one. It builds the cvmfs path from the "
                 f"last two letters of the campaign name, which does not work for '{c[-2:] if c.endswith('EE') else 'BPix'}'. "
                 "The repo copy is the older version, from before the 2026 tracker re-review.")
    cards = [("GOLDEN JSON", g["file"], where),
             ("LUMINOSITY", "brilcalc, normtag_PHYSICS",
              "Run in the BRIL container on LPC, on exactly the lumisections we processed. Muon and EGamma get "
              "their own numbers.")]
    for i, (lab, big, small) in enumerate(cards):
        cx = 128 + i * (cw + 32)
        box(fig, cx, y, cw, 420, PANEL)
        text(fig, cx + 36, y + 36, lab, 24, ACCENT, "bold")
        yy = text(fig, cx + 36, y + 86, big, 30, DARK, "bold", width=cw - 72, ls=1.25) + 18
        text(fig, cx + 36, yy, small, 26, BODY, width=cw - 72)
    y += 420 + 40
    if not g["same_as_latest"] and not g["outside_latest"]:
        y = note(fig, y, "Checked against the newest golden JSON",
                 f"All {g['processed']:,} processed lumisections are still golden in the newest version, so nothing "
                 "changes here. The framework path will still be fixed before the full run.", h=190) + 30
    elif g["outside_latest"]:
        y = note(fig, y, "Checked against the newest golden JSON",
                 f"{g['outside_latest']} of our {g['processed']:,} processed lumisections "
                 f"({100 * g['outside_latest'] / g['processed']:.2f}%) are no longer golden in the newest version. "
                 "Far too small to change anything here, but the framework path will be fixed before the full run.",
                 h=190) + 30
    else:
        y = note(fig, y, "Checked against the newest golden JSON",
                 f"All {g['processed']:,} processed lumisections are golden in the newest version.",
                 color="#E8F3EA", bar="#2E7D32", tcolor="#1B5E20", h=150) + 30
footer(fig, FOOT, n)
save(fig)
n += 1

# ------------------------------------------------------------------ MC samples
fig = page()
y = heading(fig, "MC samples") + 30
c0 = camps[0]
rows, notrun, skipped = [], [], []
for ds in FILESET[c0]:
    if "_Run20" in ds:
        continue
    pd_, proc, tier = das(c0, ds)
    short, gen = ds.split("_TuneCP5")[0], ds.split("13p6TeV_")[-1]
    if ds not in OUT[c0]:
        notrun.append(short)
        rows.append([short, gen, proc.split("-", 1)[1], f"{XS[ds]:.4g}", "not run"])
        continue
    nf = 20 - NFAIL[c0].get(ds, 0)
    if nf < 20:
        skipped.append(short)
    rows.append([short, gen, proc.split("-", 1)[1], f"{XS[ds]:.4g}", f"{nf} / {len(FILESET[c0][ds])}"])
cols = [("Sample", 440, "left"), ("Generator", 300, "left"), (f"{proc.split('-')[0]}-…", 600, "left"),
        ("σ [pb]", 150, "right"), ("Files", 174, "right")]
y = table(fig, 128, y, rows=rows, cols=cols, size=20) + 30
msg = (f"Full DAS name: /<sample>_TuneCP5_13p6TeV_<generator>/{proc.split('-')[0]}-<processing>/{tier}. Files: used / available. "
       "The DY pT(ℓℓ) samples are stitched: each binned sample keeps only its own LHE pT(ℓℓ) slice and the "
       "inclusive one covers pT(ℓℓ) < 100 GeV. DY events are split by the hadron flavour of the leading jet "
       "(b, c or light). tt̄ and dibosons are not split. Cross sections as in the MC-only study.")
if skipped:
    msg += (f" {', '.join(skipped)}: one file timed out when opened and was skipped; the normalisation uses the "
            "files that were read.")
if notrun:
    msg += f" {', '.join(notrun)} not run here (too slow to read from remote sites)."
text(fig, 128, y, msg, 24, BODY, width=1664)
footer(fig, FOOT, n)
save(fig)
n += 1

# ------------------------------------------------------------------ corrections
conf = correction_config[c0]["default"]
JEC, JER = conf["JME"]["MC"].split()
JETVETO = next(iter(conf["jetveto"]))
EGM_ERA = next(k for k in conf["EGM"] if k.startswith("ele_ID")).split()[1]
PU_KEY = next(iter(correctionlib.CorrectionSet.from_file(
    f"{CVMFS}/LUM/{_cvmfs_dir(c0, 'LUM')}/latest/puWeights.json.gz").keys()))
fig = page()
y = heading(fig, "Corrections and scale factors") + 30
rows = [["Jet energy corrections", "data + MC", "JME jet_jerc", f"{JEC} (data: with residuals)"],
        ["Jet energy resolution", "MC", "JME jet_jerc, jer_smear", JER],
        ["MET", "data + MC", "from the corrected jets", "type-1 PuppiMET"],
        ["Jet veto map", "data + MC", "JME jetvetomaps", JETVETO],
        ["Muon momentum scale and resolution", "data + MC", "MUO muon_scalesmearing", "Run 3 recipe"],
        ["Electron energy scale / smearing", "data / MC", "EGM electronSS_EtDependent", "Scale / SmearAndSyst"],
        ["Pileup weight", "MC", "LUM puWeights", PU_KEY],
        ["Muon ID and isolation SF", "MC", "MUO muon_Z", "NUM_TightID_DEN_TrackerMuons, NUM_TightPFIso_DEN_TightID"],
        ["Muon trigger SF (leading muon)", "MC", "MUO muon_Z", "NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight"],
        ["Electron ID and reco SF", "MC", "EGM electron", f"Electron-ID-SF: Tight and Reco ({EGM_ERA})"],
        ["Electron trigger SF (leading electron)", "MC", "EGM electronHlt", "HLT_SF_Ele30_TightID"],
        ["b- and c-tag SF", "MC", "BTV btagging, ctagging", "not applied yet (no tag cut)"]]
cols = [("Correction", 470, "left"), ("Applied to", 190, "left"), ("POG file", 400, "left"),
        ("Key / tag", 604, "left")]
y = wtable(fig, 128, y, cols, rows, 20) + 16
text(fig, 128, y, f"Every file is the official one on cvmfs: {CVMFS}/<POG>/{_cvmfs_dir(c0, 'JME')}/latest/. "
     "The framework uses them for all BTV workflows."
     + (" In 2022EE the electron ID SFs are lower (about 0.90–0.94 per electron), as expected after the ECAL "
        "endcap issue." if c0 == "Summer22EE" else ""), 20, BODY, width=1664)
footer(fig, FOOT, n)
save(fig)
n += 1

# ------------------------------------------------------------------ POG recommendations vs us
STATUS = {"Same": "#2E7D32", "Differs": "#C0561B", "Simplified": "#B7791F", "Not yet": MUTED, "Check": "#C0561B"}
g = GOLDEN[c0]
POG_PAGES = [
    ("Data and jets", [
        ["Golden JSON (DC)", "Use the latest golden JSON",
         "Latest version from cvmfs" if g["cvmfs"] else
         "Older repo copy (path bug, see the golden JSON page); " +
         (f"{g['outside_latest']} of our lumisections affected" if g["outside_latest"] else
          "none of our lumisections affected"), "Same" if g["cvmfs"] else "Differs"],
        ["Luminosity (LUM)", "brilcalc with normtag_PHYSICS", "Same, on the lumisections we processed", "Same"],
        ["Pileup (LUM)", "Official pileup weights", "Same file", "Same"],
        ["Jet energy corrections (JME)", f"{JEC}, resolution {JER}", "Same tags", "Same"],
        ["Jet ID (JME)", "Tight lepton veto ID; the NanoAODv12 jetId branch needs the JME fix", "Fix applied",
         "Same"],
        ["Jet veto map (JME)", "Veto the event if a jet with pT > 15 GeV, tight ID, EM fraction < 0.9 and away "
         "from muons falls in the map", "Framework vetoes on any jet in the map. Drops about 6% of Z→μμ events "
         "instead of 1–2%; data/MC moves by 0.3% or less", "Differs"],
        ["Rare high-pT jets (JME)", "Reject jets with rawFactor > 0.9 (known JEC issue)",
         "Not applied. About 1 event in a million, mostly forward, outside |η| < 2.5", "Not yet"]]),
    ("Leptons and tagging", [
        ["Muon ID and isolation (MUO)", "Tight ID, PF isolation < 0.15 (Tight), SFs from muon_Z", "As recommended", "Same"],
        ["Muon trigger SF (MUO)", "IsoMu24 SF per muon (Tight ID + Tight iso)",
         "Leading muon only (pT > 35 GeV, on the plateau). Effect of using both muons not checked yet", "Simplified"],
        ["Electron ID and reco (EGM)", "Cut-based Tight ID, SFs for the 22Sep2023 re-reco", "As recommended", "Same"],
        ["Electron trigger SF (EGM)", "HLT_SF_Ele30_TightID per electron",
         "Leading electron only. Using both electrons raises the Z→ee MC by 1.1–1.9% (quick estimate)",
         "Simplified"],
        ["Lepton energy scale (EGM, MUO)", "Scale in data, smearing in MC",
         "Same files and recipe. The Z→ee peak is 1.5–4% wider in MC than in data (all four campaigns), to be "
         "understood", "Check"],
        ["b/c tagging (BTV)", "AK4 PUPPI, pT > 20, |η| < 2.5, tight ID, hadronFlavour. PNet b: fixed-WP and shape "
         "SFs; PNet c: fixed-WP SFs only", "pT > 30, |η| < 2.5, tight ID, hadronFlavour. No tag SFs yet "
         "(no tag cut)", "Not yet"],
        ["L1 prefiring", "No prefiring weight in Run 3", "None", "Same"]]),
]
for i, (sub, rows) in enumerate(POG_PAGES):
    fig = page()
    y = heading(fig, f"POG recommendations vs what we do ({i + 1}/2)") + 12
    y = text(fig, 128, y, sub, 30, ACCENT, "bold") + 16
    cols = [("Topic", 330, "left"), ("POG recommendation", 560, "left"), ("What we do", 590, "left"),
            ("Status", 184, "left")]
    y = wtable(fig, 128, y, cols, rows, 21, colors=STATUS) + 20
    if i == 0:
        text(fig, 128, y, "Read on 26 October 2026: BTV scale factor page, MUO usage recommendations, JME jet energy "
             "scale page, EGamma Run 3 TWiki (last edited 2023, older than the cvmfs files we use). Jet veto recipe "
             "from the JME jet veto map recommendation. The 6% and 1–2% are quick estimates on one chunk.",
             20, MUTED, width=1664)
    else:
        text(fig, 128, y, "c-tagging has no shape SFs for 2022/2023, only fixed working points. A template fit in "
             "the CvL–CvB plane needs a plan for that. UParT SFs exist only for NanoAODv15.", 22, BODY, width=1664)
    footer(fig, FOOT, n)
    save(fig)
    n += 1

# ------------------------------------------------------------------ Hsin-Wei's merge
fig = page()
y = heading(fig, "What Hsin-Wei's update brought") + 30
y = text(fig, 128, y, "We merged her latest coffea_machine branch (5 commits, up to 1 October) into ours on "
         "26 October, before this run.", 28, BODY, width=1664) + 20
cw = (1664 - 2 * 32) / 3
cards = [("FIXED FOR EVERYONE", "Electron SFs with two electrons",
          "The shared electron SF code used to keep only the last electron's SF. Her fix multiplies the SFs of "
          "all electrons. We had worked around it by calling it once per electron, so our numbers do not change, "
          "but the common code is now right."),
         ("SAFER", "Empty lepton slots",
          "The SF code now fills empty lepton slots before calling the POG files. The 2023 reco SFs also need the "
          "electron φ, and that path is now protected too."),
         ("TO REUSE", "Matched electron trigger SF",
          "Her Run 2 electron trigger SF takes the electron that fired the trigger, matched to the HLT object. "
          "That is the right way to do it, and we plan to bring it to Run 3 instead of using the leading electron.")]
for i, (lab, big, small) in enumerate(cards):
    cx = 128 + i * (cw + 32)
    box(fig, cx, y, cw, 420, PANEL)
    text(fig, cx + 36, y + 36, lab, 22, ACCENT, "bold")
    yy = text(fig, cx + 36, y + 84, big, 32, DARK, "bold", width=cw - 72, ls=1.2) + 18
    text(fig, cx + 36, yy, small, 24, BODY, width=cw - 72)
y += 420 + 24
note(fig, y, "Bottom line",
     "Her Run 2 electron SF files and settings do not touch the Run 3 inputs, and both branches now share one "
     "correction code. Where files clashed we kept our validated Run 2 selection. One thing to tell her: in the "
     "muon SF code the trigger-SF pT clip gets overwritten (we do not use that path).",
     color="#E8F3EA", bar="#2E7D32", tcolor="#1B5E20", h=190)
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
text(fig, 128, y, "Data/MC only means something from the two-lepton step on. At the trigger step the data are "
     "mostly single-lepton events (W→ℓν, multijet) that fire the same trigger but are not simulated: we only "
     "have DY, tt̄ and VV. The two-lepton cut keeps 2–5% of the triggered data but 30–40% of the MC, and "
     "data/MC drops from about 10 to about 1. MC here is before SFs (generator weight × σ × L / Σw only), "
     "so data/MC is expected a few % off 1 at the lepton steps.", 24, BODY, width=1664)
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
summ = summ.get(args.which, summ)
fig = page()
y = heading(fig, "Summary and next steps") + 40
y = note(fig, y, summ["title"], summ["body"], color="#E8F3EA", bar="#2E7D32", tcolor="#1B5E20", h=300) + 40
for it in summ["next"]:
    y = text(fig, 128, y, "• " + it, 30, DARK, width=1664, ls=1.35) + 12
footer(fig, FOOT, n)
save(fig)

pdf.close()
print("wrote", outfile, f"({n} pages)")
