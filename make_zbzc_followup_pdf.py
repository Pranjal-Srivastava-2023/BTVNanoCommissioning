"""Follow-up deck for the meeting of 8 November 2026 (Summer22, run zbzc_run3_v2): every recommendation
with the question, what was done, what was found and what it means, plus two slides on the full analysis
setup. Replaces slides_zbzc_v2_Summer22.pdf and advisor_recommendations_2026-11-08.pdf (user, 2026-11-08:
"slides should be self-explanatory").

Numbers are read from the run's output files (muvar/muvar_table.txt, channels_summary.json,
pu/pu_closure.txt + pu_profiles.json, tagger_summary.txt) and the pT(ll) shape table is computed from the
coffea outputs of hists_zbzc_run3_tag (237-page deck) and hists_zbzc_run3_v2. The trigger example uses the
MUO IsoMu24 efficiencies from the framework's Summer22 correction set.

Usage:  python make_zbzc_followup_pdf.py [--date "8 November 2026"]
Output: hists_zbzc_run3_v2/Summer22/slides_followup_2026-11-08_Summer22.pdf
"""
import argparse
import datetime
import glob
import json

import numpy as np
from coffea.util import load

from zbzc_slides_common import (CHS, D, DARK, GOOD, INFO, OPEN, TAGGER_CL, Deck, bullets, f3, heading, image, note, note_height, page,
                                read_muvar, read_pu, read_tags, reading_slide, setup_slides, table, text, working_points)

parser = argparse.ArgumentParser()
parser.add_argument("--date", default=None)
args = parser.parse_args()
DATE = args.date or datetime.date.today().strftime("%-d %B %Y")
OUT = f"{D}/slides_followup_2026-11-08_Summer22.pdf"

MUV, ETA = read_muvar()
TAGS = read_tags()
PU, SHIFT = read_pu()
WPV = working_points()
CH = json.load(open(f"{D}/channels_summary.json"))
FINAL, ALLZ = CH["stages"]["final: MET<50, >=1 jet"], CH["stages"]["all Z events"]
OLD, NEW = MUV[("final", "prev")], MUV[("final", "nominal")]

# trigger SF example: one muon at eta 0.5, pT 45 GeV (MUO IsoMu24, Tight ID + Tight iso)
from BTVNanoCommissioning.utils.correction import load_SF  # noqa: E402

_c = load_SF("2022", "Summer22")["MUO"]["NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight"]
ED, EM = _c.evaluate(0.5, 45.0, "nominal_DATAeff"), _c.evaluate(0.5, 45.0, "nominal_MCeff")
PD, PM = 1 - (1 - ED) ** 2, 1 - (1 - EM) ** 2

# pT(ll) shape: data/MC per range / overall data/MC, full selection
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
    return [(d[(c > a) & (c < b)].sum() / m[(c > a) & (c < b)].sum() / tot, int(d[(c > a) & (c < b)].sum())) for a, b in RANGES]


SHAPE = {"Z→μμ, 237-page deck": shape("hists_zbzc_run3_tag", "Zmm"), "Z→μμ, now": shape("hists_zbzc_run3_v2", "Zmm"),
         "Z→ee (unchanged)": shape("hists_zbzc_run3_v2", "Zee")}

deck = Deck(OUT, "Summer22 (2022 C–D), 13.6 TeV · Z→ℓℓ + jets · 20 files per sample · statistical errors only")
IMG_BOTTOM = 905  # images end above this, the conclusion box goes below


def plot_page(title, sub, path, concl, body="", style=GOOD):
    fig = page()
    y = heading(fig, title, sub)
    y = image(fig, path, y, hmax=1020 - note_height(concl, body) - 8 - y) + 8
    note(fig, y, concl, body, style)
    deck.save(fig)


# ------------------------------------------------------------------ cover
fig = page(DARK)
text(fig, 110, 290, "Follow-up to the meeting of 8 November", 64, "white", "bold", width=1700)
text(fig, 110, 400, "Z + jets in Summer22: the muon channel, other b/c taggers, pileup, and the plot fixes", 32, "#C9D3E3", width=1650)
text(fig, 110, 520, "Same data and simulation files as the 237-page deck, so every number can be compared directly.", 26, "#C9D3E3", width=1650)
text(fig, 110, 860, DATE, 26, "#C9D3E3")
deck.save(fig, foot=False)

