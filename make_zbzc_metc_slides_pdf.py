"""Short follow-up deck to the MET study (make_zbzc_met_slides_pdf.py): run C, Summer22, 2026-11-16.

Run C = run A (zpt setup + PuppiMET XY, MC with JER smearing) with ONE change: in the type-1 MET only gen-matched jets
are JER-smeared (jets without a gen jet, incl. all CorrT1METJet, get factor 1). The analysis jets are smeared as in A.
Same events (20 files per sample) as A and B; the data are run A's (symlinked).
  A  hists_zbzc_run3_metxy             MC with JER smearing (nominal)
  B  hists_zbzc_run3_metxy_nojer       MC without JER smearing (jets and MET)
  C  hists_zbzc_run3_metxy_jermatched  MC, JER in the type-1 MET only for gen-matched jets

Inputs: postprocess_zbzc_met_c.sh (plots of C + ZBZC_MET_C=1 python plot_zbzc_met_compare.py -> C/met_compare/)
Usage:  PYTHONPATH=$PWD python make_zbzc_metc_slides_pdf.py [--date "16 November 2026"]
Output: hists_zbzc_run3_metxy_jermatched/Summer22/slides_zbzc_metC_Summer22.pdf
"""
import argparse
import datetime
import json
import os

RA, RB, RC = ("hists_zbzc_run3_metxy/Summer22", "hists_zbzc_run3_metxy_nojer/Summer22",
              "hists_zbzc_run3_metxy_jermatched/Summer22")
os.environ["ZBZC_DECK_DIR"] = RC

import zbzc_slides_common as common  # noqa: E402
from zbzc_slides_common import (ACCENT, CHS, DARK, GOOD, INFO, OPEN, Deck, bullets, heading, image, note,  # noqa: E402
                                page, read_yields, reading_slide, setup_slides, table, text)

parser = argparse.ArgumentParser()
parser.add_argument("--date", default=None)
args = parser.parse_args()
DATE = args.date or datetime.date.today().strftime("%-d %B %Y")
common.SETUP = dict(mu_pt=26, mu_eta=2.4, zpt=True, tau=False, met_xy=True, jer="abc")
OUT = f"{RC}/slides_zbzc_metC_Summer22.pdf"
CMP = f"{RC}/met_compare"
J = json.load(open(f"{CMP}/met_compare.json"))
RUNS = {"A": RA, "B": RB, "C": RC}
KEY = {"A": "JER", "B": "noJER", "C": "matched"}
NAME = {"A": "A: JER on (nominal)", "B": "B: JER off", "C": "C: JER in MET only matched"}
Y = {k: read_yields(f"{d}/yields.txt")[0] for k, d in RUNS.items()}


def cutflow(fn):
    """{ch: {step: (MC, data)}} from the lumi-scaled 'MC sum(genWeight) ... (no SFs)' block of yields.txt."""
    lines = open(fn).read().splitlines()
    steps = next(l for l in lines if l.startswith("dataset")).split()[1:]
    out, ch = {}, None
    for i, l in enumerate(lines):
        if l.startswith("-- Summer22 ") and "sum(genWeight)" in l:
            ch = l.split()[2].rstrip(":")
            mc = [float(x) for x in lines[i + 1].split()[1:]]
            da = [float(x) for x in lines[i + 2].split()[1:]]
            out[ch] = {s: (m, d) for s, m, d in zip(steps, mc, da)}
    return out


CF = {k: cutflow(f"{d}/yields.txt") for k, d in RUNS.items()}
# chi2/ndf of the pT balance (leading jet pT / Z pT, full selection), read off the stat boxes of plots/pt_balance.png
PTBAL = {"A": ("40/40", "110/40"), "B": ("58/40", "144/40"), "C": ("45/40", "125/40")}


def r3(x):
    return f"{x[0]:.3f} ± {x[1]:.3f}"


FOOT = "Summer22 (2022 C–D), 13.6 TeV · Z→ℓℓ + jet · MET study, run C · 20 files per sample · statistical errors only"

