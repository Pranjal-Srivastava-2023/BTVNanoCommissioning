import hist as Hist


def get_histograms(axes, **kwargs):
    """
    Boosted-jet substructure/tagger histograms for the Z(bb) boosted QCD validation
    workflow. Guarded by jet_fields so it degrades gracefully if run on a jet
    collection (e.g. AK4) that doesn't have these branches.
    """
    hists = {}

    jet_fields = kwargs.get("jet_fields", [])

    score_axis = Hist.axis.Regular(50, 0, 1, name="discr", label="discriminant")
    n2b1_axis = Hist.axis.Regular(50, 0, 0.5, name="n2b1", label=r"$N_{2}^{\beta=1}$")

    # fourvec.py's generic "dilep" handling only produces pt/eta/phi (no mass),
    # so define dilep_mass here explicitly, same convention as dy.py/dy_sfl.py.
    hists["dilep_mass"] = Hist.Hist(
        axes["syst"],
        Hist.axis.Regular(60, 60, 120, name="mass", label=r" $m_{\ell\ell}$ [GeV]"),
        Hist.storage.Weight(),
    )

    # jet0_pt/jet0_msoftdrop/njet below deliberately override the generic
    # fourvec.py/common.py versions (hist_collections=["common","fourvec","QCD"]
    # in QCD_validation.py merges later collections over earlier ones by key
    # name, and "QCD" — this file — is listed last). The shared axes in
    # utils/histogramming/axes/common.py are reused by many other workflows,
    # so rather than editing those (and changing binning everywhere), we
    # define workflow-local axes here with ranges that actually match this
    # boosted AK8 selection — e.g. the hard pT>200 selection cut wasted 2/3 of
    # the shared 0-300 "pt" axis. Only affects QCD_sf's own output.
    jet0_pt_axis = Hist.axis.Regular(50, 200, 600, name="pt", label=r" $p_{T}$ [GeV]")
    softdrop_axis = Hist.axis.Regular(
        60, 0, 250, name="mass", label=" softdrop mass [GeV]"
    )
    njet_axis = Hist.axis.Integer(0, 6, name="n", label="N obj")

    hists["jet0_pt"] = Hist.Hist(
        axes["syst"], axes["flav"], jet0_pt_axis, Hist.storage.Weight()
    )
    hists["njet"] = Hist.Hist(axes["syst"], njet_axis, Hist.storage.Weight())

    if "msoftdrop" in jet_fields:
        hists["jet0_msoftdrop"] = Hist.Hist(
            axes["syst"], axes["flav"], softdrop_axis, Hist.storage.Weight()
        )
    if "tau1" in jet_fields and "tau2" in jet_fields:
        hists["jet0_tau21"] = Hist.Hist(
            axes["syst"], axes["flav"], axes["ptratio"], Hist.storage.Weight()
        )
    if "tau2" in jet_fields and "tau3" in jet_fields:
        hists["jet0_tau32"] = Hist.Hist(
            axes["syst"], axes["flav"], axes["ptratio"], Hist.storage.Weight()
        )
    if "n2b1" in jet_fields:
        hists["jet0_n2b1"] = Hist.Hist(
            axes["syst"], axes["flav"], n2b1_axis, Hist.storage.Weight()
        )
    if "deepTagMD_ZbbvsQCD" in jet_fields:
        hists["jet0_deepTagMD_ZbbvsQCD"] = Hist.Hist(
            axes["syst"], axes["flav"], score_axis, Hist.storage.Weight()
        )
    if "particleNetMD_Xbb" in jet_fields:
        hists["jet0_particleNetMD_Xbb"] = Hist.Hist(
            axes["syst"], axes["flav"], score_axis, Hist.storage.Weight()
        )
    if "particleNetMD_QCD" in jet_fields:
        hists["jet0_particleNetMD_QCD"] = Hist.Hist(
            axes["syst"], axes["flav"], score_axis, Hist.storage.Weight()
        )
    # Named without the jet0_ prefix: histo_writter's "btag" branch matches
    # discriminator histograms by their raw jet-field name (see common.py).
    if "btagDDBvLV2" in jet_fields:
        hists["btagDDBvLV2"] = Hist.Hist(
            axes["syst"], axes["flav"], score_axis, Hist.storage.Weight()
        )

    # Comparison histograms matching the old ROOT-based ZbAnalysis_boosted
    # workflow's plots (see WORKFLOW_GUIDE.md), so the two can be compared
    # directly. Filled manually by QCD_validation.py's fill_comparison_hists
    # (not through the generic histo_writter dispatcher), hence "cmp_" names
    # deliberately avoid substrings ("jet", "dilep", "btag", ...) that would
    # otherwise get silently intercepted by histo_writter's pattern matching.
    # Ranges match the old workflow (Plots.cxx); bin counts are coarser, since
    # the old code's very fine binning (e.g. 1000-10000 bins) was for later
    # ROOT-side rebinning, not the as-filled resolution.
    if "particleNetMD_Xbb" in jet_fields and "particleNetMD_QCD" in jet_fields:
        region_axis = Hist.axis.StrCategory(
            ["Z_jet", "Z_bjet"], name="region", label="jet category"
        )
        channel_axis = Hist.axis.StrCategory(
            ["Zee", "Zmm"], name="channel", label="lepton channel"
        )
        # Ranges below were re-tightened from the old workflow's very wide
        # defaults (e.g. pT 0-1000, dR 0-5, mass 0-500) after checking actual
        # filled content on a real 47-file DY2J run: most of those ranges was
        # empty space, e.g. subjet dR tops out around 0.9 (collimated boosted
        # topology) and cmp_pt_lep1/cmp_pt_sub1 rarely exceed ~300 GeV. Kept
        # some headroom above the observed max for other datasets' tails.
        wide_pt_axis = Hist.axis.Regular(
            90, 0, 900, name="pt", label=r"$p_{T}$ [GeV]"
        )  # Z candidate / fatjet / leading-subjet pT (cmp_pt_zcand, _fj, _sub0)
        lep_pt_axis = Hist.axis.Regular(
            70, 0, 700, name="pt", label=r"$p_{T}$ [GeV]"
        )  # leading lepton pT (cmp_pt_lep0)
        sub_pt_axis = Hist.axis.Regular(
            70, 0, 350, name="pt", label=r"$p_{T}$ [GeV]"
        )  # subleading lepton/subjet pT (cmp_pt_lep1, cmp_pt_sub1)
        wide_eta_axis = Hist.axis.Regular(60, -3, 3, name="eta", label=r"$\eta$")
        sub_phi_axis = Hist.axis.Regular(60, -3.2, 3.2, name="phi", label=r"$\phi$")
        sub_mass_axis = Hist.axis.Regular(60, 0, 120, name="mass", label="mass [GeV]")
        zmass_wide_axis = Hist.axis.Regular(
            60, 60, 120, name="mass", label=r"$m_{\ell\ell}$ [GeV]"
        )  # matches dilep_mass's window/binning convention
        dr_axis = Hist.axis.Regular(40, 0, 1.5, name="dr", label=r"$\Delta R$")
        n_axis = Hist.axis.Integer(0, 6, name="n", label="N jets")

        def cmp_hist(var_axis):
            return Hist.Hist(
                axes["syst"], region_axis, channel_axis, var_axis, Hist.storage.Weight()
            )

        hists["cmp_pt_lep0"] = cmp_hist(lep_pt_axis)
        hists["cmp_eta_lep0"] = cmp_hist(wide_eta_axis)
        hists["cmp_pt_lep1"] = cmp_hist(sub_pt_axis)
        hists["cmp_eta_lep1"] = cmp_hist(wide_eta_axis)
        hists["cmp_mass_zcand"] = cmp_hist(zmass_wide_axis)
        hists["cmp_pt_zcand"] = cmp_hist(wide_pt_axis)
        hists["cmp_pt_fj"] = cmp_hist(wide_pt_axis)
        hists["cmp_eta_fj"] = cmp_hist(wide_eta_axis)
        hists["cmp_n_fj"] = cmp_hist(n_axis)
        hists["cmp_pt_sub0"] = cmp_hist(wide_pt_axis)
        hists["cmp_eta_sub0"] = cmp_hist(wide_eta_axis)
        hists["cmp_phi_sub0"] = cmp_hist(sub_phi_axis)
        hists["cmp_mass_sub0"] = cmp_hist(sub_mass_axis)
        hists["cmp_pt_sub1"] = cmp_hist(sub_pt_axis)
        hists["cmp_eta_sub1"] = cmp_hist(wide_eta_axis)
        hists["cmp_phi_sub1"] = cmp_hist(sub_phi_axis)
        hists["cmp_mass_sub1"] = cmp_hist(sub_mass_axis)
        hists["cmp_dr_subjets"] = cmp_hist(dr_axis)

    return hists
