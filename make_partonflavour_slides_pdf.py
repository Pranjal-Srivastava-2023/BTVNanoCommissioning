"""Short PDF deck explaining how the Zb_Zc_ratio workflow labels jet flavour (hadronFlavour and
partonFlavour), for the group meeting. Follows NOTES_partonFlavour_explained.txt and uses the same
look as make_zbzc_ak4_slides_pdf.py. All percentages are read from the coffea outputs.

Usage:
    python make_partonflavour_slides_pdf.py [hists_zbzc_ak4_20files/merged] [--ref hists_zbzc_ak4_test/test_zbzc_ak4]
writes <indir>/slides_partonflavour_explained.pdf
"""
import argparse
import datetime
import glob
import json
import os
import re
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from coffea.util import load
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch, Polygon

parser = argparse.ArgumentParser()
parser.add_argument("indir", nargs="?", default="hists_zbzc_ak4_20files/merged")
parser.add_argument("--ref", default="hists_zbzc_ak4_test/test_zbzc_ak4", help="1-file AK4 test, for the 92% remark")
parser.add_argument("--date", default=None)
args = parser.parse_args()
outfile = os.path.join(args.indir, "slides_partonflavour_explained.pdf")
DATE = args.date or datetime.date.today().strftime("%-d %B %Y")
WORKFLOW = "src/BTVNanoCommissioning/workflows/Zb_Zc_ratio.py"
TWIKI = "https://twiki.cern.ch/twiki/bin/view/CMSPublic/SWGuideBTagMCTools#Hadron_parton_based_jet_flavour"

# ---------------------------------------------------------------- numbers
xs = json.load(open("metadata/Zb_Zc_ratio_xsections_Summer22.json"))
LUMI = xs["lumi_pb"]
CHS = ["Zee", "Zmm"]
HF, PF = ["b", "c", "l"], ["b", "c", "uds", "g", "none"]


def tables(path):
    """raw[ch][(hf, pf)] from the nevt_migration counter, w[ch][(hf, pf)] from the weighted jet_pt histogram."""
    o = load(glob.glob(os.path.join(path, "*.coffea"))[0])
    raw = {ch: {(f, p): 0.0 for f in HF for p in PF} for ch in CHS}
    w = {ch: {(f, p): 0.0 for f in HF for p in PF} for ch in CHS}
    for ds, od in o.items():
        sc = xs[ds] * LUMI / od["sumw"]
        for ch in CHS:
            for k, v in od["nevt_migration"][ch].items():
                raw[ch][tuple(k.split("|"))] += v
            h = od["jet_pt"][{"channel": ch}]
            for f in HF:
                for p in PF:
                    w[ch][(f, p)] += h[{"flav": f, "pflav": p}].sum(flow=True).value * sc
    for d in (raw, w):
        d["both"] = {k: d["Zee"][k] + d["Zmm"][k] for k in d["Zee"]}
    return raw, w


def row_frac(t, f, p):  # of hadron-flavour-f jets, % with parton flavour p
    return 100 * t[(f, p)] / sum(t[(f, q)] for q in PF)


def col_frac(t, p, f):  # of parton-flavour-p jets, % with hadron flavour f
    return 100 * t[(f, p)] / sum(t[(g, p)] for g in HF)


RAW, WGT = tables(args.indir)
RAW1, WGT1 = tables(args.ref)
B_AGREE, C_AGREE = row_frac(WGT["both"], "b", "b"), row_frac(WGT["both"], "c", "c")

# ---------------------------------------------------------------- layout (same look as the AK4 deck)
W, H = 1920, 1080
DARK, LIGHT, PANEL, ACCENT, BODY, MUTED = "#14213D", "#FBFBF8", "#EEF1F5", "#1F5FA8", "#4A5568", "#6A7179"
GREEN_BG, GREEN, GREEN_TXT = "#E8F3EA", "#2E7D32", "#1B5E20"
AMBER_BG, AMBER, AMBER_TXT = "#FDF3E1", "#B26A00", "#7A4A00"
PX = 72 / 100
plt.rcParams["font.family"] = "DejaVu Sans"
MONO = "DejaVu Sans Mono"
FOOT = "Jet flavour labels · Summer22 DY→ℓℓ MC · 20 files per sample · leading AK4 jet"