# Findings: written by hand after looking at the plots
FINDINGS = {
    "glance": ("Run C fixes about half of the MET 50–100 deficit",
               "MET 50–100 data/MC: 0.70 → 0.84 (Zee) and 0.69 → 0.84 (Zmm), compared with 0.96 when the smearing is "
               "switched off completely (B). Better in every Δφ bin, but still below B everywhere.", OPEN),
    "met_overlay": ("The green MC sits between blue and red",
                    "From 30 to about 100 GeV run C (green) is lower than the nominal MC (blue), but still above the MC "
                    "without smearing (red) and above the data. Above about 120 GeV the statistics are too low to tell.", INFO),
    "dphi_overlay": ("Lower at every Δφ, not only at one angle",
                     "Run C is below run A in all Δφ bins. So the unmatched jets add MET in every direction, and so do the "
                     "matched jets that are still smeared in C. No single jet direction explains it.", INFO),
    "jany_overlay": ("Z events before the jet cut: most of the B gain, still far from 1",
                     "data/MC 0.50 (A) → 0.66 (C) → 0.72 (B) for Zee, 0.49 → 0.67 → 0.72 for Zmm. Run C gets most of what B "
                     "gets, so in these events the unmatched jets matter most. But even B is only 0.72.", OPEN),
    "recoil_Z": ("Recoil in Z events: C is close to B, still 2 GeV wider than data at low qT",
                 "RMS(u⊥) at qT < 10 GeV: data 13.9, A 17.1, B 15.7, C 15.9 GeV. The ~2 GeV left at low qT does not come "
                 "from the JER smearing at all. The response (u∥ + qT) is the same in A, B and C, 1–2.5 GeV below data.", OPEN),
    "recoil_Zjet": ("Recoil with all cuts except MET: C halfway between A and B",
                    "RMS(u⊥) in C is about 0.5 GeV above B and 0.5–1 GeV below A at every qT. B matches the data best "
                    "(within 0.5 GeV). The response is again the same in A, B and C.", INFO),
}
FINDINGS["summary"] = [
    ("1. The smearing of jets without a gen jet is about half of the MET 50–100 deficit",
     "Run C changes only the MET (the analysis jets are the same as in A, the cutflow is identical up to the MET cut). "
     "MET 50–100 data/MC goes from 0.69–0.70 to 0.84 in both channels. Switching all smearing off (B) gives 0.96.", GOOD),
    ("2. The other half comes from the smearing of gen-matched jets in the MET",
     "That is the only smearing still in the MET of run C. The matched-jet smearing scales the jet by the measured "
     "resolution (the JME-recommended method). Since it still adds too much MET, possible causes are: the JER scale factors "
     "for the jets that enter the MET (soft or forward), or the way the smearing is propagated to the MET. Not tested.", OPEN),
    ("3. What does not change between A, B and C",
     "The recoil response (data recoil 1–2.5 GeV lower than MC) and about 2 GeV of extra MC recoil width at low qT in Z "
     "events. These are not from the JER smearing. In Z events before the jet cut, data/MC at MET 50–100 is 0.66–0.67 in C "
     "and 0.72 even in B.", OPEN),
    ("4. Effect on the final numbers",
     "Better MET modelling moves MC events from above 50 GeV to below it, so the final data/MC goes down: 0.971 / 0.964 (A), "
     "0.959 / 0.952 (B), 0.954 / 0.945 (C) for Zee / Zmm. Before the MET cut all three runs have the same data/MC.", INFO),
]


class CountDeck:
    def __init__(self):
        self.n = 0

    def save(self, fig, foot=True):
        import matplotlib.pyplot as plt
        self.n += 1
        plt.close(fig)


