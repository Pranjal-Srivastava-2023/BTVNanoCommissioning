"""Deck: why does MC have more MET above 50 GeV than data? Summer22, 2026-11-16 (user: separate deck, same style as the
3-tagger decks, usual selection; Delta phi study + JER test; MET XY correction applied in both runs).

Two runs, same events (20 files per sample), both = zpt setup (8 Nov selection + DY Z pT weights) + JME PuppiMET XY:
  A  hists_zbzc_run3_metxy        MC with JER smearing (nominal)
  B  hists_zbzc_run3_metxy_nojer  MC without JER smearing (data: the same files as A, symlinked)
Every stack plot is shown for A, then the same plot for B on the next page.

Inputs (make them first):
  ZBZC_RUN=zbzc_run3_metxy       ZBZC_MET=1 python plot_zbzc_run3.py Summer22   -> plots/, plots/met/, yields.txt
  ZBZC_RUN=zbzc_run3_metxy_nojer ZBZC_MET=1 python plot_zbzc_run3.py Summer22
  python plot_zbzc_met_compare.py                                              -> met_compare/ (overlays, recoil, json)
Usage:  PYTHONPATH=$PWD python make_zbzc_met_slides_pdf.py [--date "16 November 2026"]
Output: hists_zbzc_run3_metxy/Summer22/slides_zbzc_met_Summer22.pdf
(ZBZC_MET_TEST=<prefix>: layout test on hists_<prefix>metxy / hists_<prefix>metxy_nojer)
"""
import argparse
import datetime
import json
import os

PRE = os.environ.get("ZBZC_MET_TEST", "zbzc_run3_")
RA, RB = f"hists_{PRE}metxy/Summer22", f"hists_{PRE}metxy_nojer/Summer22"
os.environ["ZBZC_DECK_DIR"] = RA

import zbzc_slides_common as common  # noqa: E402
from zbzc_slides_common import (ACCENT, BODY, CHS, DARK, GOOD, INFO, OPEN, Deck, bullets, heading, image, note,  # noqa: E402
                                page, read_yields, reading_slide, setup_slides, table, text)

parser = argparse.ArgumentParser()
parser.add_argument("--date", default=None)
args = parser.parse_args()
DATE = args.date or datetime.date.today().strftime("%-d %B %Y")
common.SETUP = dict(mu_pt=26, mu_eta=2.4, zpt=True, tau=False, met_xy=True, jer="both")
OUT = f"{RA}/slides_zbzc_met_Summer22.pdf"
CMP = f"{RA}/met_compare"
J = json.load(open(f"{CMP}/met_compare.json"))
YA, _ = read_yields(f"{RA}/yields.txt")
YB, _ = read_yields(f"{RB}/yields.txt")
YZ, _ = read_yields("hists_zbzc_run3_zpt/Summer22/yields.txt")
RUNLAB = {"A": "Run A · MC with JER smearing (nominal)", "B": "Run B · MC WITHOUT JER smearing (test)"}
RUNDIR = {"A": RA, "B": RB}
MB = {"0-50": "MET < 50 GeV", "50-100": "50 < MET < 100 GeV", "100plus": "MET > 100 GeV"}
OBJ = {"j1": ("the leading jet", "Leading jet = the selected jet (pT > 30 GeV, |η| < 2.5) we study and tag."),
       "jmin": ("the closest selected jet", "Smallest Δφ between MET and any selected jet (pT > 30 GeV, |η| < 2.5)."),
       "z": ("the Z (lepton pair)", "MET along the Z (Δφ ≈ 0) or opposite (Δφ ≈ π) points to a Z / recoil mismeasurement."),
       "lep0": ("the leading lepton", "MET along a lepton would point to a lepton momentum problem."),
       "lep1": ("the second lepton", "MET along a lepton would point to a lepton momentum problem.")}