# ------------------------------------------------------------------ summary
fig = page()
y = heading(fig, "Summary: the seven requests and what we found") + 6
cav = {t: np.mean([TAGS[(c, "ctag", t, wp)]["er"] for c in CHS for wp in "LMT"]) for t in TAGGER_CL}
items = [
    ("1. Muon channel looks different from electrons",
     f"One real problem found: the muon trigger SF was computed from the leading muon only. Fixed. Z→μμ data/MC is now "
     f"{NEW['r']:.3f} (was {OLD['r']:.3f}), the same as Z→ee ({FINAL['Zee']['r']:.3f}). The pT(ℓℓ) shape did not change and is the "
     "same in electrons, so it is not a muon effect."),
    ("2. Other b/c taggers, Loose/Medium/Tight",
     "DeepJet and RobustParT added next to ParticleNet, each with its own BTV SFs. Similar purity at the same working point. "
     "b-tag: data and MC agree for all three. c-tag: the taggers differ by a few percent."),
    ("3. Loose tau ID veto", "Postponed, as agreed."),
    ("4. ee and μμ pileup look different",
     "Our 20 test files of each channel come from different runs with slightly different pileup. That explains the difference."),
    ("5. ee vs μμ MC colours", "Fixed: both channels now use the same stack and legend order."),
    ("6. MET up to ~200 GeV", "Done. MC is well above data between 40 and 120 GeV (known 2022 jet/MET issue)."),
    ("7. Zoom into high-statistics bins", "Done: zoomed copies of 10 plots in every region."),
]
for k, v in items:
    text(fig, 110, y, k, 23, DARK, "bold", width=560)
    y2 = text(fig, 700, y, v, 22, DARK, width=1110)
    y = max(y2, y + 60) + 16
deck.save(fig)

setup_slides(deck)
reading_slide(deck, extra=[
    ("Test version", "Muon study only: a copy of the muon selection with ONE thing changed, filled in the same run to see "
                     "how much it matters. Tests are for comparison only and are not used in the analysis."),
    ("Tag ratio", "Fraction of events with a tagged jet in data divided by the same fraction in MC. "
                  "It tests the tagging and its SFs, independent of the overall normalisation."),
    ("Purity", "Share of real b (or c) jets among the tagged jets in the DY simulation."),
])

# ------------------------------------------------------------------ 1. muons
fig = page()
y = heading(fig, "1 · Muon channel: the question and how we checked it",
            "Advisor: the muon channel shows a small discrepancy compared with electrons. Check the trigger turn-on, the η cut, "
            "the SFs and corrections, Rochester; follow the POG; maybe pT > 26 GeV and |η| < 2.4 help.") + 10
rows = [
    ["Trigger SF", "SF from the data and MC efficiencies of both muons", "YES: was leading muon only (wrong)"],
    ["Muon pT cut", "both muons pT > 26 GeV (start of the POG trigger SFs)", "YES: second muon was > 25 GeV"],
    ["Leading muon pT", "> 35 GeV (on the trigger plateau)", "no"],
    ["η cut", "|η| < 2.4", "no (already there)"],
    ["Momentum correction", "MUO scale and smearing (Run 3 replacement of Rochester)", "no (already applied)"],
    ["ID and isolation", "Tight ID, Tight PF isolation, with their POG SFs", "no (already applied)"],
    ["Pileup weights", "official LUM weights", "no (already applied)"],
]
y = table(fig, 110, y, [("ingredient", 330, "left"), ("what the analysis does now (POG recommendation)", 830, "left"),
                        ("changed?", 540, "left")], rows, 22, shade_rows=(0, 1)) + 22
note(fig, y, "How we measured the effect of each ingredient",
     "In the same run we also filled 10 test versions of the muon selection. Each changes ONE ingredient, e.g. switches the "
     "pileup weights off, so we can see how much data/MC moves. The tests are only for comparison: the analysis and all plots "
     "use the default setup with every correction applied.", INFO)
deck.save(fig)

