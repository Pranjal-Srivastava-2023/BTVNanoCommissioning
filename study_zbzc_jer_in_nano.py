#!/usr/bin/env python
"""Is JER smearing already inside the NanoAOD (Summer22 v12 MC)? -> would our framework double count it?

Four independent tests on raw NanoAOD MC (no framework code involved):
 T1 jets, slope test: r = Jet_pt(nano) / (raw * L1L2L3(V4)), d = (pT_JEC - pT_gen) / pT_JEC for well matched jets.
    The JME hybrid (scaling) smearing gives pT_smear = pT_JEC * (1 + (SF-1) d), so if nano jets were smeared,
    r - 1 = (SF-1) d -> slope = SF - 1 (0.1 ... 0.6 depending on |eta|). Unsmeared: slope ~ 0.
 T2 jets, width test: core width of pT(nano)/pT_gen vs MC PtResolution (unsmeared) and SF x PtResolution (smeared).
 T3 MET: R = PuppiMET(nano) - T1MET(JEC only, rebuilt from RawPuppiMET). J = MET shift the JER (scaling part) would
    give: -sum (SF-1)(pT_JEC - pT_gen) over type-1 jets. Projection slope sum(R.J)/sum(J.J): 1 = nano MET has JER,
    0 = nano MET is JEC-only. Same slope for RawPuppiMET - (raw, no corr.) as a sanity line.
 T4 MET, direct: |PuppiMET(nano) - T1(JEC only)| vs |PuppiMET(nano) - T1(JEC+JER scaling)|.

Output: hists_zbzc_run3_jerinnano/Summer22/{jerinnano.txt, jerinnano.json, *.png}
Run: source /uscms_data/d3/psrivast/micromamba/bin/activate zbb-btv; python study_zbzc_jer_in_nano.py [nevents]
"""
import json
import os
import sys

import awkward as ak
import correctionlib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import uproot

NEV = int(sys.argv[1]) if len(sys.argv) > 1 else 150000
OUT = "hists_zbzc_run3_jerinnano/Summer22"
os.makedirs(OUT, exist_ok=True)
JSON = "/cvmfs/cms-griddata.cern.ch/cat/metadata/JME/Run3-22CDSep23-Summer22-NanoAODv12/latest/jet_jerc.json.gz"
JEC = "Summer22_22Sep2023_V4_MC"
JER = "Summer22_22Sep2023_JRV2_MC"
ALGO = "AK4PFPuppi"

meta = json.load(open("metadata/Zb_Zc_ratio_run3_Summer22.json"))
SAMPLES = {
    "DY inclusive": meta["DYto2L-2Jets_MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8"][:2],
    "DY PTLL-200": meta["DYto2L-2Jets_MLL-50_PTLL-200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8"][:1],
    "TTto2L2Nu": meta["TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8"][:1],
}
BR = [
    "Jet_pt", "Jet_eta", "Jet_phi", "Jet_rawFactor", "Jet_area", "Jet_genJetIdx", "Jet_chEmEF", "Jet_neEmEF",
    "Jet_muonSubtrFactor", "CorrT1METJet_rawPt", "CorrT1METJet_eta", "CorrT1METJet_phi", "CorrT1METJet_area",
    "CorrT1METJet_muonSubtrFactor", "GenJet_pt", "GenJet_eta", "GenJet_phi", "Rho_fixedGridRhoFastjetAll",
    "PuppiMET_pt", "PuppiMET_phi", "RawPuppiMET_pt", "RawPuppiMET_phi", "GenMET_pt",
]

cs = correctionlib.CorrectionSet.from_file(JSON)
L123 = cs.compound[f"{JEC}_L1L2L3Res_{ALGO}"]
L1 = cs[f"{JEC}_L1FastJet_{ALGO}"]
RES = cs[f"{JER}_PtResolution_{ALGO}"]
SF = cs[f"{JER}_ScaleFactor_{ALGO}"]
sf_has_syst = len(SF.inputs) == 3


