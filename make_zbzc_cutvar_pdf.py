"""Deck for the Z->mumu cut study and the first MET > 50 GeV check (Summer22, run zbzc_run3_cutvar).

Requests of 2026-11-15: change the current muon-channel cuts one at a time (values near the POG ones),
show all plots for comparison with a statistics box, include the loose tau veto (advisor 2026-11-08,
item 3) as a variant, and start the MET > 50 GeV data/MC study with Delta phi(MET, X).

Numbers are read from <run>/cutvar/cutvar_table.json (plot_zbzc_cutvar.py) and from the coffea outputs
(Delta phi tables); images from <run>/cutvar/. The sentences in FINDINGS / DPHI_FINDINGS are written by
hand after looking at the plots (rule: no claim that the plots do not show).

Usage:  python make_zbzc_cutvar_pdf.py [run dir, default hists_zbzc_run3_cutvar/Summer22]
Output: <run dir>/slides_zbzc_cutvar_Summer22.pdf
"""
import datetime
import glob
import json
import os
import sys

import numpy as np
from coffea.util import load

from zbzc_slides_common import (DARK, GOOD, INFO, OPEN, Deck, bullets, heading, image, note, note_height, page,
                                reading_slide, setup_slides, table, text)

RD = sys.argv[1] if len(sys.argv) > 1 else "hists_zbzc_run3_cutvar/Summer22"
CV = f"{RD}/cutvar"
OUTPDF = f"{RD}/slides_zbzc_cutvar_Summer22.pdf"
DATE = datetime.date.today().strftime("%-d %B %Y")
T = json.load(open(f"{CV}/cutvar_table.json"))

# same groups / descriptions as plot_zbzc_cutvar.py
from zbzc_cutvar_defs import DESC, GROUPS, VARS  # noqa: E402

GROUP_WHY = {
    "mupt": "MUO trigger SFs start at 26 GeV, so 26 is the lowest valid value; 30 tests the trigger turn-on region. "
            "The leading-muon cut (35) is ours, not a POG value: 30 tests it.",
    "mueta": "Muons are reconstructed up to |η| = 2.4 (the POG SF range); 2.1 removes the most forward region.",
    "zmass": "71–111 GeV is our window; 76–106 and 81–101 are common tighter choices.",
    "met": "MET < 50 GeV removes tt̄; 40 and 60 move the cut, 'no cut' shows its full effect.",
    "jet": "BTV SFs are valid for pT ≥ 20 GeV and |η| < 2.5; JME recommends the Tight-lepton-veto ID, Tight is the "
           "looser alternative.",
    "tau": "Loose hadronic-τ veto, recommended by the advisor (8 November, item 3).",
}
NOMVAL = {"sub30": ("26", "30"), "lead30": ("35", "30"), "eta21": ("2.4", "2.1"), "mass76": ("71–111", "76–106"),
          "mass81": ("71–111", "81–101"), "met40": ("< 50", "< 40"), "met60": ("< 50", "< 60"),
          "noMET": ("< 50", "none"), "jpt25": ("30", "25"), "jpt40": ("30", "40"), "jeta24": ("2.5", "2.4"),
          "jidTight": ("TightLepVeto", "Tight"), "tauVeto": ("none", "loose τh veto")}
CUTNAME = {"sub30": "Both muons pT [GeV]", "lead30": "Leading muon pT [GeV]", "eta21": "Muon |η|",
           "mass76": "m(μμ) window [GeV]", "mass81": "m(μμ) window [GeV]", "met40": "MET [GeV]", "met60": "MET [GeV]",
           "noMET": "MET [GeV]", "jpt25": "Jet pT [GeV]", "jpt40": "Jet pT [GeV]", "jeta24": "Jet |η|",
           "jidTight": "Jet ID", "tauVeto": "Tau veto"}
