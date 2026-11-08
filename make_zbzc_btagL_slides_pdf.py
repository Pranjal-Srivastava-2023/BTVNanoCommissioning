"""Deck: Summer22 Z + b-tagged leading jet at the Loose working point, for three taggers (PNet, DeepJet,
RobustParT), each with its own BTV SFs, with all of the 2026-11-08 changes (muon trigger SF from both muons,
muon pT > 26, MET without the MET cut up to 200 GeV, zoomed plots, one legend order). Like the 237-page deck,
but only the Loose b-tag regions and the most important plots (user, 2026-11-08).

Numbers are parsed from hists_zbzc_run3_v2/Summer22/yields.txt and yields_<region>.txt; working points from
the BTV Summer22 correctionlib files.

Usage:  python make_zbzc_btagL_slides_pdf.py [--date "8 November 2026"]
Output: hists_zbzc_run3_v2/Summer22/slides_zbzc_btagL_3taggers_Summer22.pdf
"""
import argparse
import datetime
import os
import re
import textwrap

import correctionlib
import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch

parser = argparse.ArgumentParser()
parser.add_argument("--date", default=None)
args = parser.parse_args()
DATE = args.date or datetime.date.today().strftime("%-d %B %Y")
D = "hists_zbzc_run3_v2/Summer22"
OUT = f"{D}/slides_zbzc_btagL_3taggers_Summer22.pdf"
TAGGERS = {"PNet": ("btag_L", "particleNet", "PNet B"), "DeepJet": ("btagDeepJet_L", "deepJet", "DeepJet B"),
           "RobustParT": ("btagRobustParT_L", "robustParticleTransformer", "RobustParT B")}
CHS = {"Zee": "Z→ee", "Zmm": "Z→μμ"}

# ------------------------------------------------------------------ inputs
def read_yields(fn):
    """{channel: dict(l, c, b, tt, VV, mc, mce, data)} from the hadronFlavour section,
    and {channel: {dataset: (n_b, SF_b, n_c, SF_c, n_l, SF_l, n_tag, n_both) or (n_tag, n_both) for data}}."""
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


INCL, _ = read_yields(f"{D}/yields.txt")
Y, SF = {}, {}
for t, (reg, _, _) in TAGGERS.items():
    Y[t], SF[t] = read_yields(f"{D}/yields_{reg}.txt")
    assert set(Y[t]) == set(CHS) and all(len(SF[t][c]) == 11 for c in CHS), (t, Y[t].keys(), {c: len(SF[t][c]) for c in SF[t]})
BTV = "/cvmfs/cms-griddata.cern.ch/cat/metadata/BTV/Run3-22CDSep23-Summer22-NanoAODv12/latest"
CB = correctionlib.CorrectionSet.from_file(f"{BTV}/btagging.json.gz")
WP = {t: CB[f"{c}_wp_values"].evaluate(wp) for t, (_, c, _) in TAGGERS.items() for wp in ["L"]}
WPALL = {(t, wp): CB[f"{c}_wp_values"].evaluate(wp) for t, (_, c, _) in TAGGERS.items() for wp in "LMT"}


def nums(t, ch):
    y, i = Y[t][ch], INCL[ch]
    r = y["data"] / y["mc"]
    re_ = r * np.hypot(y["data"] ** -0.5, y["mce"] / y["mc"])
    effd, effm = y["data"] / i["data"], y["mc"] / i["mc"]
    er = effd / effm
    ere = er * np.hypot(np.sqrt(effd * (1 - effd) / i["data"]) / effd, y["mce"] / y["mc"])
    sh = {k: y[k] / y["mc"] for k in ("b", "c", "l", "tt", "VV")}
    return dict(r=r, re=re_, effd=effd, effm=effm, er=er, ere=ere, **sh)


def mean_sf(t):
    """Mean SF of the tagged leading jet per hadron flavour, DY MC of both channels, weighted by raw counts;
    overlap = fraction of b-tagged jets that also pass the c-tag at the same WP (DY MC raw, data Zmm)."""
    nb = sb = nc = sc = nl = sl = ntag = nboth = 0.0
    for ch in CHS:
        for ds, v in SF[t][ch].items():
            if ds.startswith("DY"):
                nb += v[0]; sb += v[0] * v[1]; nc += v[2]; sc += v[2] * v[3]; nl += v[4]; sl += v[4] * v[5]
                ntag += v[6]; nboth += v[7]
    dt = sum(v[0] for ds, v in SF[t]["Zmm"].items() if ds.startswith("Muon"))
    db = sum(v[1] for ds, v in SF[t]["Zmm"].items() if ds.startswith("Muon"))
    return sb / nb, sc / nc, sl / nl, nboth / ntag, db / dt