def sf_eval(eta, pt):
    return SF.evaluate(eta, pt, "nom") if sf_has_syst else SF.evaluate(eta, pt)


def load(files):
    arrs = []
    left = NEV
    for f in files:
        with uproot.open(f, timeout=300) as fh:
            t = fh["Events"]
            n = min(left, t.num_entries)
            arrs.append(t.arrays(BR, entry_stop=n))
            left -= n
        if left <= 0:
            break
    return ak.concatenate(arrs)


def flat(x):
    return np.asarray(ak.flatten(x), dtype=np.float64)


ETA_BINS = [0, 1.3, 2.5, 2.65, 2.964, 3.139, 5.2]
results = {}
store = {}
for name, files in SAMPLES.items():
    print(f"== {name}: reading {NEV} events from {len(files)} file(s)", flush=True)
    ev = load(files)
    rho = ev.Rho_fixedGridRhoFastjetAll
    # ---- analysis jets (Jet) ----
    J = ev[["Jet_pt", "Jet_eta", "Jet_phi", "Jet_rawFactor", "Jet_area", "Jet_genJetIdx"]]
    nj = ak.num(ev.Jet_pt)
    raw = ev.Jet_pt * (1 - ev.Jet_rawFactor)
    rho_j = ak.broadcast_arrays(rho, raw)[0]
    corr = ak.unflatten(L123.evaluate(flat(ev.Jet_area), flat(ev.Jet_eta), flat(raw), flat(rho_j)), nj)
    corrL1 = ak.unflatten(L1.evaluate(flat(ev.Jet_area), flat(ev.Jet_eta), flat(raw), flat(rho_j)), nj)
    ptjec = raw * corr
    gidx = ev.Jet_genJetIdx
    has = gidx >= 0
    gsafe = ak.where(has, gidx, 0)
    gpt = ak.where(has, ev.GenJet_pt[gsafe], -1.0)
    geta = ev.GenJet_eta[gsafe]
    gphi = ev.GenJet_phi[gsafe]
    dphi = (ev.Jet_phi - gphi + np.pi) % (2 * np.pi) - np.pi
    dR = np.sqrt((ev.Jet_eta - geta) ** 2 + dphi**2)
    res = ak.unflatten(RES.evaluate(flat(ev.Jet_eta), flat(ptjec), flat(rho_j)), nj)
    sf = ak.unflatten(sf_eval(flat(ev.Jet_eta), flat(ptjec)), nj)
    # JME matching for the deterministic (scaling) part: dR < 0.2 and |pT - pT_gen| < 3 sigma pT
    match = has & (dR < 0.2) & (abs(ptjec - gpt) < 3 * res * ptjec)

    # T1: slope of r-1 vs d per |eta| bin (pT_JEC > 20)
    sel = match & (ptjec > 20)
    r = flat((ev.Jet_pt / ptjec)[sel])
    d = flat(((ptjec - gpt) / ptjec)[sel])
    aeta = np.abs(flat(ev.Jet_eta[sel]))
    sfv = flat(sf[sel])
    resv = flat(res[sel])
    selw = has & (dR < 0.2) & (ptjec > 20)  # width test: dR match only (no 3 sigma cut, it clips the tails)
    ptnano_over_gen = flat((ev.Jet_pt / gpt)[selw])
    ptgen = flat(gpt[selw])
    aeta_w = np.abs(flat(ev.Jet_eta[selw]))
    resv_w = flat(res[selw])
    sfv_w = flat(sf[selw])
    t1 = []
    for lo, hi in zip(ETA_BINS[:-1], ETA_BINS[1:]):
        m = (aeta >= lo) & (aeta < hi)
        if m.sum() < 50:
            continue
        x = d[m] - d[m].mean()
        y = (r[m] - 1) - (r[m] - 1).mean()
        slope = float((x * y).sum() / (x * x).sum())
        t1.append(dict(eta=f"{lo}-{hi}", njets=int(m.sum()), slope=slope, expected_if_smeared=float(np.mean(sfv[m]) - 1),
                       mean_r=float(r[m].mean()), rms_r=float(r[m].std())))
    # T2: core width of pT_nano/pT_gen vs resolution, gen pT 30-60 and 60-150
    t2 = []
    for lo, hi in zip(ETA_BINS[:-1], ETA_BINS[1:]):
        for plo, phi_ in [(30, 60), (60, 150)]:
            m = (aeta_w >= lo) & (aeta_w < hi) & (ptgen >= plo) & (ptgen < phi_)
            if m.sum() < 100:
                continue
            x = ptnano_over_gen[m] / np.median(ptnano_over_gen[m])
            s = x.std()
            for _ in range(10):  # iterative 2-sigma core
                c = np.abs(x - 1) < 2 * s
                s = x[c].std() / 0.88  # std of a +-2 sigma truncated Gaussian is 0.88 sigma
            t2.append(dict(eta=f"{lo}-{hi}", ptgen=f"{plo}-{phi_}", njets=int(m.sum()), width_nano=float(s),
                           mc_resolution=float(np.mean(resv_w[m])),
                           sf_x_resolution=float(np.mean(resv_w[m] * sfv_w[m]))))

    # ---- type-1 MET rebuilt from RawPuppiMET (JEC only) + JER vector ----
    def t1parts(rawpt, eta, phi, area, musf, emef, gptj, matchj, sfj):
        n = ak.num(rawpt)
        rho_b = ak.broadcast_arrays(rho, rawpt)[0]
        nomu = rawpt * (1 - musf)
        c123 = ak.unflatten(L123.evaluate(flat(area), flat(eta), flat(rawpt), flat(rho_b)), n)
        c1 = ak.unflatten(L1.evaluate(flat(area), flat(eta), flat(rawpt), flat(rho_b)), n)
        full = nomu * c123
        ok = (full > 15) & (abs(eta) < 5.2) & (emef < 0.9)
        dpt = ak.where(ok, full - nomu * c1, 0.0)
        # JER scaling shift of the full-corr. muon-subtracted pT, only for JME-matched jets
        djer = ak.where(ok & matchj, (sfj - 1) * (full - gptj * (full / (rawpt * c123))), 0.0)
        return (ak.sum(dpt * np.cos(phi), axis=1), ak.sum(dpt * np.sin(phi), axis=1),
                ak.sum(djer * np.cos(phi), axis=1), ak.sum(djer * np.sin(phi), axis=1))

    emef = ev.Jet_chEmEF + ev.Jet_neEmEF
    ax1, ay1, jx1, jy1 = t1parts(raw, ev.Jet_eta, ev.Jet_phi, ev.Jet_area, ev.Jet_muonSubtrFactor, emef, gpt, match, sf)
    # CorrT1METJet: low-pT jets not in Jet; no gen matching / EmEF stored -> JEC only, no JER term (small)
    cj = ev.CorrT1METJet_rawPt
    zeros = ak.zeros_like(cj)
    ax2, ay2, _, _ = t1parts(cj, ev.CorrT1METJet_eta, ev.CorrT1METJet_phi, ev.CorrT1METJet_area,
                             ev.CorrT1METJet_muonSubtrFactor, zeros, zeros - 1, zeros > 1, zeros + 1)
    rx = ev.RawPuppiMET_pt * np.cos(ev.RawPuppiMET_phi)
    ry = ev.RawPuppiMET_pt * np.sin(ev.RawPuppiMET_phi)
    t1x = rx - ax1 - ax2
    t1y = ry - ay1 - ay2
    jerx = -jx1  # MET shift that JER (scaling part) would add
    jery = -jy1
    nx = ev.PuppiMET_pt * np.cos(ev.PuppiMET_phi)
    ny = ev.PuppiMET_pt * np.sin(ev.PuppiMET_phi)
    Rx, Ry = np.asarray(nx - t1x), np.asarray(ny - t1y)
    jerx, jery = np.asarray(jerx), np.asarray(jery)
    big = np.hypot(jerx, jery) > 2  # events where JER would move the MET by > 2 GeV
    slope = float(((Rx * jerx + Ry * jery)[big]).sum() / ((jerx**2 + jery**2)[big]).sum())
    # same for the raw MET: raw - T1_ours = sum of JEC shifts by construction -> project the residual
    # (nano T1 - nano raw) - (ours T1 - ours raw) is identical to R; so test raw via its own definition:
    Rrawx = np.asarray(rx - (t1x + ax1 + ax2))  # = 0 identically, printed as a bookkeeping check
    d_jec = np.hypot(Rx, Ry)
    d_jer = np.hypot(Rx - jerx, Ry - jery)
    met_nano = np.asarray(ev.PuppiMET_pt)
    t1pt = np.hypot(np.asarray(t1x), np.asarray(t1y))
    t1jerpt = np.hypot(np.asarray(t1x) + jerx, np.asarray(t1y) + jery)
    results[name] = dict(
        nevents=len(ev),
        T1_jet_slope=t1,
        T2_jet_width=t2,
        T3_met_slope=dict(nevents_used=int(big.sum()), slope=slope,
                          note="1 = nano PuppiMET contains the JER shift, 0 = JEC-only"),
        T4_met_direct=dict(
            median_abs_diff_nano_vs_T1_JEC=float(np.median(d_jec[big])),
            median_abs_diff_nano_vs_T1_JEC_JER=float(np.median(d_jer[big])),
            frac_events_closer_to_JEC_only=float((d_jec[big] < d_jer[big]).mean()),
            frac_MET50_nano=float((met_nano > 50).mean()),
            frac_MET50_T1_JEC=float((t1pt > 50).mean()),
            frac_MET50_T1_JEC_JER=float((t1jerpt > 50).mean()),
            max_abs_bookkeeping=float(np.abs(Rrawx).max()),
        ),
    )
    store[name] = dict(d=d, r=r, aeta=aeta, Rpar=(Rx * jerx + Ry * jery)[big] / np.hypot(jerx, jery)[big],
                       Jmag=np.hypot(jerx, jery)[big], d_jec=d_jec[big], d_jer=d_jer[big])
    print(json.dumps(results[name], indent=1), flush=True)