VLABEL = {"muvar_z_pt": "pT(μμ)", "muvar_lep0_pt": "leading muon pT", "muvar_lep1_pt": "subleading muon pT",
          "muvar_jet_pt": "leading jet pT", "muvar_lep0_eta": "leading muon η", "muvar_lep1_eta": "subleading muon η",
          "muvar_jet_eta": "leading jet η", "muvar_z_mass": "m(μμ)", "muvar_met_pt": "MET", "muvar_n_jet": "number of jets"}
CUTVARS = [v for g in GROUPS.values() for v in g[1] if f"{v}|final" in T]

def row(v, stage, var):
    return T[f"{v}|{stage}"].get(var)


XS = json.load(open("metadata/Zb_Zc_ratio_xsections_run3.json"))
LUMI = json.load(open(f"{RD}/lumi.json"))
OUT = {}
for f in sorted(glob.glob(f"{RD}/zbzc_run3/zbzc_run3_*.coffea")):
    OUT.update(load(f))
DR = [(0, 0.6, "Δφ < 0.6"), (0.6, 2.5, "0.6–2.5"), (2.5, np.pi + 1e-6, "Δφ > 2.5")]


def dphi_ratios(ch, obj, metbin, name="dphi_met", stages=None):
    nb = len(OUT[next(iter(OUT))][name].axes["dphi"].edges) - 1
    d, m = np.zeros(nb), np.zeros(nb)
    for ds, o in OUT.items():
        h = o[name][{"channel": ch, "flav": sum, "pflav": sum, "obj": obj, "metbin": metbin}]
        if stages is not None:
            h = sum(h[{"stage": s}] for s in stages)
        if ds.startswith(("Muon", "EGamma")):
            if ds.startswith("Muon" if ch == "Zmm" else "EGamma"):
                d = d + h.values()
        else:
            m = m + h.values() * XS[ds] * LUMI[ch] / o["sumw"]
    e = OUT[next(iter(OUT))][name].axes["dphi"].edges
    c = 0.5 * (e[1:] + e[:-1])
    out = []
    for lo, hi, _ in DR:
        s = (c >= lo) & (c < hi)
        out.append((d[s].sum() / m[s].sum() if m[s].sum() > 0 else np.nan, d[s].sum(), m[s].sum() / m.sum()))
    return out


def nzero_frac(ch):
    """Share of Z events without a selected jet that have a lepton-cleaned jet with pT > 15 at any |eta|:
    (data, MC)."""
    out = []
    for obj in ("jany", "z"):
        d = m = 0.0
        for ds, o in OUT.items():
            h = o["stage_dphi_met"][{"channel": ch, "flav": sum, "pflav": sum, "obj": obj, "metbin": sum}]
            v = sum(h[{"stage": s}].sum().value for s in ("none", "MET"))
            if ds.startswith(("Muon", "EGamma")):
                if ds.startswith("Muon" if ch == "Zmm" else "EGamma"):
                    d += v
            else:
                m += v * XS[ds] * LUMI[ch] / o["sumw"]
        out.append((d, m))
    return out[0][0] / out[1][0], out[0][1] / out[1][1]


