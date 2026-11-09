"""Deck: Summer22 Z + b-tagged leading jet at the Loose working point for three taggers (ParticleNet, DeepJet,
RobustParT), each with its own BTV SFs, with all of the 2026-11-08 changes. Like the 237-page deck but only the
Loose b-tag regions; all kinematic plots of each tagger with an explanation on every page, plus the analysis
setup slides (user, 2026-11-08: self-explanatory slides, more kinematic plots).

Numbers are parsed from hists_zbzc_run3_v2/Summer22/yields.txt and yields_<region>.txt; working points from
the BTV Summer22 correctionlib files. Layout and setup slides: zbzc_slides_common.py.

Usage:  python make_zbzc_btagL_slides_pdf.py [--date "8 November 2026"]
Output: hists_zbzc_run3_v2/Summer22/slides_zbzc_btagL_3taggers_Summer22.pdf
"""
import argparse
import datetime
import os

import numpy as np

from zbzc_slides_common import (ACCENT, BODY, CHS, D, DARK, GOOD, INFO, OPEN, TAGGER_CL, Deck, bullets, heading, image,
                                note, note_height, page, read_yields, reading_slide, setup_slides, table, text, working_points)

parser = argparse.ArgumentParser()
parser.add_argument("--date", default=None)
args = parser.parse_args()
DATE = args.date or datetime.date.today().strftime("%-d %B %Y")
OUT = f"{D}/slides_zbzc_btagL_3taggers_Summer22.pdf"
REG = {"PNet": "btag_L", "DeepJet": "btagDeepJet_L", "RobustParT": "btagRobustParT_L"}
LONG = {"PNet": "ParticleNet", "DeepJet": "DeepJet", "RobustParT": "RobustParT (Robust Particle Transformer)"}
WPV = working_points()
WP = {t: WPV[(t, "L")][0] for t in TAGGER_CL}

INCL, _ = read_yields(f"{D}/yields.txt")
Y, SF = {}, {}
for t, reg in REG.items():
    Y[t], SF[t] = read_yields(f"{D}/yields_{reg}.txt")
    assert set(Y[t]) == set(CHS) and all(len(SF[t][c]) == 11 for c in CHS), t


def nums(t, ch):
    y, i = Y[t][ch], INCL[ch]
    r = y["data"] / y["mc"]
    effd, effm = y["data"] / i["data"], y["mc"] / i["mc"]
    er = effd / effm
    return dict(r=r, re=r * np.hypot(y["data"] ** -0.5, y["mce"] / y["mc"]), effd=effd, effm=effm, er=er,
                ere=er * np.hypot(np.sqrt(effd * (1 - effd) / i["data"]) / effd, y["mce"] / y["mc"]),
                **{k: y[k] / y["mc"] for k in ("b", "c", "l", "tt", "VV")})


def mean_sf(t):
    """Mean SF of the tagged jet per true flavour (DY MC of both channels, weighted by the number of tagged jets);
    fraction of b-tagged jets that also pass the same tagger's Loose c-tag (DY MC, and Z->mumu data)."""
    nb = sb = nc = sc = nl = sl = ntag = nboth = 0.0
    for ch in CHS:
        for ds, v in SF[t][ch].items():
            if ds.startswith("DY"):
                nb += v[0]; sb += v[0] * v[1]; nc += v[2]; sc += v[2] * v[3]; nl += v[4]; sl += v[4] * v[5]
                ntag += v[6]; nboth += v[7]
    dt = sum(v[0] for ds, v in SF[t]["Zmm"].items() if ds.startswith("Muon"))
    db = sum(v[1] for ds, v in SF[t]["Zmm"].items() if ds.startswith("Muon"))
    return sb / nb, sc / nc, sl / nl, nboth / ntag, db / dt


def pct(x):
    return f"{100 * x:.0f}%"


