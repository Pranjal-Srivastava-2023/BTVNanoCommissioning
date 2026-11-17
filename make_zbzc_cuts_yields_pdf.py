"""Short summary deck (2026-11-17): the cuts, the cutflow and the yields of every Summer22 setup behind the
latest decks (four one-change b-tag decks of 15 Nov, MET runs A/B/C of 16 Nov), side by side.

Numbers only from files written by the runs:
  hists_zbzc_run3_<setup>/Summer22/yields/yields.json    (make_zbzc_yields.py: cutflow without SFs, yields with all
                                                          weights per stage and per PNet tag region)
  hists_zbzc_run3_<setup>/Summer22/yields_btag*_L.txt    (plot_zbzc_run3.py: Loose b-tag yields of the 3 taggers)

Usage:  PYTHONPATH=$PWD python make_zbzc_cuts_yields_pdf.py [--date "17 November 2026"]
        (ZBZC_PPTX=1 and pylibs_pptx on PYTHONPATH -> editable .pptx of the same deck)
Output: hists_zbzc_run3_summary/Summer22/slides_zbzc_cuts_yields_Summer22.pdf (or .pptx)
"""
import argparse
import datetime
import json
import os

os.environ.setdefault("ZBZC_DECK_DIR", "hists_zbzc_run3_zpt/Summer22")
from zbzc_slides_common import (ACCENT, BODY, DARK, GOOD, INFO, OPEN, Deck, bullets, heading, note, page,  # noqa: E402
                                table, text)

parser = argparse.ArgumentParser()
parser.add_argument("--date", default=None)
args = parser.parse_args()
DATE = args.date or datetime.date.today().strftime("%-d %B %Y")
OUTDIR = "hists_zbzc_run3_summary/Summer22"
os.makedirs(OUTDIR, exist_ok=True)
OUT = f"{OUTDIR}/slides_zbzc_cuts_yields_Summer22.pdf"

# (key, short label, run dir, change with respect to its reference, reference, deck)
SETUPS = [
    ("zpt", "Base", "zpt", "DY Z pT weights on (reference of the b-tag decks)", "8 Nov setup", "b-tag deck, base"),
    ("mupt30", "Muon pT > 30", "zpt_mupt30", "Both muons pT > 30 GeV (was 26)", "Base", "b-tag deck, muon pT"),
    ("mueta21", "Muon |η| < 2.1", "zpt_mueta21", "Both muons |η| < 2.1 (was 2.4)", "Base", "b-tag deck, muon η"),
    ("tauveto", "τ veto", "zpt_tauveto", "Loose hadronic τ veto added (both channels)", "Base", "b-tag deck, τ veto"),
    ("A", "MET A: JER on", "metxy", "PUPPI MET XY correction added; JER as in Base", "Base", "MET deck"),
    ("B", "MET B: JER off", "metxy_nojer", "No JER smearing in MC (jets and MET)", "MET A", "MET deck"),
    ("C", "MET C: JER matched", "metxy_jermatched", "JER in the MET only for gen-matched jets", "MET A",
     "Run C deck"),
]
Y = {k: json.load(open(f"hists_zbzc_run3_{d}/Summer22/yields/yields.json")) for k, _, d, *_ in SETUPS}
LAB = {k: lab for k, lab, *_ in SETUPS}
CHS = {"Zee": "Z→ee", "Zmm": "Z→μμ"}
LUMI = json.load(open("hists_zbzc_run3_zpt/Summer22/lumi.json"))


def tagged(run, reg):
    """Loose b-tag yields (all weights) from the hadronFlavour block of yields_<reg>.txt: {ch: (MC, data, r, err)}."""
    fn = f"hists_zbzc_run3_{run}/Summer22/yields_{reg}.txt"
    if not os.path.exists(fn):
        return None
    lines = open(fn).read().splitlines()
    i = next(n for n, l in enumerate(lines) if l.startswith("== hadronFlavour"))
    out = {}
    for n in range(i + 2, i + 9):
        p = lines[n].split()
        if p and p[0] in CHS:
            e = lines[n + 1].split()
            out[p[0]] = (float(p[6]), float(p[7]), float(p[8]), float(e[-1]))
    return out


def k0(x):
    return f"{x:,.0f}".replace(",", " ")


def rr(d):
    return f"{d['data/MC']:.3f} ± {d['data/MC_err']:.3f}"


FOOT = "Summer22 (2022 C–D), 13.6 TeV · Z→ℓℓ + jet · 20 files per sample · statistical errors only"
deck = Deck(OUT, FOOT)

# ---------------------------------------------------------------- 1. title + setups
fig = page(DARK)
text(fig, 110, 70, "Cuts, cutflow and yields of the Summer22 studies", 54, "white", "bold", width=1700)
text(fig, 110, 150, f"The full selection, every correction, scale factor and weight, and the cutflow and yields behind the "
     f"b-tag decks (15 November) and the MET decks (16 November). {DATE}.", 26, "#C9D3E3", width=1700)