# ---- findings: written after looking at every plot (2026-11-15); all numbers filled in from the outputs
_fin = {v: row(v, "final", "muvar_z_pt") for v in ["nominal"] + CUTVARS}
_jet = {v: row(v, "final", "muvar_jet_pt") for v in ["nominal"] + CUTVARS}
_zst = {v: row(v, "Z", "muvar_z_pt") for v in ["nominal"] + CUTVARS}
_s = [r["slope"] for r in _fin.values()]
_sj = [r["slope"] for r in _jet.values()]
_szm = [_zst[v]["slope"] for v in ["nominal"] + [v for v in CUTVARS if v in GROUPS["mupt"][1] + GROUPS["mueta"][1]]]
_nonmet = [v for v in CUTVARS if v not in GROUPS["met"][1]]
_dmax = max(abs(_fin[v]["ratio"] - _fin["nominal"]["ratio"]) for v in _nonmet)
_n, _t = _fin["nominal"], _fin["tauVeto"]
FINDINGS = [
    ("No single cut changes the data/MC slope versus pT.",
     f"We changed {len(CUTVARS)} cuts one at a time (muon pT and |η|, Z mass window, MET, jet pT / |η| / ID, τ veto). "
     f"After the full selection the slope of data/MC versus pT(μμ) stays between {min(_s):+.1f} and {max(_s):+.1f} %/100 GeV "
     f"(nominal {_n['slope']:+.1f} ± {_n['slope_err']:.1f}), and versus the leading-jet pT between {min(_sj):+.1f} and "
     f"{max(_sj):+.1f} (nominal {_jet['nominal']['slope']:+.1f} ± {_jet['nominal']['slope_err']:.1f}). The overlay plots show "
     "the same point-by-point pattern for every variant, including the low data/MC at pT(μμ) ≈ 25–50 GeV."),
    ("Only the MET cut moves the normalisation.",
     f"data/MC = {_fin['met40']['ratio']:.3f} (MET < 40), {_n['ratio']:.3f} (< 50, nominal), {_fin['met60']['ratio']:.3f} (< 60), "
     f"{_fin['noMET']['ratio']:.3f} (no cut): the looser the MET cut, the lower data/MC, because MC has too many events with "
     f"MET > 40 GeV. All other variants change data/MC by at most {_dmax:.3f}."),
    ("The loose τ veto removes about 1% of the events, the same in data and MC.",
     f"Full selection: data {100 * (_t['data'] / _n['data'] - 1):+.1f}%, MC {100 * (_t['mc'] / _n['mc'] - 1):+.1f}%; "
     f"data/MC {_n['ratio']:.3f} → {_t['ratio']:.3f}; the fitted slopes are unchanged (result table). τ ID scale factors "
     "are not applied."),
    ("Before the jet and MET cuts the pT(μμ) slope is larger, and muon cuts do not change it.",
     f"Z selection only: slope {_zst['nominal']['slope']:+.1f} ± {_zst['nominal']['slope_err']:.1f} %/100 GeV; with the muon "
     f"pT or |η| variants {min(_szm):+.1f} to {max(_szm):+.1f}. This is the known DY Z pT modelling (8 November deck), "
     "not a muon effect."),
    ("Open: the MET > 50 GeV deficit. First Δφ result on the last pages.", ""),
]
_fd, _fm = nzero_frac("Zmm")
_fde, _fme = nzero_frac("Zee")
_a = dphi_ratios("Zmm", "jany", "50-100", "stage_dphi_met", ["none", "MET"])
_ae = dphi_ratios("Zee", "jany", "50-100", "stage_dphi_met", ["none", "MET"])
_j = dphi_ratios("Zmm", "j1", "50-100")
_z = dphi_ratios("Zmm", "z", "50-100")
DPHI_FINDINGS = [
    ("MC has more soft or forward jets than data, and its extra MET points away from them.",
     f"In Z events without a selected jet, {100 * _fm:.0f}% of the MC events have a jet with pT > 15 GeV at any |η| "
     f"(after lepton cleaning) against {100 * _fd:.0f}% of the data (Z→μμ; Z→ee {100 * _fme:.0f}% vs {100 * _fde:.0f}%). "
     f"With MET 50–100 GeV, {100 * _a[2][2]:.0f}% of these MC events have the MET opposite to that jet (Δφ > 2.5), and "
     f"there data/MC is {_a[2][0]:.2f} (Z→ee {_ae[2][0]:.2f}). MET opposite to a jet means the jet carries too much pT "
     "compared with the rest of the event."),
    ("With a selected jet, the deficit is in every direction.",
     f"All cuts except MET, MET 50–100 GeV, Z→μμ: data/MC {_j[0][0]:.2f} / {_j[1][0]:.2f} / {_j[2][0]:.2f} for Δφ(MET, leading "
     f"jet) < 0.6 / 0.6–2.5 / > 2.5, and {_z[0][0]:.2f} / {_z[1][0]:.2f} / {_z[2][0]:.2f} for Δφ(MET, Z). It is smallest when "
     "the MET is opposite to the jet or the Z. So the extra MC MET does not come from one badly measured hard jet."),
    ("Our reading, not proven yet: soft or forward MC jets come out too energetic.",
     "This fits the 28 October test, where switching off the MC jet energy smearing removed most of the 2022 MET tail. "
     "Next: the same Δφ plots and the pT / |η| of these jets with the MC smearing switched off (diag_zbzc_met.py nojer), "
     "then the recoil components along and across the Z."),
]