# Findings: written by hand after looking at the plots (None = no box on that page)
FINDINGS = {
    "glance": ("What the table says",
               "Without the JER smearing (B) the MET 50–100 data/MC goes from 0.70 to 0.96 (Zee) and from 0.69 to 0.96 (Zmm), "
               "in every Δφ region. The MET XY correction changes nothing here (zpt vs A). But MET < 50 drops by about 1% in B, "
               "so switching the smearing off is not the fix: see the summary.", GOOD),
    "phi_noXY": ("Without the correction",
                 "The data MET φ is not flat: Zee dips near φ ≈ 1, Zmm has fewer events at φ between 0.3 and 2.5. "
                 "χ²/ndf = 73/32 (Zee) and 108/32 (Zmm).", INFO),
    "phi_XY": ("With the correction",
               "Flatter in data: χ²/ndf goes to 50/32 (Zee) and 75/32 (Zmm), mean φ closer to 0. Not perfectly flat yet "
               "(the overall 0.94 normalisation is part of the χ²).", GOOD),
    "phi_XY_50": ("MET 50–100 GeV", "After the correction the deficit is spread over all φ: it is not a direction effect.", INFO),
    "met_overlay": ("MET without JER smearing",
                    "The red MC (no smearing) follows the data from 30 to about 120 GeV in both channels; the blue MC (nominal "
                    "smearing) is 30% above the data there. Above 120 GeV the statistics are too low to tell.", GOOD),
    "dphi_overlay": ("Where the extra MET points",
                     "With smearing, MC is too high at every Δφ, not only at 0 or π. Without smearing data/MC is close to 1 "
                     "everywhere (Zmm Δφ < 0.6 is still 0.80 ± 0.07). So it is not one jet measured too high or too low.", GOOD),
    "jany_overlay": ("Z events before the jet cut: NOT fixed",
                     "Without smearing data/MC rises from 0.49 to 0.72, but 0.72 is still far from 1, mostly at Δφ > 2 (MET "
                     "opposite to a soft or forward jet). Part of the MC MET excess here is not from the JER smearing.", OPEN),
    "recoil_Z": ("Recoil in Z events (no jet cut)",
                 "Width: without smearing MC ≈ data above qT = 50 GeV, but still ~2 GeV wider at low qT (15.7 vs 13.9 at "
                 "qT < 10). Response: data u∥ + qT is 1.5–2.5 GeV larger (recoil measured lower) with and without smearing.",
                 OPEN),
    "recoil_Zjet": ("Recoil with all cuts except MET",
                    "Width: with smearing the MC is 1–2 GeV wider than data at every qT; without it the MC agrees with data "
                    "within about 0.5 GeV. Response: u∥ + qT is 0.5–2 GeV lower in MC than in data, with and without smearing.", GOOD),
    ("pt_balance", "B"): ("The jets get worse without smearing",
                          "Compared with run A, the χ²/ndf grows from 40 to 58 (Zee) and from 110 to 144 (Zmm); the MC "
                          "peak becomes narrower than data. The smearing is needed for the selected jets.", OPEN),
}
FINDINGS["summary"] = [
    ("1. The Δφ wrap is fine; the MET XY correction is now applied",
     "Every Δφ is already folded into [0, π], so the Run 2 problem is not here. The XY correction makes the data MET φ "
     "flatter but changes the MET by only about 1 GeV and does not touch the MET > 50 deficit.", INFO),
    ("2. Most of the MET 50–100 deficit comes from the JER smearing as propagated to the MET",
     "Without the MC JER smearing, the MET 50–100 data/MC goes from 0.69–0.70 to 0.96 in both channels, at every Δφ, and the "
     "MC recoil width matches the data once a jet > 30 GeV is required.", GOOD),
    ("3. But switching it off is not the answer",
     "Without smearing the selected-jet pT balance gets worse, MET < 50 drops by about 1% and the final data/MC drops by about "
     "1.5% (MC gains the events that the smearing had pushed above 50 GeV). The smearing is right for the selected jets, so "
     "the extra MET probably comes from other jets in the type-1 sum. A candidate, NOT tested yet: the low-pT CorrT1METJet "
     "jets and gen-unmatched (pileup) jets get the random smearing, because they have no gen jet.", OPEN),
    ("4. What is still not explained",
     "In Z events before the jet cut, data/MC at MET 50–100 is still 0.72 without smearing, and the MC recoil width at low "
     "qT is still about 2 GeV wider than data. The data recoil response is also 1.5–2.5 GeV lower than in MC. Next step: smear "
     "only gen-matched jets in the type-1 MET (one-change run), then look at the unclustered / pileup part.", OPEN),
]


