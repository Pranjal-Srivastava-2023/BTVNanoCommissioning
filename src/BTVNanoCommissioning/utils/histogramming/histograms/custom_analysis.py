import hist as Hist

# Leading AK8 jet variables to histogram. tau21/tau32 are derived ratios
# (tau2/tau1, tau3/tau2), computed in histo_writter -- not raw NanoAOD fields.
JET_VARS = {
    "pt": (1000, 0.0, 1000.0, "$p_{T}$ [GeV]"),
    "eta": (300, -3.0, 3.0, "$\\eta$"),
    "phi": (400, -4.0, 4.0, "$\\phi$"),
    "mass": (500, 0., 500., "Jet mass [GeV]"),
    "mSD": (300, 0.0, 300.0, "Soft-drop mass [GeV]"),
    "tau21": (100, 0.0, 1.0, "$\\tau_{21}$"),
    "tau32": (100, 0.0, 1.0, "$\\tau_{32}$"),
}

# Subjets of the leading jet (subJetIdx1/subJetIdx2), always histogrammed
# regardless of obj_list -- same treatment as leptons/MET/dilepton.
SUBJET_VARS = {
    "pt": (500, 0, 500, "$p_{T}$ [GeV]"),
    "eta": (300, -3, 3, "$\\eta$"),
    "phi": (400, -4, 4, "$\\phi$"),
    "mass": (300, 0, 300, "Mass [GeV]"),
}


LEP_VARS = {
    "mu": {
        "pt": (1000, 0, 1000, "Muon $p_{T}$ [GeV]"),
        "eta": (300, -3, 3, "Muon $\\eta$"),
        "phi": (400, -4, 4, "Muon $\\phi$"),
    },
    "ele": {
        "pt": (1000, 0, 1000, "Electron $p_{T}$ [GeV]"),
        "eta": (300, -3, 3, "Electron $\\eta$"),
        "phi": (400, -4, 4, "Electron $\\phi$"),
    },
}