deck = Deck(OUTPDF, "Summer22 (2022 C–D), 13.6 TeV · Z→μμ + jets · 20 files per sample · statistical errors only")


def fmt_slope(r):
    return "–" if r is None or not np.isfinite(r.get("slope", np.nan)) else f"{r['slope']:+.1f} ± {r['slope_err']:.1f}"


# ------------------------------------------------------------------ cover
fig = page(DARK)
text(fig, 110, 270, "Z→μμ + jets: changing one cut at a time, and a first look at the MET tail", 60, "white", "bold", width=1700)
text(fig, 110, 470, "Does any single selection cut change the data/MC level or its slope versus pT? "
     "Includes the loose τ veto. Where does the MET > 50 GeV deficit point (Δφ)?", 30, "#C9D3E3", width=1650)
text(fig, 110, 600, "Same data and simulation files as the 8 November decks (Summer22, 20 files per sample).", 26, "#C9D3E3", width=1650)
text(fig, 110, 860, DATE, 26, "#C9D3E3")
deck.save(fig, foot=False)

# ------------------------------------------------------------------ summary (hand-written findings)
fig = page()
y = heading(fig, "Summary") + 10
if FINDINGS is None:
    note(fig, y, "Summary not written yet", "Placeholder: filled in after looking at every plot.", OPEN)
else:
    for title, body in FINDINGS:
        y = note(fig, y, title, body, GOOD if not title.startswith("Open") else OPEN, size=19) + 10
deck.save(fig)

setup_slides(deck)
reading_slide(deck, extra=[
    ("Variant", "A copy of the Z→μμ selection with ONE cut changed, filled in the same run. Variants are tests only, "
                "they are NOT applied in the analysis. Electron cuts are not changed."),
    ("Statistics box", "Data and MC yields, data/MC, mean and RMS of data and MC, χ²/ndf of data vs MC (data and MC "
                       "statistical errors), and for pT plots the fitted slope with its fit range."),
    ("Overlay", "data/MC of the nominal (black) and of each variant of one cut, on top of each other."),
])

# ------------------------------------------------------------------ what was changed
fig = page()
y = heading(fig, "What was changed: one cut at a time, Z→μμ only",
            "Each variant differs from the nominal selection in exactly one cut. Everything else (corrections, scale "
            "factors, other cuts) stays as in the nominal. The variants are NOT applied.") + 6
cols = [("Variant", 190, "left"), ("Cut", 330, "left"), ("Nominal", 230, "left"), ("Variant value", 260, "left"),
        ("Why this value", 690, "left")]
rows = []
for g, (gname, members) in GROUPS.items():
    for v in members:
        if v in CUTVARS:
            rows.append([v, CUTNAME[v], NOMVAL[v][0], NOMVAL[v][1], ""])
table(fig, 110, y, cols, rows, size=19)
yy = y + 19 * 1.85 + 19 * 0.42
done = set()
for i, r in enumerate(rows):
    g = next(k for k, (_, m) in GROUPS.items() if r[0] in m)
    if g not in done:
        text(fig, 110 + 190 + 330 + 230 + 260 + 10, yy + i * 19 * 1.85, GROUP_WHY[g], 14, DARK, width=680, ls=1.1)
        done.add(g)