TWOJ = "Only events with at least two jets."
Z = lambda a, b: f"Zoom: {a}–{b}, linear scale, data/MC from 0.8 to 1.2."  # noqa: E731
# (file, title, explanation). The tagger's own scores are added per section.
VARS = [
    ("z_mass", "Mass of the lepton pair, m(ℓℓ)", "The Z peak, linear scale. Selection: 71–111 GeV. Tests the lepton energy scale "
     "and resolution."),
    ("z_pt", "Transverse momentum of the lepton pair, pT(ℓℓ) = Z pT", "Log scale up to 1 TeV. This is the distribution with the "
     "pT trend discussed in the follow-up slides (low at 30–60 GeV, high at 100–150 GeV)."),
    ("z_pt_zoom", "Z pT, zoom on 0–200 GeV", Z(0, 200)),
    ("z_eta", "Pseudorapidity of the lepton pair, η(ℓℓ)", ""),
    ("lep0_pt", "Leading-lepton pT", "The selection requires pT > 35 GeV for the leading lepton (on the trigger plateau)."),
    ("lep0_pt_zoom", "Leading-lepton pT, zoom on 30–200 GeV", Z(30, 200)),
    ("lep0_eta", "Leading-lepton η", "|η| < 2.4. For electrons the barrel–endcap gap (1.44 < |η| < 1.57) is removed, so that bin is low."),
    ("lep0_phi", "Leading-lepton φ", "Expected to be flat; dips would point to detector problems."),
    ("lep1_pt", "Second-lepton pT", "The selection requires pT > 25 GeV for electrons and > 26 GeV for muons."),
    ("lep1_pt_zoom", "Second-lepton pT, zoom on 20–150 GeV", Z(20, 150)),
    ("lep1_eta", "Second-lepton η", ""),
    ("lep1_phi", "Second-lepton φ", ""),
    ("dR_ll", "Angular distance between the two leptons, ΔR(ℓℓ)", "ΔR = √(Δη² + Δφ²). Small ΔR = boosted Z."),
    ("dphi_ll", "Azimuthal angle between the two leptons, Δφ(ℓℓ)", "Close to π (back to back) when the Z has low pT."),
    ("n_jet", "Number of selected jets", "AK4 jets with pT > 30 GeV, |η| < 2.5, away from the leptons. The leading jet is "
     "b-tagged here, so every event has at least one jet."),
    ("jet_pt", "Leading-jet pT (this is the b-tagged jet)", "pT > 30 GeV."),
    ("jet_pt_zoom", "Leading-jet pT, zoom on 30–200 GeV", Z(30, 200)),
    ("jet_eta", "Leading-jet η", "|η| < 2.5 (tracker coverage, needed for b-tagging)."),
    ("jet_phi", "Leading-jet φ", "Expected to be flat."),
    ("jet1_pt", "Second-jet pT", TWOJ + " The second jet is not tagged."),
    ("jet1_pt_zoom", "Second-jet pT, zoom on 30–150 GeV", Z(30, 150) + " " + TWOJ),
    ("jet1_eta", "Second-jet η", TWOJ),
    ("dR_jj", "Angular distance between the two leading jets, ΔR(jj)", TWOJ),
    ("dphi_jj", "Azimuthal angle between the two leading jets, Δφ(jj)", TWOJ),
    ("m_jj", "Mass of the two leading jets, m(jj)", TWOJ),
    ("m_jj_zoom", "m(jj), zoom on 0–400 GeV", Z(0, 400) + " " + TWOJ),
    ("dphi_zj", "Azimuthal angle between the Z and the leading jet, Δφ(Z, j)", "Close to π when the jet recoils against the Z."),
    ("dR_zj", "Angular distance between the Z and the leading jet, ΔR(Z, j)", ""),
    ("dR_lj_min", "Smallest ΔR between a lepton and the leading jet", "Must be > 0.4 by selection (jets overlapping a lepton are removed)."),
    ("pt_balance", "pT balance: leading-jet pT / Z pT", "Close to 1 when the jet alone balances the Z. Sensitive to the jet "
     "energy scale and to extra jets."),
    ("pt_balance_zoom", "pT balance, zoom on 0–2", Z(0, 2)),
    ("met_pt", "Missing transverse momentum (type-1 PUPPI MET), after the MET cut", "The selection requires MET < 50 GeV, so the "
     "plot stops there."),
    ("met_pt_nm1", "MET without the MET cut, up to 200 GeV", "All other cuts applied, so the region removed by MET < 50 GeV is "
     "visible. tt̄ dominates at high MET. MC is above data at 40–120 GeV, as without tagging (known 2022 jet/MET issue)."),
    ("met_pt_nm1_zoom", "MET without the MET cut, zoom on 0–100 GeV", Z(0, 100)),
    ("npv", "Number of good primary vertices", "After the pileup weights. Data and MC differ slightly because our 20 test data "
     "files cover runs with less (ee) or about the same (μμ) pileup as all of 2022 C–D, which the MC is weighted to."),
    ("npv_zoom", "Number of good primary vertices, zoom on 10–50", Z(10, 50)),
    ("lhe_vpt", "Generator-level Z pT (simulation only)", "Z pT from the event generator, before any detector effect; no data. "
     "Shows which pT(ℓℓ)-binned DY sample contributes where."),
    ("lhe_vpt_zoom", "Generator-level Z pT, zoom on 0–200 GeV", Z(0, 200)),
]
SCORES = [("B", "B score (b vs everything)", "The score used for the selection: only jets above {wp} enter this region."),
          ("CvL", "CvL score (c vs light)", "Not used in this b-tag selection; shown for comparison."),
          ("CvB", "CvB score (c vs b)", "Not used in this b-tag selection. Low values = b-like.")]
