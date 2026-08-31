import numpy as np
import awkward as ak
import os
from coffea import processor
from BTVNanoCommissioning.helpers.func import update, dump_lumi
from BTVNanoCommissioning.utils.histogramming.histogrammer import (
    histogrammer,
    histo_writter,
)
from BTVNanoCommissioning.utils.array_writer import array_writer
from BTVNanoCommissioning.helpers.update_branch import missing_branch
from BTVNanoCommissioning.utils.correction import (
    load_lumi,
    #load_SF,
    weight_manager,
    #common_shifts,
    reweighting,
)
from BTVNanoCommissioning.utils.selection import *
from coffea.analysis_tools import PackedSelection
import correctionlib


class NanoProcessor(processor.ProcessorABC):
    trigger_config = {
        # 2016 preVFP & postVFP 
            "2016preVFP-UL": {
                "eleTrig": ["Ele27_WPTight_Gsf"],
                "muonTrig": ["IsoMu24", "IsoTkMu24"],
        },
            "2016postVFP-UL": {
                "eleTrig": ["Ele27_WPTight_Gsf"],
                "muonTrig": ["IsoMu24", "IsoTkMu24"],
        },
        # 2017
            "2017-UL": {
                "eleTrig": ["Ele32_WPTight_Gsf_L1DoubleEG"],
                "muonTrig": ["IsoMu27"],
        },
        # 2018
            "2018-UL": {
                "eleTrig": ["Ele32_WPTight_Gsf"],
                "muonTrig": ["IsoMu24"],
            },
        #Run 3 fix 
        # 2018
            "Summer24": {
                "eleTrig": ["Ele32_WPTight_Gsf"],
                "muonTrig": ["IsoMu24"],
            },
        }
    # "Loose" ParticleNetMD Xbb-vs-QCD working point per year, from the old
    # ZbAnalysis_boosted workflow's Configs/inputParameters.txt (jet_PNETL_*).
    # Defines the Z_bjet comparison-histogram region (see fill_comparison_hists).
    pnet_loose_wp = {
        "2016preVFP-UL": 0.9088,
        "2016postVFP-UL": 0.9137,
        "2017-UL": 0.9105,
        "2018-UL": 0.9172,
    }

    # Define histograms
    def __init__(
        self,
        year="2022",
        campaign="Summer22Run3",
        name="",
        isSyst=False,
        isArray=False,
        noHist=False,
        chunksize=75000,
        addsel=False,
    ):
        self._year = year
        self._campaign = campaign
        self.name = name
        self.isSyst = isSyst
        self.isArray = isArray
        self.noHist = noHist
        self.lumiMask = load_lumi(self._campaign)
        self.chunksize = chunksize
        ## Load corrections FIX LATER
        #self.SF_map = load_SF(self._year, self._campaign)

    @property
    def accumulator(self):
        return self._accumulator

    def process(self, events):
        events = missing_branch(events)
        sumws = reweighting(events, self.isSyst)
        #vetoed_events, shifts = common_shifts(self, events)
        # Temporarily disable JME/common shifts
        

        return self.process_shift(events, sumws, None)
        #return processor.accumulate(
            #self.process_shift(update(vetoed_events, collections), sumws, name)
            #for collections, name in shifts
        #)

    def process_shift(self, events, sumws, shift_name):
        isRealData = not hasattr(events, "genWeight")
        dataset = events.metadata["dataset"]
        selection = PackedSelection() #cutflow
        cutflow = processor.defaultdict_accumulator(int)
        cutflow_Zee = processor.defaultdict_accumulator(int)
        cutflow_Zmm = processor.defaultdict_accumulator(int)
        output = {}
        if not self.noHist:
            output = histogrammer(
                events.FatJet.fields,
                obj_list=["jet0", "dilep"],
                hist_collections=["common", "fourvec", "QCD"],
            )

        if shift_name is None:
            output["sumw"] = sumws["sumw"]
            output["cutflow"] = cutflow
            output["cutflow_Zee"] = cutflow_Zee
            output["cutflow_Zmm"] = cutflow_Zmm
            if not isRealData and self.isSyst:
                if "LHEPdfWeight" in events.fields:
                    output["PDF_sumwUp"] = sumws["PDF_sumwUp"]
                    output["PDF_sumwDown"] = sumws["PDF_sumwDown"]
                    output["aS_sumwUp"] = sumws["aS_sumwUp"]
                    output["aS_sumwDown"] = sumws["aS_sumwDown"]
                    output["PDFaS_sumwUp"] = sumws["PDFaS_sumwUp"]
                    output["PDFaS_sumwDown"] = sumws["PDFaS_sumwDown"]
                if "LHEScaleWeight" in events.fields:
                    output["muR_sumwUp"] = sumws["muR_sumwUp"]
                    output["muR_sumwDown"] = sumws["muR_sumwDown"]
                    output["muF_sumwUp"] = sumws["muF_sumwUp"]
                    output["muF_sumwDown"] = sumws["muF_sumwDown"]
                if "PSWeight" in events.fields:
                    if len(events.PSWeight[0]) == 4:
                        output["ISR_sumwUp"] = sumws["ISR_sumwUp"]
                        output["ISR_sumwDown"] = sumws["ISR_sumwDown"]
                        output["FSR_sumwUp"] = sumws["FSR_sumwUp"]
                        output["FSR_sumwDown"] = sumws["FSR_sumwDown"]

        ####################
        #    Selections    #
        ####################
        ## HLT
        """
        triggers = {
            "PFJet40": [45, 80],
            "PFJet60": [80, 110],
            "PFJet80": [110, 180],
            "PFJet140": [180, 250],
            "PFJet200": [250, 310],
            "PFJet260": [310, 380],
            "PFJet320": [380, 460],
            "PFJet400": [460, 520],
            "PFJet450": [520, 580],
            "PFJet500": [580, 1e7],
        }
        """

        cutflow["Total Events"] += len(events)
        
        req_trig = np.zeros(len(events), dtype="bool")
        trigbools = {}
        """
        for trigger, ptrange in triggers.items():
            ptmin = ptrange[0]
            ptmax = ptrange[1]
            # Require *leading jet* to be in the pT range of the trigger
            thistrigreq = (
                (HLT_helper(events, [trigger]))
                & (ak.fill_none(ak.firsts(event_jet.pt) >= ptmin, False))
                & (ak.fill_none(ak.firsts(event_jet.pt) < ptmax, False))
            )
            trigbools[trigger] = thistrigreq
            req_trig = (req_trig) | (thistrigreq)
            """
        req_lumi = np.ones(len(events), dtype="bool")
        if isRealData:
            req_lumi = self.lumiMask(events.run, events.luminosityBlock)
        if shift_name is None:
            output = dump_lumi(events[req_lumi], output)
            
        #pass lumi_mask
        events = events[req_lumi]
        
        
        # -----------------------------------------------------------
        # EVALUATE HLT TRIGGERS
        # -----------------------------------------------------------
        # Evaluate HLT_helper for the current chunk
        trig_decisions = HLT_helper(
            events, 
            self.trigger_config, 
            campaign=self._campaign # Or let it resolve via events.metadata
        )
        # Access the individual boolean arrays
        ele_trig_pass = trig_decisions["eleTrig"]    # ak.Array of booleans
        mu_trig_pass = trig_decisions["muonTrig"]  # ak.Array of booleans
        selection.add("ele_trig", ele_trig_pass)
        selection.add("muon_trig", mu_trig_pass)
        
        
        #Electron selection
        """
        electrons = events.Electron
        cutflow["ele_all"] += ak.sum(ak.num(electrons))

        ip_mask = ele_ip_mask(events, self._campaign)
        ele_ip = electrons[ip_mask]
       
        
        cutflow["ele_ip"] += ak.sum(ak.num(ele_ip))

        ele_kin_mask = lep_kin(ele_ip)
        ele_kin = ele_ip[ele_kin_mask]
        ele_EE_EB_mask = ele_EE_EB_removal(ele_kin)
        ele_EE_EB = ele_kin[ele_EE_EB_mask]
        cutflow["ele_EE_EB_gap"] += ak.sum(ak.num(ele_EE_EB))
        ele_id_mask = ele_ID(ele_EE_EB)
        ele_id = ele_EE_EB[ele_id_mask]
        cutflow["ele_ID"] += ak.sum(ak.num(ele_id))
        """
        
        electrons = events.Electron
        
        # All electrons

        ip_req = ele_ip_mask(events, self._campaign)

        
        # Object cutflow
        
        ele_ip = electrons[ip_req]
        
        ele_kin_mask = lep_kin(ele_ip)
        ele_kin = ele_ip[ele_kin_mask]
        
        ele_EE_EB_mask = ele_EE_EB_removal(ele_kin)
        ele_EE_EB = ele_kin[ele_EE_EB_mask]
        
        ele_id_mask = ele_ID(ele_EE_EB)
        ele_id = ele_EE_EB[ele_id_mask]
        
        cutflow["ele_all"] += ak.sum(ak.num(electrons))
        cutflow["ele_ip"] += ak.sum(ak.num(ele_ip))
        cutflow["ele_kin"] += ak.sum(ak.num(ele_kin))
        cutflow["ele_EE_EB"] += ak.sum(ak.num(ele_EE_EB))
        cutflow["ele_ID"] += ak.sum(ak.num(ele_id))
       
        ele_req = ak.pad_none(ele_id, 2, axis=1) 
        
        #for jet-ele removal 
        eles_jetOverlap_mask = ele_for_jet_removal(electrons)
        eles_jetOverlap = electrons[eles_jetOverlap_mask]
             
        
        
        #Muon selection
        muons = events.Muon
        
        #for jet-mu removal 
        mus_jetOverlap_mask = mu_for_jet_removal(muons)
        mus_jetOverlap = muons[mus_jetOverlap_mask]
        
        mu_kin_req = lep_kin(muons)
        
        
        #cutflow 
        
        cutflow["mu_all"] += ak.sum(ak.num(muons))
        mu_kin = muons[mu_kin_req]
        cutflow["mu_kin"] += ak.sum(ak.num(mu_kin))

        mu_ID_mask = mu_kin.mediumId
        mu_ID = mu_kin[mu_ID_mask]
        cutflow["mu_ID"] += ak.sum(ak.num(mu_ID))
        
        mu_iso_mask = mu_iso(mu_ID)
        mu_iso_cut = mu_ID[mu_iso_mask]
        cutflow["mu_iso"] += ak.sum(ak.num(mu_iso_cut))
        
        mu_req = ak.pad_none(mu_iso_cut, 2, axis=1) 
        
        for key, value in cutflow.items():
            print(f"{key:20s} {value}")
            
            
        #AK8 Jet selection
        jets = events.FatJet
        cutflow["jet_all"] += ak.sum(ak.num(jets))
        
        #Jet-electron overlap removal 
        jet_ele_pairs = ak.cartesian(
            {"jet": jets, "ele": eles_jetOverlap},
            axis=1,
            nested=True
        )

        dr_jet_ele = jet_ele_pairs.jet.delta_r(jet_ele_pairs.ele)

        jet_ele_clean = ak.all(dr_jet_ele > 0.8, axis=2)
        jets_ele_removed = jets[jet_ele_clean]
        cutflow["jet_ele_removed"] += ak.sum(ak.num(jets_ele_removed))
        
        #Jet-muon overlap removal 
        jet_mu_pairs = ak.cartesian(
            {"jet": jets_ele_removed, "mu": mus_jetOverlap},
            axis=1,
            nested=True
        )

        dr_jet_mu = jet_mu_pairs.jet.delta_r(jet_mu_pairs.mu)

        jet_mu_clean = ak.all(dr_jet_mu > 0.8, axis=2)
        jets_mu_removed = jets_ele_removed[jet_mu_clean]
        cutflow["jet_mu_removed"] += ak.sum(ak.num(jets_mu_removed))       
        jet_ID_mask = jets_mu_removed.jetId >= 2
        jets_ID = jets_mu_removed[jet_ID_mask]
        
        
        cutflow["jet_ID"] += ak.sum(ak.num(jets_ID))
        
        subjet_mask = (
            (jets_ID.subJetIdx1 >= 0)& (jets_ID.subJetIdx2 >= 0)
        )
        
        jets_subjet_cut = jets_ID[subjet_mask]
        cutflow["subjet_req"] += ak.sum(ak.num(jets_subjet_cut))

        print("Jet cutflow:")
        for key in ["jet_all", "jet_ele_removed", "jet_mu_removed", "jet_ID", "subjet_req"]:
            print(f"  {key:20s} {cutflow[key]}")

        jet_req = ak.pad_none(jets_subjet_cut, 1, axis=1)

        #######################
        # Selected Zee events #
        #######################
        zee_cut = PackedSelection()
        
        zee_cut.add("trigger", ele_trig_pass)
        
        req_Zee_lepton = ak.fill_none(
        (ak.count(ele_id.pt, axis=1) >= 2)
        & (ele_req[:, 0].pt >= 35),
        False,
        )
        zee_cut.add("electron", req_Zee_lepton)

        Zee_mass = (ele_req[:, 0] + ele_req[:, 1]).mass

        req_Zee_mass = ak.fill_none(
        (Zee_mass >= 71) & (Zee_mass <= 111),
        False,
        )
        zee_cut.add("Zmass", req_Zee_mass)
        
        req_Zee_MET = ak.fill_none(
        events.MET.pt < 50,
        False,
        )
        zee_cut.add("MET", req_Zee_MET)
        
        req_Zee_jet = ak.fill_none(
        (ak.num(jet_req, axis=1) >= 1)
        & (jet_req[:, 0].pt >= 200)
        & (abs(jet_req[:, 0].eta) < 2.5),
        False,
        )
        zee_cut.add("jet", req_Zee_jet)
        
        zee_cuts = [
            "trigger",
            "electron",
            "Zmass",
            "MET",
            "jet",
        ]
        for i, cut in enumerate(zee_cuts):
            passed = zee_cut.all(*zee_cuts[:i + 1])
            cutflow_Zee[cut] += ak.sum(passed)

        print("Zee cutflow:")
        for key, value in cutflow_Zee.items():
            print(f"  {key:10s} {value}")

        zee_event_level = zee_cut.all(*zee_cuts)
        zee_events = events[zee_event_level]
            
            
        #######################
        # Selected Zmm events #
        #######################
        zmm_cut = PackedSelection()
        
        zmm_cut.add("trigger", mu_trig_pass)
        
        req_Zmm_lepton = ak.fill_none(
        (ak.count(mu_iso_cut.pt, axis=1) >= 2)
        & (mu_req[:, 0].pt >= 35),
        False,
        )
        zmm_cut.add("muon", req_Zmm_lepton)

        Zmm_mass = (mu_req[:, 0] + mu_req[:, 1]).mass

        req_Zmm_mass = ak.fill_none(
        (Zmm_mass >= 71) & (Zmm_mass <= 111),
        False,
        )
        zmm_cut.add("Zmass", req_Zmm_mass)
        
        req_Zmm_MET = ak.fill_none(
        events.MET.pt < 50,
        False,
        )
        zmm_cut.add("MET", req_Zmm_MET)
        
        req_Zmm_jet = ak.fill_none(
        (ak.num(jet_req, axis=1) >= 1)
        & (jet_req[:, 0].pt >= 200)
        & (abs(jet_req[:, 0].eta) < 2.5),
        False,
        )
        zmm_cut.add("jet", req_Zmm_jet)
        
        zmm_cuts = [
            "trigger",
            "muon",
            "Zmass",
            "MET",
            "jet",
        ]
        for i, cut in enumerate(zmm_cuts):
            passed = zmm_cut.all(*zmm_cuts[:i + 1])
            cutflow_Zmm[cut] += ak.sum(passed)

        print("Zmm cutflow:")
        for key, value in cutflow_Zmm.items():
            print(f"  {key:10s} {value}")

        zmm_event_level = zmm_cut.all(*zmm_cuts)
        zmm_events = events[zmm_event_level]


        event_level = zee_event_level | zmm_event_level

        if len(events[event_level]) == 0:
            if self.isArray:
                array_writer(
                    self,
                    events[event_level],
                    events,
                    None,
                    ["nominal"],
                    dataset,
                    isRealData,
                    empty=True,
                )
            return {dataset: output}

        ####################
        # Selected objects #
        ####################
        # Zee/Zmm are mutually exclusive per event (event_level = zee | zmm), so pick
        # whichever candidate actually fired for each event.
        Zee_cand = ele_req[:, 0] + ele_req[:, 1]
        Zmm_cand = mu_req[:, 0] + mu_req[:, 1]
        dilep_pt = ak.where(zee_event_level, Zee_cand.pt, Zmm_cand.pt)
        dilep_eta = ak.where(zee_event_level, Zee_cand.eta, Zmm_cand.eta)
        dilep_phi = ak.where(zee_event_level, Zee_cand.phi, Zmm_cand.phi)
        dilep_mass = ak.where(zee_event_level, Zee_cand.mass, Zmm_cand.mass)

        # Keep the structure of events and pruned the object size
        pruned_ev = events[event_level]
        pruned_ev["SelJet"] = jets_subjet_cut[event_level][:, 0]
        pruned_ev["njet"] = ak.num(jets_subjet_cut[event_level], axis=1)
        # tau1/tau2/tau3 ratios aren't precomputed branches, derive them for the QCD hists
        pruned_ev["SelJet", "tau21"] = ak.where(
            pruned_ev.SelJet.tau1 > 0,
            pruned_ev.SelJet.tau2 / pruned_ev.SelJet.tau1,
            -1.0,
        )
        pruned_ev["SelJet", "tau32"] = ak.where(
            pruned_ev.SelJet.tau2 > 0,
            pruned_ev.SelJet.tau3 / pruned_ev.SelJet.tau2,
            -1.0,
        )
        pruned_ev["dilep"] = ak.zip(
            {
                "pt": dilep_pt[event_level],
                "eta": dilep_eta[event_level],
                "phi": dilep_phi[event_level],
                "mass": dilep_mass[event_level],
            }
        )

        # Leading/subleading lepton of whichever Z candidate fired, and the two
        # subjets of the leading AK8 jet -- needed to reproduce the comparison
        # plots from the old ROOT-based ZbAnalysis_boosted workflow (see
        # WORKFLOW_GUIDE.md). FatJet.subjets is coffea's built-in cross-reference
        # via subJetIdx1/subJetIdx2, resolved here since jets_subjet_cut already
        # required both indices to be valid.
        lep0_pt = ak.where(zee_event_level, ele_req[:, 0].pt, mu_req[:, 0].pt)
        lep0_eta = ak.where(zee_event_level, ele_req[:, 0].eta, mu_req[:, 0].eta)
        lep1_pt = ak.where(zee_event_level, ele_req[:, 1].pt, mu_req[:, 1].pt)
        lep1_eta = ak.where(zee_event_level, ele_req[:, 1].eta, mu_req[:, 1].eta)
        pruned_ev["lep0"] = ak.zip(
            {"pt": lep0_pt[event_level], "eta": lep0_eta[event_level]}
        )
        pruned_ev["lep1"] = ak.zip(
            {"pt": lep1_pt[event_level], "eta": lep1_eta[event_level]}
        )
        pruned_ev["SubJet0"] = pruned_ev.SelJet.subjets[:, 0]
        pruned_ev["SubJet1"] = pruned_ev.SelJet.subjets[:, 1]
        # zee/zmm are mutually exclusive within event_level, so this is well-defined
        pruned_ev["channel"] = ak.where(zee_event_level[event_level], "Zee", "Zmm")

        ####################
        #     Output       #
        ####################
        # Configure SFs
        weights = weight_manager(
            pruned_ev,
            None,
            self.isSyst,
            campaign=self._campaign,
        )

        # Configure systematics
        if shift_name is None:
            systematics = ["nominal"] + list(weights.variations)
        else:
            systematics = [shift_name]

        # Configure histograms
        if not self.noHist:
            output = histo_writter(
                pruned_ev, output, weights, systematics, self.isSyst, None
            )
            self.fill_comparison_hists(pruned_ev, jets_subjet_cut[event_level], output, weights)
        # Output arrays
        if self.isArray:
            array_writer(
                self,
                pruned_ev,
                events,
                weights,
                systematics,
                dataset,
                isRealData,
                kinOnly=[],
                doOnly=["SelJet", "njet", "PuppiMET"],
            )

        return {dataset: output}

    def fill_comparison_hists(self, pruned_ev, all_seljets, output, weights):
        """
        Fill the cmp_* histograms added to match the old ROOT-based
        ZbAnalysis_boosted workflow's plots (see WORKFLOW_GUIDE.md), so the two
        can be compared directly. Filled manually rather than through the
        shared histo_writter dispatcher because these carry two extra axes the
        dispatcher has no concept of:
        - "channel": "Zee" or "Zmm", whichever Z candidate fired (mutually
          exclusive per event) -- the old workflow keeps these as entirely
          separate plots per lepton channel.
        - "region": "Z_jet" (all selected events, no b-tag requirement) and
          "Z_bjet" (the same events additionally passing the loose
          ParticleNetMD Xbb-vs-QCD working point on the leading jet -- see
          pnet_loose_wp).

        Unlike the old code, phi_sub0/eta_sub0 (and sub1) are filled with the
        correct quantities -- the old workflow has them swapped due to a bug in
        Plots.cxx (h_phi_sub0 filled with Eta(), h_eta_sub0 filled with Phi()).
        """
        if any(f"cmp_{name}" not in output for name in ["pt_lep0"]):
            return  # guarded off (e.g. missing subjet/tagger branches)

        wp = self.pnet_loose_wp.get(self._campaign, self.pnet_loose_wp["2018-UL"])

        weight = weights.weight()
        syst = np.full(len(weight), "nominal")

        fj = pruned_ev.SelJet
        totXbb = fj.particleNetMD_Xbb + fj.particleNetMD_QCD
        pnet_leading = ak.where(totXbb > 0, fj.particleNetMD_Xbb / totXbb, -1.0)
        is_bjet = ak.to_numpy(pnet_leading >= wp)

        channel = ak.to_numpy(pruned_ev.channel)
        region_jet = np.full(len(weight), "Z_jet")
        region_bjet = np.full(int(is_bjet.sum()), "Z_bjet")

        def fill_both(histname, values):
            output[histname].fill(syst, region_jet, channel, values, weight=weight)
            output[histname].fill(
                syst[is_bjet],
                region_bjet,
                channel[is_bjet],
                values[is_bjet],
                weight=weight[is_bjet],
            )

        fill_both("cmp_pt_lep0", pruned_ev.lep0.pt)
        fill_both("cmp_eta_lep0", pruned_ev.lep0.eta)
        fill_both("cmp_pt_lep1", pruned_ev.lep1.pt)
        fill_both("cmp_eta_lep1", pruned_ev.lep1.eta)
        fill_both("cmp_mass_zcand", pruned_ev.dilep.mass)
        fill_both("cmp_pt_zcand", pruned_ev.dilep.pt)
        fill_both("cmp_pt_fj", fj.pt)
        fill_both("cmp_eta_fj", fj.eta)
        fill_both("cmp_pt_sub0", pruned_ev.SubJet0.pt)
        fill_both("cmp_eta_sub0", pruned_ev.SubJet0.eta)
        fill_both("cmp_phi_sub0", pruned_ev.SubJet0.phi)
        fill_both("cmp_mass_sub0", pruned_ev.SubJet0.mass)
        fill_both("cmp_pt_sub1", pruned_ev.SubJet1.pt)
        fill_both("cmp_eta_sub1", pruned_ev.SubJet1.eta)
        fill_both("cmp_phi_sub1", pruned_ev.SubJet1.phi)
        fill_both("cmp_mass_sub1", pruned_ev.SubJet1.mass)
        fill_both("cmp_dr_subjets", pruned_ev.SubJet0.delta_r(pruned_ev.SubJet1))

        # Njet is filled unconditionally in both regions (matching the old
        # workflow): Z_jet = count of all selected AK8 jets, Z_bjet = count of
        # those additionally passing the loose PNet working point.
        all_totXbb = all_seljets.particleNetMD_Xbb + all_seljets.particleNetMD_QCD
        all_pnet = ak.where(all_totXbb > 0, all_seljets.particleNetMD_Xbb / all_totXbb, -1.0)
        n_bjet = ak.sum(all_pnet >= wp, axis=1)
        output["cmp_n_fj"].fill(
            syst, region_jet, channel, pruned_ev.njet, weight=weight
        )
        output["cmp_n_fj"].fill(
            syst, np.full(len(weight), "Z_bjet"), channel, n_bjet, weight=weight
        )

    def postprocess(self, accumulator):
        return accumulator