fig = page()
y = heading(fig, "1 · The muon trigger SF was wrong; now fixed",
            "HLT_IsoMu24 fires if EITHER muon fires. The event trigger efficiency is 1 − (1−ε₁)(1−ε₂), which is close to 1. "
            "Our code used the SF of the leading muon only, as if only that muon could fire the trigger.") + 14
text(fig, 110, y, "Example: one muon at η = 0.5, pT = 45 GeV, efficiencies from the MUO file", 23, DARK, "bold")
y = table(fig, 110, y + 40, [("", 700, "left"), ("efficiency in data", 330, "right"), ("in MC", 260, "right"),
                             ("SF = data / MC", 410, "right")],
          [["old: leading muon only", f"{ED:.3f}", f"{EM:.3f}", f"{ED / EM:.3f}"],
           ["new: either of two such muons", f"{PD:.4f}", f"{PM:.4f}", f"{PD / PM:.3f}"]], 23) + 24
y = note(fig, y, f"The old SF lowered every MC event by about {100 * (1 - (ED / EM) / (PD / PM)):.0f}%. That made Z→μμ "
                 f"look better than it really was.",
         f"With the correct SF: Z→μμ data/MC {OLD['r']:.3f} → {NEW['r']:.3f}. Z→ee was already done this way and stays at "
         f"{FINAL['Zee']['r']:.3f}. The goal is a correct prediction, not data/MC = 1: the remaining 5–6% is common to both "
         "channels (two pages on).") + 18
note(fig, y, "Second change: both muons pT > 26 GeV (was 25 for the second muon)",
     f"The POG trigger efficiencies start at 26 GeV, so a muon below that cannot be used in the formula. Effect on data/MC: "
     f"{-MUV[('final', 'sub25')]['vsnom']:+.1f}%.", INFO)
deck.save(fig)

fig = page()
y = heading(fig, "1 · Tests (not applied): how much does data/MC depend on each ingredient?",
            "First row: the default used in the analysis. Other rows: the same run with one thing changed, for comparison only. "
            "Slope: straight-line fit of data/MC vs pT(μμ), full selection, % per 100 GeV.") + 8
TESTS = [("nominal", "DEFAULT (used everywhere)"), ("prev", "old setup (237-page deck)"),
         ("trigLead", "trigger SF of leading muon only"), ("trigMatch", "other POG trigger method: match lead muon"),
         ("sub25", "second muon pT > 25 instead of 26"), ("lead26", "leading muon pT > 26 instead of 35"),
         ("eta21", "|η| < 2.1 instead of 2.4"), ("noSS", "without muon scale/smearing"),
         ("noIDIsoSF", "without ID + isolation SFs"), ("noPU", "without pileup weights"), ("noTrigSF", "without trigger SF")]
rows = []
for v, desc in TESTS:
    f, z = MUV[("final", v)], MUV[("Z", v)]
    rows.append([desc, f"{f['r']:.3f}", "–" if v == "nominal" else f"{f['vsnom'] + 0.0:+.1f}%".replace("-0.0", "+0.0"), f"{z['r']:.3f}",
                 "–" if v == "nominal" else f"{z['vsnom'] + 0.0:+.1f}%".replace("-0.0", "+0.0"), f"{f['slope']:+.1f} ± {f['slope_err']:.1f}"])
y = table(fig, 110, y, [("version", 640, "left"), ("data/MC, full sel.", 260, "right"), ("change", 150, "right"),
                        ("data/MC, Z sel.", 240, "right"), ("change", 150, "right"), ("slope", 260, "right")],
          rows, 21, bold_rows=(0,), shade_rows=(0,)) + 16
sl = [MUV[("final", v)]["slope"] for v, _ in TESTS]
note(fig, y, "Only the scale factors move the normalisation. None of the choices changes the shape.",
     f"Slopes go from {min(sl):+.1f} to {max(sl):+.1f}; the versions share almost all events, so this spread is the real "
     f"effect. The two POG trigger methods agree within {abs(MUV[('final', 'trigMatch')]['vsnom']):.1f}%.")
deck.save(fig)

fig = page()
y = heading(fig, "1 · After the fix, muons and electrons agree at every step",
            "data/MC for each group of events. The first four rows add up to all Z events; the last row is the final selection.") + 8
