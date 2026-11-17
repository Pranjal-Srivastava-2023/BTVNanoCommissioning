"""Shared pieces of the Summer22 Z + b/c decks of 2026-11-08 (make_zbzc_followup_pdf.py,
make_zbzc_btagL_slides_pdf.py): slide layout helpers, parsers of the run's output tables, and the
analysis-setup and "how to read" slides. Facts on the setup slides are taken from
workflows/Zb_Zc_ratio.py, utils/selection.py, utils/AK4_parameters.py (Summer22) and the jsonPOG files.
"""
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
from matplotlib.patches import FancyBboxPatch

# run directory of the deck (ZBZC_DECK_DIR, default: the 2026-11-08 run)
D = os.environ.get("ZBZC_DECK_DIR", "hists_zbzc_run3_v2/Summer22")
# selection / weights shown on the setup slides; a deck script may change these before setup_slides()
SETUP = dict(mu_pt=26, mu_eta=2.4, zpt=False, tau=False)
# optional keys (MET deck, 2026-11-16): met_xy=True (JME PuppiMET XY correction), jer="both" (JER on/off runs)
W, H = 1920, 1080
DARK, LIGHT, ACCENT, BODY, MUTED = "#14213D", "#FBFBF8", "#1F5FA8", "#3B4450", "#6A7179"
GOOD = ("#E8F3EA", "#2E7D32", "#1B5E20")
OPEN = ("#FDF1E4", "#E07B24", "#7A3E00")
INFO = ("#EEF2F8", "#1F5FA8", DARK)
PX = 72 / 100
plt.rcParams["font.family"] = "DejaVu Sans"
TAGGER_CL = {"PNet": "particleNet", "DeepJet": "deepJet", "RobustParT": "robustParticleTransformer"}
CHS = {"Zee": "Z→ee", "Zmm": "Z→μμ"}


# ZBZC_PPTX=1: Deck writes an editable .pptx (same file name, .pptx) instead of the PDF. Every layout helper
# below also records what it draws in fig._ops; Deck.save turns those into PowerPoint shapes (text boxes, tables,
# rounded boxes, pictures). Upload the .pptx to Google Drive and "Open with Google Slides" to edit it there.
PPTX = os.environ.get("ZBZC_PPTX", "0") == "1"
# ZBZC_CLEAN=1 (user request 2026-11-17): drop the zoomed-plot pages, "Analysis setup 1/2", "Contents" and
# "How to read the numbers"; the remaining setup page loses its "2/2"; page numbers stay continuous.
CLEAN = os.environ.get("ZBZC_CLEAN", "0") == "1"
DROP_TITLES = ("Contents", "Analysis setup 1/2", "How to read the numbers")


def dropped(fig):
    """True if CLEAN removes this page: title in DROP_TITLES, or 'zoom' in the title or subtitle."""
    t = [o[3] for o in getattr(fig, "_ops", None) or [] if o[0] == "text"][:2]
    return CLEAN and bool(t) and (t[0].startswith(DROP_TITLES) or any(re.search(r"\bzoom\b", s) for s in t))


def _rec(fig, *op):
    if getattr(fig, "_ops", None) is not None and not getattr(fig, "_mute", False):
        fig._ops.append(op)


# ------------------------------------------------------------------ layout
def page(bg=LIGHT):
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    fig.patch.set_facecolor(bg)
    fig._ops, fig._bg = [], bg
    return fig


def wrap(s, size, width, bold=False, indent=""):
    n = max(1, int(width / ((0.60 if bold else 0.53) * size)))
    out = []
    for p in s.split("\n"):
        out.append(textwrap.fill(p, n, subsequent_indent=indent) if p else "")
    return "\n".join(out)


def text(fig, x, y, s, size, color=DARK, weight="normal", ha="left", width=None, ls=1.35, indent=""):
    raw = s
    if width:
        s = wrap(s, size, width, weight == "bold", indent)
    _rec(fig, "text", x, y, raw, size, color, weight, ha, width, ls, indent, s.count("\n") + 1)
    fig.text(x / W, 1 - y / H, s, fontsize=size * PX, color=color, weight=weight, ha=ha, va="top", linespacing=ls, zorder=3)
    return y + size * ls * (s.count("\n") + 1)