MAP = ("lep_eta_phi_ratio", "Lepton η–φ map: data / MC", "Both Z leptons, MC normalised to data in each map, cells of 1.0 in η × "
       "π/4 in φ. Colour scale from 0.85 to 1.15; the number in each cell is data/MC. Few events per cell in a tagged region.")
N_PLOTS = len(VARS) + len(SCORES) + 1
for t, reg in REG.items():
    for v in [x[0] for x in VARS] + [f"jet_{t}{s}" for s, _, _ in SCORES] + [MAP[0]]:
        assert os.path.exists(f"{D}/plots_{reg}/{v}.png"), (reg, v)

deck = Deck(OUT, "Summer22 (2022 C–D), 13.6 TeV · Z→ℓℓ + jet, leading jet b-tagged (Loose) · 20 files per sample · "
                 "statistical errors only")
N_INTRO = 7
SEC = 1 + N_PLOTS
START = {t: N_INTRO + 1 + i * SEC for i, t in enumerate(REG)}

# ------------------------------------------------------------------ cover
fig = page(DARK)
text(fig, 110, 280, "Z + b-tagged jet in Summer22: three taggers at the Loose working point", 60, "white", "bold", width=1700, ls=1.15)
text(fig, 110, 500, "All kinematic distributions for ParticleNet, DeepJet and RobustParT, each with its own BTV scale factors. "
     "All corrections, including the muon changes of 8 November.", 30, "#C9D3E3", width=1650)
text(fig, 110, 860, DATE, 26, "#C9D3E3")
deck.save(fig, foot=False)

# ------------------------------------------------------------------ contents
fig = page()
y = heading(fig, "Contents") + 10
rows = [["Analysis setup: data, simulation, selection, corrections, scale factors", "3–4"],
        ["How to read the numbers", "5"], ["What this deck shows, and the three taggers", "6"],
        ["The three taggers side by side: yields, purity, scale factors", "7"]]
for t in REG:
    rows.append([f"{LONG[t]}, Loose b-tag (B > {WP[t]:.4g}): {N_PLOTS} plots", f"{START[t]}–{START[t] + SEC - 1}"])
rows.append(["Summary", str(N_INTRO + len(REG) * SEC + 1)])
table(fig, 110, y, [("section", 1460, "left"), ("pages", 240, "right")], rows, 24)
deck.save(fig)

setup_slides(deck)
reading_slide(deck, extra=[
    ("Loose b-tag", "The leading jet's b score is above the BTV Loose working point (about 10% of light jets pass)."),
    ("Tagged", "Fraction of Z + jet events whose leading jet is tagged."),
    ("Tag ratio", "Tagged fraction in data divided by tagged fraction in MC. Tests the tagging and its SFs, independent of the "
                  "overall normalisation."),
    ("Flavour share", "Share of all MC events whose leading jet is a true b, c or light jet (DY), or tt̄."),
])

# ------------------------------------------------------------------ what this deck shows
fig = page()
y = heading(fig, "What this deck shows",
            "The same Z + jet selection as before, with one extra requirement: the leading jet passes the Loose b-tag of one "
            "of three taggers. Each tagger is a separate set of plots.") + 10