rows = []
for lab, show, what in (("all Z events", "all Z events", "Z selection, no jet or MET requirement"),
                        ("MET<50, 0 jets", "MET < 50, no jet", "Z + nothing else (most Z events)"),
                        ("MET>50, 0 jets", "MET > 50, no jet", "large MET, no selected jet"),
                        ("MET>50, >=1 jet", "MET > 50, ≥ 1 jet", "large MET with jets (includes tt̄)"),
                        ("final: MET<50, >=1 jet", "final selection", "MET < 50 and ≥ 1 jet: the analysis sample")):
    e, m = CH["stages"][lab]["Zee"], CH["stages"][lab]["Zmm"]
    rows.append([show, what, f3(e["r"], e["re"]), f3(m["r"], m["re"])])
y = table(fig, 110, y, [("events", 300, "left"), ("what they are", 680, "left"), ("Z→ee", 360, "right"),
                        ("Z→μμ", 360, "right")], rows, 22, bold_rows=(4,), shade_rows=(4,)) + 22
y = note(fig, y, "The two channels now behave the same way everywhere.",
         "Before the fix, Z→μμ was about 2% higher than Z→ee because of the trigger SF.") + 16
note(fig, y, "The remaining 5–6% deficit is common to both channels, so it is not a lepton problem.",
     "Events without jets have MORE data than MC (1.03–1.04); events with jets have less (0.94–0.95); events with MET > 50 GeV "
     "have far less (0.4–0.7). So the MC has too many events with jets and too much MET: jet modelling, not leptons.", OPEN)
deck.save(fig)

plot_page("1 · The muon tests do not change the pT(μμ) shape",
          "data/MC versus pT(μμ) for six of the test versions, Z selection (before the jet and MET cuts). Black: old setup; "
          "red: default. The value in brackets is the overall data/MC of each version.",
          f"{D}/muvar/z_pt_Z.png", "All versions follow the same curve; they only move up or down together.",
          "So no muon setting is behind the pT trend. The same fall at high pT is seen in Z→ee (next pages).")

fig = page()
y = heading(fig, "1 · The pT(ℓℓ) trend: still there, unchanged, and the same in electrons",
            "Shape of data/MC: data/MC in each pT(ℓℓ) range divided by the overall data/MC, full selection. 1.00 = same as average.") + 8
rows = [[k] + [f"{r:.3f}" for r, _ in v] for k, v in SHAPE.items()]
rows.append(["Z→μμ data events"] + [str(nn) for _, nn in SHAPE["Z→μμ, now"]])
y = table(fig, 110, y, [("pT(ℓℓ) [GeV]", 380, "left")] + [(f"{a}–{b}", 165, "right") for a, b in RANGES], rows, 21) + 18
y = note(fig, y, "The visual trend is unchanged by the muon fixes, and Z→ee shows the same pattern.",
         "data/MC is about 2–3% low at 30–60 GeV, about 4% high at 100–150 GeV, and falls above 200 GeV (few events there).",
         OPEN) + 16
note(fig, y, "It starts before any jet or MET cut, in both channels: the Drell–Yan simulation, not the leptons.",
     f"Slope at Z selection: Z→ee {ALLZ['Zee']['slope']:+.1f} ± {ALLZ['Zee']['slope_err']:.1f}, Z→μμ "
     f"{ALLZ['Zmm']['slope']:+.1f} ± {ALLZ['Zmm']['slope_err']:.1f} % per 100 GeV. Possible next steps: the full dataset "
     "(more events above 200 GeV), an official DY pT correction or another DY sample.", INFO)
deck.save(fig)

plot_page("1 · The pT(ℓℓ) distribution as the advisor saw it (now with the fixes)",
          "Full selection. Top: events per 10 GeV, MC stacked by jet flavour. Bottom: data/MC; hatched band = MC statistical "
          "uncertainty. Left Z→ee, right Z→μμ.",
          f"{D}/plots/z_pt.png", "Same pattern in both channels: low at 30–60 GeV, high around 100–150 GeV, falling above 200 GeV.",
          "Above ~300 GeV most bins have only a few events, so their scatter is mostly statistics.", OPEN)

fig = page()
R = CH["runs"]
y = heading(fig, "1 · Where the earlier '+4.4% per 100 GeV' slope came from",
            "The same straight-line fit of data/MC vs pT(ℓℓ) (10 GeV bins, 0–400 GeV, full selection) on three runs with the same files.") + 10