cols = [("setup", 330, "left"), ("what changes", 760, "left"), ("compared with", 250, "left"), ("deck", 360, "left")]
y = 250
for x, (h, w, _) in zip([110, 440, 1200, 1450], cols):
    text(fig, x, y, h, 24, "#C9D3E3", "bold")
for i, (k, lab, d, chg, ref, dk) in enumerate(SETUPS):
    yy = y + 58 + i * 62
    for x, v in zip([110, 440, 1200, 1450], (lab, chg, ref, dk)):
        text(fig, x, yy, v, 24, "white", "bold" if x == 110 else "normal")
text(fig, 110, y + 58 + 7 * 62 + 30, "Same events in every setup: 20 files per MC sample and per data channel, "
     "data 389 pb⁻¹ (ee) and 742 pb⁻¹ (μμ). Muon cuts change only Z→μμ; the τ veto and the MET changes act in both "
     "channels. Data are identical in Base, muon and τ setups apart from the cut itself; A, B and C share the same data.",
     22, "#C9D3E3", width=1700)
deck.save(fig, foot=False)

# ---------------------------------------------------------------- full analysis description (user 2026-11-17: "every
# cut, every correction, SF, trigger, weight; don't assume people know"). Facts from
# src/BTVNanoCommissioning/workflows/Zb_Zc_ratio.py, utils/selection.py, utils/correction.py, utils/AK4_parameters.py
# (Summer22), metadata/Zb_Zc_ratio_xsections_run3.json and the correctionlib files on /cvmfs/cms-griddata.cern.ch.
XL, XR, CW = 110, 1000, 810


def columns(fig, top, left, right, size=21):
    """Two columns of titled bullet blocks [(title, [items])]; warns if a column runs into the footer."""
    ys = []
    for t, _ in left + right:
        if len(t) * 0.6 * (size + 3) > CW:
            print(f"WARNING: page {deck.n + 1} block title too wide: {t!r}")
    for x, blocks in ((XL, left), (XR, right)):
        y = top
        for t, items in blocks:
            y = bullets(fig, x, y, CW, t, items, size=size) + 12
        ys.append(y)
    if max(ys) > 1020:
        print(f"WARNING: page {deck.n + 1} text reaches y = {max(ys):.0f} (> 1020)")
    return max(ys)


# --- samples and normalisation
fig = page()
y = heading(fig, "Data and simulation, and how the MC is normalised",
            "Summer22 = 2022 runs C and D (before the ECAL endcap water leak; later runs = Summer22EE). Everything 13.6 TeV, NanoAODv12.") + 6
y = columns(fig, y, [
    ("Data (22Sep2023 reprocessing, NanoAOD)", [
        "Z→ee: /EGamma/Run2022C-22Sep2023-v1 (15 files) and /EGamma/Run2022D-22Sep2023-v1 (5 files).",
        "Z→μμ: /Muon/Run2022C-22Sep2023-v1 (12 files) and /Muon/Run2022D-22Sep2023-v1 (8 files).",
        "Each channel uses only its own primary dataset, so no data event is counted twice.",
    ]),
    ("Certified data and luminosity", [
        "Only lumisections in the golden JSON Cert_Collisions2022_355100_362760_Golden.json.",
        f"Luminosity of the lumisections actually read (brilcalc, normtag_PHYSICS): {LUMI['Zee']:.1f} pb⁻¹ "
        f"(ee) and {LUMI['Zmm']:.1f} pb⁻¹ (μμ).",
    ]),
], [
    ("Normalisation of every MC event", [
        "weight = genWeight × σ × L(channel) / Σ genWeight, with Σ genWeight summed over all events of the files read "
        "(before any cut). genWeight can be negative (aMC@NLO).",
        "MC: first 20 files of each sample. Campaign Run3Summer22NanoAODv12, conditions 130X_mcRun3_2022_realistic_v5.",
    ]),
    ("Drell–Yan stitching", [
        "The pT(ℓℓ)-binned DY samples (PTLL-X) contain every event with generator pT(ℓℓ) > X, so each is cut to its "
        "own slice of LHE_Vpt; the inclusive sample is used only below 100 GeV. This is the 'lumi_slice' cutflow step.",
    ]),
])
rows = [
    ["DYto2L-2Jets_MLL-50", "aMC@NLO FxFx (0,1,2 jets NLO) + Pythia8", "6346", "LHE pT(ℓℓ) < 100 GeV"],
    ["DYto2L-2Jets_MLL-50_PTLL-100", "same", "104.97", "100 – 200 GeV"],
    ["DYto2L-2Jets_MLL-50_PTLL-200", "same", "11.239", "200 – 400 GeV"],
    ["DYto2L-2Jets_MLL-50_PTLL-400", "same", "0.6433", "400 – 600 GeV"],
    ["DYto2L-2Jets_MLL-50_PTLL-600", "same", "0.09941", "> 600 GeV"],
    ["TTto2L2Nu", "POWHEG + Pythia8", "98.88", "NNLO σ"],
    ["WW / WZ / ZZ", "Pythia8", "75.9 / 27.6 / 12.17", "σ from TOP-22-012"],
]
y = table(fig, 110, y + 4, [("MC sample (_TuneCP5_13p6TeV_…)", 560, "left"), ("generator", 560, "left"),
                            ("σ [pb]", 280, "right"), ("used for", 300, "left")], rows, 18)
