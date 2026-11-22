"""MET > 50 study, Phase 1 (2026-11-22): which jets in the type-1 PuppiMET make the MC MET grow when JER
smearing is applied, plus the two checks from the JME talks of 2 Feb 2026 (JEC evaluated at raw vs
muon-subtracted pT; with / without CorrT1METJet). MC only (Summer22 DY), no data.

Every event gets many MET versions built from the same RawPuppiMET and the same jets. Only the MET changes
between versions; the event selection (leptons, Z, analysis jets) is the same for all of them:
  Z+jet stage = our analysis selection without the MET cut (simplified, see SELECTION below);
  Z stage     = same without the jet requirement.
Analysis jets (pT > 30, |eta| < 2.5) use the nominal JEC+JER pT, as in run A.

Usage: python study_zbzc_met_jer_split.py <outdir> [files per sample: incl,100,200,400,600]
"""
import json
import os
import sys
import time

import awkward as ak
import correctionlib
import numpy as np
import uproot

SELECTION = ("trigger IsoMu24 / Ele30_WPTight_Gsf; muons tight ID, PF iso04 < 0.15, pT > 26, |eta| < 2.4; "
             "electrons cutBased tight, pT > 25, |eta| < 2.4 without 1.4442-1.566; leading lepton pT > 35; "
             "OS, 71 < m(ll) < 111; jets: jetId tight-lep-veto, JEC+JER pT > 30, |eta| < 2.5, dR > 0.4 to "
             "leptons; weights: genWeight x pileup x xsec/sumw, DY stitched on LHE pT(ll) as in the workflow; "
             "NOT applied: lepton/trigger SFs, MET filters, jet veto map, Z pT weights, MET XY correction")

JERC = "/cvmfs/cms-griddata.cern.ch/cat/metadata/JME/Run3-22CDSep23-Summer22-NanoAODv12/latest/jet_jerc.json.gz"
SMEAR = "/cvmfs/cms-griddata.cern.ch/cat/metadata/JME/JER-Smearing/latest/jer_smear.json.gz"
PU = "/cvmfs/cms-griddata.cern.ch/cat/metadata/LUM/Run3-22CDSep23-Summer22-NanoAODv12/latest/puWeights.json.gz"
cs = correctionlib.CorrectionSet.from_file(JERC)
JEC = cs.compound["Summer22_22Sep2023_V4_MC_L1L2L3Res_AK4PFPuppi"]
RES = cs["Summer22_22Sep2023_JRV2_MC_PtResolution_AK4PFPuppi"]
SF = cs["Summer22_22Sep2023_JRV2_MC_ScaleFactor_AK4PFPuppi"]
SM = correctionlib.CorrectionSet.from_file(SMEAR)["JERSmear"]
PUW = correctionlib.CorrectionSet.from_file(PU)["Collisions2022_355100_357900_eraBCD_GoldenJson"]

STITCH = [("_PTLL-600_", 600.0, np.inf), ("_PTLL-400_", 400.0, 600.0), ("_PTLL-200_", 200.0, 400.0),
          ("_PTLL-100_", 100.0, 200.0), ("DYto2L-2Jets_MLL-50_TuneCP5", 0.0, 100.0)]
SAMPLE_TAGS = ["DYto2L-2Jets_MLL-50_TuneCP5", "_PTLL-100_", "_PTLL-200_", "_PTLL-400_", "_PTLL-600_"]

