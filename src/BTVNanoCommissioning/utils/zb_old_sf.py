"""
Lepton scale factors for the QCD_sf (boosted Z+b) workflow, reproducing the
old ROOT-based ZbAnalysis_boosted framework exactly (src/Selector.cxx:
GetSF_2DHist, CalEleSF, CalMuonSF_id_iso, GetTrigObj, CalTrigSF), using the
same TH2 inputs it reads from CalibData/ (copied into data/ZbOld/<campaign>/).

Used instead of the framework's correctionlib-based load_SF/weight_manager so
that yields can be compared one-to-one against the old framework's tables.

Old-framework conventions reproduced here on purpose:
- A lepton outside a histogram's range gets SF = 1 (no clamping to edge bins).
  Notably the muon reco histogram only extends to 40 GeV, so muons above that
  get no reco SF.
- Electron ID/reco SFs are looked up in (eta, pt); the electron trigger SF in
  (supercluster eta, pt); all muon SFs in (|eta|, pt).
- Trigger SF: find the highest-pT trigger object of the right flavour passing
  the filter bits and pT threshold, and apply the trigger SF of whichever of the
  two leptons lies closer to it, provided dR < 0.2. Otherwise SF = 1.
"""

import os
import awkward as ak
import numpy as np
import uproot

_DATA = os.path.join(os.path.dirname(__file__), "..", "data", "ZbOld")

# (file, histogram name) per SF, per campaign -- see Ana.cxx / Selector.cxx
SF_FILES = {
    "2018-UL": {
        "ele_trig": ("egammaTrigEffi_wp90noiso_EGM2D_2018.root", "EGamma_SF2D"),
        "ele_reco": ("egammaEffi_ptAbove20.txt_EGM2D_UL2018.root", "EGamma_SF2D"),
        "ele_id": ("egammaEffi.txt_Ele_Tight_EGM2D.root", "EGamma_SF2D"),
        "mu_trig": (
            "Efficiencies_muon_generalTracks_Z_Run2018_UL_SingleMuonTriggers.root",
            "NUM_IsoMu24_DEN_CutBasedIdMedium_and_PFIsoMedium_abseta_pt",
        ),
        "mu_id": (
            "Efficiencies_muon_generalTracks_Z_Run2018_UL_ID.root",
            "NUM_MediumID_DEN_TrackerMuons_abseta_pt_syst",
        ),
        "mu_iso": (
            "Efficiencies_muon_generalTracks_Z_Run2018_UL_ISO.root",
            "NUM_TightRelIso_DEN_MediumID_abseta_pt_syst",
        ),
        "mu_reco": (
            "Efficiency_muon_generalTracks_Run2018_UL_trackerMuon.root",
            "NUM_TrackerMuons_DEN_genTracks",
        ),
    },
}

# Trigger-object matching: (filterBits mask, pT threshold) per flavour, from
# ZbSelection.cxx (ele_bits/muon_bits, ptThr_ele/ptThr_muon)
TRIGOBJ = {
    "2016preVFP-UL": {11: (2, 27.0), 13: (2 + 8, 24.0)},
    "2016postVFP-UL": {11: (2, 27.0), 13: (2 + 8, 24.0)},
    "2017-UL": {11: (2, 32.0), 13: (2, 27.0)},
    "2018-UL": {11: (2, 32.0), 13: (2, 24.0)},
}


class SF2D:
    """Plain-numpy TH2 lookup, picklable so it ships to dask workers."""

    def __init__(self, path, name):
        h = uproot.open(path)[name]
        self.xedges = h.axes[0].edges()
        self.yedges = h.axes[1].edges()
        self.values = h.values()

    def __call__(self, x, y):
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        # ROOT FindFixBin: bin i covers [edge_i, edge_i+1)
        ix = np.searchsorted(self.xedges, x, side="right") - 1
        iy = np.searchsorted(self.yedges, y, side="right") - 1
        ok = (
            (ix >= 0)
            & (ix < len(self.xedges) - 1)
            & (iy >= 0)
            & (iy < len(self.yedges) - 1)
        )
        out = np.ones(len(x))
        out[ok] = self.values[ix[ok], iy[ok]]
        return out


def load_zb_old_sf(campaign):
    """Return {name: SF2D} for the campaign, or None if not available."""
    if campaign not in SF_FILES:
        return None
    return {
        k: SF2D(os.path.join(_DATA, campaign, f), h)
        for k, (f, h) in SF_FILES[campaign].items()
    }


def _np(arr, fill=-999.0):
    return ak.to_numpy(ak.fill_none(arr, fill)).astype(float)


def _delta_r(eta1, phi1, eta2, phi2):
    dphi = (phi1 - phi2 + np.pi) % (2 * np.pi) - np.pi
    return np.hypot(eta1 - eta2, dphi)


def leading_trigobj(events, pdgid, campaign):
    """Highest-pT TrigObj with |id|==pdgid, matching filter bits, above threshold.
    Returns (pt, eta, phi) numpy arrays, pt=0 where none found."""
    bits, thr = TRIGOBJ[campaign][pdgid]
    to = events.TrigObj
    to = to[(abs(to.id) == pdgid) & ((to.filterBits & bits) > 0) & (to.pt > thr)]
    best = ak.firsts(to[ak.argmax(to.pt, axis=1, keepdims=True)])
    return _np(best.pt, 0.0), _np(best.eta), _np(best.phi)


def trigger_sf(sf, l0_x, l0, l1_x, l1, trigobj):
    """CalTrigSF: SF of the lepton closer to the trigger object if dR < 0.2.
    l*_x is the x-coordinate used for the lookup (|eta| or SC eta)."""
    to_pt, to_eta, to_phi = trigobj
    dr0 = _delta_r(_np(l0.eta), _np(l0.phi), to_eta, to_phi)
    dr1 = _delta_r(_np(l1.eta), _np(l1.phi), to_eta, to_phi)
    has = to_pt > 0.01
    out = np.ones(len(to_pt))
    m0 = has & (dr0 < dr1) & (dr0 < 0.2)
    m1 = has & (dr1 < dr0) & (dr1 < 0.2)
    sf0 = sf(l0_x, _np(l0.pt))
    sf1 = sf(l1_x, _np(l1.pt))
    out[m0] = sf0[m0]
    out[m1] = sf1[m1]
    return out


def zee_sf(sfs, events, e0, e1, campaign):
    """CalEleSF x CalTrigSF(11) for the two leading selected electrons."""
    w = np.ones(len(events))
    for k in ["ele_id", "ele_reco"]:
        w *= sfs[k](_np(e0.eta), _np(e0.pt)) * sfs[k](_np(e1.eta), _np(e1.pt))
    sc0 = _np(e0.eta + e0.deltaEtaSC)
    sc1 = _np(e1.eta + e1.deltaEtaSC)
    w *= trigger_sf(
        sfs["ele_trig"], sc0, e0, sc1, e1, leading_trigobj(events, 11, campaign)
    )
    return w


def zmm_sf(sfs, events, m0, m1, campaign):
    """CalMuonSF_id_iso x CalTrigSF(13) for the two leading selected muons."""
    w = np.ones(len(events))
    a0 = np.abs(_np(m0.eta))
    a1 = np.abs(_np(m1.eta))
    for k in ["mu_id", "mu_iso", "mu_reco"]:
        w *= sfs[k](a0, _np(m0.pt)) * sfs[k](a1, _np(m1.pt))
    w *= trigger_sf(sfs["mu_trig"], a0, m0, a1, m1, leading_trigobj(events, 13, campaign))
    return w