rows = []
for run, lab in (("hists_zbzc_run3_ge1j", "29 Oct run: DY Z pT weights ON"), ("hists_zbzc_run3_tag", "237-page deck: weights OFF"),
                 ("hists_zbzc_run3_v2", "now: weights OFF + muon fixes")):
    rows.append([lab, f"{R[run]['Zee']['z_pt'][0]:+.1f} ± {R[run]['Zee']['z_pt'][1]:.1f}",
                 f"{R[run]['Zmm']['z_pt'][0]:+.1f} ± {R[run]['Zmm']['z_pt'][1]:.1f}"])
y = table(fig, 110, y, [("run", 900, "left"), ("slope Z→ee", 400, "right"), ("slope Z→μμ", 400, "right")], rows, 24) + 24
note(fig, y, "The +4.4 came from our own Z pT weights, which over-corrected. They are off since the 237-page deck.",
     "With the weights off, a straight line gives no significant slope, because the pattern goes up and then down (previous "
     "pages). The fit number alone hides it, so we look at the shape table.", INFO)
deck.save(fig)

n0, tm = ETA[("Z", "nominal")], ETA[("Z", "trigMatch")]
plot_page("1 · Still open: muons in the outer endcap (|η| > 2.0) are a few percent low",
          "data/MC versus the leading-muon η, Z selection, for six of the test versions (same colours as before).",
          f"{D}/muvar/lep0_eta_Z.png",
          f"Default: {n0[3][0]:.3f} ± {n0[3][1]:.3f} at |η| 2.0–2.4, against {n0[0][0]:.3f} in the barrel.",
          f"The other POG trigger method gives {tm[3][0]:.3f} there, so it is not the formula. Cutting at |η| < 2.1 changes the "
          f"overall data/MC by only {MUV[('Z', 'eta21')]['vsnom']:+.2f}%. Not understood yet; small effect on the total.", OPEN)

# ------------------------------------------------------------------ 2. taggers
fig = page()
y = heading(fig, "2 · Other taggers: DeepJet and RobustParT added next to ParticleNet",
            "Advisor: try other b/c taggers with Loose, Medium and Tight working points.") + 10
rows = []
for t in TAGGER_CL:
    for wp in "LMT":
        b, cvl, cvb = WPV[(t, wp)]
        rows.append([t if wp == "L" else "", {"L": "Loose", "M": "Medium", "T": "Tight"}[wp], f"{b:.4g}", f"{cvl:.4g}", f"{cvb:.4g}"])
y = table(fig, 110, y, [("tagger", 380, "left"), ("working point", 300, "left"), ("b-tag: B >", 340, "right"),
                        ("c-tag: CvL >", 340, "right"), ("and CvB >", 340, "right")], rows, 21) + 18
note(fig, y, "What was done",
     "The cut is applied to the leading jet. The working points are the official BTV Summer22 values. In MC the tagged jet "
     "gets the BTV SF of that tagger for its true flavour. Each tagger and working point is a separate set of plots: 18 tagged "
     "regions in total (3 taggers × L/M/T × b/c), all in hists_zbzc_run3_v2/Summer22/plots_<region>/.", INFO)
deck.save(fig)