deck.save(fig)

# ------------------------------------------------------------------ tau veto definition
fig = page()
y = heading(fig, "Loose hadronic-τ veto (advisor, 8 November, item 3): definition",
            "Tested as one variant: events with such a τh are removed. Not applied in the nominal selection.") + 14
y = bullets(fig, 110, y, 1700, "τh candidate (NanoAOD Tau collection, DeepTau 2018v2p5)", [
    "pT > 20 GeV, |η| < 2.5, |dz| < 0.2 cm, decay modes 0, 1, 10, 11 (the ones with DeepTau 2018v2p5 SFs).",
    "DeepTau vs jet ≥ Loose, vs electron ≥ VVLoose, vs muon ≥ VLoose.",
    "ΔR > 0.4 from the selected leptons (the same leptons used to clean the jets).",
], size=24) + 20
r0, r1 = row("nominal", "final", "muvar_z_pt"), row("tauVeto", "final", "muvar_z_pt")
z0, z1 = row("nominal", "Z", "muvar_z_pt"), row("tauVeto", "Z", "muvar_z_pt")
y = bullets(fig, 110, y, 1700, "Effect (Z→μμ)", [
    f"Z selection: data {z0['data']:.0f} → {z1['data']:.0f} ({100 * (z1['data'] / z0['data'] - 1):+.2f}%), "
    f"MC {z0['mc']:.0f} → {z1['mc']:.0f} ({100 * (z1['mc'] / z0['mc'] - 1):+.2f}%).",
    f"Full selection: data {r0['data']:.0f} → {r1['data']:.0f} ({100 * (r1['data'] / r0['data'] - 1):+.2f}%), "
    f"MC {r0['mc']:.0f} → {r1['mc']:.0f} ({100 * (r1['mc'] / r0['mc'] - 1):+.2f}%); data/MC {r0['ratio']:.3f} → {r1['ratio']:.3f}.",
], size=24) + 20
note(fig, y, "Not included: τ ID scale factors (the veto removes so few events that they do not matter at this precision).",
     "", INFO)
deck.save(fig)


# ------------------------------------------------------------------ summary tables
def summary_table(stage, members, title, sub):
    fig = page()
    y = heading(fig, title, sub) + 6
    cols = [("Variant", 150, "left"), ("Change", 490, "left"), ("data/MC", 210, "right"), ("Δ vs nom.", 150, "right"),
            ("slope pT(μμ)", 230, "right"), ("slope lead μ", 230, "right")]
    if stage == "final":
        cols.append(("slope jet pT", 230, "right"))
    nom = row("nominal", stage, "muvar_z_pt")
    rows = []
    for v in ["nominal"] + members:
        z = row(v, stage, "muvar_z_pt")
        r = [v, "(nominal)" if v == "nominal" else DESC[v], f"{z['ratio']:.3f} ± {z['ratio_err']:.3f}",
             "" if v == "nominal" else f"{z['ratio'] - nom['ratio']:+.3f}",
             fmt_slope(z), fmt_slope(row(v, stage, "muvar_lep0_pt"))]
        if stage == "final":
            r.append(fmt_slope(row(v, stage, "muvar_jet_pt")))
        rows.append(r)
    y = table(fig, 110, y, cols, rows, size=18, shade_rows=(0,), bold_rows=(0,)) + 20
    note(fig, y, "How to read", "Slopes in % per 100 GeV from a straight-line fit of data/MC. The variants share most "
         "events with the nominal, so a difference between two rows is more precise than the error of one row. "
         "Errors are statistical only.", INFO, size=19)
    deck.save(fig)


summary_table("final", CUTVARS, "Result table: full selection (MET < 50, ≥ 1 jet), Z→μμ",
              "data/MC and the data/MC slopes for the nominal (shaded) and every variant.")