BR = ["Jet_pt", "Jet_eta", "Jet_phi", "Jet_area", "Jet_rawFactor", "Jet_genJetIdx", "Jet_muonSubtrFactor",
      "Jet_chEmEF", "Jet_neEmEF", "Jet_jetId", "GenJet_pt", "Rho_fixedGridRhoFastjetAll", "event",
      "CorrT1METJet_rawPt", "CorrT1METJet_eta", "CorrT1METJet_phi", "CorrT1METJet_area",
      "CorrT1METJet_muonSubtrFactor", "RawPuppiMET_pt", "RawPuppiMET_phi", "PuppiMET_pt", "PuppiMET_phi",
      "Muon_pt", "Muon_eta", "Muon_phi", "Muon_charge", "Muon_tightId", "Muon_pfRelIso04_all",
      "Electron_pt", "Electron_eta", "Electron_phi", "Electron_charge", "Electron_cutBased",
      "Electron_deltaEtaSC", "HLT_IsoMu24", "HLT_Ele30_WPTight_Gsf", "genWeight", "Pileup_nTrueInt",
      "LHE_Vpt"]

# jet classes for "smear only this class in the MET" (class defined on the JEC pT before smearing,
# full jet, and the jet |eta|); CorrT1METJet count as unmatched (no gen link in NanoAOD)
PT_BINS = [(0, 20), (20, 30), (30, 50), (50, np.inf)]
ETA_BINS = [(0, 1.3), (1.3, 2.5), (2.5, 3.0), (3.0, 5.2)]


def classes():
    c = {"all (= run A)": lambda d: np.ones_like(d["pt"], bool),
         "Jet collection only": lambda d: ~d["c1"],
         "CorrT1METJet only": lambda d: d["c1"],
         "gen-matched Jet only (= run C)": lambda d: d["gm"],
         "unmatched Jet only": lambda d: ~d["gm"] & ~d["c1"],
         "analysis-type jets only (pT>30, |eta|<2.5)": lambda d: (d["pt"] > 30) & (d["aeta"] < 2.5),
         "all other jets": lambda d: ~((d["pt"] > 30) & (d["aeta"] < 2.5))}
    for lo, hi in PT_BINS:
        c[f"JEC pT {lo}-{hi if np.isfinite(hi) else 'inf'} only"] = (lambda lo, hi: lambda d: (d["pt"] >= lo) & (d["pt"] < hi))(lo, hi)
    for lo, hi in ETA_BINS:
        c[f"|eta| {lo}-{hi} only"] = (lambda lo, hi: lambda d: (d["aeta"] >= lo) & (d["aeta"] < hi))(lo, hi)
    for (plo, phi_), (elo, ehi) in [((0, 30), (0, 2.5)), ((0, 30), (2.5, 5.2)), ((30, np.inf), (0, 2.5)),
                                    ((30, np.inf), (2.5, 5.2))]:
        c[f"pT {plo}-{phi_ if np.isfinite(phi_) else 'inf'} & |eta| {elo}-{ehi} only"] = (
            lambda a, b, e1, e2: lambda d: (d["pt"] >= a) & (d["pt"] < b) & (d["aeta"] >= e1) & (d["aeta"] < e2))(plo, phi_, elo, ehi)
    # finer |eta| along the JER SF bin edges of the 2.5-3.139 region (SF 1.22 / 1.60 / 1.64 / 1.21 below 121 GeV)
    for lo, hi in [(2.5, 2.65), (2.65, 2.853), (2.853, 2.964), (2.964, 3.139)]:
        c[f"|eta| {lo}-{hi} only"] = (lambda lo, hi: lambda d: (d["aeta"] >= lo) & (d["aeta"] < hi))(lo, hi)
    c["all except |eta| 2.65-2.964"] = lambda d: ~((d["aeta"] >= 2.65) & (d["aeta"] < 2.964))
    c["all except |eta| 2.5-3.139"] = lambda d: ~((d["aeta"] >= 2.5) & (d["aeta"] < 3.139))
    return c


CLASSES = classes()


def tag_of(fname):
    for t in SAMPLE_TAGS:
        if t in fname:
            return t
    raise ValueError(fname)


def dphi(a, b):
    return (a - b + np.pi) % (2 * np.pi) - np.pi