def tag_page(kind):
    fl = "bfrac" if kind == "btag" else "cfrac"
    q = "b" if kind == "btag" else "c"
    fig = page()
    y = heading(fig, f"2 · {q}-tagging: the three taggers compared",
                f"Purity: share of real {q} jets among the tagged DY jets (Z→μμ). Tagged: fraction of Z + jet events with a tagged "
                "leading jet (Z→μμ data). Tag ratio: tagged fraction in data / in MC; 1 = data and MC agree.") + 8
    rows, pulls = [], []
    for t in TAGGER_CL:
        for wp in "LMT":
            e, m = TAGS[("Zee", kind, t, wp)], TAGS[("Zmm", kind, t, wp)]
            pulls += [(abs(x["er"] - 1) / x["ere"], ch, t, wp, x) for ch, x in (("Z→ee", e), ("Z→μμ", m))]
            rows.append([t if wp == "L" else "", wp, f"{100 * m[fl]:.0f}%", f"{100 * m['effd']:.1f}%", f3(e["er"], e["ere"]),
                         f3(m["er"], m["ere"])])
    y = table(fig, 110, y, [("tagger", 330, "left"), ("WP", 100, "left"), ("purity", 220, "right"), ("tagged", 220, "right"),
                            ("tag ratio Z→ee", 410, "right"), ("tag ratio Z→μμ", 420, "right")], rows, 21) + 16
    worst = max(pulls, key=lambda p: p[0])
    avg = {t: np.mean([TAGS[(c, kind, t, wp)]["er"] for c in CHS for wp in "LMT"]) for t in TAGGER_CL}
    if worst[0] < 2:
        note(fig, y, "Similar purity at the same working point, and data and MC tag the same fraction of jets for all three.",
             f"Largest difference from 1: {worst[2]} {worst[3]} {worst[1]}, {worst[4]['er']:.3f} ± {worst[4]['ere']:.3f} "
             f"({worst[0]:.1f} standard deviations). SF uncertainties are not included yet.")
    else:
        note(fig, y, "Similar purity at the same working point, but the tag ratios differ by a few percent between taggers.",
             "Average tag ratio: " + ", ".join(f"{t} {v:.3f}" for t, v in avg.items()) +
             f". Largest: {worst[2]} {worst[3]} {worst[1]}, {worst[4]['er']:.3f} ± {worst[4]['ere']:.3f} ({worst[0]:.1f} standard "
             "deviations, statistical only). SF uncertainties (a few % for c-tagging) are not included yet.", OPEN)
    deck.save(fig)


tag_page("btag")
tag_page("ctag")

# ------------------------------------------------------------------ 4. pileup
plot_page("4 · Pileup: our ee and μμ test files come from different runs",
          "Advisor: why do the ee and μμ pileup (number of vertices) plots look different? Below: how much luminosity was taken at "
          "each pileup value, for the lumisections our 20 test files cover (brilcalc), compared with all of 2022 C–D.",
          f"{D}/pu/pu_profiles.png",
          f"Mean pileup: EGamma files {PU['Zee']['mean_pu']:.1f}, Muon files {PU['Zmm']['mean_pu']:.1f}, all of 2022 C–D "
          f"{PU['full']['mean_pu']:.1f}.",
          "The MC is weighted to all of 2022 C–D. The EGamma test files have less high-pileup data, so in Z→ee the data sit at "
          "fewer vertices than the MC.", INFO)

fig = page()
y = heading(fig, "4 · Pileup: the difference is explained by the runs in the test files",
            "Check: if a channel's files have lower pileup, its data should have fewer vertices than its MC, by "
            "(pileup difference) × (vertices per pileup interaction). The MC gives 0.69 vertices per interaction.") + 8
rows = [[lab, f"{PU[k]['mean_pu']:.2f}", f"{PU[k]['mean_pu'] - PU['full']['mean_pu']:+.2f}", f"{SHIFT[k][1]:+.2f}", f"{SHIFT[k][0]:+.2f}"]
        for lab, k in (("Z→ee (EGamma files)", "Zee"), ("Z→μμ (Muon files)", "Zmm"))]
y = table(fig, 110, y, [("", 400, "left"), ("mean pileup", 250, "right"), ("vs all 2022 C–D", 330, "right"),
                        ("expected vertex shift", 360, "right"), ("observed (data − MC)", 360, "right")], rows, 22) + 10
C1, B1 = ("Expected and observed shifts agree in both channels. With the full dataset the difference should go away.",
          "Plot: number of good primary vertices, full selection; left Z→ee, right Z→μμ.")
y = image(fig, f"{D}/plots/npv.png", y, hmax=1020 - note_height(C1, B1) - 6 - y) + 6
note(fig, y, C1, B1)
deck.save(fig)

plot_page("4 · Pileup: what did not work",
          "We also tried to reweight the MC bin by bin to each channel's own pileup profile (coloured) instead of the full 2022 C–D "
          "profile (grey). Bottom: data/MC shape.",
          f"{D}/pu/npv_closure.png", "This over-corrects: Z→μμ, flat before, gets a slope. So it is not used.",
          "Probably because a per-lumisection average ignores the bunch-to-bunch spread of pileup. The check on the previous "
          "page does not depend on that. The full-dataset run is the clean test.", OPEN)