text(fig, 110, y + 8, "DY σ of the PTLL-X samples = 6346 pb × fraction of inclusive events with LHE pT(ℓℓ) > X "
     "(measured on the Summer22 inclusive sample).", 17, BODY, width=1700)
deck.save(fig)

# --- triggers and event cleaning
fig = page()
y = heading(fig, "Triggers, certified data and event cleaning",
            "Applied in data and in MC (golden JSON: data only), in this order before the lepton selection.") + 6
columns(fig, y, [
    ("Triggers (HLT paths, required in data and MC)", [
        "Z→ee: HLT_Ele30_WPTight_Gsf (single electron, pT > 30 GeV, tight ID at HLT).",
        "Z→μμ: HLT_IsoMu24 (single isolated muon, pT > 24 GeV).",
        "No matching of the leptons to the trigger objects: either Z lepton may have fired. The MC is corrected "
        "with a trigger SF built for exactly this (see the lepton pages and the weights page).",
    ]),
    ("MET filters (NanoAOD Flag_*, data and MC)", [
        "goodVertices, globalSuperTightHalo2016Filter, EcalDeadCellTriggerPrimitiveFilter, BadPFMuonFilter, "
        "BadPFMuonDzFilter, hfNoisyHitsFilter, eeBadScFilter.",
        "The code also emulates ecalBadCalibFilter, but only for runs 362433–367144 (2022 F–G), so it removes "
        "nothing in 2022 C–D.",
        "There is no other primary-vertex cut.",
    ]),
], [
    ("Jet veto map (JME recipe, data and MC)", [
        "Map Summer22_23Sep2023_RunCD_V1, type 'jetvetomap' (JME jetvetomaps.json.gz).",
        "The whole event is removed if a jet lies in a vetoed η–φ cell AND has corrected pT > 15 GeV, tight jet "
        "ID, charged + neutral EM energy fraction < 0.9 and no PF muon within ΔR < 0.2.",
        "Evaluated after the jet energy corrections.",
    ]),
    ("Golden JSON (data only)", [
        "Cert_Collisions2022_355100_362760_Golden.json; lumisections outside it are dropped first.",
    ]),
    ("Order in the cutflow", [
        "all → lumi_slice (golden JSON / DY slice) → met_filters → jetveto → trigger → leptons → OS → Zmass "
        "→ (τ veto) → MET → jet.",
    ]),
])
deck.save(fig)

# --- electrons
fig = page()
y = heading(fig, "Electrons (Z→ee channel)",
            "ηSC = η of the ECAL supercluster (Electron_eta + Electron_deltaEtaSC).") + 6
columns(fig, y, [
    ("Selection of the Z electrons", [
        "NanoAOD Electron, after the energy corrections on the right.",
        "Impact parameter, barrel (|ηSC| < 1.4442): |dxy| < 0.05 cm and |dz| < 0.1 cm; endcap: |dxy| < 0.1 cm "
        "and |dz| < 0.2 cm.",
        "pT > 25 GeV and |η| < 2.4.",
        "Barrel–endcap transition 1.442 < |ηSC| < 1.566 removed.",
        "Cut-based ID Tight (Electron_cutBased ≥ 4); this ID includes the isolation.",
        "At least two such electrons; the two with the highest pT form the Z; leading electron pT > 35 GeV.",
    ]),
    ("Electrons used to clean the jets", [
        "pT > 25 GeV, |η| < 2.5, Tight ID, impact-parameter cuts as above (no gap cut). All of them, not only "
        "the two Z electrons.",
    ]),
], [
    ("Energy scale and smearing", [
        "EGM file electronSS_EtDependent.json.gz.",
        "Data: energy scale, compound correction 'Scale' (inputs run, ηSC, r9, pT, seed gain).",
        "MC: energy smearing 'SmearAndSyst' (inputs pT, r9, |ηSC|), one Gaussian random number per electron.",
    ]),
    ("Scale factors (MC)", [
        "EGM file electron.json.gz, correction 'Electron-ID-SF', year key 2022Re-recoBCD.",
        "ID: working point 'Tight', in ηSC and pT, for each of the two Z electrons.",
        "Reconstruction: 'RecoAbove20' (all our electrons have pT > 25 GeV), for each Z electron.",
    ]),
    ("Trigger scale factor (MC)", [
        "EGM file electronHlt.json.gz, HLT_SF_Ele30_TightID.",
        "Data and MC efficiencies εD, εM of both Z electrons (Electron-HLT-DataEff / -McEff, pT from 25 GeV).",
        "Either electron can fire, so SF = [1 − (1 − εD1)(1 − εD2)] / [1 − (1 − εM1)(1 − εM2)].",
    ]),
])
deck.save(fig)