def box(fig, x, y, w, h, color):
    _rec(fig, "box", x, y, w, h, color)
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
    _rec(fig, "image", path, x, y, w, h)
    ax = fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])
    ax.imshow(img, interpolation="none")
    ax.axis("off")
    return y + h


def table(fig, x, y, cols, rows, size=22, bold_rows=(), shade_rows=()):
    _rec(fig, "table", x, y, cols, rows, size, tuple(bold_rows), tuple(shade_rows))
    fig._mute = True  # the cells below are drawn for the PDF only; the .pptx gets one real table
    try:
        return _table(fig, x, y, cols, rows, size, bold_rows, shade_rows)
    finally:
        fig._mute = False


def _table(fig, x, y, cols, rows, size, bold_rows, shade_rows):
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
        self.n, self.foot = 0, foot
        if PPTX:
            from pptx import Presentation
            self.out = re.sub(r"\.pdf$", "", out) + ".pptx"
            self.prs = Presentation()
            self.prs.slide_width, self.prs.slide_height = W * EMU, H * EMU
        else:
            from matplotlib.backends.backend_pdf import PdfPages
            self.pdf, self.out = PdfPages(out), out

    def save(self, fig, foot=True):
        if dropped(fig):
            self.n_dropped = getattr(self, "n_dropped", 0) + 1
            plt.close(fig)
            return
        self.n += 1
        if foot:
            text(fig, 110, 1040, f"{self.foot} · page {self.n}", 18, MUTED)
        if PPTX:
            pptx_slide(self.prs, fig)
        else:
            self.pdf.savefig(fig)
        plt.close(fig)

    def close(self):
        if PPTX:
            self.prs.save(self.out)
        else:
            self.pdf.close()
        print("wrote", self.out, f"({self.n} pages" + (f", {self.n_dropped} dropped by ZBZC_CLEAN)" if CLEAN else ")"))


# ------------------------------------------------------------------ .pptx backend (ZBZC_PPTX=1)
EMU = 6350          # 1920 px canvas -> 13.333 in slide (12192000 EMU)
PT = 0.5            # canvas font size -> PowerPoint pt (size * 0.72 pt on 19.2 in == size * 0.5 pt on 13.33 in)
FONT = "Arial"      # narrower than DejaVu Sans, so text never needs more lines than in the PDF


def _rgb(c):
    from pptx.dml.color import RGBColor
    return RGBColor.from_string(matplotlib.colors.to_hex(c).lstrip("#").upper())  # also named colours ("white")


def _para(p, s, size, color, bold, ha, ls, indent):
    from pptx.enum.text import PP_ALIGN
    from pptx.util import Pt
    p.alignment = {"left": PP_ALIGN.LEFT, "right": PP_ALIGN.RIGHT, "center": PP_ALIGN.CENTER}[ha]
    p.line_spacing = ls / 1.2
    if indent:  # hanging indent for "• " bullets
        m = int(0.65 * size * EMU)
        pPr = p._p.get_or_add_pPr()
        pPr.set("marL", str(m))
        pPr.set("indent", str(-m))
    r = p.add_run()
    r.text = s
    f = r.font
    f.name, f.size, f.bold, f.color.rgb = FONT, Pt(size * PT), bold, _rgb(color)


def _textbox(slide, x, y, w, h, lines, size, color, bold, ha, ls, indent, wrapw):
    from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE
    tb = slide.shapes.add_textbox(int(x * EMU), int(y * EMU), int(w * EMU), int(h * EMU))
    tf = tb.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.word_wrap, tf.auto_size, tf.vertical_anchor = wrapw, MSO_AUTO_SIZE.NONE, MSO_ANCHOR.TOP
    for i, s in enumerate(lines):
        _para(tf.paragraphs[0] if i == 0 else tf.add_paragraph(), s, size, color, bold, ha, ls, indent)
    return tb


