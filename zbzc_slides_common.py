"""Shared pieces of the Summer22 Z + b/c decks of 2026-11-08 (make_zbzc_followup_pdf.py,
make_zbzc_btagL_slides_pdf.py): slide layout helpers, parsers of the run's output tables, and the
analysis-setup and "how to read" slides. Facts on the setup slides are taken from
workflows/Zb_Zc_ratio.py, utils/selection.py, utils/AK4_parameters.py (Summer22) and the jsonPOG files.
"""
import json
import re
import textwrap

import correctionlib
import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

D = "hists_zbzc_run3_v2/Summer22"
W, H = 1920, 1080
DARK, LIGHT, ACCENT, BODY, MUTED = "#14213D", "#FBFBF8", "#1F5FA8", "#3B4450", "#6A7179"
GOOD = ("#E8F3EA", "#2E7D32", "#1B5E20")
OPEN = ("#FDF1E4", "#E07B24", "#7A3E00")
INFO = ("#EEF2F8", "#1F5FA8", DARK)
PX = 72 / 100
plt.rcParams["font.family"] = "DejaVu Sans"
TAGGER_CL = {"PNet": "particleNet", "DeepJet": "deepJet", "RobustParT": "robustParticleTransformer"}
CHS = {"Zee": "Z→ee", "Zmm": "Z→μμ"}


# ------------------------------------------------------------------ layout
def page(bg=LIGHT):
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    fig.patch.set_facecolor(bg)
    return fig


def wrap(s, size, width, bold=False, indent=""):
    n = max(1, int(width / ((0.60 if bold else 0.53) * size)))
    out = []
    for p in s.split("\n"):
        out.append(textwrap.fill(p, n, subsequent_indent=indent) if p else "")
    return "\n".join(out)


def text(fig, x, y, s, size, color=DARK, weight="normal", ha="left", width=None, ls=1.35, indent=""):
    if width:
        s = wrap(s, size, width, weight == "bold", indent)
    fig.text(x / W, 1 - y / H, s, fontsize=size * PX, color=color, weight=weight, ha=ha, va="top", linespacing=ls, zorder=3)
    return y + size * ls * (s.count("\n") + 1)


def box(fig, x, y, w, h, color):
    fig.add_artist(FancyBboxPatch((x / W, 1 - (y + h) / H), w / W, h / H, boxstyle="round,pad=0,rounding_size=0.008",
                                  transform=fig.transFigure, facecolor=color, edgecolor=color, lw=0, zorder=0))


def heading(fig, s, sub=None):
    y = text(fig, 110, 50, s, 48, DARK, "bold", ls=1.15, width=1700)
    if sub:
        y = text(fig, 110, y + 8, sub, 24, BODY, width=1700)
    return y + 10


def note(fig, y, title, body="", style=GOOD, x=110, w=1700, size=23):
    """Coloured box sized to its text; returns the y below it."""
    color, bar, tcolor = style
    yy = y + 16
    if title:
        yy = text(fig, x + 36, yy, title, size + 4, tcolor, "bold", width=w - 72, ls=1.2) + 4
    if body:
        yy = text(fig, x + 36, yy, body, size, DARK, width=w - 72, ls=1.32)
    h = yy - y + 14
    box(fig, x, y, w, h, color)
    box(fig, x, y, 6, h, bar)
    return y + h


def note_height(title, body="", w=1700, size=23):
    """Height note() will use, so a plot can be sized to leave room for it."""
    h = 16
    if title:
        h += (size + 4) * 1.2 * (wrap(title, size + 4, w - 72, True).count("\n") + 1) + 4
    if body:
        h += size * 1.32 * (wrap(body, size, w - 72).count("\n") + 1)
    return h + 14


def bullets(fig, x, y, w, title, items, size=20, tcolor=ACCENT):
    """A titled block of bullet points (wrapped with a hanging indent)."""
    if title:
        y = text(fig, x, y, title, size + 3, tcolor, "bold", ls=1.2) + 4
    for it in items:
        y = text(fig, x, y, "• " + it, size, DARK, width=w, indent="   ", ls=1.28) + 5
    return y


def image(fig, path, y, x=110, w=1700, hmax=None):
    img = mpimg.imread(path)
    h = w * img.shape[0] / img.shape[1]
    if hmax and h > hmax:
        w2 = hmax * img.shape[1] / img.shape[0]
        x, w, h = x + (w - w2) / 2, w2, hmax
    ax = fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])
    ax.imshow(img, interpolation="none")
    ax.axis("off")
    return y + h