def r3(x):
    return f"{x[0]:.3f} ± {x[1]:.3f}"


FOOT = "Summer22 (2022 C–D), 13.6 TeV · Z→ℓℓ + jet · MET study · 20 files per sample · statistical errors only"


class CountDeck:
    """Counting pass: pages are made and dropped, only their number is kept (for the contents page)."""
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
            text(fig, 110, 34, tag, 24, ACCENT if "nominal" in tag or "Data vs" in tag else "#B03A2E", "bold")
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


    def pair(name, title, expl, sub="plots/met"):
        """The same stack plot for run A, then for run B."""
        for k in ("A", "B"):
            plot_page(f"{RUNDIR[k]}/{sub}/{name}.png", title, expl, RUNLAB[k], FINDINGS.get((name, k)))


    # ------------------------------------------------------------------ cover
    fig = page(DARK)
    text(fig, 110, 250, "Why does the MC have more MET above 50 GeV than the data?", 60, "white", "bold", width=1700, ls=1.15)
    text(fig, 110, 470, "Summer22 Z + jet: where the extra MET points (Δφ), the hadronic recoil, and what happens without the "
         "jet energy resolution smearing in MC. MET XY correction applied.", 30, "#C9D3E3", width=1650)
    text(fig, 110, 700, "Same selection, corrections and Z pT weights as the 15 November base deck (zpt). Two runs on the same "
         "events: MC with JER smearing (nominal) and MC without it.", 28, "white", "bold", width=1650)
    text(fig, 110, 880, DATE, 26, "#C9D3E3")
    deck.save(fig, foot=False)

    # ------------------------------------------------------------------ the question
    fig = page()
    y = heading(fig, "The question",
                "With every cut except the MET cut, data/MC drops from about 0.96 below MET = 50 GeV to about 0.7 between 50 and "
                "100 GeV, in both channels. The MET < 50 GeV cut removes most of these events, but we want to know why.") + 10
    y = bullets(fig, 110, y, 1700, "What we already knew (decks of 8 and 15 November)", [
        "It is not the tagger: at the same working point ParticleNet, DeepJet and RobustParT give the same MET 50–100 data/MC. "
        "The deficit follows the share of DY + light jets, not the tagger.",
        "It is not the muon or tau selection: changing the muon pT / |η| cuts or adding a τ veto does not move it.",
        "It is there even without jets: in Z events with no selected jet, data/MC falls from 1.13 (MET < 25 GeV) to 0.35 "
        "(MET 75–100 GeV). So the MC MET is too wide even when there is no jet above 30 GeV.",
        "Δφ (15 November): MC has more Z events with a soft or forward jet (pT > 15 GeV, any η) than data (49% vs 38%). "
        "At MET 50–100 the MET in MC mostly points opposite to that jet (Δφ > 2.5), where data/MC is 0.4.",
        "A first test on 28 October without the MC jet energy resolution (JER) smearing removed most of the 2022 MET tail.",
    ], size=22)
    y = note(fig, y + 10, "Our working idea (not proven yet)",
             "The JER smearing in the 2022 MC makes some soft or forward jets too energetic. These jets enter the type-1 MET and "
             "create fake MET opposite to them. This deck tests it with a full run without the smearing.", OPEN)
    deck.save(fig)

    # ------------------------------------------------------------------ what we did
    fig = page()
    y = heading(fig, "What we did",
                "Two runs on exactly the same events (20 files per sample). Data are the same in both: JER smearing only "
                "exists in MC.") + 10
    rows = [["A (nominal)", "on", "on", "zpt setup: 8 Nov selection and corrections + DY Z pT weights"],
            ["B (test)", "OFF", "on", "the same, but MC jets and type-1 MET without JER smearing"]]
    y = table(fig, 110, y, [("run", 300, "left"), ("JER smearing (MC)", 330, "left"), ("MET XY corr.", 280, "left"),
                            ("everything else", 790, "left")], rows, 22) + 20
    y = bullets(fig, 110, y, 1700, "Two things we checked or added first", [
        "Δφ wrap-around (the Run 2 problem): every Δφ is folded into [0, π] (|φ₁ − φ₂| > π → 2π − |φ₁ − φ₂|), and the MET φ "
        "is always in [−π, π]. Checked on the 15 November outputs: no entry outside [0, π]. Nothing to fix.",
        "MET XY (φ-modulation) correction from JME: it was not applied before. It is now applied in both runs (data and MC). "
        "It shifts the MET by about 1 GeV, so it cannot explain a 30% deficit, but it makes the MET direction right.",
    ], size=22) + 10
    y = bullets(fig, 110, y, 1700, "New plots", [
        "Δφ between MET and the leading jet, the closest jet, the Z and each lepton, in three MET bins (all cuts except MET).",
        "Z events before the MET and jet cuts: Δφ(MET, Z) and Δφ(MET, leading jet with pT > 15 GeV at any η), and that jet's "
        "pT and |η|.",
        "Hadronic recoil u = −(MET + pT(ℓℓ)): the part along the Z (u∥ + qT, 0 when balanced) and across it (u⊥, its width "
        "is the MET resolution), in bins of qT = pT(ℓℓ).",
        "MET φ before and after the XY correction.",
    ], size=22)
    deck.save(fig)

    # ------------------------------------------------------------------ contents (page numbers from the counting pass)
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
        ("Δφ", "Angle between MET and an object in the transverse plane, 0 to π. 0 = MET along it, π = MET opposite to it."),
        ("Recoil", "u = −(MET + pT(ℓℓ)) = everything except the two leptons. u∥ + qT ≈ 0 and narrow u⊥ = well-measured MET."),
        ("A / B", "Run A = MC with JER smearing (nominal), run B = MC without it. Same data in both. Every plot: A, then B."),
    ])

    # ------------------------------------------------------------------ results at a glance
    fig = page()
    y = heading(fig, "Results at a glance: data/MC with all cuts except MET",
                "zpt = the 15 November base deck (no MET XY correction). A = with MET XY, MC with JER smearing. "
                "B = with MET XY, MC without JER smearing.") + 6
    rows = []
    for ch, lab in CHS.items():
        for key, name in (("zpt", "zpt (15 Nov)"), ("JER", "A: JER on"), ("noJER", "B: JER off")):
            b = J[f"metbin_{ch}_{key}"]
            rows.append([f"{lab}, {name}"] + [r3(x) for x in b])
    y = table(fig, 110, y, [("", 480, "left"), ("MET < 50", 400, "right"), ("MET 50–100", 400, "right"),
                            ("MET 100–200", 420, "right")], rows, 21, shade_rows=(0, 1, 2)) + 14
    rows = []
    for ch, lab in CHS.items():
        for key, name in (("JER", "A: JER on"), ("noJER", "B: JER off")):
            b = J[f"dphi_{ch}_{key}"]
            rows.append([f"{lab}, {name}"] + [r3(x) for x in b[:3]] + [f"{100 * b[3]:.0f}%"])
    text(fig, 110, y, "MET 50–100 GeV, split by Δφ(MET, leading jet):", 22, ACCENT, "bold")
    y = table(fig, 110, y + 36, [("", 480, "left"), ("Δφ < 0.6", 330, "right"), ("0.6–2.5", 330, "right"),
                                 ("> 2.5", 330, "right"), ("MC share > 2.5", 230, "right")], rows, 21, shade_rows=(0, 1)) + 10
    if FINDINGS.get("glance"):
        note(fig, y, *FINDINGS["glance"])
    deck.save(fig)

    # ------------------------------------------------------------------ 1. MET XY correction
    SECTIONS.append(("1. MET XY correction: MET φ before and after", deck.n + 1))
    expl_phi = ("All cuts except MET, all MET values. Without the correction the MET φ is not flat (the detector and beam spot "
                "are not perfectly centred); the XY correction removes this modulation in data and in MC.")
    plot_page(f"{RA}/plots/met/met_phi_nm1_noXY.png", "MET φ before the XY correction", expl_phi, RUNLAB["A"],
              FINDINGS.get("phi_noXY"))
    plot_page(f"{RA}/plots/met/met_phi_nm1_XY.png", "MET φ after the XY correction", expl_phi, RUNLAB["A"], FINDINGS.get("phi_XY"))
    plot_page(f"{RA}/plots/met/met_phi_nm1_noXY_50-100.png", "MET φ before the XY correction, 50 < MET < 100 GeV",
              "Only the events in the MET region with the deficit.", RUNLAB["A"])
    plot_page(f"{RA}/plots/met/met_phi_nm1_XY_50-100.png", "MET φ after the XY correction, 50 < MET < 100 GeV",
              "Only the events in the MET region with the deficit.", RUNLAB["A"], FINDINGS.get("phi_XY_50"))

    # ------------------------------------------------------------------ 2. MET with and without JER
    SECTIONS.append(("2. MET with and without JER smearing", deck.n + 1))
    plot_page(f"{CMP}/met_nm1_jer_vs_nojer.png", "MET, all cuts except MET: data vs MC with and without JER smearing",
              "Black: data. Blue: MC with JER smearing (run A). Red: MC without it (run B). Lower panel: data/MC for each. "
              "Both runs have the MET XY correction.", "Data vs MC A and MC B", FINDINGS.get("met_overlay"))
    pair("met_pt_nm1", "MET, all cuts except MET", "Full stack, 0–200 GeV, log scale. The MET < 50 GeV cut is not applied here.",
         sub="plots")
    pair("met_pt_nm1_zoom", "MET, all cuts except MET, zoom 0–100 GeV", "Linear scale, data/MC from 0.8 to 1.2.", sub="plots")

    # ------------------------------------------------------------------ 3. Delta phi, all cuts except MET
    SECTIONS.append(("3. Where does the MET point? Δφ(MET, X), all cuts except MET", deck.n + 1))
    plot_page(f"{CMP}/dphi_j1_50-100_jer_vs_nojer.png", "Δφ(MET, leading jet) at 50 < MET < 100 GeV: data vs MC A and MC B",
              "If the extra MC MET comes from a mismeasured jet, the MC excess sits at Δφ ≈ 0 (jet too low) or Δφ ≈ π "
              "(jet too high), and should shrink without the JER smearing.", "Data vs MC A and MC B", FINDINGS.get("dphi_overlay"))
    for mb in ("50-100", "100plus", "0-50"):
        for obj, (oname, oexpl) in OBJ.items():
            pair(f"dphi_met_{obj}_{mb}", f"Δφ(MET, {oname}), {MB[mb]}", f"All cuts except MET. {oexpl}")

    # ------------------------------------------------------------------ 4. Z events before the MET and jet cuts
    SECTIONS.append(("4. Z events before the MET and jet cuts: the soft / forward jet", deck.n + 1))
    plot_page(f"{CMP}/stage_dphi_jany_50-100_jer_vs_nojer.png",
              "Δφ(MET, leading jet with pT > 15 GeV at any η), Z events, 50 < MET < 100 GeV",
              "Z selection only (no MET or jet cut). \"Any-η jet\" = the leading lepton-cleaned jet with pT > 15 GeV anywhere "
              "in the detector, i.e. the jets that enter the type-1 MET. Data vs MC A and MC B.", "Data vs MC A and MC B",
              FINDINGS.get("jany_overlay"))
    for mb in ("50-100", "100plus", "0-50"):
        pair(f"stage_dphi_met_jany_{mb}", f"Δφ(MET, leading any-η jet), Z events, {MB[mb]}",
             "Z selection only. Only events that have such a jet (pT > 15 GeV, any η).")
        pair(f"stage_jany_pt_{mb}", f"pT of the leading any-η jet, Z events, {MB[mb]}",
             "Z selection only, 15–150 GeV shown. Jets between 15 and 30 GeV are not selected jets but still enter the MET.")
        pair(f"stage_jany_abseta_{mb}", f"|η| of the leading any-η jet, Z events, {MB[mb]}",
             "Z selection only. |η| > 2.5: no tracker; 2.5–3.0: endcap-forward transition; > 3.0: forward calorimeter (HF).")
        pair(f"stage_dphi_met_z_{mb}", f"Δφ(MET, Z), Z events, {MB[mb]}", "Z selection only, all Z events.")

    # ------------------------------------------------------------------ 5. recoil
    SECTIONS.append(("5. Hadronic recoil: response and resolution", deck.n + 1))
    for sel, sname in (("Z", "Z events (no MET or jet cut)"), ("Zjet", "all cuts except MET")):
        plot_page(f"{CMP}/recoil_{sel}.png", f"Recoil vs pT(ℓℓ), {sname}",
                  "Top: mean of u∥ + qT (0 = the recoil balances the Z; > 0 = recoil measured too low). Bottom: RMS of u⊥ "
                  "(the MET resolution; larger = wider MET). Black: data, blue: MC with JER (A), red: MC without JER (B). "
                  "From the |u| < 100 GeV range.", "Data vs MC A and MC B", FINDINGS.get(f"recoil_{sel}"))
    QT = ["0-10", "10-20", "20-30", "30-50", "50-75", "75-100", "100-150", "150-1000"]
    for sel, sname in (("Z", "Z events"), ("Zjet", "all cuts except MET")):
        for comp, cname, cexpl in (("uperp", "u⊥", "Perpendicular to the Z: centred at 0, its width is the MET resolution."),
                                   ("upar_qt", "u∥ + qT", "Along the Z: 0 when the recoil balances the Z exactly.")):
            for q in QT:
                qlab = "qT > 150 GeV" if q == "150-1000" else f"{q.replace('-', '–')} GeV in qT"
                pair(f"recoil_{sel}_{comp}_qt{q}", f"Recoil {cname}, {sname}, {qlab}", cexpl)

    # ------------------------------------------------------------------ 6. jets with and without JER
    SECTIONS.append(("6. Usual kinematic plots with and without JER smearing", deck.n + 1))
    KIN = [("n_jet", "Number of selected jets", "Full selection except the jet requirement shows the 0 bin; jets pT > 30 GeV, |η| < 2.5."),
           ("jet_pt", "Leading jet pT", "Full selection. JER smearing changes the MC jet pT, so this tests the smearing directly."),
           ("jet_eta", "Leading jet η", "Full selection."),
           ("jet1_pt", "Second jet pT", "Full selection, events with at least two jets."),
           ("z_pt", "Z pT", "Full selection; DY Z pT weights applied."),
           ("pt_balance", "pT balance: leading jet pT / Z pT", "Full selection. 1 = jet balances the Z; JER widens this in MC."),
           ("dphi_zj", "Δφ(Z, leading jet)", "Full selection."),
           ("met_pt", "MET after the MET < 50 GeV cut", "Full selection."),
           ("npv", "Number of primary vertices", "Full selection; pileup weights applied.")]
    for var, title, expl in KIN:
        pair(var, title, expl, sub="plots")

    # ------------------------------------------------------------------ summary
    SECTIONS.append(("Summary", deck.n + 1))
    fig = page()
    y = heading(fig, "Summary") + 14
    for f in FINDINGS.get("summary", []):
        y = note(fig, y, *f) + 14
    deck.save(fig)
    return SECTIONS


CONTENTS = build(CountDeck(), [("(counting)", 1)])
deck = Deck(OUT, FOOT)
assert build(deck, CONTENTS) == CONTENTS
deck.close()
for sname, p0 in CONTENTS:
    print(f"{p0:4d}  {sname}")