def _op_text(slide, x, y, s, size, color, weight, ha, width, ls, indent, nlines):
    h = size * ls * nlines
    if width:
        w = width
    else:
        w = max(len(l) for l in s.split("\n")) * 0.62 * size + size
    x0 = x if ha == "left" else (x - w if ha == "right" else x - w / 2)
    _textbox(slide, x0, y, w, h, s.split("\n"), size, color, weight == "bold", ha, ls, indent, bool(width))


def _op_box(slide, x, y, w, h, color):
    from pptx.enum.shapes import MSO_SHAPE
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, int(x * EMU), int(y * EMU), int(w * EMU), int(h * EMU))
    sh.adjustments[0] = min(0.5, 10 / max(1, min(w, h)))
    sh.fill.solid()
    sh.fill.fore_color.rgb = _rgb(color)
    sh.line.fill.background()
    sh.shadow.inherit = False


def _op_image(slide, path, x, y, w, h):
    slide.shapes.add_picture(path, int(x * EMU), int(y * EMU), int(w * EMU), int(h * EMU))


def _op_table(slide, x, y, cols, rows, size, bold_rows, shade_rows):
    from lxml import etree
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.oxml.ns import qn
    from pptx.util import Pt
    rh = size * 1.85
    tw = sum(c[1] for c in cols)
    allrows = [[c[0] for c in cols]] + rows
    gf = slide.shapes.add_table(len(allrows), len(cols), int(x * EMU), int(y * EMU), int(tw * EMU),
                                int(rh * len(allrows) * EMU))
    tbl = gf.table
    tblPr = tbl._tbl.tblPr
    tblPr.set("firstRow", "0")
    tblPr.set("bandRow", "0")
    sid = tblPr.find(qn("a:tableStyleId"))
    if sid is None:
        sid = etree.SubElement(tblPr, qn("a:tableStyleId"))
    sid.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"  # "No Style, No Grid"
    for j, c in enumerate(cols):
        tbl.columns[j].width = int(c[1] * EMU)
    for i, r in enumerate(allrows):
        tbl.rows[i].height = int(rh * EMU)
        for j, ((hdr, w, al), val) in enumerate(zip(cols, r)):
            cell = tbl.cell(i, j)
            cell.margin_left = cell.margin_right = int(10 * EMU)
            cell.margin_top = cell.margin_bottom = 0
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.alignment = {"left": PP_ALIGN.LEFT, "right": PP_ALIGN.RIGHT, "center": PP_ALIGN.CENTER}[al]
            run = p.add_run()
            run.text = str(val)
            f = run.font
            f.name, f.size, f.color.rgb = FONT, Pt(size * PT), _rgb(DARK)
            f.bold = i == 0 or (i - 1) in bold_rows
            # tcPr: thin rule under each row (dark under the header), then the fill (schema order lnB before fill)
            tcPr = cell._tc.get_or_add_tcPr()
            for child in list(tcPr):
                tcPr.remove(child)
            for tag in ("a:lnL", "a:lnR", "a:lnT"):
                ln = etree.SubElement(tcPr, qn(tag), w="0")
                etree.SubElement(ln, qn("a:noFill"))
            ln = etree.SubElement(tcPr, qn("a:lnB"), w=str((2 if i == 0 else 1) * 12700))
            sf = etree.SubElement(ln, qn("a:solidFill"))
            etree.SubElement(sf, qn("a:srgbClr"), val=(DARK if i == 0 else "#C9D3E3").lstrip("#").upper())
            if i >= 1 and (i - 1) in shade_rows:
                sf = etree.SubElement(tcPr, qn("a:solidFill"))
                etree.SubElement(sf, qn("a:srgbClr"), val="EAF1FB")
            else:
                etree.SubElement(tcPr, qn("a:noFill"))


_ZORDER = {"box": 0, "image": 0, "table": 2, "text": 3}


