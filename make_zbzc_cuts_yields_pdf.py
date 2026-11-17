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
from zbzc_slides_common import ACCENT, BODY, DARK, GOOD, INFO, OPEN, Deck, heading, note, page, table, text  # noqa: E402

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
text(fig, 110, 150, f"One place for the numbers behind the b-tag decks (15 November) and the MET decks (16 November). "
     f"{DATE}.", 26, "#C9D3E3", width=1700)
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

# ---------------------------------------------------------------- 2. cuts applied
fig = page()
y = heading(fig, "Cuts applied, in the order of the cutflow",
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
    ["jet", "≥ 1 AK4 PUPPI jet: pT > 30 GeV, |η| < 2.5, TightLepVeto ID, ΔR > 0.4 from the leptons", "B, C (jet JER)"],
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