rows = [[LONG[t], f"{WPV[(t, 'L')][0]:.4g}", f"{WPV[(t, 'M')][0]:.4g}", f"{WPV[(t, 'T')][0]:.4g}",
         f"{TAGGER_CL[t]}_comb / _light"] for t in REG]
y = table(fig, 110, y, [("tagger (b score cut)", 600, "left"), ("Loose", 160, "right"), ("Medium", 160, "right"),
                        ("Tight", 160, "right"), ("BTV SFs used in MC", 620, "left")], rows, 22) + 8
y = text(fig, 110, y, "Only Loose is used here; Medium and Tight are listed for reference. The SF is applied to the tagged jet "
         "according to its true flavour (_comb for b and c jets, _light for light jets).", 21, BODY, width=1700) + 18
y = bullets(fig, 110, y, 1700, "How to read the plots", [
    "Left panel Z→ee, right panel Z→μμ. Black points: data. Coloured stack: MC, split by the true flavour of the leading jet "
    "(DY+b, DY+c, DY+light) plus tt̄ and dibosons (VV).",
    "Lower panel: data/MC. The hatched band is the MC statistical uncertainty. No systematic uncertainties yet.",
    "The overall data/MC is about 0.93–0.96 in every region, so points sit slightly below 1 everywhere; look at the shape.",
    "The order of the plots is the same for each tagger, so the same page of each section can be compared directly.",
], size=22)
deck.save(fig)

# ------------------------------------------------------------------ side by side
fig = page()
y = heading(fig, "The three taggers side by side",
            "Flavour shares are of all MC. Tagged = fraction of Z + jet events whose leading jet passes the Loose b-tag. "
            "Tag ratio = tagged fraction in data / in MC (1 = data and MC agree).") + 6
rows = []
for ch, lab in CHS.items():
    i = INCL[ch]
    rows.append([f"no tag, {lab}", f"{i['data'] / i['mc']:.3f}", pct(i["b"] / i["mc"]), pct(i["c"] / i["mc"]),
                 pct(i["l"] / i["mc"]), "100%", "–"])
for t in REG:
    for ch, lab in CHS.items():
        x = nums(t, ch)
        rows.append([f"{t}, {lab}", f"{x['r']:.3f} ± {x['re']:.3f}", pct(x["b"]), pct(x["c"]), pct(x["l"]),
                     f"{100 * x['effd']:.1f}%", f"{x['er']:.3f} ± {x['ere']:.3f}"])
y = table(fig, 110, y, [("", 360, "left"), ("data/MC", 250, "right"), ("DY+b", 140, "right"), ("DY+c", 140, "right"),
                        ("DY+light", 170, "right"), ("tagged (data)", 250, "right"), ("tag ratio", 390, "right")],
          rows, 21, shade_rows=(0, 1)) + 12
rows = []
for t in REG:
    b, c, l, ov, ovd = mean_sf(t)
    rows.append([t, f"{b:.2f}", f"{c:.2f}", f"{l:.2f}", pct(ov), pct(ovd)])
y = table(fig, 110, y, [("mean BTV SF of the tagged jet (DY MC)", 640, "left"), ("b jets", 170, "right"), ("c jets", 170, "right"),
                        ("light jets", 200, "right"), ("also c-tagged, MC", 260, "right"), ("data μμ", 260, "right")],
          rows, 21) + 12
note(fig, y, "All three select a similar sample at Loose: about 1 in 6 Z + jet events, of which only ~20% are real b jets.",
     "Light jets are mistagged more often in data than in MC (light SF ≈ 1.2); the SFs correct for it. Most Loose b-tagged jets "
     "also pass the Loose c-tag of the same tagger (last two columns).", INFO, size=21)
deck.save(fig)


# ------------------------------------------------------------------ one section per tagger
def plot_page(t, var, title, expl):
    fig = page()
    text(fig, 110, 34, f"{LONG[t]} · Loose b-tag (B > {WP[t]:.4g})", 24, ACCENT, "bold")
    y = text(fig, 110, 70, title, 42, DARK, "bold", width=1700, ls=1.15)
    if expl:
        y = text(fig, 110, y + 6, expl, 23, BODY, width=1700)
    image(fig, f"{D}/plots_{REG[t]}/{var}.png", y + 12, hmax=1025 - y - 12)
    deck.save(fig)