def pptx_slide(prs, fig):
    """One slide from the shapes recorded by the layout helpers on fig."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = _rgb(fig._bg)
    for op in sorted(fig._ops, key=lambda o: _ZORDER[o[0]]):
        {"text": _op_text, "box": _op_box, "image": _op_image, "table": _op_table}[op[0]](slide, *op[1:])


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
        f"Muons: pT > {SETUP['mu_pt']:g} GeV, |η| < {SETUP['mu_eta']:g}, Tight ID, PF isolation (ΔR = 0.4) < 0.15 (Tight).",
    ])
    y = bullets(fig, xr, y + 14, cw, "Z + jet selection (applied in this order)", [
        "Trigger fired; two leptons of the channel, leading lepton pT > 35 GeV; opposite charge; 71 < m(ℓℓ) < 111 GeV.",
    ] + ([
        "Loose hadronic τ veto (both channels): no τh with pT > 20 GeV, |η| < 2.5, |dz| < 0.2 cm, decay mode 0/1/10/11, "
        "DeepTau 2018v2p5 VSjet ≥ Loose, VSe ≥ VVLoose, VSμ ≥ VLoose, ΔR > 0.4 from the leptons. No τ SFs.",
    ] if SETUP["tau"] else []) + [
        "Missing transverse momentum (type-1 PUPPI MET) < 50 GeV, to remove tt̄.",
        "At least one AK4 jet (PUPPI): pT > 30 GeV, |η| < 2.5, Tight-lepton-veto ID (with the NanoAODv12 fix), "
        "ΔR > 0.4 from the leptons. The leading jet is the one we study and tag.",
    ])
    deck.save(fig)

    fig = page()
    top = heading(fig, ("Analysis setup" if CLEAN else "Analysis setup 2/2") + ": corrections, scale factors, b/c tagging",
                  "All corrections from the CMS jsonPOG files (/cvmfs/cms-griddata.cern.ch/cat/metadata), Summer22 versions.") + 10
    y = bullets(fig, xl, top, cw, "Jets and MET", [
        "Jet energy corrections Summer22_22Sep2023_V4 (data per run era and MC); jet energy resolution smearing "
        "Summer22_22Sep2023_JRV2 (MC)" + (" in the nominal run; switched off in the second run of this deck (the test)."
                                          if SETUP.get("jer") == "both" else
                                          ". Run A: all jets smeared (nominal). Run B: no smearing, neither the jets nor the "
                                          "MET. Run C: jets smeared as in A, but in the type-1 MET only gen-matched jets are "
                                          "smeared." if SETUP.get("jer") == "abc" else "."),
        "Type-1 PUPPI MET recomputed with the corrected jets.",
    ] + ([
        "PUPPI MET XY correction (JME met_xyCorrections_2022, epoch 2022, data and MC versions): removes the "
        "φ modulation of the MET; shifts MET by about 1 GeV.",
    ] if SETUP.get("met_xy") else []) + [
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
    ] + ([
        "DY Z pT weights (not a POG correction): DY MC reweighted in bins of reconstructed pT(ℓℓ), weights from Z→μμ "
        "data/MC before the MET and jet cuts, total DY yield unchanged; applied in both channels.",
        "Not applied: L1 prefiring weight (not needed in Run 3).",
    ] if SETUP["zpt"] else [
        "Not applied: L1 prefiring weight (not needed in Run 3), DY Z pT reweighting (switched off).",
    ]))
    y = bullets(fig, xr, y + 14, cw, "b and c tagging (leading jet only)", [
        "Taggers: ParticleNet, DeepJet, RobustParT. Official BTV Summer22 Loose/Medium/Tight working points.",
        "b-tag: B score > cut. c-tag: CvL > cut and CvB > cut. b-tag and c-tag are separate selections.",
        "MC: the tagged jet is weighted by the BTV SF for its true flavour (b-tag: _comb for b and c, _light for light; "
        "c-tag: _wc for c, _tnp for b, _light for light). Outside the SF range the SF at the edge is used.",
    ])
    y = bullets(fig, xr, y + 14, cw, "Uncertainties and software", [
        "Statistical only (data and MC). All SFs are applied with their central values; their uncertainties and the other "
        "systematic uncertainties are not included yet.",
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