# ------------------------------------------------------------------ 5, 6, 7
plot_page("5 · MC colours: the legend order is now the same in both channels",
          "Advisor: in the Z→ee plots DY+b and DY+c were swapped in the legend. Example: leading-lepton pT, full selection.",
          f"{D}/plots/lep0_pt.png", "Fixed. Cause: each channel sorted the stack by its own yields, so the order changed when DY+b "
                                    "and DY+c had similar sizes.",
          "Now one fixed order everywhere: DY+b, DY+c, DY+light, tt̄, VV. The colours were already the same. The 237-page deck's "
          "plots were remade too.")

plot_page("6 · MET up to 200 GeV, without the MET cut",
          "Advisor: extend the MET plot to ~200 GeV. New plot: all cuts applied except MET < 50 GeV, so the region the analysis "
          "removes is visible. Available in every region.",
          f"{D}/plots/met_pt_nm1.png", "MC is well above data between about 40 and 120 GeV in both channels (data/MC down to ~0.6).",
          "This is the 2022 jet/MET issue we traced in October (jets mismeasured in the MET). Above ~120 GeV tt̄ dominates and "
          "agrees. Not fixed. The analysis cuts at 50 GeV, but the 40–50 GeV bins are already a bit low.", OPEN)

plot_page("7 · Zoomed plots of the high-statistics region",
          "Advisor: zoom into the high-statistics bins. Example: Z pT from 0 to 200 GeV, linear scale, data/MC from 0.8 to 1.2.",
          f"{D}/plots/z_pt_zoom.png", "Done for 10 variables in every region (files *_zoom.png).",
          "Z pT, both lepton pTs, leading and second jet pT, generator Z pT, MET (no MET cut), number of vertices, dijet mass and "
          "pT balance.")

# ------------------------------------------------------------------ checks, open, files
fig = page()
y = heading(fig, "Checks on this run") + 14
y = note(fig, y, "Same files and lumisections as the 237-page deck.",
         "Z→ee was not touched, and all 237 Z→ee histograms came out bit-for-bit identical. The old muon setup (one of the test "
         f"versions) reproduces the old Z→μμ yields exactly (data {OLD['data']}, MC {OLD['mc']:.1f}). So every difference in "
         "these slides comes from the intended changes.") + 18
y = note(fig, y, "Every sample read all of its files.",
         "Two files had read timeouts on the first try and were rerun. One DY file cannot be read from the FNAL disk server at "
         "the moment, so the identical copy was read through the CMS redirector (same events). The job logs are now checked "
         "for the number of files read, not only for success.", INFO)
deck.save(fig)

fig = page()
y = heading(fig, "Still open, and what we suggest next") + 14
y = bullets(fig, 110, y, 1700, "Not understood or not fixed yet", [
    "A 5–6% deficit after the jet and MET cuts, the same in both channels: MC has too many events with jets and with MET.",
    "The pT(ℓℓ) pattern (low at 30–60 GeV, high at 100–150 GeV, falling above 200 GeV), the same in both channels.",
    "Muons at |η| > 2.0 are about 3% low before the jet and MET cuts.",
    "Loose tau ID veto (postponed). SF and systematic uncertainties. Only 20 files per sample so far.",
], size=23) + 20
y = bullets(fig, 110, y, 1700, "To decide", [
    "Keep the new muon setup (trigger SF from both muons, both muons pT > 26 GeV) as the default? We recommend yes: it is the "
    "POG prescription and makes the channels consistent.",
    "Which tagger and working point to use for b and for c.",
    "Then: run the full Summer22 dataset, add the SF uncertainties, and look at the pT(ℓℓ) trend with an official DY correction.",
], size=23) + 20
bullets(fig, 110, y, 1700, "Files (hists_zbzc_run3_v2/Summer22/)", [
    "slides_zbzc_btagL_3taggers_Summer22.pdf: all kinematic plots, Loose b-tag, three taggers.",
    "plots_<region>/: 49 plots for each of the 19 regions. Tables: muvar/, pu/, tagger_summary.txt, channels_summary.txt.",
], size=21)
deck.save(fig)
deck.close()