summary_table("Z", [v for v in CUTVARS if v in GROUPS["mupt"][1] + GROUPS["mueta"][1] + GROUPS["zmass"][1] + GROUPS["tau"][1]],
              "Result table: Z selection only (no MET or jet cut), Z→μμ",
              "Only the muon, mass-window and τ-veto variants change this stage.")


# ------------------------------------------------------------------ per group: overlays, then every variant
def var_note(v, var):
    r0, r1 = row("nominal", "final", var) or {}, row(v, "final", var) or {}
    if not r0 or not r1:
        return "", ""
    t = f"data/MC {r0['ratio']:.3f} (nominal) → {r1['ratio']:.3f} (variant)"
    if np.isfinite(r1.get("slope", np.nan)):
        t += f"; slope {r0['slope']:+.1f} ± {r0['slope_err']:.1f} → {r1['slope']:+.1f} ± {r1['slope_err']:.1f} %/100 GeV"
    return t + ".", ""


for g, (gname, members) in GROUPS.items():
    members = [v for v in members if v in CUTVARS]
    if not members:
        continue
    fig = page(DARK)
    text(fig, 110, 380, gname, 64, "white", "bold", width=1700)
    text(fig, 110, 500, "Variants: " + "; ".join(DESC[v] for v in members), 30, "#C9D3E3", width=1650)
    text(fig, 110, 640, GROUP_WHY[g], 26, "#C9D3E3", width=1650)
    deck.save(fig, foot=False)
    ovl = [f"ovl_{g}_{v[6:]}.png" for v in ("muvar_z_pt", "muvar_lep0_pt", "muvar_lep1_pt", "muvar_jet_pt",
                                            "muvar_lep0_eta", "muvar_jet_eta")]
    for i in range(0, len(ovl), 2):
        fig = page()
        y = heading(fig, f"{gname}: data/MC of nominal and variants",
                    "Full selection. Black = nominal; colours = variants (not applied). Fitted slopes in the legend.") + 4
        for j, f in enumerate(ovl[i:i + 2]):
            if os.path.exists(f"{CV}/{f}"):
                image(fig, f"{CV}/{f}", y, x=110 + j * 860, w=840)
        deck.save(fig)
    for v in members:
        for var in VARS:
            f = f"{CV}/var_{v}_{var[6:]}.png"
            if not os.path.exists(f):
                continue
            fig = page()
            y = heading(fig, f"{gname} · {VLABEL[var]}",
                        f"Left: nominal. Right: variant (not applied): {DESC[v]}. Full selection, Z→μμ.")
            t, b = var_note(v, var)
            y = image(fig, f, y, hmax=1020 - note_height(t, b, size=21) - 8 - y) + 8
            if t:
                note(fig, y, t, b, INFO, size=21)
            deck.save(fig)

# ------------------------------------------------------------------ MET: Delta phi


fig = page(DARK)
text(fig, 110, 380, "MET > 50 GeV: first check with Δφ", 64, "white", "bold", width=1700)
text(fig, 110, 500, "Where does the missing transverse momentum point in the events where MC is above data?", 30,
     "#C9D3E3", width=1650)
deck.save(fig, foot=False)

fig = page()
y = heading(fig, "Why Δφ, and what we know already",
            "Δφ(MET, X) = angle in the transverse plane between the MET and an object X.") + 10