# --- muons
fig = page()
y = heading(fig, "Muons (Z→μμ channel)", "The two muon setups change only the first two cuts below.") + 6
columns(fig, y, [
    ("Selection of the Z muons", [
        "NanoAOD Muon, after the momentum corrections on the right.",
        "pT > 26 GeV (setup 'Muon pT > 30': 30 GeV). 26 GeV is where the MUO trigger SFs start.",
        "|η| < 2.4 (setup 'Muon |η| < 2.1': 2.1).",
        "Tight ID (Muon_tightId).",
        "PF relative isolation in a cone ΔR = 0.4, all particles, < 0.15 (Muon_pfRelIso04_all, MUO 'Tight').",
        "At least two such muons; the two with the highest pT form the Z; leading muon pT > 35 GeV.",
    ]),
    ("Muons used to clean the jets", [
        "pT > 25 GeV, |η| < 2.5, Tight ID, isolation < 0.15. All of them, not only the two Z muons.",
    ]),
], [
    ("Momentum scale and smearing", [
        "MUO file muon_scalesmearing.json.gz. Run 3 MUO recipe (replaces the Rochester correction): momentum scale in data and MC, resolution smearing in "
        "MC (inputs pT, η, φ, charge, number of tracker layers).",
    ]),
    ("Scale factors (MC)", [
        "MUO file muon_Z.json.gz.",
        "ID: NUM_TightID_DEN_TrackerMuons, for each Z muon.",
        "Isolation: NUM_TightPFIso_DEN_TightID, for each Z muon.",
    ]),
    ("Trigger scale factor (MC)", [
        "MUO muon_Z.json.gz, NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight.",
        "Data and MC efficiencies (nominal_DATAeff, nominal_MCeff) of both Z muons.",
        "Either muon can fire: SF = [1 − (1 − εD1)(1 − εD2)] / [1 − (1 − εM1)(1 − εM2)]. A muon below 26 GeV "
        "(outside the MUO range) counts as not firing.",
    ]),
])
deck.save(fig)

# --- Z candidate, vetoes
fig = page()
y = heading(fig, "The Z candidate, the two channels and the extra vetoes") + 10
columns(fig, y, [
    ("Z candidate (steps leptons, OS, Zmass)", [
        "The channel's trigger has fired.",
        "At least two selected leptons of the channel (electrons for Z→ee, muons for Z→μμ).",
        "The two with the highest pT form the Z: leading pT > 35 GeV, the other above the lepton pT cut "
        "(25 GeV electrons, 26 GeV muons).",
        "Opposite electric charge.",
        "71 < m(ℓℓ) < 111 GeV.",
        "No cut on the Z pT.",
    ]),
    ("What is not vetoed", [
        "Additional leptons are allowed (no third-lepton veto).",
        "No b-tag or jet-flavour requirement at this stage.",
    ]),
], [
    ("Channels", [
        "Data: Z→ee only from the EGamma dataset, Z→μμ only from the Muon dataset.",
        "MC: every event is tested for both channels independently.",
    ]),
    ("Loose τ veto (only in the 'τ veto' setup)", [
        "Event removed if it has a τh with pT > 20 GeV, |η| < 2.5, |dz| < 0.2 cm, decay mode 0, 1, 10 or 11, "
        "DeepTau 2018v2p5 VSjet ≥ Loose, VSe ≥ VVLoose, VSμ ≥ VLoose, and ΔR > 0.4 from every jet-cleaning "
        "electron and muon.",
        "Applied after the Z mass cut, in both channels. No τ scale factors.",
    ]),
    ("After the Z (next pages)", [
        "MET < 50 GeV (type-1 PUPPI MET), against tt̄.",
        "At least one selected AK4 jet.",
    ]),
])
deck.save(fig)

# --- jets
fig = page()
y = heading(fig, "Jets", "AK4 jets clustered from PUPPI particles (NanoAOD Jet). JME file jet_jerc.json.gz.") + 6
columns(fig, y, [
    ("Jet energy corrections (JEC), data and MC", [
        "Start from the raw jet pT = (1 − rawFactor) × pT.",
        "MC: Summer22_22Sep2023_V4_MC_L1L2L3Res_AK4PFPuppi (L1 pileup offset, L2 η, L3 absolute).",
        "Data: Summer22_22Sep2023_V4_DATA_L1L2L3Res_AK4PFPuppi (adds the residual correction, by run).",
        "Inputs: jet area, η, pT, ρ (fixedGridRhoFastjetAll), run number (data).",
    ]),
    ("Jet energy resolution smearing (JER), MC only", [
        "Resolution Summer22_22Sep2023_JRV2_MC_PtResolution_AK4PFPuppi, data/MC scale factor "
        "Summer22_22Sep2023_JRV2_MC_ScaleFactor_AK4PFPuppi.",
        "JME hybrid method (JER-Smearing/jer_smear.json.gz): jets with a matched generator jet (Jet_genJetIdx) are "
        "scaled with their gen pT; the others get a random Gaussian smearing.",
        "Setup MET B: no JER at all (jets and MET). Setup MET C: jets as nominal, change only in the MET.",
    ]),
], [
    ("Jet selection", [
        "pT > 30 GeV (after JEC and JER) and |η| ≤ 2.5.",
        "Jet ID TightLepVeto with the NanoAODv12 fix (JME JetID13p6TeV twiki): for |η| ≤ 2.7, Jet_jetId ≥ 2 and "
        "muon energy fraction < 0.8 and charged EM fraction < 0.8.",
        "ΔR > 0.4 from every jet-cleaning electron and muon (lepton pages).",
        "No pileup jet ID (PUPPI already removes most pileup).",
        "Event needs at least one such jet. The highest-pT one is 'the jet': it is plotted, tagged and gives the "
        "flavour.",
    ]),
    ("Jet flavour in MC", [
        "Jet_hadronFlavour of the leading jet: 5 → b, 4 → c, anything else → light. DY events are split into "
        "DY+b, DY+c and DY+light with this.",
    ]),
])
deck.save(fig)