def page(bg=LIGHT):
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    fig.patch.set_facecolor(bg)
    return fig


def text(fig, x, y, s, size, color=DARK, weight="normal", ha="left", width=None, family=None, ls=1.4, url=None):
    """Text with its top-left at (x, y) px; wrapped to `width` px. Returns the bottom y."""
    if width:
        s = "\n".join(textwrap.fill(p, max(1, int(width / (0.55 * size)))) for p in s.split("\n"))
    fig.text(x / W, 1 - y / H, s, fontsize=size * PX, color=color, weight=weight, ha=ha, va="top",
             family=family or plt.rcParams["font.family"], linespacing=ls, url=url)
    return y + size * ls * (s.count("\n") + 1)


def box(fig, x, y, w, h, color):
    fig.add_artist(FancyBboxPatch((x / W, 1 - (y + h) / H), w / W, h / H, boxstyle="round,pad=0,rounding_size=0.008",
                                  transform=fig.transFigure, facecolor=color, edgecolor=color, lw=0))


def heading(fig, s, y=110):
    return text(fig, 128, y, s, 60, DARK, "bold", ls=1.15)


def bullets(fig, x, y, items, size=28, width=1664, gap=14, color=DARK):
    for it in items:
        y = text(fig, x, y, "• " + it, size, color, width=width, ls=1.3) + gap
    return y


def panel(fig, x, y, w, h, title, items, size=26):
    box(fig, x, y, w, h, PANEL)
    yy = text(fig, x + 36, y + 28, title, 32, ACCENT, "bold", ls=1.2) + 14
    bullets(fig, x + 36, yy, items, size, w - 72, 10)


def callout(fig, y, h, title, body, kind="green", size=26):
    bg, edge, tc = (GREEN_BG, GREEN, GREEN_TXT) if kind == "green" else (AMBER_BG, AMBER, AMBER_TXT)
    box(fig, 128, y, 1664, h, bg)
    box(fig, 128, y, 6, h, edge)
    yy = text(fig, 168, y + 22, title, 32, tc, "bold", ls=1.2) + 8
    text(fig, 168, yy, body, size, DARK, width=1584, ls=1.35)


def table(fig, x, y, cols, rows, size=28, shade=()):
    """cols: [(header, width px, align)]; rows: list of lists. Returns the bottom y."""
    rh = size * 2.0
    for i, row in enumerate([[c[0] for c in cols]] + rows):
        if i - 1 in shade:
            box(fig, x, y + i * rh, sum(c[1] for c in cols), rh, "#DDE7F3")
        cx = x
        for (hdr, w, al), val in zip(cols, row):
            tx = cx + (w - 12 if al == "right" else w / 2 if al == "center" else 12)
            text(fig, tx, y + i * rh + size * 0.45, str(val), size, DARK, "bold" if i == 0 else "normal", ha=al)
            cx += w
        fig.add_artist(plt.Line2D([x / W, (x + sum(c[1] for c in cols)) / W], [1 - (y + (i + 1) * rh) / H] * 2,
                                  color="#C9D3E3" if i else DARK, lw=1 if i else 2, transform=fig.transFigure))
    return y + (len(rows) + 1) * rh


def code(fig, x, y, w, s, size=22):
    n = s.count("\n") + 1
    h = n * size * 1.35 + 48
    box(fig, x, y, w, h, "#1E2633")
    text(fig, x + 28, y + 24, s, size, "#E6EDF3", family=MONO, ls=1.35)
    return y + h


pdf = PdfPages(outfile)
page_no = [1]


def save(fig):
    if page_no[0] > 1:
        text(fig, 128, 1010, f"{FOOT} · {page_no[0]}", 22, MUTED)
    pdf.savefig(fig)
    plt.close(fig)
    page_no[0] += 1