# ------------------------------------------------------------------ layout (as make_zbzc_tag_slides_pdf.py)
W, H = 1920, 1080
DARK, LIGHT, ACCENT, BODY, MUTED = "#14213D", "#FBFBF8", "#1F5FA8", "#4A5568", "#6A7179"
GOOD = ("#E8F3EA", "#2E7D32", "#1B5E20")
OPEN = ("#FDF1E4", "#E07B24", DARK)
PX = 72 / 100
plt.rcParams["font.family"] = "DejaVu Sans"
FOOT = "Summer22 (2022 C–D), 13.6 TeV · Z→ℓℓ + ≥1 jet, leading jet b-tagged (Loose) · 20 files per sample · stat. errors only"


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


def table(fig, x, y, cols, rows, size=24):
    rh = size * 1.9
    for i, r in enumerate([[c[0] for c in cols]] + rows):
        cx = x
        for (hdr, w, al), val in zip(cols, r):
            tx = cx + (w - 12 if al == "right" else 12)
            text(fig, tx, y + i * rh + size * 0.45, str(val), size, DARK, "bold" if i == 0 else "normal", ha=al)
            cx += w
        fig.add_artist(plt.Line2D([x / W, (x + sum(c[1] for c in cols)) / W], [1 - (y + (i + 1) * rh) / H] * 2,
                                  color="#C9D3E3" if i else DARK, lw=1 if i else 2, transform=fig.transFigure))
    return y + (len(rows) + 1) * rh


def pct(x):
    return f"{100 * x:.0f}%"


# (file, title, caption); the tagger's own B score is added per section
TWOJ = "Events with at least 2 jets."
ZOOM = "Zoom: linear scale, ratio 0.8–1.2."
VARS = [
    ("z_mass", "Dilepton mass", "71 < m(ℓℓ) < 111 GeV, linear scale."),
    ("z_pt", "Z pT", "pT of the lepton pair."),
    ("z_pt_zoom", "Z pT, 0–200 GeV", ZOOM),
    ("z_eta", "Z η", ""),
    ("lep0_pt", "Leading-lepton pT", "Leading lepton pT > 35 GeV."),
    ("lep0_eta", "Leading-lepton η", ""),
    ("lep1_pt", "Second-lepton pT", "Second lepton pT > 25 GeV (electrons), > 26 GeV (muons, new: trigger SF range)."),
    ("lep1_eta", "Second-lepton η", ""),
    ("n_jet", "Number of jets", "AK4 jets with pT > 30 GeV, |η| < 2.5, away from the leptons."),
    ("jet_pt", "Leading-jet pT", "The b-tagged jet."),
    ("jet_pt_zoom", "Leading-jet pT, 30–200 GeV", ZOOM),
    ("jet_eta", "Leading-jet η", ""),
    ("jet1_pt", "Second-jet pT", TWOJ),
    ("m_jj", "Dijet mass", TWOJ),
    ("dphi_zj", "Δφ(Z, leading jet)", ""),
    ("pt_balance", "pT balance: leading-jet pT / Z pT", ""),
    ("met_pt_nm1", "PUPPI MET without the MET cut, up to 200 GeV", "All other cuts applied; the selection cuts at 50 GeV."),
    ("npv", "Number of good primary vertices", "After pileup weights."),
]
SEC_LEN = 1 + len(VARS) + 1  # section page, plots, own B score
N_INTRO = 4
START = {t: N_INTRO + 1 + i * SEC_LEN for i, t in enumerate(TAGGERS)}
for t, (reg, _, _) in TAGGERS.items():
    for v, _, _ in VARS + [(f"jet_{t}B", "", "")]:
        assert os.path.exists(f"{D}/plots_{reg}/{v}.png"), (reg, v)

pdf = PdfPages(OUT)
n = 0


def save(fig, foot=True):
    global n
    n += 1
    if foot:
        text(fig, 128, 1035, f"{FOOT} · {n}", 19, MUTED)
    pdf.savefig(fig)
    plt.close(fig)


# ------------------------------------------------------------------ cover
fig = page(DARK)
text(fig, 128, 300, "Z + b-tagged jet in Summer22: three taggers at the Loose working point", 62, "white", "bold", width=1650, ls=1.15)
text(fig, 128, 520, "ParticleNet, DeepJet and RobustParT, each with its own BTV SFs. All POG corrections, "
     "including the muon changes of 8 November.", 32, "#C9D3E3", width=1600)