def table(fig, x, y, cols, rows, size=22, bold_rows=(), shade_rows=()):
    rh = size * 1.85
    tw = sum(c[1] for c in cols)
    for i in shade_rows:
        box(fig, x, y + (i + 1) * rh + 2, tw, rh - 4, "#EAF1FB")
    for i, r in enumerate([[c[0] for c in cols]] + rows):
        cx = x
        for (hdr, w, al), val in zip(cols, r):
            tx = cx + (w - 10 if al == "right" else 10)
            text(fig, tx, y + i * rh + size * 0.42, str(val), size, DARK,
                 "bold" if i == 0 or (i - 1) in bold_rows else "normal", ha=al)
            cx += w
        fig.add_artist(plt.Line2D([x / W, (x + tw) / W], [1 - (y + (i + 1) * rh) / H] * 2,
                                  color="#C9D3E3" if i else DARK, lw=1 if i else 2, transform=fig.transFigure))
    return y + (len(rows) + 1) * rh


class Deck:
    def __init__(self, out, foot):
        from matplotlib.backends.backend_pdf import PdfPages
        self.pdf, self.n, self.foot, self.out = PdfPages(out), 0, foot, out

    def save(self, fig, foot=True):
        self.n += 1
        if foot:
            text(fig, 110, 1040, f"{self.foot} · page {self.n}", 18, MUTED)
        self.pdf.savefig(fig)
        plt.close(fig)

    def close(self):
        self.pdf.close()
        print("wrote", self.out, f"({self.n} pages)")


def f3(r, e):
    return f"{r:.3f} ± {e:.3f}"


# ------------------------------------------------------------------ inputs of the run
def read_yields(fn):
    """hadronFlavour section {ch: dict(l, c, b, tt, VV, mc, mce, data)} and the tag-SF section
    {ch: {dataset: (n_b, SF_b, n_c, SF_c, n_l, SF_l, n_tag, n_both)  |  data: (n_tag, n_both)}}."""
    lines = open(fn).read().splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith("== hadronFlavour"))
    fl = {}
    for k in range(i + 2, len(lines)):
        if lines[k].startswith("=="):
            break
        p = lines[k].split()
        if p and p[0] in CHS:
            e = lines[k + 1].split()
            fl[p[0]] = dict(l=float(p[1]), c=float(p[2]), b=float(p[3]), tt=float(p[4]), VV=float(p[5]),
                            mc=float(p[6]), mce=float(e[6]), data=float(p[7]))
    sf, ch = {}, None
    for l in lines:
        m = re.match(r"-- Summer22 (Zee|Zmm)$", l.strip())
        if m:
            ch = m.group(1)
            sf[ch] = {}
            continue
        p = l.split()
        if ch and len(p) == 9 and not p[0].startswith("dataset"):
            sf[ch][p[0]] = tuple(map(float, p[1:]))
        elif ch and len(p) == 6 and p[0].startswith(("Muon", "EGamma")):
            sf[ch][p[0]] = (float(p[4]), float(p[5]))
    return fl, sf


def read_muvar():
    """{(stage, variant): dict(data, mc, r, re, vsnom, slope, slope_err)} and
    {(stage, variant): [(r, e)] for leading-muon |eta| 0-0.8, 0.8-1.2, 1.2-2.0, 2.0-2.4}."""
    muv, eta, stage, eta_mode = {}, {}, None, False
    row = re.compile(r"^(\w+)\s+.*?\s(\d+)\s+([\d.]+)\s+([\d.]+)\+-([\d.]+)\s+([+-][\d.]+)%\s+([+-][\d.]+)\+-\s*([\d.]+)")
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
                muv[(stage, g[0])] = dict(data=int(g[1]), mc=float(g[2]), r=int(g[1]) / float(g[2]), re=float(g[4]),
                                          vsnom=float(g[5]), slope=float(g[6]), slope_err=float(g[7]))
        else:
            p = line.split()
            if p and stage and len(p) == 5 and "+-" in p[1]:
                eta[(stage, p[0])] = [tuple(map(float, c.split("+-"))) for c in p[1:]]
    assert len(muv) == 22 and len(eta) == 22, (len(muv), len(eta))
    return muv, eta


def read_tags():
    """{(channel, kind, tagger, wp): dict(...)} from tagger_summary.txt."""
    tags, ch = {}, None
    for line in open(f"{D}/tagger_summary.txt"):
        m = re.match(r"== (\w+):", line)
        if m:
            ch = m.group(1)
        m = re.match(r"^(btag|ctag) (\w+) ([LMT])\s+(\d+)\s+([\d.]+)\s+([\d.]+)\+-([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)"
                     r"\s+([\d.]+)\s+([\d.]+)\+-([\d.]+)", line)
        if m:
            g = m.groups()
            tags[(ch, g[0], g[1], g[2])] = dict(data=int(g[3]), mc=float(g[4]), r=float(g[5]), re=float(g[6]), bfrac=float(g[7]),
                                                cfrac=float(g[8]), effd=float(g[9]), effm=float(g[10]), er=float(g[11]), ere=float(g[12]))
    assert len(tags) == 36, len(tags)
    return tags