def blob(ax, cx, cy, r, phase, color):
    t = np.linspace(0, 2 * np.pi, 200)
    rr = r * (1 + 0.13 * np.sin(3 * t + phase) + 0.07 * np.cos(5 * t + 2 * phase))
    ax.add_patch(Polygon(np.c_[cx + rr * np.cos(t), cy + rr * np.sin(t)], closed=True, fc=color, ec="none", alpha=0.5))


def cartoon(fig, x, y, w, h, ghosts, note):
    """Two jets drawn as blobs with real particles (dots) and ghosts (stars). ghosts: [(x, y, label, colour)]."""
    ax = fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")
    rng = np.random.default_rng(3)
    for cx, cy, r, ph, name in [(3.6, 3.0, 2.2, 0.4, "jet 1"), (8.7, 3.1, 1.7, 2.0, "jet 2")]:
        blob(ax, cx, cy, r, ph, "#C9D9EE")
        a, d = rng.uniform(0, 2 * np.pi, 22), r * np.sqrt(rng.uniform(0, 0.75, 22))
        ax.scatter(cx + d * np.cos(a), cy + d * np.sin(a), s=rng.uniform(30, 160, 22), c="#1F5FA8", alpha=0.75, lw=0)
        ax.text(cx, cy + r * 1.22, name, ha="center", va="bottom", fontsize=20 * PX, color=DARK, weight="bold")
    for gx, gy, lab, col in ghosts:
        ax.scatter([gx], [gy], marker="*", s=520, c=col, edgecolors=DARK, lw=1.2, zorder=5)
        ax.text(gx + 0.22, gy - 0.12, lab, fontsize=19 * PX, color=col, weight="bold", va="top", zorder=6)
    ax.scatter([0.4], [0.35], s=90, c="#1F5FA8", lw=0)
    ax.text(0.65, 0.35, "real particle", fontsize=17 * PX, va="center", color=BODY)
    ax.scatter([3.2], [0.35], marker="*", s=260, c="white", edgecolors=DARK, lw=1.2)
    ax.text(3.45, 0.35, "ghost (direction only, energy ≈ 0)", fontsize=17 * PX, va="center", color=BODY)
    ax.text(12, 0.35, note, fontsize=17 * PX, va="center", ha="right", color=MUTED, style="italic")


def pct(v, d=1):
    return f"{v:.{d}f}%"


# ================================================================= 1. cover
fig = page(DARK)
text(fig, 128, 250, "ZB_ZC_RATIO · ANSWERS FROM THE LAST MEETING", 28, "#7FB3E6", "bold")
text(fig, 128, 330, "How we label jet flavour in MC", 88, LIGHT, "bold", width=1664, ls=1.1)
text(fig, 128, 470, "hadronFlavour and partonFlavour: where they come from, what our code does with them, "
     "and where the 99% / 95% on slide 21 comes from", 40, "#C9D3E3", width=1600, ls=1.35)
text(fig, 128, 800, f"Summer22 DY→ℓℓ MC · 20 files per sample · {DATE}", 28, "#C9D3E3")
save(fig)

# ================================================================= 2. the questions + short answers
fig = page()
y = heading(fig, "The questions, and the short answers") + 36
qa = [("Do we calculate partonFlavour ourselves?",
       "No. Every MC jet in NanoAOD already has it (Jet_partonFlavour). We read it as it is."),
      ("Is it the official CMS way?",
       "Yes. CMS fills it with its own tool, the same for every analysis. We don't change any jet's value."),
      ("Did the 99% / 95% on slide 21 come from the TWiki?",
       f"No. We measured it ourselves on our 20-file DY MC ({pct(B_AGREE)} b, {pct(C_AGREE)} c). "
       "The TWiki gives no numbers, only that the two labels disagree \"in rare instances\"."),
      ("Is our b / c / uds / g grouping made up?",
       "No. It follows the standard particle codes and is the same as the official BTV code, "
       "except that we put s together with u and d.")]