text(fig, 128, 860, DATE, 26, "#C9D3E3")
save(fig, foot=False)

# ------------------------------------------------------------------ contents
fig = page()
y = heading(fig, "Contents", f"Selection: Z→ee or Z→μμ + at least 1 jet, leading jet b-tagged at Loose. "
            f"Every tagger has the same {len(VARS) + 1} plots in the same order.") + 30
rows = [["What is applied, working points", "3"], ["Yields and tagging SFs for the three taggers", "4"]]
for t in TAGGERS:
    rows.append([f"{t} Loose b-tag (B > {WP[t]:.4g})", f"{START[t]}–{START[t] + SEC_LEN - 1}"])
rows.append(["Summary", str(N_INTRO + len(TAGGERS) * SEC_LEN + 1)])
table(fig, 128, y, [("section", 1400, "left"), ("pages", 264, "right")], rows, 26)
save(fig)

# ------------------------------------------------------------------ what is applied
fig = page()
y = heading(fig, "What goes into these plots") + 26
y = note(fig, y, "Corrections and SFs (POG recipes)",
         "Jets: JEC, JER, jet veto map, type-1 PUPPI MET. Leptons: scale and smearing (muons: the Run 3 replacement of "
         "Rochester), ID, isolation and reco SFs, trigger SFs. Events: golden JSON, pileup weights, MET filters. "
         "DY Z pT weights off.", h=170) + 22
y = note(fig, y, "New since the 237-page deck (8 November)",
         "Muon trigger SF from both muons (IsoMu24 fires if either muon fires) and both muons pT > 26 GeV: Z→μμ "
         f"data/MC {INCL['Zmm']['data'] / INCL['Zmm']['mc']:.3f}, Z→ee {INCL['Zee']['data'] / INCL['Zee']['mc']:.3f}. "
         "MET shown without the MET cut up to 200 GeV, zoomed plots, same legend order in both channels.", h=170) + 22
rows = [[t, f"{WPALL[(t, 'L')]:.4g}", f"{WPALL[(t, 'M')]:.4g}", f"{WPALL[(t, 'T')]:.4g}",
         f"{TAGGERS[t][1]}_comb (b, c), {TAGGERS[t][1]}_light"] for t in TAGGERS]
y = table(fig, 128, y, [("tagger", 260, "left"), ("Loose", 170, "right"), ("Medium", 170, "right"), ("Tight", 170, "right"),
                        ("SFs (BTV, fixed WP)", 894, "left")], rows, 23) + 8
text(fig, 128, y, "B-score cut on the leading jet. Only Loose is shown in this deck. In MC the tagged jet gets the SF "
     "for its true flavour.", 21, MUTED, width=1664)
save(fig)

# ------------------------------------------------------------------ yields + SFs
fig = page()
y = heading(fig, "Yields and tagging SFs for the three taggers",
            "Flavour shares are of all MC (DY + tt + VV). Tagged = fraction of Z + jet events with a tagged leading jet. "
            "Tag ratio = tagged in data / tagged in MC (the overall normalisation cancels).") + 20
rows = []
for ch, lab in CHS.items():
    i = INCL[ch]
    rows.append([f"no tag, {lab}", f"{i['data'] / i['mc']:.3f}", pct(i["b"] / i["mc"]), pct(i["c"] / i["mc"]),
                 pct(i["l"] / i["mc"]), "–", "–", "–"])
for t in TAGGERS:
    for ch, lab in CHS.items():
        x = nums(t, ch)
        rows.append([f"{t}, {lab}", f"{x['r']:.3f} ± {x['re']:.3f}", pct(x["b"]), pct(x["c"]), pct(x["l"]),
                     f"{100 * x['effm']:.1f}%", f"{100 * x['effd']:.1f}%", f"{x['er']:.3f} ± {x['ere']:.3f}"])
y = table(fig, 128, y, [("", 330, "left"), ("data/MC", 230, "right"), ("DY+b", 130, "right"), ("DY+c", 130, "right"),
                        ("DY+light", 160, "right"), ("tagged MC", 200, "right"), ("tagged data", 210, "right"),
                        ("tag ratio", 274, "right")], rows, 22) + 22
rows = []
for t in TAGGERS:
    b, c, l, ov, ovd = mean_sf(t)
    rows.append([t, f"{b:.2f}", f"{c:.2f}", f"{l:.2f}", pct(ov), pct(ovd)])
y = table(fig, 128, y, [("mean SF of the tagged jet (DY MC)", 560, "left"), ("b jets", 180, "right"), ("c jets", 180, "right"),
                        ("light jets", 200, "right"), ("also c-tag L, MC", 270, "right"), ("also c-tag L, data μμ", 274, "right")],
          rows, 22) + 10