def read_pu():
    pu = json.load(open(f"{D}/pu/pu_profiles.json"))
    shift, ch = {}, None
    for line in open(f"{D}/pu/pu_closure.txt"):
        m = re.match(r"== (\w+):", line)
        if m:
            ch = m.group(1)
        m = re.search(r"data - MC mean N\(PV\) = ([+-][\d.]+); expected .* x dN\(PV\)/dnTrueInt ([\d.]+) = ([+-][\d.]+)$", line.strip())
        if m:
            shift[ch] = (float(m.group(1)), float(m.group(3)), float(m.group(2)))
    assert set(shift) == {"Zee", "Zmm"}
    return pu, shift


def working_points():
    btv = "/cvmfs/cms-griddata.cern.ch/cat/metadata/BTV/Run3-22CDSep23-Summer22-NanoAODv12/latest"
    cb, cc = (correctionlib.CorrectionSet.from_file(f"{btv}/{k}tagging.json.gz") for k in "bc")
    return {(t, wp): (cb[f"{c}_wp_values"].evaluate(wp), cc[f"{c}_wp_values"].evaluate(wp, "CvL"),
                      cc[f"{c}_wp_values"].evaluate(wp, "CvB")) for t, c in TAGGER_CL.items() for wp in "LMT"}


def lumi():
    return json.load(open("hists_zbzc_run3/Summer22/lumi.json"))