for q, a in qa:
    y = text(fig, 128, y, q, 32, ACCENT, "bold", width=1664, ls=1.2) + 6
    y = text(fig, 160, y, a, 28, DARK, width=1630, ls=1.3) + 26
callout(fig, max(y, 790), 150, "Bottom line",
        "The flavour labels are 100% the official CMS ones. The only things that are ours are the grouping "
        "(a relabelling) and the agreement percentage (a measurement).")
save(fig)

# ================================================================= 3. what is jet flavour
fig = page()
y = heading(fig, "What \"jet flavour\" means in simulation") + 30
y = text(fig, 128, y, "A jet starts from one quark or gluon. In data we never know which one. In MC we do, because "
         "the generator remembers every particle it made. CMS uses that to put a \"truth\" label on each MC jet.",
         30, BODY, width=1664, ls=1.35) + 34
cw = (1664 - 32) / 2
panel(fig, 128, y, cw, 400, "Jet_hadronFlavour", [
    "Looks at HADRONS (what a quark turns into: B mesons, D mesons, ...)",
    "Values: 5 = b, 4 = c, 0 = light",
    "What BTV recommends for b and c tagging",
    "All b/c-tag scale factors are measured for it",
    "This is what we use for Z+b / Z+c"])
panel(fig, 128 + cw + 32, y, cw, 400, "Jet_partonFlavour", [
    "Looks at PARTONS (the quarks and gluons themselves)",
    "Values: 5 = b, 4 = c, 1/2/3 = d/u/s, 21 = gluon, 0 = nothing found",
    "Can tell gluon jets from u/d/s jets (hadronFlavour can't)",
    "We only use it as a cross-check"])
y += 400 + 28
callout(fig, y, 130, "Both labels are already in NanoAOD",
        "Same CMS tool, same method. Only the input is different: one looks at hadrons, the other at partons.")
save(fig)

# ================================================================= 4. the ghost trick
fig = page()
y = heading(fig, "Which quarks belong to a jet? The \"ghost\" trick") + 26
y = text(fig, 128, y, "Old way: draw a circle around the jet. Problem: the answer depends on the circle size. "
         "CMS dropped that. The current way has no circle at all:", 28, BODY, width=1664, ls=1.3) + 22
steps = ["Take the generator particles you care about (B/C hadrons, or quarks and gluons)",
         "Make their energy almost zero (×10⁻¹⁸). Direction stays the same. These are the \"ghosts\"",
         "Build the jets again, with the ghosts mixed in with the real particles",
         "See which ghosts ended up inside each jet. Ghosts carry no energy, so the jets don't change"]
sw = (1664 - 3 * 24) / 4
for i, s in enumerate(steps):
    sx = 128 + i * (sw + 24)
    box(fig, sx, y, sw, 250, PANEL)
    text(fig, sx + 26, y + 18, f"Step {i + 1}", 28, ACCENT, "bold")
    text(fig, sx + 26, y + 66, s, 23, DARK, width=sw - 52, ls=1.3)
y += 250 + 10
cartoon(fig, 128, y, 1664, 430,
        [(3.0, 3.6, "b quark ghost", "#C62828"), (3.9, 2.4, "B hadron ghost", "#6A1B9A"),
         (8.9, 2.6, "gluon ghost", "#2E7D32")],
        "cartoon: jet 1 gets hadronFlavour = 5 and partonFlavour = 5; jet 2 gets 0 and 21")
save(fig)

# ================================================================= 5. the rules
fig = page()
y = heading(fig, "The rules: which number a jet gets") + 36
cw = (1664 - 48) / 2
text(fig, 128, y, "hadronFlavour (from hadron ghosts)", 32, ACCENT, "bold")
table(fig, 128, y + 56, [("value", 170, "center"), ("when", cw - 170, "left")],
      [["5  (b)", "at least one B hadron in the jet"],
       ["4  (c)", "a C hadron, but no B hadron"],
       ["0  (light)", "neither"]], size=26)
