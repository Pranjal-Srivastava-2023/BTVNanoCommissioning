"""Deck for the group meeting of 23 November 2026: MET > 50 GeV study, Summer22.

Answers the two questions from the previous meeting (is JER already in NanoAOD / should JER stay off), compares our
type-1 MET with the JME recipe (documentation + talks uploaded to src/BTVNanoCommissioning/*.pdf), Phase 1 (which jets
make the MC MET grow under JER, MC only: study_zbzc_met_jer_split.py -> hists_zbzc_run3_metsplit/) and Phase 2 (data/MC
for MET versions with the JER removed for those jets: run zbzc_run3_metvar, plot_zbzc_metvar.py -> metvar/).

Usage:  PYTHONPATH=$PWD python make_zbzc_metvar_slides_pdf.py [--date "23 November 2026"]
        (+ ZBZC_PPTX=1 ZBZC_CLEAN=1 PYTHONPATH=$PWD:/uscms_data/d3/psrivast/pylibs_pptx for the editable .pptx)
Output: hists_zbzc_run3_metvar/Summer22/slides_zbzc_metvar_Summer22.pdf
"""
import argparse
import datetime
import json
import os

RV = os.environ.get("ZBZC_METVAR_DIR", "hists_zbzc_run3_metvar/Summer22")
RS = "hists_zbzc_run3_metsplit/Summer22"
os.environ["ZBZC_DECK_DIR"] = RV

import zbzc_slides_common as common  # noqa: E402
from zbzc_slides_common import (ACCENT, CHS, DARK, GOOD, INFO, OPEN, Deck, bullets, heading, image, note,  # noqa: E402
                                page, setup_slides, table, text)

parser = argparse.ArgumentParser()
parser.add_argument("--date", default="23 November 2026")
args = parser.parse_args()
DATE = args.date
common.SETUP = dict(mu_pt=26, mu_eta=2.4, zpt=True, tau=False, met_xy=True, jer="metvar")
OUT = f"{RV}/slides_zbzc_metvar_Summer22.pdf"
MV = f"{RV}/metvar"
J = json.load(open(f"{MV}/metvar.json"))
P1 = json.load(open(f"{RS}/met_jer_split.json"))
BODY = common.BODY
FOOT = "Summer22 (2022 C–D), 13.6 TeV · Z→ℓℓ + jet · MET > 50 GeV study · statistical errors only"

VERS = ["all", "noJERhighSF", "noJERfwd", "noJERsoftfwd", "noJERsoft", "noJERcorrT1", "noJER", "B"]
VNAME = {"all": "JER for all jets in the MET (nominal, run A)",
         "noJERhighSF": "no JER in the MET for 2.65 < |η| < 2.964",
         "noJERfwd": "no JER in the MET for 2.5 < |η| < 3.139",
         "noJERsoftfwd": "no JER in the MET for pT < 30 and 2.5 < |η| < 3.139",
         "noJERsoft": "no JER in the MET for pT < 30 GeV",
         "noJERcorrT1": "no JER in the MET for the CorrT1METJet jets",
         "noJER": "no JER in the MET at all",
         "B": "run B: no JER anywhere (jets and MET)"}
VSHORT = {"all": "nominal (A)", "noJERhighSF": "no JER 2.65–2.964", "noJERfwd": "no JER 2.5–3.139",
          "noJERsoftfwd": "no JER soft & 2.5–3.139", "noJERsoft": "no JER pT < 30", "noJERcorrT1": "no JER CorrT1",
          "noJER": "no JER in MET", "B": "run B (all off)"}


def r3(x):
    return f"{x[0]:.3f} ± {x[1]:.3f}"


def p1(ch, key, stage="Z+jet (all cuts except MET)"):
    return P1[f"{ch} | {stage}"][key]["ratio_noJER"]


# ---------------------------------------------------------------- findings (written by hand after looking at the plots)
FINDINGS = json.load(open(f"{MV}/findings.json")) if os.path.exists(f"{MV}/findings.json") else {}