y = bullets(fig, 110, y, 1700, "Known from the 8 November run (same files)", [
    "With all cuts except MET, data/MC for MET 50–100 GeV is 0.65–0.74 for ParticleNet, DeepJet and RobustParT alike "
    "(Loose b-tag and Loose c-tag). The deficit follows the share of DY+light, not the tagger: it is smallest in Tight "
    "b-tag (0.86–0.92), where tt̄ (real MET) is about half of the MC.",
    "Z events with no selected jet also show it: data/MC 1.13 at MET < 25 GeV and 0.35–0.42 at 50–100 GeV, so the MC MET "
    "distribution is too wide even without jets. On 28 October, switching off the MC jet energy smearing removed most "
    "of this tail (open item).",
], size=22) + 16
bullets(fig, 110, y, 1700, "How to read Δφ", [
    "MET along (Δφ ≈ 0) or opposite (Δφ ≈ π) to a jet: that jet is mis-measured (too high or too low).",
    "MET opposite to the Z (Δφ(MET, Z) ≈ π): the hadronic recoil is measured too low; along the Z: too high.",
    "A flat Δφ distribution: resolution / pileup-like smearing without a preferred direction.",
    "Objects: leading jet, closest selected jet, Z, each lepton; for Z events without the jet cut also the leading "
    "jet with pT > 15 GeV at any |η| (the jets that enter the type-1 MET).",
], size=22)
deck.save(fig)

fig = page()
y = heading(fig, "Δφ: where is the deficit?",
            "data/MC in three Δφ ranges per MET bin; in brackets the share of the MC in that range. 'leading jet' and 'Z': "
            "all cuts except MET. '(0 jets)': Z events without a selected jet, no MET cut.") + 6
cols = [("Channel", 140, "left"), ("Object", 330, "left"), ("MET bin", 150, "left")] + \
       [(lab, 360, "right") for _, _, lab in DR]
rows = []
for ch in ("Zmm", "Zee"):
    for obj, name, st, lab in (("j1", "dphi_met", None, "leading jet"), ("z", "dphi_met", None, "Z"),
                               ("z", "stage_dphi_met", ["none", "MET"], "Z (0 jets)"),
                               ("jany", "stage_dphi_met", ["none", "MET"], "any jet>15 (0 jets)")):
        for mb in ("0-50", "50-100"):
            r = dphi_ratios(ch, obj, mb, name, st)
            rows.append([{"Zmm": "Z→μμ", "Zee": "Z→ee"}[ch], lab, mb] +
                        [f"{a:.2f} ({100 * s:.0f}% MC)" for a, n, s in r])
table(fig, 110, y, cols, rows, size=16)
deck.save(fig)

for obj, lab in (("j1", "leading jet"), ("jmin", "closest selected jet"), ("z", "Z"), ("lep0", "leading lepton"),
                 ("lep1", "subleading lepton")):
    f = f"{CV}/dphi_{obj}.png"
    if os.path.exists(f):
        fig = page()
        y = heading(fig, f"Δφ(MET, {lab}): all cuts except MET < 50",
                    "Rows: Z→ee, Z→μμ. Columns: MET 0–50, 50–100, > 100 GeV. DY split by leading-jet flavour.")
        image(fig, f, y, hmax=1020 - y)
        deck.save(fig)
for obj, lab in (("z", "Z"), ("jany", "leading jet, pT > 15 GeV, any |η|")):
    for jl, tag in (("no selected jet", "0j"), ("≥ 1 selected jet", "ge1j")):
        f = f"{CV}/stage_dphi_{obj}_{tag}.png"
        if os.path.exists(f):
            fig = page()
            y = heading(fig, f"Δφ(MET, {lab}): Z events with {jl}, before the MET cut",
                        "Rows: Z→ee, Z→μμ. Columns: MET 0–50, 50–100, > 100 GeV.")
            image(fig, f, y, hmax=1020 - y)
            deck.save(fig)

fig = page()
y = heading(fig, "Δφ: what it tells us, and next steps") + 10
if DPHI_FINDINGS is None:
    note(fig, y, "Not written yet", "Placeholder: filled in after looking at the Δφ plots.", OPEN)
else:
    for t, b in DPHI_FINDINGS:
        y = note(fig, y, t, b, OPEN if t.startswith("Our reading") else GOOD, size=21) + 14
deck.save(fig)
deck.close()