x2 = 128 + cw + 48
text(fig, x2, y, "partonFlavour (from quark/gluon ghosts)", 32, ACCENT, "bold")
table(fig, x2, y + 56, [("value", 170, "center"), ("when", cw - 170, "left")],
      [["5  (b)", "at least one b quark in the jet"],
       ["4  (c)", "a c quark, but no b quark"],
       ["1, 2, 3", "only d/u/s: the most energetic one wins"],
       ["21  (g)", "same, but the most energetic is a gluon"],
       ["0", "no quark or gluon landed in the jet"]], size=26)
y += 56 + 6 * 52 + 50
y = bullets(fig, 128, y, [
    "A minus sign means antiquark (−5 = anti-b). We drop the sign.",
    "The two labels are worked out separately. Neither is allowed to overwrite the other "
    "(CMS setting hadronFlavourHasPriority = False).",
    "That is why, for a few jets, they can disagree (more on slide 11)."], size=27)
save(fig)

# ================================================================= 6. official sources
fig = page()
y = heading(fig, "Where this is written down officially") + 30
text(fig, 128, y, "1. CMS TWiki: SWGuideBTagMCTools, \"Hadron parton based jet flavour\"", 30, ACCENT, "bold")
text(fig, 128, y + 44, TWIKI, 20, ACCENT, family=MONO, url=TWIKI)
y = bullets(fig, 160, y + 86, [
    "Gives the rules on the previous slide",
    "\"the main use case for the hadron-based flavour is b tagging\"",
    "hadron flavour \"cannot be used to distinguish different types of light-flavour jets\" (that's what "
    "partonFlavour is for)",
    "\"In rare instances a conflict between the hadron- and parton-based flavours can occur\" (no numbers given)"],
    size=25, width=1630, gap=6) + 18
text(fig, 128, y, "2. The CMS software that fills the NanoAOD branch (CMSSW 13_0_X, used for Summer22)", 30, ACCENT, "bold")
y = code(fig, 128, y + 52, 1664,
         "PhysicsTools/NanoAOD/python/jetMC_cff.py\n"
         "    partonFlavour = Var(\"partonFlavour()\", \"int16\", doc=\"flavour from parton matching\")\n"
         "PhysicsTools/PatAlgos/python/mcMatchLayer0/jetFlavourId_cff.py\n"
         "    patJetFlavourAssociation = JetFlavourClustering   (the ghost method)\n"
         "    jetAlgorithm=\"AntiKt\", rParam=0.4, ghostRescaling=1e-18, hadronFlavourHasPriority=False\n"
         "PhysicsTools/PatAlgos/python/producersLayer1/jetProducer_cfi.py\n"
         "    useLegacyJetMCFlavour = False   (old circle method only for heavy-ion running)\n"
         "PhysicsTools/PatAlgos/python/slimming/miniAOD_tools.py + tools/jetTools.py\n"
         "    Run 3 PUPPI jets (slimmedJetsPuppi) get their own copy of the same ghost tool",
         size=21) + 18
text(fig, 128, y, "Heads-up: the doc string says \"parton matching\". That's an old name. The value really "
     "comes from the ghost method.", 25, AMBER_TXT, "bold", width=1664, ls=1.3)
save(fig)

# ================================================================= 7. checked in our own file
fig = page()
y = heading(fig, "Checked directly in one of our input files") + 30
y = text(fig, 128, y, "Summer22 DY NanoAODv12 file used in the run (read with uproot, 2026-10-21):", 28, BODY) + 14
y = code(fig, 128, y, 1664,
         "/store/mc/Run3Summer22NanoAODv12/DYto2L-2Jets_MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/\n"
         "    NANOAODSIM/130X_mcRun3_2022_realistic_v5-v5/120000/02c39db3-e55f-45aa-b3e8-cca8f2fbe820.root\n\n"
         "branch              type     description stored in the file\n"
         "Jet_partonFlavour   int16    \"flavour from parton matching\"\n"
         "Jet_hadronFlavour   uint8    \"flavour from hadron ghost clustering\"\n"
         "nJet                int32    \"slimmedJetsPuppi, i.e. ak4 PFJets Puppi with JECs applied, ...\"\n\n"
         "partonFlavour values seen:  -5 -4 -3 -2 -1  0  1  2  3  4  5  21\n"
         "hadronFlavour values seen:   0  4  5", size=23) + 30