json.dump(results, open(f"{OUT}/jerinnano.json", "w"), indent=1)

# ---------------- text table ----------------
L = []
L.append("Is JER already applied in Summer22 NanoAODv12 MC?  (study_zbzc_jer_in_nano.py)")
L.append(f"JEC {JEC}, JER {JER}, {ALGO}; first {NEV} events per sample\n")
for name, R in results.items():
    L.append(f"=== {name} ({R['nevents']} events)")
    L.append(" T1  jets: slope of [Jet_pt(nano)/(raw x L1L2L3) - 1] vs (pT_JEC - pT_gen)/pT_JEC")
    L.append(f"   {'|eta|':12s} {'jets':>8s} {'slope':>8s} {'if smeared (SF-1)':>18s} {'<r>':>7s}")
    for t in R["T1_jet_slope"]:
        L.append(f"   {t['eta']:12s} {t['njets']:8d} {t['slope']:8.3f} {t['expected_if_smeared']:18.3f} {t['mean_r']:7.3f}")
    L.append(" T2  jets: core width of pT(nano)/pT(gen)")
    L.append(f"   {'|eta|':12s} {'pTgen':8s} {'jets':>7s} {'nano':>7s} {'MC res':>7s} {'SFxres':>7s}")
    for t in R["T2_jet_width"]:
        L.append(f"   {t['eta']:12s} {t['ptgen']:8s} {t['njets']:7d} {t['width_nano']:7.3f} {t['mc_resolution']:7.3f} {t['sf_x_resolution']:7.3f}")
    m = R["T3_met_slope"]
    L.append(f" T3  MET: projection slope of [PuppiMET(nano) - T1(JEC only)] on the JER shift: {m['slope']:.3f}"
             f"  ({m['nevents_used']} events with |JER shift| > 2 GeV; 1 = JER inside, 0 = not)")
    m = R["T4_met_direct"]
    L.append(f" T4  MET: median |nano - T1(JEC only)| = {m['median_abs_diff_nano_vs_T1_JEC']:.2f} GeV, "
             f"|nano - T1(JEC+JER)| = {m['median_abs_diff_nano_vs_T1_JEC_JER']:.2f} GeV; "
             f"closer to JEC-only in {100*m['frac_events_closer_to_JEC_only']:.1f} % of events")
    L.append(f"      fraction MET > 50: nano {100*m['frac_MET50_nano']:.2f} %, T1 JEC-only {100*m['frac_MET50_T1_JEC']:.2f} %, "
             f"T1 JEC+JER(scaling) {100*m['frac_MET50_T1_JEC_JER']:.2f} %\n")
