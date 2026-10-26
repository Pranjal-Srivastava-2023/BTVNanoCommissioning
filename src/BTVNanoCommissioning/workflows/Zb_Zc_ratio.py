"""
Run 3 Z(->ee/mumu) + heavy-flavour jet workflow, for measuring the Z+b / Z+c
ratio. The jet collection is chosen with `jet`:

- "AK4" (default, workflow "Zb_Zc_ratio"): resolved Z+jet. Leading AK4 (PUPPI)
  jet with pT > 30, |eta| < 2.5, tight-lepton-veto jet ID and dR > 0.4 from the
  leptons; no Z pT requirement. Tagger: ParticleNet AK4 B / CvL / CvB.
  Flavour from Jet_hadronFlavour: b (5), c (4), l (else). AK4 jets carry no
  hadron counts in NanoAOD, so there is no b/bb or c/cc split. Every AK4
  histogram also has a second flavour axis "pflav" from |Jet_partonFlavour|:
  b (5), c (4), uds (1-3), g (21), none (0, no parton matched), so the two
  definitions can be compared; nevt_migration holds the raw hadron x parton
  flavour counts.
- "AK8" (workflow "Zb_Zc_ratio_AK8"): boosted selection following the Run 2
  QCD_sf workflow (QCD_validation.py) -- leading AK8 jet with pT > 200,
  |eta| < 2.5, msoftdrop > 40 and two subjets, dR > 0.8 from the leptons.
  Tagger: ParticleNet XbbVsQCD / XccVsQCD (particleNetMD_* no longer exist).
  Flavour from B/C hadron counts: bb (>= 2 B), b (1 B), cc (0 B, >= 2 C),
  c (0 B, 1 C), l.

Common Z selection, with these Run 3 changes w.r.t. Run 2: two leptons in the
Z mass window, low MET, tight muon ID (matches the MUO tight ID / tight PF iso
SFs), opposite-sign lepton pair, PuppiMET; framework correctionlib SFs (pileup,
lepton ID/iso/reco) instead of the old framework's histograms; no L1 prefiring
weight (none in Run 3).

Campaigns: Summer22 (2022 C-D), Summer22EE (2022 E-G), Summer23 (2023 C),
Summer23BPix (2023 D), MC and data. The framework's common_shifts applies the
JEC/JER (jets and type-1 PuppiMET), muon and electron scale/smearing and the
jet veto map (events with any jet in a vetoed region are dropped). MC weights:
pileup, lepton ID/iso/reco SFs and the single-lepton trigger SF of the leading
lepton (IsoMu24 / Ele30_WPTight; the leading lepton has pT > 35, on the plateau).
Data datasets must carry their run era (e.g. "Muon_Run2022C") so that the JEC
era can be matched.

The DY pT(ll)-binned samples (PTLL-X) are inclusive above X, so each one is
restricted to its own LHE pT(ll) slice (STITCH below) and the inclusive sample
covers pT(ll) < 100. sumw is over the full sample, before the slice cut.
"""

import numpy as np
import awkward as ak
import hist
from coffea import processor
from coffea.analysis_tools import PackedSelection, Weights
from BTVNanoCommissioning.helpers.func import update, dump_lumi
from BTVNanoCommissioning.helpers.update_branch import missing_branch
from BTVNanoCommissioning.utils.correction import (
    load_lumi,
    load_SF,
    reweighting,
    common_shifts,
    puwei,
    muSFs,
    eleSFs,
)
from BTVNanoCommissioning.utils.selection import (
    ele_ip_mask,
    lep_kin,
    ele_EE_EB_removal,
    ele_ID,
    mu_iso,
    jet_id,
)

FLAVOURS = {
    "AK4": ["b", "c", "l", "data"],
    "AK8": ["bb", "b", "cc", "c", "l", "data"],
}
PARTON_FLAVOURS = ["b", "c", "uds", "g", "none", "data"]
CHANNELS = ["Zee", "Zmm"]