callout(fig, y, 150, "What this tells us",
        "The branches are there, they are filled by CMS, and they only take the values the rules allow. "
        "The jets are PUPPI jets, which (previous slide) use the same ghost tool.")
save(fig)

# ================================================================= 8. what our code does
src = open(WORKFLOW).read()
m = re.search(r"\n(    def jet_flavour\(self, jet\):.*?)\n\n    def fill_jets", src, re.S)
snippet = textwrap.dedent(m.group(1))
snippet = re.sub(r"\n    nb = ak.to_numpy.*?\n    \)\n", "\n    ...  # AK8 jets (nBHadrons / nCHadrons), not used here\n", snippet, flags=re.S)
fig = page()
y = heading(fig, "What our code does with these numbers") + 26
text(fig, 128, y, f"{WORKFLOW}  (exact code, read from the file when making this slide)", 22, MUTED, family=MONO)
code(fig, 128, y + 44, 1000, snippet, size=21)
bullets(fig, 1170, y + 50, [
    "Leading AK4 jet only: pT > 30 GeV, |η| < 2.5, jet ID, ΔR > 0.4 from both leptons",
    "hadronFlavour → b / c / light. This is the label for the Z+b / Z+c result",
    "partonFlavour → drop the sign, then b / c / uds / g / none",
    "No circles, no matching, no thresholds of our own",
    "We never change a jet's value, we only sort it into groups"], size=25, width=620, gap=14)
save(fig)

# ================================================================= 9. is the grouping made up?
fig = page()
y = heading(fig, "Is our grouping made up? No") + 26
y = text(fig, 128, y, "The numbers are standard particle codes (PDG IDs), used by CMS and every generator: "
         "1 = d, 2 = u, 3 = s, 4 = c, 5 = b, 21 = gluon. The official BTVNanoCommissioning code groups them "
         "almost the same way:", 28, BODY, width=1664, ls=1.3) + 18
code(fig, 128, y, 800,
     "# upstream cms-btv-pog master:\n"
     "# utils/histogramming/histograms/qgtag.py\n"
     "def _flavor_label(flav):\n"
     "    absflavs = np.abs(flav)\n"
     "    # 1,2 -> ud   3 -> s   4 -> c\n"
     "    # 5 -> b   21 -> g   else -> other", size=21)
table(fig, 968, y, [("|partonFlavour|", 260, "center"), ("official BTV", 290, "center"), ("ours", 274, "center")],
      [["5", "b", "b"], ["4", "c", "c"], ["1, 2", "ud", "uds"], ["3", "s", "uds"], ["21", "g", "g"],
       ["0", "other", "none"]], size=26, shade=(3,))
y += 7 * 52 + 30
callout(fig, y, 175, "Only difference: s is kept on its own in BTV, merged with u/d by us",
        "The slide-21 numbers only use the b and c groups, which are identical to BTV's. The s merge only "
        "affects the light-jet split (uds vs g). Easy to split back out if we prefer the BTV convention. "
        "Other official workflows (DY_sfl.py, histogrammer.py) also keep partonFlavour = 0 as its own class.")
save(fig)

# ================================================================= 10. our numbers
fig = page()
y = heading(fig, "Our numbers: how often do the two labels agree?") + 24
y = text(fig, 128, y, "Start from the hadronFlavour label (what we use), then ask what partonFlavour says. "
         "Z→ee + Z→μμ, weighted by cross-section (what slide 21 shows).", 27, BODY, width=1664, ls=1.3) + 18
HNAME = {"b": "hadron b", "c": "hadron c", "l": "hadron light"}
rows = [[HNAME[f], f"{sum(RAW['both'][(f, p)] for p in PF):,.0f}"] + [pct(row_frac(WGT["both"], f, p), 2) for p in PF]
        for f in HF]