open(f"{OUT}/jerinnano.txt", "w").write("\n".join(L) + "\n")
print("\n".join(L))

# ---------------- plots ----------------
for name, S in store.items():
    tag = name.replace(" ", "_")
    fig, axs = plt.subplots(1, 3, figsize=(16, 4.8))
    for (lo, hi), col in zip([(0, 1.3), (2.65, 2.964)], ["C0", "C3"]):
        m = (S["aeta"] >= lo) & (S["aeta"] < hi)
        bins = np.linspace(-0.4, 0.4, 17)
        idx = np.digitize(S["d"][m], bins)
        xc, yc = [], []
        for i in range(1, len(bins)):
            k = idx == i
            if k.sum() > 30:
                xc.append(0.5 * (bins[i - 1] + bins[i]))
                yc.append(np.mean(S["r"][m][k]) - 1)
        axs[0].plot(xc, yc, "o", color=col, label=f"nano jets, |eta| {lo}-{hi}")
        sfm = [t for t in results[name]["T1_jet_slope"] if t["eta"] == f"{lo}-{hi}"]
        if sfm:
            e = sfm[0]["expected_if_smeared"]
            axs[0].plot(bins, e * bins + np.mean(yc), "--", color=col, label=f"if JER-smeared (slope {e:.2f})")
    axs[0].set_xlabel("(pT_JEC - pT_gen) / pT_JEC")
    axs[0].set_ylabel("Jet_pt(nano) / (raw x JEC) - 1")
    axs[0].legend(fontsize=8)
    axs[0].set_title("T1: are NanoAOD jets smeared?")
    Jb = np.linspace(0, 30, 16)
    idx = np.digitize(S["Jmag"], Jb)
    xc = [0.5 * (Jb[i - 1] + Jb[i]) for i in range(1, len(Jb)) if (idx == i).sum() > 30]
    yc = [np.mean(S["Rpar"][idx == i]) for i in range(1, len(Jb)) if (idx == i).sum() > 30]
    axs[1].plot(xc, yc, "ko", label="nano PuppiMET - T1(JEC only), along JER shift")
    axs[1].plot(Jb, Jb, "r--", label="expected if nano MET had JER")
    axs[1].plot(Jb, 0 * Jb, "b:", label="expected if nano MET is JEC-only")
    axs[1].set_xlabel("|MET shift JER would give| [GeV]")
    axs[1].set_ylabel("mean projection [GeV]")
    axs[1].legend(fontsize=8)
    axs[1].set_title("T3: is NanoAOD PuppiMET smeared?")
    b = np.linspace(0, 20, 41)
    axs[2].hist(S["d_jec"], b, histtype="step", color="b", label="|nano - T1(JEC only)|")
    axs[2].hist(S["d_jer"], b, histtype="step", color="r", label="|nano - T1(JEC+JER)|")
    axs[2].set_xlabel("|vector difference| [GeV]")
    axs[2].set_ylabel("events (|JER shift| > 2 GeV)")
    axs[2].legend(fontsize=8)
    axs[2].set_title("T4: nano PuppiMET vs rebuilt T1 MET")
    fig.suptitle(f"Summer22 NanoAODv12, {name}")
    fig.tight_layout()
    fig.savefig(f"{OUT}/jerinnano_{tag}.png", dpi=110)
    plt.close(fig)
print("wrote", OUT)