class NanoProcessor(processor.ProcessorABC):
    trigger_config = {
        c: {"eleTrig": ["Ele30_WPTight_Gsf"], "muonTrig": ["IsoMu24"]}
        for c in ["Summer22", "Summer22EE", "Summer23", "Summer23BPix"]
    }
    # (dataset-name substring, LHE pT(ll) lower edge, upper edge); first match wins
    STITCH = [
        ("_PTLL-600_", 600.0, np.inf),
        ("_PTLL-400_", 400.0, 600.0),
        ("_PTLL-200_", 200.0, 400.0),
        ("_PTLL-100_", 100.0, 200.0),
        ("DYto2L-2Jets_MLL-50_TuneCP5", 0.0, 100.0),
    ]

    def __init__(
        self,
        year="2022",
        campaign="Summer22",
        name="",
        isSyst=False,
        isArray=False,
        noHist=False,
        chunksize=75000,
        jet="AK4",
    ):
        if campaign not in self.trigger_config:
            raise KeyError(
                f"Zb_Zc_ratio: campaign {campaign} not configured "
                f"(have {list(self.trigger_config)})"
            )
        if jet not in FLAVOURS:
            raise KeyError(f"Zb_Zc_ratio: jet must be one of {list(FLAVOURS)}")
        self._year = year
        self._campaign = campaign
        self.jet = jet
        self.name = name
        self.isSyst = isSyst
        self.isArray = isArray
        self.noHist = noHist
        self.chunksize = chunksize
        self.lumiMask = load_lumi(self._campaign)
        self.SF_map = load_SF(self._year, self._campaign)

    def make_hists(self):
        ch = hist.axis.StrCategory(CHANNELS, name="channel")
        fl = [hist.axis.StrCategory(FLAVOURS[self.jet], name="flav")]
        if self.jet == "AK4":
            fl.append(hist.axis.StrCategory(PARTON_FLAVOURS, name="pflav"))

        def h(*axes):
            return hist.Hist(ch, *fl, *axes, storage=hist.storage.Weight())

        Reg = hist.axis.Regular
        if self.jet == "AK4":
            hists = {
                "jet_pt": h(Reg(50, 30, 530, name="pt", label="AK4 jet $p_T$ [GeV]")),
                "jet_eta": h(Reg(25, -2.5, 2.5, name="eta", label=r"AK4 jet $\eta$")),
                "jet_PNetB": h(Reg(50, 0, 1, name="score", label="PNet B")),
                "jet_PNetCvL": h(Reg(50, 0, 1, name="score", label="PNet CvL")),
                "jet_PNetCvB": h(Reg(50, 0, 1, name="score", label="PNet CvB")),
                "jet_CvL_CvB": h(
                    Reg(25, 0, 1, name="cvl", label="PNet CvL"),
                    Reg(25, 0, 1, name="cvb", label="PNet CvB"),
                ),
                "n_jet": h(hist.axis.Integer(0, 10, name="n", label="N AK4 jets")),
            }
        else:
            hists = {
                "fj_pt": h(Reg(50, 200, 1200, name="pt", label="AK8 jet $p_T$ [GeV]")),
                "fj_eta": h(Reg(25, -2.5, 2.5, name="eta", label=r"AK8 jet $\eta$")),
                "fj_msd": h(Reg(52, 40, 300, name="mass", label="AK8 jet $m_{SD}$ [GeV]")),
                "fj_mreg": h(Reg(60, 0, 300, name="mass", label="AK8 jet PNet regressed mass [GeV]")),
                "fj_Xbb": h(Reg(50, 0, 1, name="score", label="PNet XbbVsQCD")),
                "fj_Xcc": h(Reg(50, 0, 1, name="score", label="PNet XccVsQCD")),
                "fj_Xbb_Xcc": h(
                    Reg(25, 0, 1, name="xbb", label="PNet XbbVsQCD"),
                    Reg(25, 0, 1, name="xcc", label="PNet XccVsQCD"),
                ),
                "fj_tau21": h(Reg(25, 0, 1, name="tau21", label=r"AK8 jet $\tau_{21}$")),
                "n_fj": h(hist.axis.Integer(0, 6, name="n", label="N AK8 jets")),
            }
        hists.update(
            {
                "z_mass": h(Reg(40, 71, 111, name="mass", label="$m_{\\ell\\ell}$ [GeV]")),
                "z_pt": h(Reg(50, 0, 1000, name="pt", label="$p_T^{\\ell\\ell}$ [GeV]")),
                "lep0_pt": h(Reg(50, 0, 1000, name="pt", label="Leading lepton $p_T$ [GeV]")),
                "lep1_pt": h(Reg(50, 0, 500, name="pt", label="Subleading lepton $p_T$ [GeV]")),
                "lhe_vpt": h(Reg(75, 0, 1500, name="pt", label="LHE $p_T^{\\ell\\ell}$ [GeV]")),
            }
        )
        return hists

    @property
    def accumulator(self):
        return self._accumulator

    def process(self, events):
        events = missing_branch(events)
        sumws = reweighting(events, self.isSyst)
        isRealData = not hasattr(events, "genWeight")
        dataset = events.metadata["dataset"]

        def count(ev):
            # (raw events, sum of genWeight) for the cutflow
            if isRealData:
                return len(ev), float(len(ev))
            return len(ev), float(ak.sum(ev.genWeight))

        pre = {"all": count(events)}
        ## Lumi mask (data) / LHE pT(ll) stitching slice (DY MC)
        req_lumi = np.ones(len(events), dtype="bool")
        if isRealData:
            req_lumi = self.lumiMask(events.run, events.luminosityBlock)
        else:
            for tag, lo, hi in self.STITCH:
                if tag in dataset:
                    vpt = ak.to_numpy(events.LHE.Vpt)
                    req_lumi = (vpt >= lo) & (vpt < hi)
                    break
        events = events[req_lumi]
        pre["lumi_slice"] = count(events)

        ## JEC/JER + type-1 MET, lepton scale/smearing, jet veto map
        if len(events) == 0:
            vetoed_events, shifts = events, [({}, None)]
        else:
            vetoed_events, shifts = common_shifts(self, events)
        pre["jetveto"] = count(vetoed_events)
        output = processor.accumulate(
            self.process_shift(update(vetoed_events, collections), sumws, name)
            for collections, name in shifts
        )

        out = output[dataset]
        if isRealData:
            # golden-JSON lumisections processed, for brilcalc
            dump_lumi(events, out)
        # prepend the pre-selection steps to the per-channel cutflows
        for key, idx, typ in (("cutflow_raw", 0, int), ("cutflow", 1, float)):
            for c in CHANNELS:
                steps = processor.defaultdict_accumulator(typ)
                for step, n in pre.items():
                    steps[step] = n[idx]
                for step, n in out[key][c].items():
                    steps[step] = n
                out[key][c] = steps
        return output

    def process_shift(self, events, sumws, shift_name):
        isRealData = not hasattr(events, "genWeight")
        dataset = events.metadata["dataset"]
        output = {} if self.noHist else self.make_hists()
        output["sumw"] = sumws["sumw"]
        cutflow = {
            c: processor.defaultdict_accumulator(float) for c in CHANNELS
        }
        cutflow_raw = {c: processor.defaultdict_accumulator(int) for c in CHANNELS}
        output["cutflow"] = cutflow
        output["cutflow_raw"] = cutflow_raw
        # unweighted number of selected events per jet flavour
        output["nevt_flav"] = {
            c: processor.defaultdict_accumulator(int) for c in CHANNELS
        }
        if self.jet == "AK4":
            # unweighted hadron x parton flavour counts, keys "hadron|parton"
            output["nevt_migration"] = {
                c: processor.defaultdict_accumulator(int) for c in CHANNELS
            }
            # leading-jet GenJet match (Jet_genJetIdx >= 0) per hadron x parton
            # flavour, keys "hadron|parton|gen" with gen = matched / nomatch;
            # unmatched jets are the pileup candidates
            output["nevt_genmatch"] = {
                c: processor.defaultdict_accumulator(int) for c in CHANNELS
            }
            output["sumw_genmatch"] = {
                c: processor.defaultdict_accumulator(float) for c in CHANNELS
            }

        if len(events) == 0:
            return {dataset: output}

        ## HLT
        trig = {}
        for key, paths in self.trigger_config[self._campaign].items():
            trig[key] = np.zeros(len(events), dtype="bool")
            for p in paths:
                trig[key] = trig[key] | ak.to_numpy(events.HLT[p])

        ## Electrons: IP, pT > 25 |eta| < 2.4, EB-EE gap veto, tight cut-based ID
        ele = events.Electron[ele_ip_mask(events, self._campaign)]
        ele_jetveto = ele[(abs(ele.eta) < 2.5) & (ele.pt > 25) & (ele.cutBased >= 4)]
        ele = ele[lep_kin(ele)]
        ele = ele[ele_EE_EB_removal(ele)]
        ele = ele[ele_ID(ele)]

        ## Muons: pT > 25 |eta| < 2.4, tight ID, PF iso < 0.15
        mu_jetveto = events.Muon[
            (abs(events.Muon.eta) < 2.5)
            & (events.Muon.pt > 25)
            & events.Muon.tightId
            & (events.Muon.pfRelIso04_all < 0.15)
        ]
        mu = events.Muon[lep_kin(events.Muon)]
        mu = mu[mu.tightId]
        mu = mu[mu_iso(mu)]

        # pT order can change after the scale/smearing corrections
        ele = ele[ak.argsort(ele.pt, ascending=False)]
        mu = mu[ak.argsort(mu.pt, ascending=False)]

        jets, lead, req_jet = self.select_jets(events, ele_jetveto, mu_jetveto)
        # events.MET = type-1 corrected PuppiMET from common_shifts
        req_met = ak.to_numpy(events.MET.pt < 50)

        ## Per-channel selection
        genw = (
            np.ones(len(events))
            if isRealData
            else ak.to_numpy(events.genWeight).astype(float)
        )
        leps = {"Zee": ele, "Zmm": mu}
        trigkey = {"Zee": "eleTrig", "Zmm": "muonTrig"}
        for channel in CHANNELS:
            lep = ak.pad_none(leps[channel], 2, axis=1)
            l0, l1 = lep[:, 0], lep[:, 1]
            zcand = l0 + l1
            sel = PackedSelection()
            sel.add("trigger", trig[trigkey[channel]])
            sel.add(
                "leptons",
                ak.to_numpy(
                    ak.fill_none((ak.num(leps[channel]) >= 2) & (l0.pt > 35), False)
                ),
            )
            sel.add("OS", ak.to_numpy(ak.fill_none(l0.charge * l1.charge < 0, False)))
            sel.add(
                "Zmass",
                ak.to_numpy(
                    ak.fill_none((zcand.mass > 71) & (zcand.mass < 111), False)
                ),
            )
            sel.add("MET", req_met)
            sel.add("jet", req_jet)
            steps = ["trigger", "leptons", "OS", "Zmass", "MET", "jet"]
            for i, step in enumerate(steps):
                passed = sel.all(*steps[: i + 1])
                cutflow[channel][step] += float(np.sum(genw[passed]))
                cutflow_raw[channel][step] += int(np.sum(passed))

            mask = sel.all(*steps)
            if self.noHist or not mask.any():
                continue

            ev = events[mask]
            jet = lead[mask]
            z = zcand[mask]
            weight = genw[mask]
            if not isRealData:
                weight = weight * self.mc_sf(ev, l0[mask], l1[mask], channel)

            if isRealData:
                flav = np.full(len(ev), "data")
            else:
                flav = self.jet_flavour(jet)
            for f, n in zip(*np.unique(flav, return_counts=True)):
                output["nevt_flav"][channel][str(f)] += int(n)
            flavs = {"flav": flav}
            if self.jet == "AK4":
                pflav = (
                    np.full(len(ev), "data")
                    if isRealData
                    else self.parton_flavour(jet)
                )
                for hp, n in zip(
                    *np.unique(np.char.add(np.char.add(flav, "|"), pflav), return_counts=True)
                ):
                    output["nevt_migration"][channel][str(hp)] += int(n)
                flavs["pflav"] = pflav
                if not isRealData:
                    gen = np.where(
                        ak.to_numpy(jet.genJetIdx) >= 0, "matched", "nomatch"
                    )
                    key = np.char.add(np.char.add(np.char.add(flav, "|"), pflav), "|")
                    key = np.char.add(key, gen)
                    for k in np.unique(key):
                        sel_k = key == k
                        output["nevt_genmatch"][channel][str(k)] += int(np.sum(sel_k))
                        output["sumw_genmatch"][channel][str(k)] += float(
                            np.sum(weight[sel_k])
                        )

            def fill(name, **values):
                output[name].fill(channel=channel, **flavs, **values, weight=weight)

            self.fill_jets(fill, jet, jets[mask])
            fill("z_mass", mass=ak.to_numpy(z.mass))
            fill("z_pt", pt=ak.to_numpy(z.pt))
            fill("lep0_pt", pt=ak.to_numpy(l0[mask].pt))
            fill("lep1_pt", pt=ak.to_numpy(l1[mask].pt))
            # pure pythia8 samples (WW, WZ, ZZ) have no LHE block
            if not isRealData and "LHE" in ev.fields:
                fill("lhe_vpt", pt=ak.to_numpy(ev.LHE.Vpt))

        return {dataset: output}

    def select_jets(self, events, ele_jetveto, mu_jetveto):
        """Selected jet collection, its leading jet and the per-event jet requirement."""
        if self.jet == "AK4":
            # pT > 30, |eta| < 2.5, tight-lepton-veto ID (with the NanoAODv12
            # jetId fix), lepton cleaning dR > 0.4
            jets = events.Jet[jet_id(events, self._campaign, max_eta=2.5, min_pt=30)]
            jets = jets[ak.all(jets.metric_table(ele_jetveto) > 0.4, axis=2)]
            jets = jets[ak.all(jets.metric_table(mu_jetveto) > 0.4, axis=2)]
            lead = ak.pad_none(jets, 1, axis=1)[:, 0]
            req_jet = ak.to_numpy(ak.num(jets) >= 1)
            return jets, lead, req_jet

        ## AK8 jets: lepton cleaning (dR > 0.8), tight jet ID, two subjets.
        # FatJet_jetId in NanoAODv12 is only wrong for |eta| > 2.7, outside our
        # |eta| < 2.5 selection, so it is used as is.
        fj = events.FatJet
        fj = fj[ak.all(fj.metric_table(ele_jetveto) > 0.8, axis=2)]
        fj = fj[ak.all(fj.metric_table(mu_jetveto) > 0.8, axis=2)]
        fj = fj[fj.jetId >= 2]
        fj = fj[(fj.subJetIdx1 >= 0) & (fj.subJetIdx2 >= 0)]
        lead = ak.pad_none(fj, 1, axis=1)[:, 0]
        req_jet = ak.to_numpy(
            ak.fill_none(
                (lead.pt > 200) & (abs(lead.eta) < 2.5) & (lead.msoftdrop > 40),
                False,
            )
        )
        return fj, lead, req_jet

    def jet_flavour(self, jet):
        if self.jet == "AK4":
            hf = ak.to_numpy(jet.hadronFlavour)
            return np.select([hf == 5, hf == 4], ["b", "c"], default="l")
        nb = ak.to_numpy(jet.nBHadrons)
        nc = ak.to_numpy(jet.nCHadrons)
        return np.select(
            [nb >= 2, nb == 1, nc >= 2, nc == 1],
            ["bb", "b", "cc", "c"],
            default="l",
        )

    @staticmethod
    def parton_flavour(jet):
        pf = np.abs(ak.to_numpy(jet.partonFlavour))
        return np.select(
            [pf == 5, pf == 4, (pf >= 1) & (pf <= 3), pf == 21],
            ["b", "c", "uds", "g"],
            default="none",
        )

    def fill_jets(self, fill, jet, jets):
        if self.jet == "AK4":
            cvl = ak.to_numpy(jet.btagPNetCvL)
            cvb = ak.to_numpy(jet.btagPNetCvB)
            fill("jet_pt", pt=ak.to_numpy(jet.pt))
            fill("jet_eta", eta=ak.to_numpy(jet.eta))
            fill("jet_PNetB", score=ak.to_numpy(jet.btagPNetB))
            fill("jet_PNetCvL", score=cvl)
            fill("jet_PNetCvB", score=cvb)
            fill("jet_CvL_CvB", cvl=cvl, cvb=cvb)
            fill("n_jet", n=ak.to_numpy(ak.num(jets)))
            return
        xbb = ak.to_numpy(jet.particleNet_XbbVsQCD)
        xcc = ak.to_numpy(jet.particleNet_XccVsQCD)
        fill("fj_pt", pt=ak.to_numpy(jet.pt))
        fill("fj_eta", eta=ak.to_numpy(jet.eta))
        fill("fj_msd", mass=ak.to_numpy(jet.msoftdrop))
        fill("fj_mreg", mass=ak.to_numpy(jet.particleNet_massCorr * jet.mass))
        fill("fj_Xbb", score=xbb)
        fill("fj_Xcc", score=xcc)
        fill("fj_Xbb_Xcc", xbb=xbb, xcc=xcc)
        fill(
            "fj_tau21",
            tau21=ak.to_numpy(ak.where(jet.tau1 > 0, jet.tau2 / jet.tau1, -1.0)),
        )
        fill("n_fj", n=ak.to_numpy(ak.num(jets)))

    def mc_sf(self, ev, l0, l1, channel):
        """
        Pileup x lepton ID/iso/reco SFs for the two Z leptons x single-lepton
        trigger SF of the leading lepton.

        Each lepton's ID/iso/reco SF is evaluated separately and the products
        are multiplied here (written for the old eleSFs, which kept only the
        last electron's SF; still correct with the fixed version). The trigger
        SF is evaluated here rather than through muSFs/eleSFs: the Run 3 POG
        files give SFs only (no data/MC efficiencies for muons), and the
        leading lepton (pT > 35) is on the trigger plateau.
        """
        w = Weights(len(ev))
        puwei(ev.Pileup.nTrueInt, self.SF_map, w, False)
        sf = w.weight()
        for lep in (l0, l1):
            wl = Weights(len(ev))
            if channel == "Zee":
                eleSFs(lep, self.SF_map, wl, False, False)
            else:
                muSFs(lep, self.SF_map, wl, False, False)
            sf = sf * wl.weight()
        if channel == "Zee":
            # EGM year/scenario label, e.g. "2022Re-recoBCD", as in the ID SF key
            year = next(iter(self.SF_map["EGM_cfg"])).split(" ")[1]
            trig = self.SF_map["EGM_HLT"]["Electron-HLT-SF"].evaluate(
                year,
                "sf",
                "HLT_SF_Ele30_TightID",
                np.clip(ak.to_numpy(l0.eta + l0.deltaEtaSC), -2.5, 2.5),
                np.clip(ak.to_numpy(l0.pt), 30.0, None),
            )
        else:
            trig = self.SF_map["MUO"][
                "NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight"
            ].evaluate(
                np.clip(ak.to_numpy(l0.eta), -2.4, 2.399999),
                np.clip(ak.to_numpy(l0.pt), 26.0, None),
                "nominal",
            )
        return sf * trig

    def postprocess(self, accumulator):
        return accumulator