# --- MET
fig = page()
y = heading(fig, "Missing transverse momentum (MET)", "The cut is MET < 50 GeV; it mainly removes tt̄.") + 6
columns(fig, y, [
    ("Type-1 PUPPI MET, recomputed", [
        "Start from the uncorrected PUPPI MET (RawPuppiMET).",
        "Jets used: Jet and CorrT1METJet (the low-pT jets NanoAOD keeps for this), with corrected pT > 15 GeV, "
        "|η| < 5.2 and EM energy fraction < 0.9, muons inside the jet subtracted.",
        "For each of them the MET changes by −(pT after L1L2L3Res [× JER in MC] − pT after L1 only) along the jet "
        "direction (JME recipe, cms-jerc Type1MET).",
        "So the MET in data and MC sees exactly the JEC and JER of our jets.",
    ]),
], [
    ("MET XY correction (only setups MET A, B, C)", [
        "JME met_xyCorrections_2022_2022.json.gz, PuppiMET, epoch 2022, separate DATA and MC versions, as a "
        "function of the number of good primary vertices. Removes the φ modulation of the MET (shifts of order 1 GeV).",
        "Not applied in the Base, muon and τ setups.",
    ]),
    ("JER in the MET (the MET study)", [
        "MET A: nominal, every jet in the MET sum smeared as above.",
        "MET B: no smearing anywhere in MC.",
        "MET C: in the MET sum only jets with a generator jet are smeared (scaling); jets without one (all "
        "CorrT1METJet, pileup jets) get factor 1. The selected jets are smeared as in A.",
    ]),
])
deck.save(fig)

# --- b tagging
fig = page()
y = heading(fig, "b tagging of the leading jet (the Loose b-tag decks)",
            "BTV Summer22 files btagging.json.gz / ctagging.json.gz. Only the leading jet is tagged.") + 6
y = columns(fig, y, [
    ("Taggers and cut", [
        "Three taggers, each a separate selection: ParticleNet (Jet_btagPNetB), DeepJet (Jet_btagDeepFlavB), "
        "RobustParT (Jet_btagRobustParTAK4B).",
        "b-tagged = the B score is above the BTV working point. The decks use Loose.",
        "Data: no weight.",
    ]),
], [
    ("Scale factors on tagged MC jets", [
        "Fixed-working-point SFs.",
        "SF of the leading jet for its hadronFlavour: b and c jets <tagger>_comb, light jets <tagger>_light, "
        "'central' value.",
        "Outside the SF range (|η| < 2.5, 20 < pT < 1000 GeV) the value at the edge is used.",
        "Only tagged events are plotted, so no MC tagging efficiencies are needed.",
    ]),
])
rows = [["ParticleNet", "particleNet", "0.047", "0.245", "0.6734"],
        ["DeepJet", "deepJet", "0.0583", "0.3086", "0.7183"],
        ["RobustParT", "robustParticleTransformer", "0.0849", "0.4319", "0.8482"]]
y = table(fig, 110, y + 4, [("tagger", 300, "left"), ("BTV name", 420, "left"), ("Loose", 200, "right"),
                            ("Medium", 200, "right"), ("Tight", 200, "right")], rows, 20, shade_rows=())
text(fig, 110, y + 10, "Working points (B score > value) read from <BTV name>_wp_values. c-tag regions (CvL and CvB "
     "cuts, SFs _wc / _tnp / _light) exist in the runs but are not used in these decks.", 18, BODY, width=1700)
deck.save(fig)

# --- all MC weights
fig = page()
y = heading(fig, "Every weight on an MC event",
            "w = genWeight × σ L / Σ genWeight × w(PU) × w(leptons) × w(trigger) × w(Z pT, DY only) "
            "[× w(b-tag) in the tagged plots]. Data: weight 1. All SFs at their central values.") + 6