text(fig, 128, y, "Mean SF weighted by the number of tagged DY MC jets of each flavour, both channels.", 20, MUTED)
save(fig)


# ------------------------------------------------------------------ one section per tagger
def plot_page(t, title, var, vtitle, caption):
    fig = page()
    text(fig, 128, 40, title, 26, ACCENT, "bold")
    y = text(fig, 128, 78, vtitle, 46, DARK, "bold", ls=1.15)
    if caption:
        y = text(fig, 128, y + 4, caption, 23, BODY, width=1664)
    top = max(y + 12, 185)
    image(fig, f"{D}/plots_{TAGGERS[t][0]}/{var}.png", top, hmax=1010 - top)
    save(fig)


for t in TAGGERS:
    title = f"{t} Loose b-tag ({TAGGERS[t][2]} > {WP[t]:.4g})"
    fig = page(DARK)
    text(fig, 128, 200, f"{t}, Loose b-tag", 72, "white", "bold")
    text(fig, 128, 330, f"Leading jet {TAGGERS[t][2]} > {WP[t]:.4g}, with the {TAGGERS[t][1]} BTV SFs", 32, "#C9D3E3", width=1600)
    hdr = ["", "data/MC", "DY+b", "DY+c", "DY+light", "tt", "tagged MC", "tagged data"]
    xs = [128, 420, 720, 880, 1040, 1230, 1370, 1600]
    for x, h in zip(xs, hdr):
        text(fig, x, 470, h, 26, "#C9D3E3", "bold")
    for k, (ch, lab) in enumerate(CHS.items()):
        v = nums(t, ch)
        vals = (lab, f"{v['r']:.3f} ± {v['re']:.3f}", pct(v["b"]), pct(v["c"]), pct(v["l"]), pct(v["tt"]),
                f"{100 * v['effm']:.1f}%", f"{100 * v['effd']:.1f}%")
        for x, val in zip(xs, vals):
            text(fig, x, 530 + k * 60, val, 28, "white")
    text(fig, 128, 720, "Flavour shares are of all MC. Tagged = fraction of Z + jet events with a tagged leading jet. "
         "Errors are statistical only.", 22, "#C9D3E3", width=1600)
    text(fig, 128, 800, f"{len(VARS) + 1} plots follow. Left Z→ee, right Z→μμ.", 22, "#C9D3E3", width=1600)
    save(fig)
    for var, vtitle, caption in VARS:
        plot_page(t, title, var, vtitle, caption)
    plot_page(t, title, f"jet_{t}B", f"Leading-jet {TAGGERS[t][2]} score", f"Only jets above {WP[t]:.4g} enter this region.")

# ------------------------------------------------------------------ summary
fig = page()
y = heading(fig, "Summary") + 30
pur = {t: (nums(t, "Zee")["b"], nums(t, "Zmm")["b"]) for t in TAGGERS}
y = note(fig, y, "All three taggers select a similar sample at Loose.",
         "DY+b share of all MC: " + ", ".join(f"{t} {pct(a)} / {pct(b)}" for t, (a, b) in pur.items()) + " (Z→ee / Z→μμ). "
         "About 1 in 6 Z + jet events has a Loose b-tagged leading jet; most of them are still c or light jets.", h=150) + 26
er = {t: (nums(t, "Zee"), nums(t, "Zmm")) for t in TAGGERS}
pulls = [abs(x["er"] - 1) / x["ere"] for a, b in er.values() for x in (a, b)]
y = note(fig, y, "Data and MC tag the same fraction of jets " + ("within the stat. errors." if max(pulls) < 2 else "within a few percent."),
         "Tag ratio (data / MC): " + "; ".join(f"{t} {a['er']:.3f} ± {a['ere']:.3f} / {b['er']:.3f} ± {b['ere']:.3f}"
                                             for t, (a, b) in er.items()) + " (Z→ee / Z→μμ).",
         style=GOOD if max(pulls) < 2 else OPEN, h=150) + 26
ls = [mean_sf(t)[2] for t in TAGGERS]
y = note(fig, y, f"Light jets are mistagged more in data than in MC (mean light SF {min(ls):.2f}–{max(ls):.2f}).",
         "The SFs take care of it; the SF uncertainties are not in these plots yet.", style=OPEN, h=120) + 26
note(fig, y, "Not included yet",
     "SF up/down uncertainties, the loose tau veto, the full dataset (these are 20 files per sample).", style=OPEN, h=110)
save(fig)

pdf.close()
print("wrote", OUT, f"({n} pages)")