y = table(fig, 128, y, [("", 250, "left"), ("MC events", 200, "right")] +
          [(f"parton {p}", 242, "right") for p in PF], rows, size=27, shade=(0, 1)) + 26
cw = (1664 - 32) / 2
panel(fig, 128, y, cw, 300, "Checked three ways, all agree", [
    f"Weighted, jet_pt histogram (the slide): b {pct(B_AGREE)}, c {pct(C_AGREE)}",
    f"Plain event count (nevt_migration): b {pct(row_frac(RAW['both'], 'b', 'b'))}, "
    f"c {pct(row_frac(RAW['both'], 'c', 'c'))}",
    f"Per channel, c: Z→ee {pct(row_frac(WGT['Zee'], 'c', 'c'))}, Z→μμ {pct(row_frac(WGT['Zmm'], 'c', 'c'))}"],
      size=25)
panel(fig, 128 + cw + 32, y, cw, 300, "Why the old deck said 92% for c", [
    f"The 1-file-per-sample deck had few events: c came out {pct(row_frac(WGT1['both'], 'c', 'c'))}",
    f"Z→μμ alone was {pct(row_frac(WGT1['Zmm'], 'c', 'c'))}",
    "With 20 files it settles at 95%. Use the 20-file number"], size=25)
save(fig)

# ================================================================= 11. why they disagree + direction
fig = page()
y = heading(fig, "Why the labels can disagree + a warning") + 24
cartoon(fig, 128, y, 1000, 380,
        [(5.3, 3.6, "c quark ghost", "#C62828"), (7.6, 2.3, "C hadron ghost", "#6A1B9A")],
        "jet 1: parton c, hadron light")
bullets(fig, 1170, y + 20, [
    "A quark and the hadron it becomes don't fly in exactly the same direction",
    "Near a jet's edge, the quark ghost can land in one jet and the hadron ghost in the next one "
    "(or in no jet)",
    "Then the labels differ. Normal for the method, not a bug in our code"], size=25, width=620, gap=14)
y += 400
light_c = row_frac(WGT["both"], "l", "c")
rev = col_frac(WGT["both"], "c", "c")
from_light = col_frac(WGT["both"], "c", "l")
callout(fig, y, 270, "Careful: the 95% only works in one direction", (
    f"\"Of jets that hadronFlavour calls c, {pct(C_AGREE, 0)} are partonFlavour c\": yes. "
    f"But \"of jets that partonFlavour calls c, how many are hadronFlavour c?\" gives only {pct(rev, 0)}. "
    f"Reason: {pct(light_c)} of light jets carry a c quark ghost, and light jets are so common that this "
    f"is {pct(from_light, 0)} of all partonFlavour-c jets. (Same for b: "
    f"{pct(col_frac(WGT['both'], 'b', 'b'), 0)} the other way.) The slide wording \"of b jets / of c jets\" "
    "means hadron-flavour jets, so it's correct as written."), kind="amber", size=25)
save(fig)

# ================================================================= 12. summary
fig = page()
y = heading(fig, "Summary") + 40
y = bullets(fig, 128, y, [
    "hadronFlavour and partonFlavour both come straight from NanoAOD. CMS fills them with its "
    "official ghost tool. We don't compute or change them.",
    "We use hadronFlavour for the result, as BTV recommends. partonFlavour is only a cross-check "
    "(and splits light jets into uds vs gluon).",
    "Our grouping is the standard particle codes, same as the official BTV code (except s is merged into uds).",
    f"The {pct(B_AGREE, 0)} (b) and {pct(C_AGREE, 0)} (c) agreement is our own measurement on 20 files/sample. "
    "CMS gives no official number. The TWiki just says disagreements are \"rare\", which fits.",
    "Full write-up: NOTES_partonFlavour_explained.txt in the repo."], size=30, gap=22)
callout(fig, max(y + 10, 760), 170, "Open question for the group",
        "Do we want to split s back out of uds, so the light-jet plots match the BTV convention exactly? "
        "It doesn't change any b or c number.")
save(fig)

pdf.close()
print(f"wrote {outfile} ({page_no[0] - 1} pages)")