def process(arr, wnorm, tag):
    """Return dict of per-event arrays for the selected events (Z stage) of one chunk."""
    lo, hi = [(l, h) for t, l, h in STITCH if t == tag][0]
    vpt = ak.to_numpy(arr.LHE_Vpt)
    arr = arr[(vpt >= lo) & (vpt < hi)]
    if len(arr) == 0:
        return None
    # leptons
    mu = ak.zip({"pt": arr.Muon_pt, "eta": arr.Muon_eta, "phi": arr.Muon_phi, "q": arr.Muon_charge,
                 "ok": arr.Muon_tightId & (arr.Muon_pfRelIso04_all < 0.15)})
    mu_veto = mu[mu.ok & (mu.pt > 25) & (abs(mu.eta) < 2.5)]
    mu = mu[mu.ok & (mu.pt > 26) & (abs(mu.eta) < 2.4)]
    el = ak.zip({"pt": arr.Electron_pt, "eta": arr.Electron_eta, "phi": arr.Electron_phi, "q": arr.Electron_charge,
                 "sc": abs(arr.Electron_eta + arr.Electron_deltaEtaSC), "id": arr.Electron_cutBased})
    el_veto = el[(el.id >= 4) & (el.pt > 25) & (abs(el.eta) < 2.5)]
    el = el[(el.id >= 4) & (el.pt > 25) & (abs(el.eta) < 2.4) & ~((el.sc > 1.4442) & (el.sc < 1.566))]
    out_ch = {}
    for ch, lep, trig in [("Zee", el, arr.HLT_Ele30_WPTight_Gsf), ("Zmm", mu, arr.HLT_IsoMu24)]:
        lep = lep[ak.argsort(lep.pt, ascending=False)]
        lp = ak.pad_none(lep, 2)
        l0, l1 = lp[:, 0], lp[:, 1]
        px = l0.pt * np.cos(l0.phi) + l1.pt * np.cos(l1.phi)
        py = l0.pt * np.sin(l0.phi) + l1.pt * np.sin(l1.phi)
        pz = l0.pt * np.sinh(l0.eta) + l1.pt * np.sinh(l1.eta)
        e = l0.pt * np.cosh(l0.eta) + l1.pt * np.cosh(l1.eta)
        m = np.sqrt(np.maximum(e**2 - px**2 - py**2 - pz**2, 0))
        sel = trig & (ak.num(lep) >= 2) & (l0.pt > 35) & (l0.q * l1.q < 0) & (m > 71) & (m < 111)
        out_ch[ch] = (ak.to_numpy(ak.fill_none(sel, False)), ak.to_numpy(ak.fill_none(px, 0)),
                      ak.to_numpy(ak.fill_none(py, 0)))
    anysel = out_ch["Zee"][0] | out_ch["Zmm"][0]
    if not anysel.any():
        return None
    arr = arr[anysel]
    mu_veto, el_veto = mu_veto[anysel], el_veto[anysel]
    chan = {ch: (v[0][anysel], v[1][anysel], v[2][anysel]) for ch, v in out_ch.items()}
    w = ak.to_numpy(arr.genWeight) * PUW.evaluate(ak.to_numpy(arr.Pileup_nTrueInt), "nominal") * wnorm

    F = lambda a: ak.to_numpy(ak.flatten(a))
    rho_e, evt = arr.Rho_fixedGridRhoFastjetAll, arr.event
    # ---- Jet collection
    nj = ak.num(arr.Jet_pt)
    raw = F(arr.Jet_pt * (1 - arr.Jet_rawFactor)); eta = F(arr.Jet_eta); phi = F(arr.Jet_phi); area = F(arr.Jet_area)
    rho = F(ak.broadcast_arrays(rho_e, arr.Jet_pt)[0]); eid = F(ak.broadcast_arrays(evt, arr.Jet_pt)[0]).astype(float)
    g = arr.Jet_genJetIdx
    okg = (g >= 0) & (g < ak.num(arr.GenJet_pt))
    gpt = F(ak.where(okg, arr.GenJet_pt[ak.where(okg, g, 0)], -1.0))
    mus = F(arr.Jet_muonSubtrFactor); emef = F(arr.Jet_chEmEF + arr.Jet_neEmEF); jid = F(arr.Jet_jetId)
    # ---- CorrT1METJet
    nc = ak.num(arr.CorrT1METJet_rawPt)
    craw = F(arr.CorrT1METJet_rawPt); ceta = F(arr.CorrT1METJet_eta); cphi = F(arr.CorrT1METJet_phi)
    carea = F(arr.CorrT1METJet_area); cmus = F(arr.CorrT1METJet_muonSubtrFactor)
    crho = F(ak.broadcast_arrays(rho_e, arr.CorrT1METJet_rawPt)[0]); ceid = F(ak.broadcast_arrays(evt, arr.CorrT1METJet_rawPt)[0]).astype(float)
    # ---- merged type-1 jet list (framework: Jet + CorrT1METJet, CorrT1METJet Genpt = -1, EmEF = 0)
    d = {"raw": np.concatenate([raw, craw]), "eta": np.concatenate([eta, ceta]), "phi": np.concatenate([phi, cphi]),
         "area": np.concatenate([area, carea]), "rho": np.concatenate([rho, crho]), "eid": np.concatenate([eid, ceid]),
         "mus": np.concatenate([mus, cmus]), "emef": np.concatenate([emef, np.zeros_like(craw)]),
         "gpt": np.concatenate([gpt, -np.ones_like(craw)]), "c1": np.concatenate([np.zeros_like(raw, bool), np.ones_like(craw, bool)])}
    # event index per jet (Jet first, then CorrT1METJet, per event via counts)
    ev_j = np.repeat(np.arange(len(arr)), ak.to_numpy(nj)); ev_c = np.repeat(np.arange(len(arr)), ak.to_numpy(nc))
    d["ev"] = np.concatenate([ev_j, ev_c])
    d["aeta"] = np.abs(d["eta"])
    jecf = lambda pt, et, ar, rh: JEC.evaluate(ar, et, pt, rh)
    d["pt"] = d["raw"] * jecf(d["raw"], d["eta"], d["area"], d["rho"])             # full-jet JEC pT
    d["gm"] = d["gpt"] > 0
    s = SF.evaluate(d["eta"], d["pt"]); r = RES.evaluate(d["eta"], d["pt"], d["rho"])
    fac = np.clip(SM.evaluate(d["pt"], d["eta"], d["gpt"], d["rho"], d["eid"], r, s), 0, None)
    nomu = d["raw"] * (1 - d["mus"])
    jec_nomu = jecf(nomu, d["eta"], d["area"], d["rho"])                            # framework: JEC at noMu pT
    jec_raw = d["pt"] / np.where(d["raw"] > 0, d["raw"], 1)                         # JME talk: JEC at raw pT
    cosp, sinp = np.cos(d["phi"]), np.sin(d["phi"])
    n_ev = len(arr)
    mx0 = ak.to_numpy(arr.RawPuppiMET_pt * np.cos(arr.RawPuppiMET_phi))
    my0 = ak.to_numpy(arr.RawPuppiMET_pt * np.sin(arr.RawPuppiMET_phi))

    def met(jec_factor, smear, use):
        full = nomu * jec_factor * smear
        ok = use & (full > 15) & (d["aeta"] < 5.2) & (d["emef"] < 0.9)
        dpt = np.where(ok, full - nomu, 0.0)
        mx = mx0 - np.bincount(d["ev"], dpt * cosp, n_ev)
        my = my0 - np.bincount(d["ev"], dpt * sinp, n_ev)
        return mx, my

    allj = np.ones_like(d["raw"], bool)
    one = np.ones_like(d["raw"])
    mets = {"no JER in MET (= run B MET)": met(jec_nomu, one, allj)}
    for name, fn in CLASSES.items():
        mets[f"JER: {name}"] = met(jec_nomu, np.where(fn(d), fac, 1.0), allj)
    mets["talk: JEC at raw pT, no JER"] = met(jec_raw, one, allj)
    mets["talk: JEC at raw pT, JER all"] = met(jec_raw, fac, allj)
    mets["no CorrT1METJet, no JER"] = met(jec_nomu, one, ~d["c1"])
    mets["no CorrT1METJet, JER all"] = met(jec_nomu, fac, ~d["c1"])
    mets["NanoAOD PuppiMET (as stored)"] = (ak.to_numpy(arr.PuppiMET_pt * np.cos(arr.PuppiMET_phi)),
                                           ak.to_numpy(arr.PuppiMET_pt * np.sin(arr.PuppiMET_phi)))

    # ---- analysis jets (nominal JEC+JER, Jet collection only), lepton cleaned
    jpt = (raw * jecf(raw, eta, area, rho)) * fac[: len(raw)]
    jets = ak.zip({"pt": ak.unflatten(jpt, nj), "eta": arr.Jet_eta, "phi": arr.Jet_phi, "id": arr.Jet_jetId})
    jets = jets[(jets.pt > 30) & (abs(jets.eta) < 2.5) & (jets.id >= 6)]
    for veto in (mu_veto, el_veto):
        pr = ak.cartesian([jets, veto], nested=True)
        drm = np.sqrt((pr["0"].eta - pr["1"].eta) ** 2 + dphi(pr["0"].phi, pr["1"].phi) ** 2)
        jets = jets[ak.all(drm > 0.4, axis=2)]
    hasjet = ak.to_numpy(ak.num(jets) >= 1)

    res_out = {}
    for ch, (sel, zx, zy) in chan.items():
        if not sel.any():
            continue
        qt = np.hypot(zx, zy)
        o = {"w": w[sel], "jet": hasjet[sel], "qt": qt[sel]}
        ux, uy = zx[sel] / np.maximum(qt[sel], 1e-6), zy[sel] / np.maximum(qt[sel], 1e-6)
        for k, (mx, my) in mets.items():
            mx_, my_ = mx[sel], my[sel]
            # recoil u = -(MET + qT); u_par along qT, u_perp perpendicular
            rx, ry = -(mx_ + zx[sel]), -(my_ + zy[sel])
            o[k] = np.stack([np.hypot(mx_, my_), rx * ux + ry * uy + qt[sel], rx * (-uy) + ry * ux]).astype(np.float32)
        res_out[ch] = o
    return res_out