for t in REG:
    fig = page(DARK)
    yy = text(fig, 110, 120, f"{LONG[t]}, Loose b-tag", 62, "white", "bold", width=1700, ls=1.15)
    text(fig, 110, yy + 20, f"Leading jet {t} B score > {WP[t]:.4g}; MC weighted with the {TAGGER_CL[t]} BTV scale factors.",
         30, "#C9D3E3", width=1650)
    hdr = ["", "data/MC", "DY+b", "DY+c", "DY+light", "tt̄", "tagged MC", "tagged data"]
    xs = [110, 400, 700, 860, 1020, 1210, 1350, 1580]
    for x, h in zip(xs, hdr):
        text(fig, x, 430, h, 26, "#C9D3E3", "bold")
    for k, (ch, lab) in enumerate(CHS.items()):
        v = nums(t, ch)
        for x, val in zip(xs, (lab, f"{v['r']:.3f} ± {v['re']:.3f}", pct(v["b"]), pct(v["c"]), pct(v["l"]), pct(v["tt"]),
                               f"{100 * v['effm']:.1f}%", f"{100 * v['effd']:.1f}%")):
            text(fig, x, 490 + k * 60, val, 28, "white")
    text(fig, 110, 680, "Flavour shares are of all MC. Tagged = fraction of Z + jet events whose leading jet passes the tag. "
         "Statistical errors only.", 23, "#C9D3E3", width=1700)
    text(fig, 110, 760, f"{N_PLOTS} plots follow, in this order: Z and leptons, jets, Z–jet, MET and vertices, generator Z pT, "
         f"the {t} scores, the lepton η–φ map. Left Z→ee, right Z→μμ.", 23, "#C9D3E3", width=1700)
    deck.save(fig)
    for var, title, expl in VARS:
        plot_page(t, var, title, expl)
    for s, title, expl in SCORES:
        plot_page(t, f"jet_{t}{s}", f"Leading-jet {t} {title}", expl.format(wp=f"{WP[t]:.4g}"))
    plot_page(t, *MAP)

# ------------------------------------------------------------------ summary
fig = page()
y = heading(fig, "Summary") + 14
pur = {t: (nums(t, "Zee")["b"], nums(t, "Zmm")["b"]) for t in REG}
er = {t: (nums(t, "Zee"), nums(t, "Zmm")) for t in REG}
pulls = [abs(x["er"] - 1) / x["ere"] for a, b in er.values() for x in (a, b)]
y = note(fig, y, "The three taggers select a similar sample at the Loose working point.",
         "Share of real b jets (DY+b) in all MC, Z→ee / Z→μμ: " + ", ".join(f"{t} {pct(a)} / {pct(b)}" for t, (a, b) in pur.items())
         + ". Loose is a loose selection: most tagged jets are c or light jets. Medium (~60% b) and Tight (~88% b) are much purer.") + 16
y = note(fig, y, "Data and MC tag the same fraction of jets " + ("within the statistical errors, for all three taggers."
                                                                 if max(pulls) < 2 else "within a few percent."),
         "Tag ratio (data/MC), Z→ee / Z→μμ: " + "; ".join(f"{t} {a['er']:.3f} / {b['er']:.3f}" for t, (a, b) in er.items())
         + f" (largest deviation from 1: {max(pulls):.1f} standard deviations).", GOOD if max(pulls) < 2 else OPEN) + 16
ls = [mean_sf(t)[2] for t in REG]
y = note(fig, y, "The MC excess at MET 40–120 GeV seen without tagging is also present for all three taggers.",
         "So it is not caused by the tagging (2022 jet/MET issue, see the follow-up slides). Compare the same page number in "
         "each section to compare the taggers plot by plot.", INFO) + 16
note(fig, y, "Not included yet",
     f"BTV SF uncertainties (light-jet SFs are {min(ls):.2f}–{max(ls):.2f}, so they matter here), other systematic uncertainties, "
     "the loose tau veto, and the full dataset (these plots use 20 files per sample).", OPEN)
deck.save(fig)
deck.close()