def F(key, default=("(to be written)", "", INFO)):
    v = FINDINGS.get(key, default)
    st = v[2] if not isinstance(v[2], str) else {"GOOD": GOOD, "OPEN": OPEN, "INFO": INFO}[v[2]]
    return (v[0], v[1], st)


class CountDeck:
    def __init__(self):
        self.n = 0

    def save(self, fig, foot=True):
        import matplotlib.pyplot as plt
        from zbzc_slides_common import dropped
        self.n += 0 if dropped(fig) else 1
        plt.close(fig)


def build(deck, CONTENTS):
    SECTIONS = []

    def plot_page(path, title, expl, tag=None, finding=None):
        fig = page()
        if tag:
            text(fig, 110, 34, tag, 24, ACCENT, "bold")
        y = text(fig, 110, 70, title, 40, DARK, "bold", width=1700, ls=1.15)
        if expl:
            y = text(fig, 110, y + 6, expl, 22, BODY, width=1700)
        hmax = 1025 - y - 12
        if finding:
            hmax -= common.note_height(finding[0], finding[1], size=19) + 8
        image(fig, path, y + 12, hmax=hmax)
        if finding:
            note(fig, 1025 - common.note_height(finding[0], finding[1], size=19), finding[0], finding[1],
                 finding[2], size=19)
        deck.save(fig)

    # ------------------------------------------------------------------ cover
    fig = page(DARK)
    text(fig, 110, 220, "MET above 50 GeV: is the JER counted twice, and which jets make the MC MET too large?",
         58, "white", "bold", width=1700, ls=1.15)
    text(fig, 110, 470, "Answers to the questions from the last meeting, a check of our type-1 MET against the JME recipe, "
         "and one new run with the JER smearing removed from the MET for the jets that cause the excess.", 30, "#C9D3E3",
         width=1650)
    text(fig, 110, 720, "Summer22 (2022 C–D), Z→ee and Z→μμ + jet, same events and selection as the MET deck of 16 November.",
         27, "white", "bold", width=1650)
    text(fig, 110, 880, DATE, 26, "#C9D3E3")
    deck.save(fig, foot=False)

    # ------------------------------------------------------------------ summary first
    fig = page()
    y = heading(fig, "Summary") + 6
    for f in FINDINGS.get("summary", [["(to be written)", "", "INFO"]]):
        y = note(fig, y, f[0], f[1], {"GOOD": GOOD, "OPEN": OPEN, "INFO": INFO}[f[2]], size=20) + 10
    deck.save(fig)

    # ------------------------------------------------------------------ contents
    fig = page()
    y = heading(fig, "Contents") + 10
    rows = []
    for i, (sname, p0) in enumerate(CONTENTS):
        p1_ = CONTENTS[i + 1][1] - 1 if i + 1 < len(CONTENTS) else p0
        rows.append([sname, f"{p0}–{p1_}" if p1_ > p0 else str(p0)])
    table(fig, 110, y, [("section", 1460, "left"), ("pages", 240, "right")], rows, 24)
    deck.save(fig)

    # ------------------------------------------------------------------ 1. JER in NanoAOD?
    SECTIONS.append(("1. Is the JER already in the NanoAOD (double counting)?", deck.n + 1))
    fig = page()
    y = heading(fig, "Question 1: is the JER smearing already in the NanoAOD, so that we apply it twice?",
                "If the NanoAOD jets or MET were already smeared, our smearing would come on top and make the MC MET too "
                "wide. We checked the code and the files.") + 6
    y = bullets(fig, 110, y, 1700, "Our code never starts from the corrected NanoAOD values", [
        "Jets: raw pT = (1 − Jet_rawFactor) × Jet_pt, then our JEC (Summer22_22Sep2023_V4), then our JER (MC only).",
        "MET: starts from RawPuppiMET (the plain sum of the PUPPI particles), not from PuppiMET. The low-pT jets of the MET "
        "start from CorrT1METJet_rawPt.",
        "So even if something were smeared in the NanoAOD, we would undo it before applying our own corrections.",
    ], size=21)
    rows = [["NanoAOD Jet_pt / (raw pT × our JEC)", "random spread ~9% at 20 GeV",
             "spread 0.3–0.9% (pT 15 → 100+ GeV)"],
            ["MC jet resolution |η| < 1.3 vs gen jets (20–30 / 50–100 GeV)", "SF × MC res.: 0.202 / 0.131",
             "0.188 / 0.111 (MC res.: 0.182 / 0.118)"],
            ["NanoAOD PuppiMET − our type-1 MET (JEC only)", "≈ our MET with JER", "median +0.06 GeV, width 1.3 GeV"],
            ["NanoAOD PuppiMET − our type-1 MET (JEC + JER)", "≈ 0", "median −1.05 GeV, width 5.4 GeV"]]
    y = table(fig, 110, y + 6, [("check (one DY file, 40k events)", 760, "left"), ("if NanoAOD were smeared", 420, "left"),
                                ("what we find", 520, "left")], rows, 20) + 14
    note(fig, y, "Answer: no double counting",
         "The NanoAOD jets and PuppiMET contain the JEC only, no JER smearing, and our code starts from the raw values anyway. "
         "The JER smearing is applied exactly once, by us, in MC.", GOOD, size=21)
    deck.save(fig)

    # ------------------------------------------------------------------ 2. JME recipe
    SECTIONS.append(("2. What JME recommends, and our code compared with it", deck.n + 1))
    fig = page()
    y = heading(fig, "Question 2: can we just keep the JER off? What the JME documentation says",
                "From the JME JERC pages and the worked examples (cms-jerc.web.cern.ch, April 2026).") + 6
    y = bullets(fig, 110, y, 1700, "Jet Energy Resolution page", [
        "\"Measurements show that the JER in data is worse than in the simulation and the jets in MC need to be smeared to "
        "describe the data.\" Apply JEC first, then JER; only in simulation.",
        "Hybrid method: a jet with a matching gen jet (ΔR < R/2 = 0.2 and |pT − pT,gen| < 3σ·pT) is scaled, "
        "c = 1 + (s − 1)(pT − pT,gen)/pT; any other jet gets a random smearing, c = 1 + N(0, σ)·√(s² − 1).",
    ], size=21)
    y = bullets(fig, 110, y + 10, 1700, "Type-1 MET page and worked example (Type1MET.pdf)", [
        "\"Each jet receives the full JEC/JER chain before contributing to the MET update\": step 7 is JER smearing (MC).",
        "The Jet and the low-pT CorrT1METJet collections are merged, and \"each jet is processed uniformly\", so the "
        "CorrT1METJet jets are smeared too. A jet enters the MET if its final (smeared) pT > 15 GeV, |η| < 5.2 and EM "
        "fraction < 0.9.",
        "The PuppiMET stored in the NanoAOD uses the JEC of the production; if the JEC changed, recompute it. "
        "That is why the NanoAOD PuppiMET has no smearing: it is a starting point, not a recommendation to skip the smearing.",
    ], size=21)
    note(fig, y + 10, "Answer: switching JER off is not what JME recommends",
         "The recipe smears the MC jets and propagates the smearing into the type-1 MET. Our nominal run (A) does exactly "
         "that. Run B (JER off) and the versions in this deck are tests, not a recommended setup.", OPEN, size=21)
    deck.save(fig)

    fig = page()
    y = heading(fig, "Our type-1 MET compared with the recipe, step by step",
                "workflow Zb_Zc_ratio → correction.py (JME_shifts, calc_T1_MET), Summer22 NanoAODv12, PUPPI jets.") + 4
    rows = [["raw jet pT, muon-subtracted: pT,raw × (1 − muonSubtrFactor)", "yes", ""],
            ["L1 offset: identity for PUPPI (no L1 subtraction)", "yes", ""],
            ["JEC L1L2L3Res, Summer22_22Sep2023_V4", "yes", ""],
            ["JER smearing (MC), Summer22_22Sep2023_JRV2, jer_smear.json", "yes", ""],
            ["Jet + CorrT1METJet merged, both smeared", "yes", ""],
            ["selection: smeared pT > 15, |η| < 5.2, EM fraction < 0.9", "yes", ""],
            ["MET shift Σ (pT,full − pT,L1), φ (+ muonSubtrDeltaPhi if present)", "yes", ""],
            ["unclustered uncertainty as a vector shift from the NanoAOD (Type1METUnc.pdf)", "yes", ""],
            ["gen matching ΔR < 0.2 and 3σ", "no: any NanoAOD genJetIdx",
             f"MET > 50 frac. ×1.075 → ×1.068"],
            ["JEC factor at raw pT (JME talk 2 Feb) vs at muon-subtracted pT", "muon-subtracted",
             f"no change: ×{p1('Zee', 'JER: all (= run A)'):.3f} vs ×{p1('Zee', 'talk: JEC at raw pT, JER all'):.3f}"],
            ["CorrT1METJet have no gen link: matched to GenJets by ΔR instead", "not done", "no change: ×1.075 → ×1.075"]]
    y = table(fig, 110, y, [("recipe step", 1000, "left"), ("in our code", 330, "left"),
                            ("effect on MC MET (tested)", 370, "left")], rows, 19, shade_rows=(8, 9, 10)) + 12
    note(fig, y, "Our MET follows the recipe; the two small differences do not matter",
         "The ×-numbers are the MC fraction of events with MET 50–100 GeV (or > 50) with JER divided by without JER, on the "
         "same events. The differences change it by less than 1%, while the JER itself changes it by about 40%.", GOOD,
         size=20)
    deck.save(fig)

    fig = page()
    y = heading(fig, "Two JME talks of 2 February 2026 (uploaded with the documentation)") + 4
    y = bullets(fig, 110, y, 1700, "N. Norjoharuddeen, \"MET Type-1 correction with NanoAODs\" (JME General)", [
        "Step-by-step recipe that reproduces CMSSW, JEC only (no JER). Closure: recomputed MET within 0.5% of PuppiMET for "
        "99.9999% of events (Summer24).",
        "Evaluate the JEC at the raw jet pT, apply it to the muon-subtracted pT. We evaluate it at the muon-subtracted pT: "
        "tested, no effect on our MET (previous page).",
    ], size=21)
    y = bullets(fig, 110, y + 10, 1700, "M. Malucchi, \"Run 3 MET performance\" (DPG-PH JetMET), Z→μμ DY MC only, no JER, no data", [
        "For 2022 NanoAODv12, the type-1 MET recomputed with JEC has a worse resolution and a larger high-MET tail than the "
        "stored PuppiMET (\"when re-applying the JEC for 2022 the MET resolution gets worse than PuppiMET; for 2023 this "
        "effect is much smaller\"). With the CorrT1METJet jets added, even the MET recomputed without new JEC no longer "
        "has the PuppiMET resolution.",
        "\"DYJetsToLL_M-50_Nanov12_2022preEE and DYto2L-4Jets_MLL-50_Nanov12_preEE seem problematic for the MET resolution\"; "
        "the NanoAODv15 version does not show it.",
        "Outlook of that talk: compute the JEC at the raw pT; include jet veto map, MET filters, a forward-jet veto "
        "(slides by Anna) and a jet ID cut.",
    ], size=21)
    note(fig, y + 10, "What this means for us",
         "Same campaign and same kind of sample as ours. Their effect comes from re-applying the JEC, without JER. In our "
         f"files the stored PuppiMET has ×{p1('Zee', 'NanoAOD PuppiMET (as stored)'):.2f} (Zee) / "
         f"×{p1('Zmm', 'NanoAOD PuppiMET (as stored)'):.2f} (Zμμ) the MET 50–100 fraction of our JEC-only MET, while "
         f"the JER gives ×{p1('Zee', 'JER: all (= run A)'):.2f} / ×{p1('Zmm', 'JER: all (= run A)'):.2f}: for us the JER is "
         "the larger effect. Their remark that the 2022 v12 DY MET is problematic could be part of what stays even with "
         "JER off (the ~2 GeV wider MC recoil); not tested.", INFO, size=20)
    deck.save(fig)

    # ------------------------------------------------------------------ 3. Phase 1
    SECTIONS.append(("3. Which jets make the MC MET grow under JER (MC only)", deck.n + 1))
    fig = page()
    y = heading(fig, "Which jets in the MET cause the excess? Method",
                "MC only: 65 DY files (stitched in LHE pT(ℓℓ) as in the workflow), simplified selection (no lepton SFs), "
                "same events for every line.") + 6
    y = bullets(fig, 110, y, 1700, "", [
        "Build the type-1 MET many times for the same events, each time applying the JER only to one class of jets "
        "(by collection, gen matching, pT, |η|), and compare with the MET without JER.",
        "Number shown: MC fraction of events with 50 < MET < 100 GeV (all cuts except MET) divided by the same fraction "
        "without JER in the MET. 1 = this class does not change the MET.",
        f"Check: all jets smeared gives ×{p1('Zee', 'JER: all (= run A)'):.2f} (Zee) and ×{p1('Zmm', 'JER: all (= run A)'):.2f} "
        "(Zmm). In the full runs, data/MC went from 0.70 (JER on) to 0.96 (JER off), a factor 1.38. So this reproduces the effect.",
    ], size=21)
    rows = []
    for key, lab in [("JER: all (= run A)", "all jets (nominal)"),
                     ("JER: |eta| 2.65-2.853 only", "only 2.65 < |η| < 2.853 (JER SF 1.60)"),
                     ("JER: |eta| 2.5-3.0 only", "only 2.5 < |η| < 3.0"),
                     ("JER: pT 0-30 & |eta| 2.5-5.2 only", "only pT < 30 and |η| > 2.5"),
                     ("JER: JEC pT 0-20 only", "only pT < 20 GeV"),
                     ("JER: CorrT1METJet only", "only CorrT1METJet"),
                     ("JER: analysis-type jets only (pT>30, |eta|<2.5)", "only pT > 30, |η| < 2.5 (selected-jet type)"),
                     ("JER: |eta| 0-1.3 only", "only |η| < 1.3"),
                     ("JER: all except |eta| 2.5-3.139", "all except 2.5 < |η| < 3.139")]:
        rows.append([lab, f"×{p1('Zee', key):.3f}", f"×{p1('Zmm', key):.3f}"])
    y = table(fig, 110, y + 4, [("JER applied in the MET to …", 1000, "left"), ("Zee", 300, "right"),
                                ("Zmm", 300, "right")], rows, 20, shade_rows=(1,)) + 10
    deck.save(fig)
    plot_page(f"{RS}/plots/met_jer_split_zjet.png", "How much each class of jets raises the MC MET 50–100 fraction",
              "Bars: increase in % when only these jets are smeared in the MET (blue Zee, red Zμμ). Common x scale.",
              "MC only", F("p1_plot", ("One |η| bin carries about half of the effect",
                                       "Jets with 2.65 < |η| < 2.853 alone raise the MET 50–100 fraction by about 18–20%, "
                                       "almost half of the full 37–39%. These are mostly soft jets (pT < 30). The jets we "
                                       "select (pT > 30, |η| < 2.5) give only about 8%.", "INFO")))
    fig = page()
    y = heading(fig, "Why that |η| bin: the JER scale factors of Summer22",
                "Summer22_22Sep2023_JRV2_MC_ScaleFactor_AK4PFPuppi (below 121 GeV one value per |η| bin) and the MC "
                "resolution at ρ = 20.") + 6
    rows = [["0 – 1.305", "1.06 – 1.13", "1.5 – 2.2%", "1.03 – 1.11", "16–24% / 10–12%"],
            ["1.305 – 2.5", "1.02 – 1.30", "3 – 12%", "0.92 – 1.22", "28–44% / 12–13%"],
            ["2.5 – 2.65", "1.22", "5.9%", "1.15", "56% / 13%"],
            ["2.65 – 2.853", "1.60", "9.6%", "1.45", "60% / 14%"],
            ["2.853 – 2.964", "1.64", "16.9%", "1.36", "75% / 16%"],
            ["2.964 – 3.139", "1.21", "11.8%", "1.06", "52% / 19%"],
            ["3.139 – 5.191", "1.12", "13.4%", "0.97", "35–38% / 9–11%"]]
    y = table(fig, 110, y, [("|η|", 330, "left"), ("JER SF", 300, "right"), ("SF uncertainty", 330, "right"),
                            ("SF − 1σ", 260, "right"), ("MC resolution at 15 / 100 GeV", 480, "right")], rows, 22,
              shade_rows=(3, 4)) + 16
    note(fig, y, "Very large smearing for soft jets at 2.65 < |η| < 2.964",
         "With SF = 1.6 and an MC resolution of 60–75% at 15 GeV, a random smearing has a width of √(1.6² − 1) × 60% ≈ 75% of "
         "the jet pT. Many soft jets there are in the MET sum (CorrT1METJet or jets above 15 GeV), so each event gets a "
         "large random MET kick. Even the SF − 1σ (1.45 and 1.36) is still large: the quoted SF uncertainty cannot "
         "cover the difference to the data.", OPEN, size=21)
    deck.save(fig)

    # ------------------------------------------------------------------ 4. Phase 2
    SECTIONS.append(("4. New run: data/MC with the JER removed from the MET for those jets", deck.n + 1))
    fig = page()
    y = heading(fig, "New run: the MET in seven versions, side by side, on the same events",
                "Run zbzc_run3_metvar = run A (zpt setup, MET XY correction, Z pT weights, 20 files per sample). "
                "Only the MET changes; the selected jets are smeared as in A in every version.") + 4
    rows = [[VSHORT[k], VNAME[k]] for k in VERS]
    y = table(fig, 110, y, [("version", 420, "left"), ("what is different (MC only)", 1280, "left")], rows, 20,
              shade_rows=(0,)) + 12
    y = bullets(fig, 110, y, 1700, "How it is done and checked", [
        "The workflow takes the framework's own type-1 jets and their JER factors and redoes the MET sum, with the factor set "
        "to 1 for one class of jets. Same MET XY correction, same MET < 50 cut.",
        "Check 1: the version \"all\" equals the framework MET in every event (difference < 0.01 GeV in all Z events) and "
        "reproduces run A's MC histogram.",
        "Data have no JER, so the data are the same for every version (run A's data). Run B (no JER anywhere) is shown "
        "for comparison.",
    ], size=20)
    deck.save(fig)
    setup_slides(deck)

    # results at a glance
    fig = page()
    y = heading(fig, "Results at a glance: data/MC with all cuts except MET",
                "Same data in every row. Statistical errors only (data and MC).") + 4
    rows = []
    for ch, lab in CHS.items():
        for k in VERS:
            rows.append([f"{lab}, {VSHORT[k]}"] + [r3(x) for x in J[f"metbin_{ch}_{k}"]])
    table(fig, 110, y, [("", 640, "left"), ("MET < 50", 350, "right"), ("MET 50–100", 350, "right"),
                        ("MET 100–200", 360, "right")], rows, 19, shade_rows=(0, 8))
    deck.save(fig)
    plot_page(f"{MV}/datamc_metbins.png", "data/MC per MET bin for every MET version",
              "Points: data/MC with all cuts except MET (squares Zee, circles Zμμ). Top row = nominal. "
              "The data are the same in every row; only the MC MET changes.", "New run",
              F("glance"))
    plot_page(f"{MV}/met_nm1_versions.png", "MET, all cuts except MET: data vs MC versions",
              "Black: data. Coloured: MC with the JER removed from the MET for the jets given in the legend; dashed grey: "
              "run B. Lower panel: data/MC. Dotted line: the MET < 50 GeV cut.", "New run", F("met_overlay"))

    # effect on the measurement
    SECTIONS.append(("5. Effect on the selection and on the b/c-tag yields", deck.n + 1))
    fig = page()
    y = heading(fig, "Effect on the full selection (MET < 50 + jet), per tag region",
                "data/MC with all weights, ParticleNet tag regions of the leading jet.") + 4
    TAGS = ["incl", "btag_L", "ctag_L", "btag_M", "ctag_M", "btag_T", "ctag_T"]
    rows = []
    for ch, lab in CHS.items():
        for k in VERS:
            rows.append([f"{lab}, {VSHORT[k]}"] + [f"{x[0]:.3f}" for x in J[f"final_{ch}_{k}"]])
    y = table(fig, 110, y, [("", 520, "left")] + [(t.replace("_", " "), 168, "right") for t in TAGS], rows, 17,
              shade_rows=(0, 8)) + 6
    text(fig, 110, y, "Statistical errors: about ±0.012 (incl), ±0.03 (Loose), ±0.05 (Medium), ±0.07 (Tight) for Zee; "
         "about 25% smaller for Zμμ.", 18, BODY, width=1700)
    deck.save(fig)
    fig = page()
    y = heading(fig, "Effect on the b-tag / c-tag yield ratio in MC",
                "MC b-tag yield / c-tag yield at the full selection (ParticleNet), and its change w.r.t. the nominal MET. "
                "This is the quantity closest to the Z+b / Z+c ratio.") + 4
    rows = []
    for ch, lab in CHS.items():
        for wp in "LMT":
            rows.append([f"{lab}, {wp}"] + [f"{100 * J[f'bc_{ch}_{wp}_{k}'][1]:+.1f} ± {100 * J[f'bc_{ch}_{wp}_{k}'][2]:.1f}"
                                              for k in VERS[1:]]
                        + [f"{J[f'bc_{ch}_{wp}_all'][0]:.3f}", f"{J[f'bc_{ch}_{wp}_data']:.3f}"])
    hdr = {"noJERhighSF": "2.65–2.964", "noJERfwd": "2.5–3.139", "noJERsoftfwd": "soft, 2.5–3.1", "noJERsoft": "pT < 30",
           "noJERcorrT1": "CorrT1", "noJER": "none in MET", "B": "run B"}
    text(fig, 310, y, "change in % (no JER in the MET for …)", 18, ACCENT, "bold")
    y = table(fig, 110, y + 30, [("", 200, "left")] + [(hdr[k], 172, "right") for k in VERS[1:]]
              + [("nominal", 150, "right"), ("data", 150, "right")], rows, 19) + 12
    note(fig, y, *F("bc"), size=20)
    deck.save(fig)

    # recoil
    SECTIONS.append(("6. Hadronic recoil", deck.n + 1))
    for sel, sname in (("Z", "Z events (no MET or jet cut)"), ("Zjet", "all cuts except MET")):
        plot_page(f"{MV}/recoil_{sel}.png", f"Recoil vs pT(ℓℓ), {sname}",
                  "u = −(MET + pT(ℓℓ)). Top: mean of u∥ + qT (0 = recoil balances the Z). Bottom: RMS of u⊥ (MET "
                  "resolution). Black data, coloured MC versions.", "New run", F(f"recoil_{sel}"))

    # conclusions and next steps
    SECTIONS.append(("Conclusions and next steps", deck.n + 1))
    fig = page()
    y = heading(fig, "Conclusions") + 6
    for f in FINDINGS.get("conclusions", [["(to be written)", "", "INFO"]]):
        y = note(fig, y, f[0], f[1], {"GOOD": GOOD, "OPEN": OPEN, "INFO": INFO}[f[2]], size=20) + 10
    deck.save(fig)
    fig = page()
    y = heading(fig, "Proposal and next steps") + 6
    for f in FINDINGS.get("next", [["(to be written)", "", "INFO"]]):
        y = note(fig, y, f[0], f[1], {"GOOD": GOOD, "OPEN": OPEN, "INFO": INFO}[f[2]], size=20) + 10
    deck.save(fig)
    return SECTIONS


CONTENTS = build(CountDeck(), [("(counting)", 1)])
deck = Deck(OUT, FOOT)
assert build(deck, CONTENTS) == CONTENTS
deck.close()
for sname, p0 in CONTENTS:
    print(f"{p0:4d}  {sname}")
print(OUT)