def get_histograms(axes, **kwargs):
    """
    Histogram collection for the Zee/Zmm AK8 analysis.

    All histograms carry a "channel" axis (zee/zmm) so both channels fill
    into the same histogram objects and can be sliced apart later, rather
    than needing separate zee_* / zmm_* histogram names.

    Jet histograms are built per object name in `obj_list` (e.g. "jet0"),
    covering kinematics plus AK8 substructure (msoftdrop, tau21, tau32).

    Expects:
        axes["syst"]  (from the "common" axes collection)
        kwargs["obj_list"]  e.g. ["jet0"]
    """
    obj_list = kwargs.get("obj_list", [])
    syst_axis = axes["syst"]
    channel_axis = Hist.axis.StrCategory(
        ["zee", "zmm"], name="channel", label="Channel", growth=False
    )

    hists = {}

    # --- Event-level ---
    hists["njet"] = Hist.Hist(
        syst_axis,
        channel_axis,
        Hist.axis.Integer(0, 10, name="njet", label="Jet multiplicity"),
        storage=Hist.storage.Weight(),
    )

    # --- Per-object jet kinematics + substructure, driven by obj_list ---
    for obj in obj_list:
        if not obj.startswith("jet"):
            continue
        for var, (bins, lo, hi, label) in JET_VARS.items():
            hists[f"{obj}_{var}"] = Hist.Hist(
                syst_axis,
                channel_axis,
                Hist.axis.Regular(bins, lo, hi, name=var, label=f"{obj} {label}"),
                storage=Hist.storage.Weight(),
            )

    # --- Subjets of the leading jet ---
    for subjet in ("subjet0", "subjet1"):
        for var, (bins, lo, hi, label) in SUBJET_VARS.items():
            hists[f"{subjet}_{var}"] = Hist.Hist(
                syst_axis,
                channel_axis,
                Hist.axis.Regular(bins, lo, hi, name=var, label=f"{subjet} {label}"),
                storage=Hist.storage.Weight(),
            )
    hists["deltaR_subjets"] = Hist.Hist(
        syst_axis,
        channel_axis,
        Hist.axis.Regular(10000,-0.5,9.5, name="dr", label="$\\Delta R$(subjet0, subjet1)"),
        storage=Hist.storage.Weight(),
    )
            
    # --- Leptons: leading (0) and subleading (1) histogrammed separately ---
    for prefix, varmap in LEP_VARS.items():
        for idx in (0, 1):
            for var, (bins, lo, hi, label) in varmap.items():
                hists[f"{prefix}{idx}_{var}"] = Hist.Hist(
                    syst_axis,
                    channel_axis,
                    Hist.axis.Regular(bins, lo, hi, name=var, label=label),
                    storage=Hist.storage.Weight(),
                )
    hists["deltaR_lep0_Jet"] = Hist.Hist(
        syst_axis,
        channel_axis,
        Hist.axis.Regular(10000,-0.5,9.5, name="dr", label="$\\Delta R$(Leading lepton, Leading Jet)"),
        storage=Hist.storage.Weight(),
    )
    hists["deltaR_lep1_Jet"] = Hist.Hist(
        syst_axis,
        channel_axis,
        Hist.axis.Regular(10000,-0.5,9.5, name="dr", label="$\\Delta R$(Subleading lepton, Leading Jet)"),
        storage=Hist.storage.Weight(),
    )


    # --- MET ---
    hists["MET_pt"] = Hist.Hist(
        syst_axis,
        channel_axis,
        Hist.axis.Regular(100, 0, 100, name="pt", label="MET $p_{T}$ [GeV]"),
        storage=Hist.storage.Weight(),
    )

    # --- Dilepton system (ee for zee events, mumu for zmm events) ---
    hists["dilep_pt"] = Hist.Hist(
        syst_axis,
        channel_axis,
        Hist.axis.Regular(1000, 0, 1000, name="pt", label="Dilepton $p_{T}$ [GeV]"),
        storage=Hist.storage.Weight(),
    )
    hists["dilep_mass"] = Hist.Hist(
        syst_axis,
        channel_axis,
        Hist.axis.Regular(300, 0, 300, name="mass", label="Dilepton mass [GeV]"),
        storage=Hist.storage.Weight(),
    )
    hists["dilep_eta"] = Hist.Hist(
        syst_axis,
        channel_axis,
        Hist.axis.Regular(300, -3.0, 3.0, name="eta", label="Dilepton $\\eta$"),
        storage=Hist.storage.Weight(),
    )
    hists["dilep_phi"] = Hist.Hist(
        syst_axis,
        channel_axis,
        Hist.axis.Regular(400, -4.0, 4.0, name="phi", label="Dilepton $\\phi$"),
        storage=Hist.storage.Weight(),
    )
    hists["deltaR_ZJet"] = Hist.Hist(
        syst_axis,
        channel_axis,
        Hist.axis.Regular(60, 0, 6, name="dr", label="$\\Delta R$(Z candidate, Leading Jet)"),
        storage=Hist.storage.Weight(),
    )
    
    #background study
    jet_flavor_axis = Hist.axis.StrCategory(
        ["unmatched", "bb", "cc", "bc", "b", "c", "light"],
        name="jet_flavor",
        label="Z+HF category",
        growth=False,
    )
 
    hists["flavor_yield"] = Hist.Hist(
        syst_axis,
        channel_axis,
        jet_flavor_axis,
        storage=Hist.storage.Weight(),
    )
    hists["flavor_jet0_pt"] = Hist.Hist(
        syst_axis,
        channel_axis,
        jet_flavor_axis,
        Hist.axis.Regular(1000, 0, 1000, name="pt", label="Leading jet $p_{T}$ [GeV]"),
        storage=Hist.storage.Weight(),
    )
    hists["flavor_jet0_msoftdrop"] = Hist.Hist(
        syst_axis,
        channel_axis,
        jet_flavor_axis,
        Hist.axis.Regular(300, 0, 300, name="msoftdrop", label="Leading jet $m_{SD}$ [GeV]"),
        storage=Hist.storage.Weight(),
    )

    return hists