# ------------------------------------------------------------------ shared slides
def setup_slides(deck):
    """Two slides with everything the analysis uses (Summer22, as run on 2026-11-08)."""
    L = lumi()
    fig = page()
    top = heading(fig, "Analysis setup 1/2: data, simulation, event selection") + 10
    xl, xr, cw = 110, 1000, 820
    y = bullets(fig, xl, top, cw, "Data", [
        "2022 runs C–D, EGamma and Muon datasets, 22Sep2023 reprocessing, NanoAODv12.",
        "Certified lumisections only (golden JSON Cert_Collisions2022_355100_362760).",
        f"Test sample: 20 files per channel = {L['Zee']:.0f} pb⁻¹ (ee) and {L['Zmm']:.0f} pb⁻¹ (μμ), "
        "measured with brilcalc (normtag_PHYSICS) on the lumisections actually read.",
    ])
    y = bullets(fig, xl, y + 14, cw, "Simulation (Run3Summer22, NanoAODv12)", [
        "Drell–Yan: DYto2L-2Jets, MadGraph5_aMC@NLO with FxFx merging (0, 1, 2 partons at NLO), m(ℓℓ) > 50 GeV. "
        "Inclusive sample used for generator pT(ℓℓ) < 100 GeV, pT(ℓℓ)-binned samples above (100–200, 200–400, 400–600, > 600).",
        "Backgrounds: tt̄ → 2ℓ2ν (POWHEG), WW, WZ, ZZ (Pythia8).",
        "Each sample scaled to cross section × luminosity / sum of generator weights. 20 files per sample.",
    ])
    y = bullets(fig, xl, y + 14, cw, "Jet flavour in MC", [
        "Leading jet's hadronFlavour: b (a B hadron in the jet), c (a C hadron, no B), light (neither).",
    ])
    y = bullets(fig, xr, top, cw, "Triggers", [
        "Z→ee: HLT_Ele30_WPTight_Gsf.   Z→μμ: HLT_IsoMu24.",
    ])
    y = bullets(fig, xr, y + 14, cw, "Leptons", [
        "Electrons: pT > 25 GeV, |η| < 2.4, cut-based Tight ID, barrel–endcap gap 1.442 < |η_SC| < 1.566 removed, "
        "impact parameter |dxy| < 0.05 (0.1) cm and |dz| < 0.1 (0.2) cm in the barrel (endcap).",
        "Muons: pT > 26 GeV, |η| < 2.4, Tight ID, PF isolation (ΔR = 0.4) < 0.15 (Tight).",
    ])
    y = bullets(fig, xr, y + 14, cw, "Z + jet selection (applied in this order)", [
        "Trigger fired; two leptons of the channel, leading lepton pT > 35 GeV; opposite charge; 71 < m(ℓℓ) < 111 GeV.",
        "Missing transverse momentum (type-1 PUPPI MET) < 50 GeV, to remove tt̄.",
        "At least one AK4 jet (PUPPI): pT > 30 GeV, |η| < 2.5, Tight-lepton-veto ID (with the NanoAODv12 fix), "
        "ΔR > 0.4 from the leptons. The leading jet is the one we study and tag.",
    ])
    deck.save(fig)

    fig = page()
    top = heading(fig, "Analysis setup 2/2: corrections, scale factors, b/c tagging",
                  "All corrections from the CMS jsonPOG files (/cvmfs/cms-griddata.cern.ch/cat/metadata), Summer22 versions.") + 10
    y = bullets(fig, xl, top, cw, "Jets and MET", [
        "Jet energy corrections Summer22_22Sep2023_V4 (data per run era and MC); jet energy resolution smearing "
        "Summer22_22Sep2023_JRV2 (MC).",
        "Type-1 PUPPI MET recomputed with the corrected jets.",
        "Jet veto map Summer22_23Sep2023_RunCD_V1: event dropped if a jet (pT > 15 GeV, tight ID, EM fraction < 0.9, no muon "
        "nearby) is in a vetoed region.",
    ])
    y = bullets(fig, xl, y + 14, cw, "Leptons", [
        "Electron energy scale (data) and smearing (MC), EGM.",
        "Muon momentum scale (data) and smearing (MC), MUO. In Run 3 this replaces the Rochester correction.",
    ])
    y = bullets(fig, xl, y + 14, cw, "Event cleaning", [
        "MET filters in data and MC: goodVertices, globalSuperTightHalo2016, EcalDeadCellTriggerPrimitive, BadPFMuon, "
        "BadPFMuonDz, hfNoisyHits, eeBadSc.",
    ])
    y = bullets(fig, xr, top, cw, "Event weights in MC", [
        "Pileup: LUM puWeights.json.gz (2022 C–D golden profile, 69.2 mb).",
        "Electrons: reconstruction and Tight ID SFs (EGM 2022 Re-reco BCD).",
        "Muons: Tight ID SF (NUM_TightID_DEN_TrackerMuons) and Tight isolation SF (NUM_TightPFIso_DEN_TightID), MUO.",
        "Trigger: either lepton can fire, so SF = [1 − (1−ε¹data)(1−ε²data)] / [1 − (1−ε¹MC)(1−ε²MC)] with the POG "
        "data and MC efficiencies of both leptons (EGM Ele30 Tight ID; MUO IsoMu24 for Tight ID + Tight isolation).",
        "Not applied: L1 prefiring weight (not needed in Run 3), DY Z pT reweighting (switched off).",
    ])
    y = bullets(fig, xr, y + 14, cw, "b and c tagging (leading jet only)", [
        "Taggers: ParticleNet, DeepJet, RobustParT. Official BTV Summer22 Loose/Medium/Tight working points.",
        "b-tag: B score > cut. c-tag: CvL > cut and CvB > cut. b-tag and c-tag are separate selections.",
        "MC: the tagged jet is weighted by the BTV SF for its true flavour (b-tag: _comb for b and c, _light for light; "
        "c-tag: _wc for c, _tnp for b, _light for light). Outside the SF range the SF at the edge is used.",
    ])
    y = bullets(fig, xr, y + 14, cw, "Uncertainties and software", [
        "Statistical only (data and MC). No systematic or SF uncertainties yet.",
        "coffea 0.7, BTVNanoCommissioning (Zb_Zc_ratio workflow), correctionlib.",
    ])
    deck.save(fig)


def reading_slide(deck, extra=()):
    fig = page()
    y = heading(fig, "How to read the numbers in these slides") + 16
    rows = [
        ("Z selection", "Trigger, two leptons, opposite charge, 71 < m(ℓℓ) < 111 GeV. No jet or MET requirement."),
        ("Full selection", "Z selection + MET < 50 GeV + at least one jet. All plots use this unless stated."),
        ("data/MC", "Data events divided by the MC prediction (all corrections and weights). 1 = perfect agreement."),
        ("Shape", "data/MC in one range divided by the overall data/MC: the normalisation is taken out, only the shape is left."),
        ("Slope", "Straight-line fit of data/MC versus pT, quoted in % per 100 GeV."),
    ] + list(extra) + [
        ("Errors", "Statistical only (data and MC). Only 20 files per sample, so small differences are not significant."),
    ]
    for k, v in rows:
        text(fig, 110, y, k, 24, ACCENT, "bold")
        y = text(fig, 470, y, v, 24, DARK, width=1340) + 22
    deck.save(fig)
