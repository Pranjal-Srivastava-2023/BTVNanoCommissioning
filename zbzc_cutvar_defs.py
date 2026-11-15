"""Definitions shared by plot_zbzc_cutvar.py and make_zbzc_cutvar_pdf.py (Z->mumu cut study, 2026-11-15)."""

# cut variants of this study, by group (the other MU_VARIANTS entries are the 2026-11-08 weight tests)
GROUPS = {
    "mupt": ("Muon pT", ["sub30", "lead30"]),
    "mueta": ("Muon |η|", ["eta21"]),
    "zmass": ("Z mass window", ["mass76", "mass81"]),
    "met": ("MET cut", ["met40", "met60", "noMET"]),
    "jet": ("Jet pT / |η| / ID", ["jpt25", "jpt40", "jeta24", "jidTight"]),
    "tau": ("Tau veto", ["tauVeto"]),
}
DESC = {
    "nominal": "nominal: μ pT > 26, lead > 35, |η| < 2.4, 71 < m < 111, MET < 50, jet pT > 30, |η| < 2.5, TightLepVeto",
    "sub30": "both muons pT > 30 GeV (nominal 26)",
    "lead30": "leading muon pT > 30 GeV (nominal 35)",
    "eta21": "muon |η| < 2.1 (nominal 2.4)",
    "mass76": "76 < m(μμ) < 106 GeV (nominal 71-111)",
    "mass81": "81 < m(μμ) < 101 GeV (nominal 71-111)",
    "met40": "MET < 40 GeV (nominal 50)",
    "met60": "MET < 60 GeV (nominal 50)",
    "noMET": "no MET cut (nominal MET < 50)",
    "jpt25": "jet pT > 25 GeV (nominal 30)",
    "jpt40": "jet pT > 40 GeV (nominal 30)",
    "jeta24": "jet |η| < 2.4 (nominal 2.5)",
    "jidTight": "jet ID Tight (nominal TightLepVeto)",
    "tauVeto": "loose τh veto (nominal: none)",
}
VARS = {
    "muvar_z_pt": ((0, 400), True),
    "muvar_lep0_pt": ((35, 300), True),
    "muvar_lep1_pt": ((26, 200), True),
    "muvar_jet_pt": ((30, 300), True),
    "muvar_lep0_eta": (None, False),
    "muvar_lep1_eta": (None, False),
    "muvar_jet_eta": (None, False),
    "muvar_z_mass": (None, False),
    "muvar_met_pt": (None, False),
    "muvar_n_jet": (None, False),
}
# slope fit range per variant where the cut moves the lower edge
FIT_LO = {("muvar_lep0_pt", "lead30"): 30, ("muvar_lep1_pt", "sub30"): 30,
          ("muvar_jet_pt", "jpt25"): 25, ("muvar_jet_pt", "jpt40"): 40}