rows = [
    ["genWeight × σ L / Σ genWeight", "NanoAOD genWeight; σ table; L per channel", "all MC"],
    ["Pileup", "LUM puWeights.json.gz, Collisions2022_355100_357900_eraBCD_GoldenJson, vs Pileup_nTrueInt", "all MC"],
    ["Electron ID", "EGM Electron-ID-SF, 2022Re-recoBCD, 'Tight' (ηSC, pT)", "each Z electron"],
    ["Electron reconstruction", "EGM Electron-ID-SF, 2022Re-recoBCD, 'RecoAbove20'", "each Z electron"],
    ["Muon ID", "MUO muon_Z.json.gz NUM_TightID_DEN_TrackerMuons", "each Z muon"],
    ["Muon isolation", "MUO muon_Z.json.gz NUM_TightPFIso_DEN_TightID", "each Z muon"],
    ["Trigger, Z→ee", "EGM electronHlt HLT_SF_Ele30_TightID, data/MC eff. of both electrons", "event"],
    ["Trigger, Z→μμ", "MUO NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight, data/MC eff. of both muons", "event"],
    ["DY Z pT weight", "own: data/ZbZc/zpt_weights_run3.json (next page); not a POG correction", "DY, both channels"],
    ["b-tag SF", "BTV btagging.json.gz <tagger>_comb (b, c) / <tagger>_light (udsg)", "tagged leading jet"],
]
y = table(fig, 110, y, [("weight", 380, "left"), ("source (file, correction)", 1020, "left"),
                        ("applied to", 300, "left")], rows, 19)
note(fig, y + 20, "The cutflow pages use only the first factor",
     "genWeight × σ L / Σ genWeight. The yield pages ('all weights') use every factor above except the b-tag SF, "
     "which enters only the b-tagged page.", INFO, size=20)
deck.save(fig)

# --- Z pT weights
ZW = json.load(open("src/BTVNanoCommissioning/data/ZbZc/zpt_weights_run3.json"))["Summer22"]
fig = page()
y = heading(fig, "DY Z pT weights (all setups in this deck)",
            "Not a POG correction: our own reweighting of the DY simulation in reconstructed pT(ℓℓ).") + 6
y = columns(fig, y, [
    ("How they were made", [
        "From Z→μμ events (all cuts up to the Z mass, no MET or jet cut) of a run without these weights: "
        "weight = data/MC in each pT(ℓℓ) bin.",
        f"Normalised (× {ZW['norm']:.4f}) so that the total DY yield does not change: they change the shape only.",
    ]),
], [
    ("How they are used", [
        "Every DY event, in both channels, gets the weight of the bin of its reconstructed pT(ℓℓ) (last bin open).",
        "tt̄ and VV are not reweighted.",
    ]),
])
e, w, er = ZW["edges"], ZW["weights"], ZW["errors"]
half = (len(w) + 1) // 2
for j, x0 in enumerate((110, 980)):
    rows = [[f"{e[i]:g} – {e[i + 1]:g}" if i < len(w) - 1 else f"> {e[i]:g}", f"{w[i]:.3f}", f"{er[i]:.3f}"]
            for i in range(j * half, min(len(w), (j + 1) * half))]
    table(fig, x0, y + 4, [("pT(ℓℓ) [GeV]", 300, "left"), ("weight", 230, "right"), ("stat. error", 260, "right")],
          rows, 19)
deck.save(fig)

# --- not applied
fig = page()
y = heading(fig, "What is NOT applied (yet)") + 10
columns(fig, y, [
    ("Weights and corrections", [
        "L1 prefiring weight (not needed in Run 3).",
        "Systematic uncertainties: every SF at its central value; all errors in this deck are statistical only "
        "(data and MC).",
        "τ scale factors (the τ veto setup only removes events).",
        "Top pT reweighting for tt̄.",
        "Uncertainty of the DY Z pT weights.",
    ]),
], [
    ("Selection", [
        "Trigger matching of the leptons to the HLT objects.",
        "Third-lepton veto.",
        "Pileup jet ID (PUPPI jets).",
        "Any cut on the Z pT.",
        "Lepton energy corrections are applied to the leptons, but the MET is built only from the jet corrections "
        "(type-1).",
    ]),
])
deck.save(fig)

# ---------------------------------------------------------------- cuts at a glance
fig = page()
y = heading(fig, "Cuts at a glance, in the order of the cutflow",
            "Base selection. The last column says which setup changes the cut.") + 10
rows = [
    ["all", "Events in the 20 files", ""],
    ["lumi_slice", "Data: golden-JSON lumisections. DY MC: generator pT(ℓℓ) slice of each sample (stitching: "
     "inclusive < 100 GeV, binned samples above)", ""],
    ["met_filters", "MET filters (goodVertices, halo, ECAL TP, BadPFMuon(Dz), hfNoisyHits, eeBadSc)", ""],
    ["jetveto", "Jet veto map Summer22_23Sep2023_RunCD_V1", ""],
    ["trigger", "Z→ee: HLT_Ele30_WPTight_Gsf · Z→μμ: HLT_IsoMu24", ""],
    ["leptons", "Two leptons, leading pT > 35 GeV. e: pT > 25, |η| < 2.4, Tight ID, no gap. "
     "μ: pT > 26, |η| < 2.4, Tight ID, PF iso < 0.15", "muon pT > 30 / |η| < 2.1"],
    ["OS", "Opposite charge", ""],
    ["Zmass", "71 < m(ℓℓ) < 111 GeV", ""],
    ["(τ veto)", "No loose τh (pT > 20, |η| < 2.5, DeepTau 2018v2p5 VSjet ≥ L), only in the τ-veto setup", "τ veto"],
    ["MET", "Type-1 PUPPI MET < 50 GeV", "A (XY corr.), B, C (JER)"],
    ["jet", "≥ 1 AK4 PUPPI jet: pT > 30 GeV, |η| < 2.5, TightLepVeto ID, ΔR > 0.4 from the leptons", "B (no jet JER)"],
]
y = table(fig, 110, y, [("step", 220, "left"), ("cut", 1130, "left"), ("changed in", 350, "left")], rows, 19)
note(fig, y + 20, "Weights in MC (not in the cutflow on the next pages)",
     "Pileup, lepton ID/iso/reco SFs, trigger SF (either lepton), DY Z pT weights (all setups here), BTV SFs for the "
     "tagged jet. The cutflow tables use generator weight × cross section × luminosity only; the yield tables use all "
     "weights.", INFO, size=20)