def build(deck, CONTENTS):

    def plot_page(path, title, expl, tag=None, finding=None):
        fig = page()
        if tag:
            text(fig, 110, 34, tag, 24, ACCENT, "bold")
        y = text(fig, 110, 70, title, 40, DARK, "bold", width=1700, ls=1.15)
        if expl:
            y = text(fig, 110, y + 6, expl, 22, BODY, width=1700)
        hmax = 1025 - y - 12
        if finding:
            hmax -= 110
        image(fig, path, y + 12, hmax=hmax)
        if finding:
            note(fig, 1025 - 103, finding[0], finding[1], finding[2] if len(finding) > 2 else INFO, size=19)
        deck.save(fig)

    BODY = common.BODY
    ABC = "Data vs MC A, B and C"
    LEG = "Black: data. Blue: run A (JER on). Red: run B (JER off). Green: run C (JER in MET only for gen-matched jets)."

    # ------------------------------------------------------------------ cover
    fig = page(DARK)
    text(fig, 110, 250, "MET above 50 GeV: smearing only the gen-matched jets in the MET", 60, "white", "bold",
         width=1700, ls=1.15)
    text(fig, 110, 470, "Follow-up to the MET study of 16 November (runs A and B). One extra run, C, with one change: "
         "in the type-1 MET, only jets that have a matching generator jet get the JER smearing.", 30, "#C9D3E3", width=1650)
    text(fig, 110, 700, "Summer22, same events, selection, corrections and Z pT weights as runs A and B.", 28, "white",
         "bold", width=1650)
    text(fig, 110, 880, DATE, 26, "#C9D3E3")
    deck.save(fig, foot=False)

    # ------------------------------------------------------------------ question
    fig = page()
    y = heading(fig, "The question",
                "In the MET deck, switching off the MC JER smearing (run B) brought the MET 50–100 data/MC from 0.7 to 0.96. "
                "But B also made the selected jets worse, so switching the smearing off is not the fix.") + 10
    y = bullets(fig, 110, y, 1700, "Why we suspected the jets without a gen jet", [
        "The JER smearing has two modes. A jet with a matching generator jet is scaled: its pT moves towards or away from "
        "the gen-jet pT by the known resolution. A jet without a gen jet gets a random (stochastic) smearing instead.",
        "The type-1 MET is built from all jets above 15 GeV plus the low-pT jets (CorrT1METJet). The low-pT jets have no gen "
        "jet in NanoAOD (our code gives them Genpt = −1), and pileup jets have none either. So all of them get the random "
        "smearing, and each random shift adds MET.",
        "The selected jets (pT > 30 GeV, |η| < 2.5) are almost all gen-matched, so they are mostly scaled, not randomly "
        "smeared.",
    ], size=22)
    y = note(fig, y + 10, "Run C tests this",
             "Keep everything as in run A, but in the type-1 MET leave the jets without a gen jet unsmeared. If the random "
             "smearing is the cause, C should look like B for the MET and like A for the jets.", INFO)
    deck.save(fig)

    # ------------------------------------------------------------------ what we did
    fig = page()
    y = heading(fig, "What we did",
                "Three runs on exactly the same events (20 files per sample). The data are the same in all three: the JER "
                "smearing only exists in MC.") + 10
    rows = [["A (nominal)", "smeared", "all jets smeared", "MET 16 Nov deck"],
            ["B (test)", "NOT smeared", "no smearing", "MET 16 Nov deck"],
            ["C (this deck)", "smeared (= A)", "only gen-matched jets smeared", "new"]]
    y = table(fig, 110, y, [("run", 300, "left"), ("analysis jets", 340, "left"), ("jets in the type-1 MET", 620, "left"),
                            ("shown in", 440, "left")], rows, 22, shade_rows=(2,)) + 24
    y = bullets(fig, 110, y, 1700, "How run C works", [
        "New workflow Zb_Zc_ratio_metxy_jermatched (option jer_met = \"matched\"). Everything else is the zpt setup + MET "
        "XY correction, as in A and B.",
        "In the type-1 MET, a jet with no gen jet (Genpt ≤ 0) keeps its unsmeared pT. Gen-matched jets are smeared as in A.",
        "The selected (analysis) jets are smeared exactly as in A: the MC cutflow of C equals A's up to the MET cut.",
        "Quick test before the run, 20k DY events (pT(ℓℓ) 100–200 sample): MC fraction with MET > 50 GeV is 40.2% (A), "
        "39.1% (C), 37.3% (B); jets identical to A.",
    ], size=22)
    deck.save(fig)

    # ------------------------------------------------------------------ contents
    fig = page()
    y = heading(fig, "Contents") + 10
    rows = [["The question; what we did; analysis setup; how to read; results at a glance", "2–8"]]
    for i, (sname, p0) in enumerate(CONTENTS):
        p1 = CONTENTS[i + 1][1] - 1 if i + 1 < len(CONTENTS) else p0
        rows.append([sname, f"{p0}–{p1}" if p1 > p0 else str(p0)])
    table(fig, 110, y, [("section", 1460, "left"), ("pages", 240, "right")], rows, 24)
    deck.save(fig)
    SECTIONS = []
    setup_slides(deck)
    reading_slide(deck, extra=[
        ("MET bins", "MET < 50, 50–100 and > 100 GeV, with every other cut applied (\"all cuts except MET\")."),
        ("Recoil", "u = −(MET + pT(ℓℓ)) = everything except the two leptons. u∥ + qT ≈ 0 and narrow u⊥ = well-measured MET."),
        ("A / B / C", "A = MC with JER smearing (nominal), B = no smearing, C = smearing in the MET only for gen-matched jets."),
    ])

    # ------------------------------------------------------------------ results at a glance
    fig = page()
    y = heading(fig, "Results at a glance: data/MC with all cuts except MET",
                "All three runs have the MET XY correction. Same data in all three.") + 6
    rows = []
    for ch, lab in CHS.items():
        for k in "ABC":
            rows.append([f"{lab}, {NAME[k]}"] + [r3(x) for x in J[f"metbin_{ch}_{KEY[k]}"]])
    y = table(fig, 110, y, [("", 640, "left"), ("MET < 50", 350, "right"), ("MET 50–100", 350, "right"),
                            ("MET 100–200", 360, "right")], rows, 20, shade_rows=(2, 5)) + 12
    rows = []
    for ch, lab in CHS.items():
        for k in "ABC":
            b = J[f"dphi_{ch}_{KEY[k]}"]
            rows.append([f"{lab}, {NAME[k]}"] + [r3(x) for x in b[:3]]
                        + [f"{100 * b[3]:.0f}%"])
    text(fig, 110, y, "MET 50–100 GeV, split by Δφ(MET, leading jet):", 21, ACCENT, "bold")
    y = table(fig, 110, y + 34, [("", 640, "left"), ("Δφ < 0.6", 280, "right"), ("0.6–2.5", 280, "right"),
                                 ("> 2.5", 280, "right"), ("MC share > 2.5", 220, "right")], rows, 20,
              shade_rows=(2, 5)) + 8
    note(fig, y, *FINDINGS["glance"], size=20)
    deck.save(fig)

    # ------------------------------------------------------------------ 1. overlays
    SECTIONS.append(("1. MET and Δφ: data vs MC A, B and C", deck.n + 1))
    plot_page(f"{CMP}/met_nm1_jer_vs_nojer.png", "MET, all cuts except MET", LEG + " Lower panel: data/MC for each.",
              ABC, FINDINGS["met_overlay"])
    plot_page(f"{CMP}/dphi_j1_50-100_jer_vs_nojer.png", "Δφ(MET, leading jet) at 50 < MET < 100 GeV, all cuts except MET",
              LEG, ABC, FINDINGS["dphi_overlay"])
    plot_page(f"{CMP}/stage_dphi_jany_50-100_jer_vs_nojer.png",
              "Δφ(MET, leading jet with pT > 15 GeV at any η), Z events, 50 < MET < 100 GeV",
              "Z selection only (no MET or jet cut): the jets that enter the type-1 MET. " + LEG, ABC,
              FINDINGS["jany_overlay"])

    # ------------------------------------------------------------------ 2. recoil
    SECTIONS.append(("2. Hadronic recoil: response and resolution", deck.n + 1))
    for sel, sname in (("Z", "Z events (no MET or jet cut)"), ("Zjet", "all cuts except MET")):
        plot_page(f"{CMP}/recoil_{sel}.png", f"Recoil vs pT(ℓℓ), {sname}",
                  "Top: mean of u∥ + qT (0 = the recoil balances the Z; > 0 = recoil measured too low). Bottom: RMS of u⊥ "
                  "(the MET resolution). " + LEG, ABC, FINDINGS[f"recoil_{sel}"])

    # ------------------------------------------------------------------ 3. final yields and jets
    SECTIONS.append(("3. Effect on the selection and on the jets", deck.n + 1))
    fig = page()
    y = heading(fig, "Effect on the yields and on the pT balance",
                "Lumi-scaled MC without SFs (the cutflow in yields.txt), then the full selection with all weights.") + 6
    rows = []
    for ch, lab in CHS.items():
        for k in "ABC":
            c = CF[k][ch]
            fz, fm, fj = (c[s][1] / c[s][0] for s in ("Zmass", "MET", "jet"))
            rows.append([f"{lab}, {NAME[k]}", f"{fz:.3f}", f"{fm:.3f}", f"{fj:.3f}", r3((Y[k][ch]["data"] / Y[k][ch]["mc"],
                         Y[k][ch]["data"] / Y[k][ch]["mc"] * ((1 / Y[k][ch]["data"]) + (Y[k][ch]["mce"] / Y[k][ch]["mc"]) ** 2)
                         ** 0.5)), PTBAL[k][0 if ch == "Zee" else 1]])
    y = table(fig, 110, y, [("", 560, "left"), ("Z (no SFs)", 210, "right"), ("+ MET (no SFs)", 250, "right"),
                            ("+ jet (no SFs)", 230, "right"), ("final, all weights", 290, "right"),
                            ("pT bal. χ²/ndf", 220, "right")], rows, 20, shade_rows=(2, 5)) + 14
    y = note(fig, y, "The jets of C are the jets of A; only the MET changed",
             "Up to the Z selection the three runs agree (B differs slightly earlier, at the jet veto map, because its jets are "
             "not smeared). The MET < 50 cut keeps more MC in B and C, so their final data/MC is 1–2% lower than A. "
             "The pT balance χ² of C (45 and 125) is between A (40, 110) and B (58, 144); since C's jets are identical to A, "
             "the change comes only from which events pass the MET cut.", INFO, size=20)
    deck.save(fig)
    plot_page(f"{RC}/plots/met_pt_nm1.png", "MET, all cuts except MET: full stack, run C",
              "0–200 GeV, log scale. The MET < 50 GeV cut is not applied here.", NAME["C"])
    plot_page(f"{RC}/plots/met/dphi_met_j1_50-100.png", "Δφ(MET, leading jet), 50 < MET < 100 GeV: full stack, run C",
              "All cuts except MET.", NAME["C"])
    plot_page(f"{RC}/plots/pt_balance.png", "pT balance (leading jet pT / Z pT): full stack, run C",
              "Full selection. Same jets as run A; the stat box gives the χ²/ndf quoted on the previous page.", NAME["C"])

    # ------------------------------------------------------------------ summary
    SECTIONS.append(("Summary and possible next steps", deck.n + 1))
    fig = page()
    y = heading(fig, "Summary") + 10
    for f in FINDINGS["summary"]:
        y = note(fig, y, *f, size=21) + 12
    deck.save(fig)
    fig = page()
    y = heading(fig, "Possible next steps (not done, need your OK)") + 10
    y = bullets(fig, 110, y, 1700, "", [
        "Find which matched jets carry the extra MET: split the MET change from the smearing by jet pT (15–30 / > 30 GeV) and "
        "|η| (< 2.5, 2.5–3.0, > 3.0). This needs no new physics run, only an extra histogram in a short run.",
        "Check the JER scale factors for those jets, and which gen jet we use for the scaling (NanoAOD genJetIdx) against the "
        "JME matching (ΔR < R/2 and |pT − pT_gen| < 3σ_JER), for Summer22.",
        "Compare our type-1 MET propagation with the JME recipe (which jets, which pT threshold, EM fraction, muon "
        "subtraction).",
        "The recoil response and the extra low-qT width in Z events are not from JER: look at the unclustered / pileup part "
        "separately.",
    ], size=23)
    note(fig, y + 20, "Bottom line",
         "About half of the MC MET excess at 50–100 GeV comes from random smearing of jets without a gen jet in the type-1 "
         "MET; the other half from the smearing of gen-matched jets in the MET. Run C does not change the selected jets.",
         GOOD)
    deck.save(fig)
    return SECTIONS


CONTENTS = build(CountDeck(), [("(counting)", 1)])
deck = Deck(OUT, FOOT)
assert build(deck, CONTENTS) == CONTENTS
deck.close()
for sname, p0 in CONTENTS:
    print(f"{p0:4d}  {sname}")
print(OUT)