def wq(x, w, qs):
    """Weighted quantiles (negative weights allowed: uses the cumulative signed weight)."""
    o = np.argsort(x)
    x, w = x[o], w[o]
    c = np.cumsum(w)
    c = c / c[-1]
    return np.interp(qs, c, x)


def summarize(store, outdir):
    lines = [f"MET > 50 study, Phase 1 (MC only, Summer22 DY, {store['nfiles']} files). Selection: {SELECTION}", ""]
    js = {}
    for ch in ("Zee", "Zmm"):
        if ch not in store["data"]:
            continue
        D = {k: np.concatenate(v, axis=-1) for k, v in store["data"][ch].items()}
        for stage, msk in [("Z+jet (all cuts except MET)", D["jet"]), ("Z (no jet cut)", np.ones_like(D["jet"]))]:
            w = D["w"][msk]
            W = w.sum()
            base = D["no JER in MET (= run B MET)"][:, msk]
            full = D["JER: all (= run A)"][:, msk]

            def frac(a, lo, hi):
                return w[(a[0] >= lo) & (a[0] < hi)].sum() / W
            fb, ff = frac(base, 50, 100), frac(full, 50, 100)
            lines.append(f"== {ch}, {stage}: weighted events {W:.4g}, raw {msk.sum()}")
            lines.append(f"   MET 50-100 fraction: no JER in MET {fb:.4f}, JER all (run A) {ff:.4f} -> A/noJER {ff/fb:.3f}")
            lines.append(f"   {'MET version':58s} {'MET<50':>7s} {'50-100':>7s} {'>100':>7s} {'50-100/noJER':>12s} "
                         f"{'share of A-noJER':>16s} {'sig(u_perp)':>11s} {'med(u_par+qT)':>13s}")
            key = f"{ch} | {stage}"
            js[key] = {}
            for k in [k for k in D if k not in ("w", "jet", "qt")]:
                a = D[k][:, msk]
                f1, f2, f3 = frac(a, 0, 50), frac(a, 50, 100), frac(a, 100, 1e9)
                share = (f2 - fb) / (ff - fb) if ff != fb else np.nan
                q = wq(a[2], w, [0.16, 0.5, 0.84])
                sig = 0.5 * (q[2] - q[0])
                med = wq(a[1], w, [0.5])[0]
                lines.append(f"   {k:58s} {f1:7.4f} {f2:7.4f} {f3:7.4f} {f2/fb:12.3f} {share:16.2f} {sig:11.2f} {med:13.2f}")
                js[key][k] = dict(lt50=f1, f50_100=f2, gt100=f3, ratio_noJER=f2 / fb, share=share, sig_uperp=sig, med_upar_qt=med)
            lines.append("")
    txt = "\n".join(lines)
    print(txt)
    with open(os.path.join(outdir, "met_jer_split.txt"), "w") as f:
        f.write(txt + "\n")
    with open(os.path.join(outdir, "met_jer_split.json"), "w") as f:
        json.dump(js, f, indent=1)


