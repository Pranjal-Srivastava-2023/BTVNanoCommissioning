"""
Run 3 boosted Z(->ee/mumu) + heavy-flavour AK8 jet workflow, for measuring the
Z+b / Z+c ratio.

Selection follows the Run 2 QCD_sf workflow (QCD_validation.py) -- two leptons
in the Z mass window, low MET, leading AK8 jet with pT > 200, |eta| < 2.5,
msoftdrop > 40 and two subjets -- with these Run 3 changes:
- tight muon ID (matches the MUO tight ID / tight PF iso SFs), opposite-sign
  lepton pair, PuppiMET
- framework correctionlib SFs (pileup, lepton ID/iso/reco) instead of the old
  framework's histograms; no L1 prefiring weight (none in Run 3)
- ParticleNet XbbVsQCD / XccVsQCD taggers (particleNetMD_* no longer exist)

Histograms are split by the generator flavour of the selected AK8 jet, from its
B/C hadron counts: bb (>= 2 B), b (1 B), cc (0 B, >= 2 C), c (0 B, 1 C), l.

The DY pT(ll)-binned samples (PTLL-X) are inclusive above X, so each one is
restricted to its own LHE pT(ll) slice (STITCH below) and the inclusive sample
covers pT(ll) < 100. sumw is over the full sample, before the slice cut.
"""

import numpy as np
import awkward as ak
import hist
from coffea import processor
from coffea.analysis_tools import PackedSelection, Weights
from BTVNanoCommissioning.helpers.func import dump_lumi
from BTVNanoCommissioning.helpers.update_branch import missing_branch
from BTVNanoCommissioning.utils.correction import (
    load_lumi,
    load_SF,
    reweighting,
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
)

FLAVOURS = ["bb", "b", "cc", "c", "l", "data"]
CHANNELS = ["Zee", "Zmm"]


class NanoProcessor(processor.ProcessorABC):
    trigger_config = {
        "Summer22": {
            "eleTrig": ["Ele30_WPTight_Gsf"],
            "muonTrig": ["IsoMu24"],
        },
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
    ):
        if campaign not in self.trigger_config:
            raise KeyError(
                f"Zb_Zc_ratio: campaign {campaign} not configured "
                f"(have {list(self.trigger_config)})"
            )
        self._year = year
        self._campaign = campaign
        self.name = name
        self.isSyst = isSyst
        self.isArray = isArray
        self.noHist = noHist
        self.chunksize = chunksize
        self.lumiMask = load_lumi(self._campaign)
        self.SF_map = load_SF(self._year, self._campaign)

    def make_hists(self):
        ch = hist.axis.StrCategory(CHANNELS, name="channel")
        fl = hist.axis.StrCategory(FLAVOURS, name="flav")

        def h(*axes):
            return hist.Hist(ch, fl, *axes, storage=hist.storage.Weight())

        Reg = hist.axis.Regular
        return {
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
            "z_mass": h(Reg(40, 71, 111, name="mass", label="$m_{\\ell\\ell}$ [GeV]")),
            "z_pt": h(Reg(50, 0, 1000, name="pt", label="$p_T^{\\ell\\ell}$ [GeV]")),
            "lep0_pt": h(Reg(50, 0, 1000, name="pt", label="Leading lepton $p_T$ [GeV]")),
            "lep1_pt": h(Reg(50, 0, 500, name="pt", label="Subleading lepton $p_T$ [GeV]")),
            "lhe_vpt": h(Reg(75, 0, 1500, name="pt", label="LHE $p_T^{\\ell\\ell}$ [GeV]")),
        }

    @property
    def accumulator(self):
        return self._accumulator

    def process(self, events):
        events = missing_branch(events)
        sumws = reweighting(events, self.isSyst)
        return self.process_shift(events, sumws, None)

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
        # unweighted number of selected events per AK8 jet flavour
        output["nevt_flav"] = {
            c: processor.defaultdict_accumulator(int) for c in CHANNELS
        }

        ## Lumi mask (data) / LHE pT(ll) stitching slice (DY MC)
        req_lumi = np.ones(len(events), dtype="bool")
        if isRealData:
            req_lumi = self.lumiMask(events.run, events.luminosityBlock)
            output = dump_lumi(events[req_lumi], output)
        else:
            for tag, lo, hi in self.STITCH:
                if tag in dataset:
                    vpt = ak.to_numpy(events.LHE.Vpt)
                    req_lumi = (vpt >= lo) & (vpt < hi)
                    break
        events = events[req_lumi]
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

        ## AK8 jets: lepton cleaning (dR > 0.8), tight jet ID, two subjets.
        # FatJet_jetId in NanoAODv12 is only wrong for |eta| > 2.7, outside our
        # |eta| < 2.5 selection, so it is used as is.
        fj = events.FatJet
        fj = fj[ak.all(fj.metric_table(ele_jetveto) > 0.8, axis=2)]
        fj = fj[ak.all(fj.metric_table(mu_jetveto) > 0.8, axis=2)]
        fj = fj[fj.jetId >= 2]
        fj = fj[(fj.subJetIdx1 >= 0) & (fj.subJetIdx2 >= 0)]
        fj_pad = ak.pad_none(fj, 1, axis=1)
        lead = fj_pad[:, 0]
        req_jet = ak.to_numpy(
            ak.fill_none(
                (lead.pt > 200) & (abs(lead.eta) < 2.5) & (lead.msoftdrop > 40),
                False,
            )
        )
        req_met = ak.to_numpy(events.PuppiMET.pt < 50)

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
            cutflow[channel]["all"] += float(np.sum(genw))
            cutflow_raw[channel]["all"] += len(events)
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
                nb = ak.to_numpy(jet.nBHadrons)
                nc = ak.to_numpy(jet.nCHadrons)
                flav = np.select(
                    [nb >= 2, nb == 1, nc >= 2, nc == 1],
                    ["bb", "b", "cc", "c"],
                    default="l",
                )
            for f, n in zip(*np.unique(flav, return_counts=True)):
                output["nevt_flav"][channel][str(f)] += int(n)

            def fill(name, **values):
                output[name].fill(channel=channel, flav=flav, **values, weight=weight)

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
            fill("n_fj", n=ak.to_numpy(ak.num(fj[mask])))
            fill("z_mass", mass=ak.to_numpy(z.mass))
            fill("z_pt", pt=ak.to_numpy(z.pt))
            fill("lep0_pt", pt=ak.to_numpy(l0[mask].pt))
            fill("lep1_pt", pt=ak.to_numpy(l1[mask].pt))
            if not isRealData:
                fill("lhe_vpt", pt=ak.to_numpy(ev.LHE.Vpt))

        return {dataset: output}

    def mc_sf(self, ev, l0, l1, channel):
        """
        Pileup x lepton ID/iso/reco SFs for the two Z leptons.

        The framework's eleSFs resets its running product for every electron,
        so passing both electrons at once would keep only the second one's SF;
        each lepton is therefore evaluated separately and the products are
        multiplied here. No trigger SF yet.
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
        return sf

    def postprocess(self, accumulator):
        return accumulator