deck.save(fig)

# ---------------------------------------------------------------- 3-4. cutflow of the base setup


def cutflow_slide(ch):
    fig = page()
    y = heading(fig, f"Cutflow {CHS[ch]}, Base setup",
                "MC: generator weight × cross section × luminosity, no SFs. Data trigger-selected, so data/MC "
                "means something only from 'trigger' on. eff = events after the step / events before.") + 10
    rows = []
    cf = Y["zpt"][ch]["cutflow"]
    prev = None
    for c in cf:
        mc = c["DY"] + c["tt"] + c["VV"]
        r = c["data"] / mc
        e_mc = f"{mc / prev[0]:.3f}" if prev else ""
        e_d = f"{c['data'] / prev[1]:.3f}" if prev else ""
        rows.append([c["step"], k0(c["DY"]), k0(c["tt"]), k0(c["VV"]), k0(mc), k0(c["data"]), f"{r:.3f}", e_mc, e_d])
        prev = (mc, c["data"])
    y = table(fig, 110, y, [("step", 220, "left"), ("DY", 220, "right"), ("tt̄", 160, "right"), ("VV", 160, "right"),
                            ("MC", 220, "right"), ("data", 220, "right"), ("data/MC", 170, "right"),
                            ("eff MC", 160, "right"), ("eff data", 170, "right")], rows, 21, shade_rows=(9,))
    st = Y["zpt"][ch]["stages"]["final (MET < 50 + jet)"]
    note(fig, y + 24, f"With all weights the final {CHS[ch]} yield is MC {k0(st['MC'])}, data {k0(st['data'])}, "
         f"data/MC {rr(st)}",
         "The last row above has no SFs and no Z pT weights, so its data/MC differs from the weighted one. "
         "The jet step keeps only about 18 % of Z events in both data and MC.", GOOD, size=20)
    deck.save(fig)


cutflow_slide("Zee")
cutflow_slide("Zmm")

# ---------------------------------------------------------------- 5. cutflow data/MC per setup
fig = page()
y = heading(fig, "Cutflow by setup: data/MC after each step (no SFs)",
            "Same normalisation as the cutflow pages. Last two columns: events after the jet step. "
            "'—' = step not in that setup.") + 4
STEPS = ["leptons", "OS", "Zmass", "tauveto", "MET", "jet"]
for ch in CHS:
    text(fig, 110, y + 6, CHS[ch], 24, ACCENT, "bold")
    rows = []
    for k, *_ in SETUPS:
        cf = {c["step"]: c for c in Y[k][ch]["cutflow"]}
        r = []
        for s in STEPS:
            if s in cf:
                c = cf[s]
                r.append(f"{c['data'] / (c['DY'] + c['tt'] + c['VV']):.3f}")
            else:
                r.append("—")
        j = cf["jet"]
        rows.append([LAB[k]] + r + [k0(j["DY"] + j["tt"] + j["VV"]), k0(j["data"])])
    y = table(fig, 110, y + 40, [("setup", 330, "left"), ("leptons", 170, "right"), ("OS", 150, "right"),
                                 ("Zmass", 160, "right"), ("τ veto", 160, "right"), ("MET", 150, "right"),
                                 ("jet", 150, "right"), ("MC", 210, "right"), ("data", 210, "right")], rows, 19) + 10
deck.save(fig)

# ---------------------------------------------------------------- 6. stages with all weights
fig = page()
y = heading(fig, "data/MC with all weights, stage by stage",
            "Z events = all cuts up to the Z mass (and τ veto). Then MET < 50 only, ≥ 1 jet only, and both (final).") + 4
ST = [("Z events", "Z events"), ("MET < 50", "MET < 50"), (">= 1 jet", "≥ 1 jet"), ("final (MET < 50 + jet)", "final")]
for ch in CHS:
    text(fig, 110, y + 6, CHS[ch], 24, ACCENT, "bold")
    rows = [[LAB[k]] + [rr(Y[k][ch]["stages"][s]) for s, _ in ST] for k, *_ in SETUPS]
    y = table(fig, 110, y + 40, [("setup", 330, "left")] + [(h, 340, "right") for _, h in ST], rows, 19) + 10
deck.save(fig)

# ---------------------------------------------------------------- 7-8. final yields per setup


