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

    if "msoftdrop" in jet_fields:
        hists["jet0_msoftdrop"] = Hist.Hist(
            axes["syst"], axes["flav"], axes["mass"], Hist.storage.Weight()
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
        wide_pt_axis = Hist.axis.Regular(
            200, 0, 1000, name="pt", label=r"$p_{T}$ [GeV]"
        )
        lep_pt_axis = Hist.axis.Regular(200, 0, 1000, name="pt", label=r"$p_{T}$ [GeV]")
        wide_eta_axis = Hist.axis.Regular(60, -3, 3, name="eta", label=r"$\eta$")
        sub_phi_axis = Hist.axis.Regular(60, -3.2, 3.2, name="phi", label=r"$\phi$")
        sub_mass_axis = Hist.axis.Regular(100, 0, 500, name="mass", label="mass [GeV]")
        zmass_wide_axis = Hist.axis.Regular(
            150, 0, 300, name="mass", label=r"$m_{\ell\ell}$ [GeV]"
        )
        dr_axis = Hist.axis.Regular(50, 0, 5, name="dr", label=r"$\Delta R$")
        n_axis = Hist.axis.Integer(0, 10, name="n", label="N jets")

        def cmp_hist(var_axis):
            return Hist.Hist(
                axes["syst"], region_axis, var_axis, Hist.storage.Weight()
            )

        hists["cmp_pt_lep0"] = cmp_hist(lep_pt_axis)
        hists["cmp_eta_lep0"] = cmp_hist(wide_eta_axis)
        hists["cmp_pt_lep1"] = cmp_hist(lep_pt_axis)
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
        hists["cmp_pt_sub1"] = cmp_hist(wide_pt_axis)
        hists["cmp_eta_sub1"] = cmp_hist(wide_eta_axis)
        hists["cmp_phi_sub1"] = cmp_hist(sub_phi_axis)
        hists["cmp_mass_sub1"] = cmp_hist(sub_mass_axis)
        hists["cmp_dr_subjets"] = cmp_hist(dr_axis)

    return hists
