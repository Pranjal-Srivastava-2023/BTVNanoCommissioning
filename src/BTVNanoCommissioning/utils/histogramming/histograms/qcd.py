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

    return hists