def final_slide(ch):
    fig = page()
    y = heading(fig, f"Final yields {CHS[ch]} by setup (all weights)",
                "MET < 50 GeV and ≥ 1 jet. DY split by the hadronFlavour of the leading jet.") + 10
    rows = []
    for k, *_ in SETUPS:
        d = Y[k][ch]["stages"]["final (MET < 50 + jet)"]
        rows.append([LAB[k], k0(d["DY-b"]), k0(d["DY-c"]), k0(d["DY-l"]), k0(d["tt"]), k0(d["VV"]),
                     f"{k0(d['MC'])} ± {k0(d['MC_err'])}", k0(d["data"]), rr(d)])
    y = table(fig, 110, y, [("setup", 330, "left"), ("DY+b", 150, "right"), ("DY+c", 150, "right"),
                            ("DY+light", 180, "right"), ("tt̄", 120, "right"), ("VV", 120, "right"),
                            ("MC", 250, "right"), ("data", 160, "right"), ("data/MC", 240, "right")], rows, 21)
    return fig, y


# Conclusions, written by hand after reading the tables (None = not written yet; the slide is then left out)
FINAL = {  # (title, body) under each final-yield table; numbers checked against yields.json 2026-11-17
    "Zee": ("Muon cuts do not touch Z→ee; the τ veto removes 1 % of data and MC",
            "MET B and C add 1.2 % and 1.8 % to the MC (more MC events pass MET < 50 GeV) with the same data, "
            "so data/MC goes from 0.971 (A) to 0.959 (B) and 0.954 (C)."),
    "Zmm": ("Muon pT > 30 removes 17.5 % and |η| < 2.1 removes 12.4 % of both data and MC",
            "So data/MC stays at 0.961–0.965. The τ veto removes 1.2 % of MC and 1.0 % of data. MET B and C add 1.3 % "
            "and 1.9 % to the MC: data/MC 0.964 (A) → 0.952 (B) and 0.945 (C)."),
}
SUMMARY = [  # (title, body, style)
    ("None of the cut changes moves data/MC",
     "Muon pT > 30, muon |η| < 2.1 and the τ veto change the final data/MC by at most 0.003 in either channel "
     "(statistical error 0.009–0.013), and by at most 0.009 with the Loose b-tag (error 0.02–0.03).", "good"),
    ("The MC excess appears when we require a jet",
     "Z events before the MET and jet cuts: data/MC 0.996 (ee) and 0.986 (μμ). With ≥ 1 jet: 0.945 and 0.938 "
     "(0.961 and 0.952 with JER off). MET < 50 alone gives 1.025 and 1.015, because the MC has more events above 50 GeV.",
     "info"),
    ("JER changes (B, C) fix the MET tail but not the normalisation",
     "With less MC MET, MET < 50 data/MC drops to about 1.00, but the MC gains 1–2 % of events, so the final data/MC "
     "goes down: 0.971 → 0.959 / 0.954 (ee), 0.964 → 0.952 / 0.945 (μμ). The MC excess after the jet cut stays in "
     "every setup: 5–6 % with JER on, 4–5 % with JER off.", "open"),
    ("Loose b-tag: same picture in every setup",
     "ParticleNet 0.95–0.97 (ee) and 0.93–0.95 (μμ), DeepJet 0.93–0.95, RobustParT 0.98–1.00; differences between "
     "setups are inside the statistical errors (0.02–0.03).", "info"),
]

# ---------------------------------------------------------------- 9. Loose b-tag yields
TAGS = [("PNet", "btag_L"), ("DeepJet", "btagDeepJet_L"), ("RobustParT", "btagRobustParT_L")]


def btag_slide():
    fig = page()
    y = heading(fig, "Leading jet b-tagged (Loose): data/MC by setup and tagger",
                "All weights incl. BTV SFs. The MET runs (A, B, C) were not made with the three-tagger plots, so only "
                "ParticleNet is shown for them (from the PNet tag regions of the same run).") + 4
    for ch in CHS:
        text(fig, 110, y + 6, CHS[ch], 24, ACCENT, "bold")
        rows = []
        for k, _, d, *_ in SETUPS:
            r = [LAB[k]]
            for t, reg in TAGS:
                tg = tagged(d, reg)
                if tg:
                    mc, da, ra, er = tg[ch]
                    r.append(f"{ra:.3f} ± {er:.3f}  ({k0(da)})")
                elif t == "PNet":
                    p = Y[k][ch]["tags"]["btag_L"]
                    r.append(f"{rr(p)}  ({k0(p['data'])})")
                else:
                    r.append("—")
            rows.append(r)
        y = table(fig, 110, y + 40, [("setup", 330, "left")] + [(t + "  (data events)", 456, "right") for t, _ in TAGS],
                  rows, 19) + 10
    return fig


for ch in CHS:
    fig, y = final_slide(ch)
    if FINAL[ch]:
        note(fig, y + 24, *FINAL[ch], style=GOOD, size=20)
    deck.save(fig)
deck.save(btag_slide())
if SUMMARY:
    fig = page()
    y = heading(fig, "What the tables show")
    for t, b, st in SUMMARY:
        y = note(fig, y + 14, t, b, style={"good": GOOD, "open": OPEN, "info": INFO}[st], size=21)
    deck.save(fig)
deck.close()