def main():
    outdir = sys.argv[1]
    nper = [int(x) for x in (sys.argv[2] if len(sys.argv) > 2 else "6,4,3,2,1").split(",")]
    os.makedirs(outdir, exist_ok=True)
    fs = json.load(open("metadata/Zb_Zc_ratio_Summer22_DY.json"))
    xs = json.load(open("metadata/Zb_Zc_ratio_xsections_Summer22.json"))
    todo = []
    for tag, n in zip(SAMPLE_TAGS, nper):
        ds = [k for k in fs if tag in k][0]
        if n > 0:
            todo.append((tag, ds, fs[ds][:n]))
    store = {"data": {}, "nfiles": sum(len(f) for _, _, f in todo)}
    for tag, ds, files in todo:
        # sumw over the processed files (full files are processed)
        sumw = 0.0
        for fn in files:
            for att in range(3):
                try:
                    sumw += float(np.sum(uproot.open(fn, timeout=300)["Runs"]["genEventSumw"].array(library="np")))
                    break
                except Exception as e:  # xrootd stall: retry
                    print("retry sumw", fn, e, flush=True)
                    time.sleep(10)
            else:
                raise RuntimeError(f"cannot read {fn}")
        wnorm = xs[ds] / sumw
        for fn in files:
            t0 = time.time()
            for att in range(3):
                try:
                    part = {}
                    for arr in uproot.iterate(f"{fn}:Events", BR, step_size=150000, timeout=300):
                        r = process(arr, wnorm, tag)
                        if r is None:
                            continue
                        for ch, o in r.items():
                            for k, v in o.items():
                                part.setdefault(ch, {}).setdefault(k, []).append(v)
                    for ch, o in part.items():
                        for k, v in o.items():
                            store["data"].setdefault(ch, {}).setdefault(k, []).extend(v)
                    break
                except Exception as e:
                    print("retry", fn, repr(e), flush=True)
                    time.sleep(10)
            else:
                raise RuntimeError(f"cannot read {fn}")
            print(f"done {tag} {os.path.basename(fn)} {time.time()-t0:.0f} s", flush=True)
    summarize(store, outdir)
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
