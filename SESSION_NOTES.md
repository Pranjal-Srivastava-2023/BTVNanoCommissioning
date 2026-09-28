# Session notes: QCD_sf boosted Zbb — LPC condor scale-up

## STATUS AS OF 2026-09-28 — 2016preVFP / 2016postVFP / 2017 runs done, merged, compared

All 16 datasets OK in each era, no skipped files. Merged -> `hists_run<ERA>_mSD_SF/merged_run<ERA>.coffea`;
`compare_<ERA>.txt`, `cutflow_<ERA>.txt`, `plots/` made with the same scripts as 2018.

new/old yields (MC total / data):
| era | Z_jet Zee | Z_jet Zmm | Z_bjet Zee | Z_bjet Zmm |
|---|---|---|---|---|
| 2016preVFP | 1.024 / 1.034 | 1.019 / 1.024 | 1.014 / 1.011 | 1.020 / 1.031 |
| 2016postVFP | 1.018 / **1.060** | 1.023 / 1.021 | 1.022 / **1.060** | 0.995 / 1.018 |
| 2017 | 1.014 / 1.010 | 1.013 / 1.014 | 1.007 / 1.007 | 0.999 / 1.007 |
| 2018 (ref) | 1.015 / 1.017 | 1.013 / 1.009 | 0.998 / 1.010 | 1.015 / 1.006 |

**2016postVFP Zee data +6% explained: the old run did not process all of its own input.**
Old `Nevt` (condor_output_mSD/<PD>_DATA_<era>.root) vs our processed events (same file lists):
SingleElectron postVFP2016 277.2M vs 291.2M (old missing 4.8%); SingleElectron preVFP2016 -0.8%;
SingleMuon preVFP2016 -0.3%, postVFP2016 -0.6%, 2017 -0.45%; EGamma 2018 -0.35%;
SingleElectron 2017 and SingleMuon 2018 identical. Correcting for it, postVFP Zee data is ~+0.9%.
2016 ttbar Z_bjet differences (up to +12%) are the known old ttbar input bugs (below).
2016 Z_jet MC residual (~2-2.5%) is a bit larger than 2017/2018 (~1.4%); not investigated.

## TODO (deferred by user 2026-09-27) — per-channel softdrop mass (and tau21/tau32)

**Problem:** our leading-jet softdrop mass plot is Zee + Zmm combined, but the old
framework plots Zee and Zmm separately (`mSD_Z_jet_{Zee,Zmm}_18_amcnlo.png`), so the
side-by-side comparison (`hists_run2018_mSD_SF/old_vs_new_2018_side_by_side.pdf`, page 1)
is not like-for-like. Same for tau21/tau32 (and jet mass).

**Why:** these exist only as `jet0_*` histograms, filled through the framework's
generic `histo_writter` (axes: syst, flav, value only; no region/channel). The
old-framework comparison histograms (`cmp_*`, `histograms/qcd.py`, with region and
channel axes, filled in `QCD_validation.py` `fill_comparison_hists`) never got
msoftdrop/tau21/tau32/mass. Oversight, no physics reason.

**Fix (not done yet):** add `cmp_msd_fj` (and optionally `cmp_tau21_fj`,
`cmp_tau32_fj`, `cmp_mass_fj`) to the `cmp_*` set in `histograms/qcd.py`, filled in
`fill_comparison_hists` per (region, channel) from the region's jet, like `cmp_pt_fj`.
Then rerun all 16 datasets of 2018 (~9 h on condor), re-merge, remake the mSD panels
per channel, and rebuild page 1 (and the tau21/tau32 pages) of the side-by-side PDF.
If 2016/2017 jobs are running at that time, make the change in a separate worktree:
each dataset job ships the current `src/` to condor.

**Related, same code path (also not done):** for 2016/2017 the `jet0_*` weights
(`QCD_validation.py`, `weight_manager` + `lepSF`, ~L594-604) lack the L1 prefiring
weight that the `cmp_*` weights have. Affects only `jet0_*` histograms of the
2016/2017 runs launched 2026-09-27; moving mSD/tau to `cmp_*` also sidesteps this.

## 2026-09-27 afternoon — plots and cutflow for the 2018 (mSD_SF) run

The old `qcd_sf_2018_*.png` in the repo root are from 2026-09-07 (pre-alignment
output) and are superseded. New, per era:
- `python3 plot_stack_sample.py --era <ERA>` and `python3 plot_full_overview.py --era <ERA>`
  read `hists_run<ERA>_mSD_SF/merged_run<ERA>.coffea`, write PNGs to
  `hists_run<ERA>_mSD_SF/plots/`. Merged .coffea, plots/, *.txt and
  `logs_run<ERA>_mSD_SF/summary.log` are committed (.gitignore exceptions);
  per-dataset .coffea files and raw logs stay local.
- `python3 print_cutflow.py --era <ERA>` -> `hists_run<ERA>_mSD_SF/cutflow_<ERA>.txt`
  (object cutflow, Zee/Zmm event cutflows per dataset, scaled final yields per group).
- Shared era config/data handling in `qcd_sf_plot_common.py`. Data per channel now
  from its own PD only (Zee: EGamma/SingleElectron, Zmm: SingleMuon); the old plots
  summed both PDs, double-counting ~2% (EGamma has 644 Zmm Z_jet events, SingleMuon
  246 Zee). `jet0_*` hists have no channel axis, so still sum both PDs ("(*)" in titles).
2018 yields from the cutflow script match `compare_2018.txt` exactly.

## STATUS AS OF 2026-09-27 12:05 CDT — 2016preVFP / 2016postVFP / 2017 runs launched

Commit `1c35472` (local) extends the 2018 validation setup to the other three
Run 2 UL eras, each kept separate (no year merging):
- `utils/zb_old_sf.py`: per-era lepton SF files/histograms from old `Ana.cxx` /
  `Selector.cxx` (files copied to `data/ZbOld/<campaign>/`). Only the muon trigger
  histogram name changes per era (2016: IsoMu24_or_IsoTkMu24, 2017: IsoMu27).
- `QCD_validation.py`: MC weight x `L1PreFiringWeight_Nom` for 2016/2017 (old
  `ZbSelection.cxx`; not in the normalization sum, as old). 2017 lumi mask is the
  Golden JSON (framework default for 2017-UL is the Muon JSON; old uses Golden).
  2016 Legacy JSON verified identical to old.
- `make_qcd_sf_fileset.py --era <era>`: builds `metadata/QCD_sf_run<era>_all.json`
  and `QCD_sf_xsections_<era>.json` straight from old `FileLists_NanoUL/` and
  `Configs/config.ini` (reproduces the 2018 JSONs exactly). 2016 DY xsecs differ
  from 2017/2018 (4620.519*1.0445 etc.); lumis 19648 / 16978 / 41480 /pb.
- `submit_qcd_sf_per_dataset.sh` takes `ERA=`; `launch_era_run.sh <ERA>` starts it
  detached inside the Apptainer container.
- `compare_yields_old_new.py --era {preVFP2016,postVFP2016,17,18}`.
Smoke-tested (iterative, 1 file of DY2J + both data PDs per era): all run, Z_jet
fills, <L1PreFiringWeight_Nom> 0.95-0.97.

**Old-framework input bugs found (affect only ttbar, small):**
1. `FileLists_NanoUL/TT_semi_powheg_MC_postVFP2016.txt` is byte-identical to the
   preVFP (APV) list. We use the real postVFP dataset from DAS instead
   (`metadata/QCD_sf_TTToSemiLeptonic_UL16postVFP_files.txt`, 138 files).
2. `config.ini` [TT] `file_preVFP2016` uses `TT_dilep_powheg_MC_postVFP2016.root`
   (postVFP file for preVFP). Expect ttbar old/new to differ somewhat in 2016.

**Runs** (launched from cmslpc323; 8 workers each, eras in parallel):
outputs `hists_run<ERA>_mSD_SF/hists_QCD_sf_QCD_sf_run<ERA>_all/`, logs
`logs_run<ERA>_mSD_SF/` (+ `summary.log`), driver log `logs_run<ERA>_mSD_SF_driver.log`.
When done, per era:
`python3 merge_qcd_sf_outputs.py --pattern 'hists_run<ERA>_mSD_SF/hists_QCD_sf_QCD_sf_run<ERA>_all/*_*.coffea' --output hists_run<ERA>_mSD_SF/merged_run<ERA>.coffea`
then `python3 compare_yields_old_new.py --new hists_run<ERA>_mSD_SF/merged_run<ERA>.coffea --era <label>`.

## REFERENCE — cuts, weights and SFs: new (QCD_sf) vs old (ZbAnalysis_boosted), 2018-UL

State as of commit `6eaaa30` (2026-09-26). "Old" = ROOT framework at
`~/nobackup/ZbExercize/CMSSW_14_0_6/src/Zb/CMSSW_14_0_6/src/ZbAnalysis_boosted`
(`src/ZbSelection.cxx`, `src/Selector.cxx`, `Ana.cxx`,
`Configs/inputParameters.txt`, `Configs/config.ini`, `Scripts/plot_dataMC_v4.py`).
"New" = `workflows/QCD_validation.py`, `utils/selection.py`, `utils/zb_old_sf.py`.
Every value below was read from those files; no value is assumed.

### Event-level (data)
| | New | Old |
|---|---|---|
| Lumi mask | `Cert_314472-325175_13TeV_Legacy2018_Collisions18_JSON.txt` | same file (content verified identical) |
| Primary datasets used per channel | Zee: EGamma only; Zmm: SingleMuon only (applied in `compare_yields_old_new.py`) | Zee: EGamma; Zmm: SingleMuon (`config.ini` [Electron]/[Muon]) |

### Triggers (2018)
| | New | Old |
|---|---|---|
| Zee | `HLT_Ele32_WPTight_Gsf` | same |
| Zmm | `HLT_IsoMu24` | same |
(2016: Ele27_WPTight_Gsf / IsoMu24 or IsoTkMu24; 2017: Ele32_WPTight_Gsf_L1DoubleEG / IsoMu27 — same in both.)

### Electrons
| Cut | New | Old |
|---|---|---|
| Impact parameter | barrel (\|etaSC\|<1.4442): \|dz\|<0.1, \|dxy\|<0.05; endcap: \|dz\|<0.2, \|dxy\|<0.1 | same |
| Kinematics | pT > 25, \|eta\| < 2.4 | same |
| EB-EE gap veto | 1.442 < \|etaSC\| < 1.566 (etaSC = eta + deltaEtaSC) | same |
| ID | cutBased >= 4 (tight) | same |

### Muons
| Cut | New | Old |
|---|---|---|
| Momentum correction | **none** | **Rochester** (`RoccoR2018UL.txt`; data kScaleDT, MC kSpreadMC/kSmearMC) |
| Kinematics | pT > 25, \|eta\| < 2.4 | same, on Rochester-corrected pT |
| ID | mediumId | same |
| Isolation | pfRelIso04_all < 0.15 | same |

### Z candidate (per channel, evaluated independently in both)
| Cut | New | Old |
|---|---|---|
| Lepton multiplicity | >= 2 selected leptons | same |
| Leading lepton pT | >= 35 (subleading >= 25 from object cut) | same |
| Mass of two leading leptons | 71 <= m_ll <= 111 | same |
| Opposite charge | not required | not required |
| MET | PF `MET_pt` < 50 | same |

### AK8 jets (FatJet)
| Cut | New | Old |
|---|---|---|
| Overlap removal | drop jet if dR <= 0.8 to any: electron (after IP cuts, pT>25, \|eta\|<2.5, tight) or muon (pT>25, \|eta\|<2.5, medium, iso<0.15) | same (old muon pT is Rochester-corrected) |
| Jet ID | `FatJet_jetId >= 2` | **`Jet_jetId[i] >= 2` — AK4 branch indexed with the FatJet index (bug)** |
| Subjets | subJetIdx1 >= 0 and subJetIdx2 >= 0 | same |
| **Z_jet** | leading selected jet: pT >= 200, \|eta\| < 2.5, **msoftdrop > 40** | same |
| **Z_bjet** | first selected jet with PNetMD Xbb/(Xbb+QCD) >= 0.9172 (loose, 2018), and that jet pT >= 200, \|eta\| < 2.5; no msoftdrop cut; not a subset of Z_jet | same |

### MC event weight
| Factor | New | Old |
|---|---|---|
| Generator weight | raw `genWeight` | sign(genWeight) = ±1 (equivalent: \|genWeight\| is constant per sample, verified for TT; e.g. ±72.70 TTTo2L2Nu, ±303.36 TTToSemiLeptonic) |
| Pileup reweighting | not applied | not applied (`puSF = 1`; the pileup file is loaded but unused) |
| L1 prefiring | not applied | applied only for 2016/2017 (`L1PreFiringWeight_Nom`); none for 2018 |
| Electron ID SF | tight, both electrons, (eta, pT): `egammaEffi.txt_Ele_Tight_EGM2D.root` | same file |
| Electron reco SF | both electrons, (eta, pT): `egammaEffi_ptAbove20.txt_EGM2D_UL2018.root` | same file |
| Electron trigger SF | `egammaTrigEffi_wp90noiso_EGM2D_2018.root`, (etaSC, pT) | same |
| Muon ID SF | `NUM_MediumID_DEN_TrackerMuons_abseta_pt_syst`, both muons, (\|eta\|, pT) | same |
| Muon iso SF | `NUM_TightRelIso_DEN_MediumID_abseta_pt_syst`, both muons | same |
| Muon reco SF | `NUM_TrackerMuons_DEN_genTracks`, both muons (histogram only covers 2-40 GeV, so SF=1 above 40) | same |
| Muon trigger SF | `NUM_IsoMu24_DEN_CutBasedIdMedium_and_PFIsoMedium_abseta_pt` | same |
| Trigger SF logic | highest-pT TrigObj with matching id, filterBits & 2, pT > 32 (e) / 24 (mu); SF of the lepton closer to it if dR < 0.2, else 1 | same |
| SF outside histogram range | 1 | same |
| b-tag SF, PU-jet-ID SF, JEC/JER variations | none | none |
| Top pT reweighting | **not in event weight, but included in the TT normalization sum** (see below) | not applied |

SF files are byte-identical copies of the old `CalibData/` files, stored in
`src/BTVNanoCommissioning/data/ZbOld/2018-UL/`.

### Normalization
| | New | Old |
|---|---|---|
| Scale factor | xsec x lumi / sumw, sumw = sum of genWeight over processed events | xsec x lumi / (sum of sign(genWeight)) (`Nevt` bin 4) |
| Lumi | 59832 /pb | same (`config.ini` lumi_18) |
| Cross-sections | `metadata/QCD_sf_xsections_2018.json` | `config.ini` xSec_18 (all 14 values verified identical) |

**Known inconsistency (not yet fixed):** the framework's `reweighting()`
(`utils/correction.py`) multiplies genWeight by the top-pT weight when
building `sumw` for any dataset whose name contains "TT", while our event
weight does not include it. The mean top-pT weight is 0.9895 (TTTo2L2Nu and
TTToSemiLeptonic), so our ttbar yields are about 1.1% too high relative to
the old framework's convention. ttbar is ~1% of MC in Z_jet and ~4-6% in
Z_bjet. Fix options: drop the top-pT factor from `sumw` (matches old), or
also apply it per event (physically standard).

### Differences not replicated on purpose
- Rochester muon corrections (effect seen: -0.2% at the two-muon step).
- Old jet-ID bug (likely cause of the ~+1-1.5% excess at the jet step, same in
  data and MC; not yet proven).
- Subjet plots: old swaps subjet eta/phi (Plots.cxx) and uses the leading
  jet's subjets in Z_bjet; ours fills the correct quantities for the region's
  jet. Affects subjet histograms only, not yields.

## STATUS AS OF 2026-09-26 — yield validation vs. old framework (2018), selection + SFs aligned, full rerun in progress

**Goal**: compare event yields with the old ROOT `ZbAnalysis_boosted` framework,
Run 2 UL, starting with 2018 only. **Reference = old framework's latest run,
`ZbAnalysis_boosted/condor_output_mSD/event_counts_{Z_jet,Z_bjet}_amcnlo.txt`
(2026-06-27)**, chosen by the user — *not* the older `plots/` tables
(2024-09-13), whose source ROOT files no longer exist and whose 2018 Zmm data
looks incomplete (Data/MC 0.67).

Hsin-Wei's 3 newer commits on `hsinwei/coffea_machine` (c7c65ae etc., which
also add msoftdrop>40 / load_SF / Zmm fix, but c7c65ae has a SyntaxError) were
deliberately **not** merged — user said to set them aside for now. Merging will
conflict in `QCD_validation.py` and `histogrammer.py`.

**First comparison (old selection, before changes)**: Z_jet was ~4x too high in
ours (old framework requires leading-jet msoftdrop > 40, we didn't); Z_bjet
already within ~10%.

**Changes made to match the old framework** (read from its `src/ZbSelection.cxx`,
`src/Selector.cxx`, `Ana.cxx`, `Configs/inputParameters.txt`):
1. `Z_jet`: leading AK8 jet `msoftdrop > 40` added (both channels).
2. `Z_bjet`: now = first selected AK8 jet passing loose PNet Xbb WP (not
   necessarily the leading jet), pT>200, |eta|<2.5, **no** msoftdrop cut —
   so Z_bjet is no longer a subset of Z_jet. Cutflow key `bjet` added to
   `cutflow_Zee`/`cutflow_Zmm`.
3. Zee and Zmm evaluated independently (an event can enter both), as old code.
4. Lepton SFs: new `utils/zb_old_sf.py` reproduces old `CalEleSF` (ele ID
   tight x reco, both electrons, in (eta, pt)), `CalMuonSF_id_iso` (muon
   medium ID x tight-iso x reco, both muons, in (|eta|, pt)) and `CalTrigSF`
   (trigger SF of the lepton within dR<0.2 of the leading matching TrigObj).
   Uses the *same* TH2 files, copied to `data/ZbOld/2018-UL/`. Out-of-range
   lookups -> SF=1, as in the old code (note: muon reco histogram stops at
   40 GeV). Old code applies no PU reweighting (puSF=1) — neither do we.
   Checked on DY2J: <SF_Zee>=0.894, <SF_Zmm>=0.971.
5. `selection.py` fixes: `ele_EE_EB_removal` was buggy (`abs()` applied to a
   boolean, so the gap veto only worked for eta>0; now vetoes
   1.442<|etaSC|<1.566); jet-overlap leptons now |eta|<2.5, muons require
   mediumId, electrons taken after the IP cuts — all as in old code.
6. `fill_comparison_hists` rewritten: fills each (region, channel) from its own
   mask/jet/leptons/weight. `cmp_n_fj` now filled before any jet requirement
   (old `FillNjet`). `histo_writter` hists (jet0_*, dilep_*) cover Z_jet only.

**Known remaining differences (not replicated)**: old applies Rochester muon
corrections; old jet ID reads `Jet_jetId[i]` (AK4 branch indexed by FatJet
index — a bug); old normalizes MC with sign(genWeight), we use raw genWeight
(identical when |genWeight| is constant per sample).

**Tools**: `compare_yields_old_new.py --new <merged.coffea>` prints the
old-vs-new table (Zee data from EGamma only, Zmm data from SingleMuon only).
`submit_qcd_sf_per_dataset.sh` now takes `OUTDIR=`/`LOGDIR=` env vars and runs
all 16 datasets by default.

**RESULT (2026-09-27 04:25 CDT) — 2018 validation DONE, agreement ~1-1.5%.**
All 16 datasets OK, no hangs. Merged: `hists_run2018_mSD_SF/merged_run2018.coffea`;
table saved in `hists_run2018_mSD_SF/compare_2018.txt` (both gitignored/local).
new/old: Z_jet Zee MC 1.015 / data 1.017; Z_jet Zmm MC 1.013 / data 1.009;
Z_bjet Zee MC 0.998 / data 1.010; Z_bjet Zmm MC 1.015 / data 1.006.
Data/MC old vs new: Z_jet Zee 1.052/1.054, Z_jet Zmm 1.036/1.032,
Z_bjet Zee 1.167/1.182, Z_bjet Zmm 1.238/1.226.
Per-dataset cutflow checks vs old ROOT files (condor_output_mSD):
- SingleMuon: identical input (985,422,152 events) and identical trigger
  count; Zee chain identical at every step; Zmm 2-muon step -0.2% (Rochester
  not applied); Z_jet +0.86%, Z_bjet +0.6%.
- EGamma: all 738 files; old read 0.35% fewer events (old lost a file or so),
  constant offset through lepton steps; Z_jet +1.3% net.
- DY0J: Zmm Z_jet weighted yield 208.0 vs 208.0 exactly.
- Residual ~+1-1.5% appears only at the jet step, in data and MC alike, both
  channels -> consistent with the old framework's jet-ID bug
  (`r->Jet_jetId[i]`, AK4 branch indexed by FatJet index). Not yet proven —
  could test by emulating the bug on one file.
Data-integrity notes: our DY1J lost 1/78 files to xrootd (73FCAF1C-...,
~49.5k events, MC so normalization unaffected). Old `condor_output_mSD/
DY_2J_amcatnlo_MC_2018.root` is truncated (needs ROOT recovery; cutflows lost;
old processed 1.2% fewer DY2J events than ours).

**Run details** (launched 2026-09-26 19:41 CDT from cmslpc323, inside the
Apptainer container, detached with nohup/setsid):
`OUTDIR=hists_run2018_mSD_SF LOGDIR=logs_run2018_mSD_SF ./submit_qcd_sf_per_dataset.sh`
-> outputs `hists_run2018_mSD_SF/hists_QCD_sf_QCD_sf_run2018_all/*_<dataset>.coffea`,
driver log `logs_run2018_mSD_SF_driver.log`, per-dataset logs + `summary.log` in
`logs_run2018_mSD_SF/`. The previous (pre-change) 2018 outputs in
`hists_QCD_sf_QCD_sf_run2018_all/` are untouched. When done: merge with
`python3 merge_qcd_sf_outputs.py --pattern 'hists_run2018_mSD_SF/hists_QCD_sf_QCD_sf_run2018_all/*_*.coffea' --output hists_run2018_mSD_SF/merged_run2018.coffea`
then run `compare_yields_old_new.py` on it.

**Next**: after 2018 agrees, extend to 2016preVFP/2016postVFP/2017 (file lists
can come straight from the old framework's `FileLists_NanoUL/`; SF files per
era from its `Ana.cxx`; L1 prefiring weight must be added for 2016/2017).

## PLANNED (not started) — extend to 2016preVFP, 2016postVFP, 2017

Next round of scale-up work: add the `2016preVFP-UL`, `2016postVFP-UL`,
and `2017-UL` datasets (same 16-dataset-style fileset per era, MC + data).
**Explicit decision: keep each era's results completely separate — do
NOT merge multiple years into one combined output/plot.** This matches
the old ROOT-based `ZbAnalysis_boosted` analysis's own convention at
`~/nobackup/ZbExercize/.../ZbAnalysis_boosted/plots/`, which keeps one
subdirectory per era (`20preVFP2016/`, `20postVFP2016/`, `2017/`,
`2018/`) — note that old analysis *also* has an `All/` combined folder,
but we are deliberately not doing that (at least not yet/not without
being asked).

Before starting this: per the "is the code ready for more datasets"
discussion, `submit_qcd_sf_per_dataset.sh`, `merge_qcd_sf_outputs.py`,
and both plot scripts all currently hardcode `2018`/`run2018_all`
(json path, `--campaign`/`--year` flags, output file naming, `LUMI_PB`,
the xsections JSON) — these need to be parameterized (or duplicated
per-era) before a second year can be run without overwriting/colliding
with the 2018 outputs. Not done yet — explicitly deferred ("not yet") as
of this note.

## STATUS AS OF 2026-09-07 (evening) — plots now have Data/MC ratio panels; x-ranges cropped; region double-count fixed

**TL;DR since the last status entry below**: three more plotting
refinements landed on top of the completed 16-dataset run and the
log-scale switch, all committed/pushed to `myfork/coffea_machine`
(commits `359a2ed` → `a953577`). Full detail also written up in
`WORKFLOW_GUIDE.md` Section 8 and `concept.md`'s status section — this
entry is deliberately brief, see those for the complete picture.

1. **x-axis ranges cropped to the actually-populated range** per
   histogram, measured directly against the merged `.coffea` output
   (e.g. `m_ll` → 70-110 GeV, jet pT starting at the real 200 GeV cut).
   Several histogram axes were defined wider than the selection
   populates, showing as blank hatched padding on the log-scale plots.
   Commit `359a2ed`.
2. **Fixed a `region`-axis double-counting bug** in
   `plot_full_overview.py`: it was summing `Z_jet + Z_bjet` together for
   most `cmp_*` histograms, but `Z_bjet` is a strict *subset* of `Z_jet`
   (same events plus the tag requirement), not an exclusive category —
   so b-tagged events were counted twice. Now explicitly selects
   `region="Z_jet"`. Verified numerically: old-yield minus new-yield
   exactly matched the independently-computed `Z_bjet`-only contribution.
   Commit `c3cdc22`.
3. **Added a Data/MC ratio panel below every stacked plot**, in both
   `plot_stack_sample.py` and all 15 panels of `plot_full_overview.py`.
   Matches the old ROOT-based `ZbAnalysis_boosted` analysis's own
   convention — confirmed by inspecting its saved `TCanvas` macros
   (`SubmitToCondor/condor_output_mSD/*/*.C`): 70/30 top/bottom split,
   black error-bar ratio markers, horizontal line at 1, "Data/MC" y-axis
   label. Implemented via nested matplotlib `GridSpec`s rather than a
   single `Axes` per panel; ratio uncertainty combines data + MC
   statistical uncertainty in quadrature. The ratio panels make the
   missing-SF normalization gap (see below) directly visible as a
   systematic offset below 1 in almost every panel, plus some
   variable-dependent shape trends (e.g. `tau21`, `eta`) worth digging
   into further if this gets revisited. Commit `a953577`.
4. **Wrote up a full status summary in `concept.md`** for sharing with
   Hsin-Wei directly (commit `8a8e21d`, and this section's changes not
   yet folded in there — do that if resuming this thread).

**Everything is committed and pushed** to `myfork/coffea_machine`;
`.coffea` data files remain local-only (see reminder below, still true).

## STATUS AS OF 2026-09-07 (later same day) — plots now all log-scale; found root cause of data/MC normalization gap

**Log-scale plots**: `plot_full_overview.py` (all 15 panels) and `plot_stack_sample.py`
(all panels, `make_plot(..., logy=True)` now the default) were switched to
log-scale y-axes. This is now the standing default for these two scripts —
keep it log-scale going forward, don't revert to linear. Linear scale was
hiding the sub-dominant backgrounds (ttbar, single top, diboson, ZH)
almost completely under DY+jets; log-scale reveals them clearly across the
full range, including down in the `Z_bjet` (b-tagged) region where ttbar
and diboson become much more comparable to DY, as physically expected.

**Root cause found for the data/MC normalization gap** (MC ~16% high vs.
data, first noticed comparing total scaled yields): in
`src/BTVNanoCommissioning/workflows/QCD_validation.py:83`, the line
```python
#self.SF_map = load_SF(self._year, self._campaign)
```
is commented out. This means `self.SF_map` is never set, and
`weight_manager()` (`utils/correction.py:3924`) receives `SF_map=None`,
which makes it return immediately after adding only `genweight` to the
event weight:
```python
if "genWeight" in pruned_ev.fields:
    weights.add("genweight", pruned_ev.genWeight)
if SF_map is None:
    return weights
```
So **no pileup reweighting, no muon/electron ID-iso-trigger SFs, and no
b-tagging SFs are applied anywhere in this workflow** — every MC event's
weight is just its raw `genWeight`. The framework already has `puwei`,
`muSFs`, `eleSFs`, `btagSFs` fully implemented and ready to use, just not
wired in for `QCD_sf`. This is the concrete, code-level explanation for
the MC/data normalization offset, and likely also contributes to shape-
level mismatches (anything correlated with pileup or lepton kinematics).
~~Also confirmed: no golden-JSON/certified-lumi mask is applied to the data
samples either.~~ **WRONG (corrected 2026-09-26)**: `QCD_validation.py`
does apply `self.lumiMask` (`load_lumi(campaign)`) to data right after the
trigger setup.
**Not yet fixed** — flagged to the user as a workflow-design decision
(whether/how to enable `load_SF` for `QCD_sf`) rather than acted on
unilaterally; likely worth raising with Hsin-Wei before touching it, since
enabling it might require correction-JSON files that need to be confirmed
present for 2018-UL.

**Cutflow reference file**: `cutflow_full_16dataset_run.log` (repo root,
regenerated from the merged `.coffea`, not committed — see `.gitignore`
note below) reproduces the same format as the earlier `output_with_hist.log`
per-chunk printout, but aggregated over the full merged run: general
cutflow (`Total Events` → `ele_*`/`mu_*` preselection → `Jet cutflow:`
block) plus separate `Zee cutflow:` and `Zmm cutflow:` blocks per dataset,
plus `sumw`. Regenerate anytime via `coffea.util.load` on the merged
output — see the merge script's docstring/[[zbb_boosted_qcd_task]] memory
for the exact snippet.

**Reminder — `.coffea` outputs are gitignored, local-only**: the merged
and per-dataset `.coffea` files (`hists_QCD_sf_QCD_sf_run2018_all/`) are
excluded from git by this repo's existing `*.coffea`/`hists_*` rules, so
they are **not** part of any commit — only the code and PNG plots are
version-controlled. They currently exist only on this LPC `nobackup` disk.
See exact paths in the `zbb_boosted_qcd_task` Claude memory entry if
picking this up in a fresh session.

## STATUS AS OF 2026-09-07 03:00 CDT (superseded by above) — full 16-dataset run COMPLETE via per-dataset split

**TL;DR**: Following a suggestion from Hsin-Wei, restructured the full-scale
submission from one combined 16-dataset job into 16 independent per-dataset
condor jobs, run sequentially. Result: **all 16 datasets now complete and
merged**, full-statistics stacked plots regenerated and look physically
sane. This is the successful conclusion of the multi-day scale-up effort
described below.

**Mechanism**: no new metadata files or code changes needed. `runner.py`
already has an `--only <dataset>` flag (existed already, just unused for
this purpose before) that filters the existing combined
`metadata/QCD_sf_run2018_all.json` down to one dataset *before*
validation touches any files — so each `--only` invocation is a fully
independent job (own dask cluster, own condor jobs, own `.coffea` output
`hists_QCD_sf_QCD_sf_run2018_all/hists_QCD_sf_QCD_sf_run2018_all_<dataset>.coffea`),
with zero risk of one dataset's failure affecting another. New scripts
added: `submit_qcd_sf_per_dataset.sh` (sequential wrapper, one dataset at
a time, `--scaleout 8`, logs to `logs_qcd_sf_split/<dataset>.log` +
running `logs_qcd_sf_split/summary.log`) and `merge_qcd_sf_outputs.py`
(dict-unions the per-dataset `.coffea` outputs into the single combined
file `plot_stack_sample.py` already expects — safe because each dataset
is a disjoint top-level key in the workflow's output dict, so merging is
a plain union, not a histogram-level sum).

**Validated the mechanism first** on the smallest untested dataset (`ZZ`,
6 files) before committing to the full run — ran clean, isolated,
correct output.

**Ran the remaining 14 datasets sequentially** (all of `all.json` except
`DYJetsToLL_2J`, already validated 2026-09-01). Result: **13/14 succeeded
cleanly** on the first pass (`WZ`, `ST_s-channel`, `ST_tW_antitop`,
`ZH_HToBB`, `WW`, `ST_tW_top`, `ST_t-channel_antitop`, `ST_t-channel_top`,
`TTTo2L2Nu`, `SingleMuon_Run2018`, `EGamma_Run2018` — plus `ZZ` from the
validation step). **3 hit the same dask/lpcjobqueue deadlock described
below** (`DYJetsToLL_0J`, `DYJetsToLL_1J`, `TTToSemiLeptonic` — each
stuck at 98-99% with driver+worker CPU time frozen, confirmed via the
same `condor_ssh_to_job` CPU-time-before/after-a-wait method used to
diagnose attempt 6). Each was killed cleanly with `SIGINT` (same clean
teardown behavior as before — condor jobs cleared, no `condor_rm`
needed) and **did not affect the other datasets already running/queued**
— exactly the resilience the restructuring was meant to provide. This is
useful new information: the deadlock is real and can recur even at
much smaller per-dataset scale (not just the old full 16-dataset combined
run), so it's some kind of dask/lpcjobqueue-level issue, not something
tied to combined-run scale specifically. Root cause of the deadlock
itself is still not understood (see "Next steps" further below — the
dashboard-enabling suggestion from the original investigation was never
acted on).

**All 3 retried individually afterward** — all 3 succeeded on the second
attempt (`DYJetsToLL_0J` in 10min, `DYJetsToLL_1J` in 14min,
`TTToSemiLeptonic` in 76min — no deadlock recurrence on retry).

**Merge**: `merge_qcd_sf_outputs.py` initially only found 15/16 (missed
`DYJetsToLL_2J` — its default search pattern pointed at a path that
didn't actually exist). Found the correct file among several stale
candidates left over from earlier sessions
(`hists_DY2J_condor_rebin/hists_QCD_sf_QCD_sf_run2018_DY2J/hists_QCD_sf_QCD_sf_run2018_DY2J.coffea`
— verified as the correct one via cutflow total events matching the
documented 44,484,852 exactly, and via histogram binning matching
today's fresh outputs, since it postdates the 2026-09-01 rebin commit
`8b39021` while the other DY2J candidates lying around predate it or are
small sanity-test runs). Fixed the script's default pattern to this path.
Final merge: **16/16 dataset keys**, all with non-trivial, proportionally
sensible statistics (3.2M events for `ZZ` up to 1.38B for `EGamma_Run2018`).

**Plots regenerated** via the existing `plot_stack_sample.py` (no changes
needed — already pointed at the correct combined output path). All three
plot sets look physically sane at full statistics:
`qcd_sf_2018_sample_stack.png` (Z-candidate mass, sharp ~90 GeV peak in
both `Z_jet`/`Z_bjet` regions), `qcd_sf_2018_sample_stack2.png` (leading
AK8 jet pT falling spectrum from the 200 GeV cut, ParticleNetMD Xbb score
piling near 0 as expected for DY+jets background),
`qcd_sf_2018_sample_stack_by_channel.png` (Zee vs Zmm both healthy and
non-empty, confirming the 2026-09-01 Zmm mass-window bug fix holds at
full scale).

**Not yet done**: none of this session's new files
(`submit_qcd_sf_per_dataset.sh`, `merge_qcd_sf_outputs.py`, this note
update) or the new plots have been committed/pushed to `myfork` yet.

**Next steps**: commit/push; decide what to share with Hsin-Wei (the
successful per-dataset restructuring result, and the still-unresolved
dask deadlock as a known recurring issue worth further investigation per
the original attempt-6 root-cause notes below — dashboards were never
enabled to see *why* it deadlocks).

Working with senior postdoc Hsin-Wei Hsia (GitHub: hsinweihsia) on her
boosted Z(bb)+jet analysis, `QCD_sf` workflow, built on BTVNanoCommissioning.

**Env clarification (asked 2026-09-01): are we using micromamba?** No —
despite the install directory being named `micromamba`
(`/uscms_data/d3/psrivast/micromamba/`), it's actually a full
Miniconda-style installer, not the standalone `micromamba` binary. Both
`conda` and `mamba` binaries exist in its `bin/`, but "big mamba" has no
activation mechanism of its own — it delegates to conda's `conda.sh` for
`activate`/`deactivate` (confirmed: the `activate` script here is a
conda-authored file). So `zbb-btv` is correctly called a conda env
(matches `WORKFLOW_GUIDE.md`'s existing wording); `mamba` is only useful
here as a faster drop-in for `mamba install`/`mamba create`, not for
running/activating the env day to day.

## STATUS AS OF 2026-09-01 15:05 CDT, READ THIS FIRST — DY2J validated end-to-end on condor, deadlock resolved (was infra, not code)

**TL;DR**: Attempt 6's deadlock is dead and gone — killed cleanly with no
data loss (coffea doesn't checkpoint, so nothing was recoverable anyway).
Root-caused a second, unrelated infra issue (missing VOMS proxy) that was
masquerading as dataset/storage flakiness. Resubmitted just the DY2J
dataset (47 files, small on purpose) through the full condor path as a
validation step before going back to full scale — it ran clean in under
8 minutes, no hang, no deadlock. Code/histograms confirmed correct at
both local and condor-distributed scale. Full 16-dataset resubmission is
the natural next step but was not started this session — held pending a
go-ahead.

**1. Attempt 6 killed** (EOS maintenance had finished; user gave the
go-ahead). `Ctrl-C` to the driver in tmux `qcd_sf_submission` on
`cmslpc364` tore the cluster down cleanly — `condor_q` confirmed zero
jobs left, no `condor_rm` needed. Consistent with attempt 3's teardown
behavior noted below. Driver had been frozen at 99% for **~17 hours**
total by the time it was killed (confirmed via repeated CPU-time checks
on the driver PID — identical before/after a wait, every time it was
checked).

**2. New, unrelated bug found: missing/expired VOMS proxy masquerading as
storage flakiness.** Before resubmitting, ran a small local (`iterative`,
no condor) sanity check on a `DYJetsToLL_2J`-only metadata subset
(`metadata/QCD_sf_run2018_DY2J.json`, 47 files) to confirm the code path
was solid — this was explicitly requested: verify our side is correct
before spending more time on condor. **Every single file failed** with
`XRootD error: [ERROR] Operation expired`, which looked exactly like the
already-known "scattered replica flakiness" pattern, except **100% of
files failing** (not scattered) was new and suspicious. Diagnosis:
- Direct `xrdfs stat` on the *same* failing files succeeded fine — so the
  files/storage were reachable, ruling out a real dataset-wide outage.
- The actual full-content read (`uproot.open(...)`, same call coffea's
  validator makes under the hood) failed with the identical error.
- Root cause: `voms-proxy-info -all` → `Couldn't find a valid proxy.`
  `xrdfs stat` doesn't require full grid auth; an actual file *open* does.
  No proxy → every open fails uniformly, which is why it looked like 100%
  storage failure across *every* dataset tried (DY2J and DY0J both failed
  identically), not a per-dataset problem.
- **Fix**: `voms-proxy-init -voms cms -rfc --valid 192:00`. Requires the
  private key passphrase, so Claude can't do this unsupervised — ask the
  user, or run it directly in an interactive SSH/tmux session yourself.
- **Node-local gotcha, same shape as the Kerberos one** (see
  `~/.claude/.../memory/lpc_kerberos_ssh_gotcha.md`): the proxy lands in
  `/tmp/x509up_u<uid>` on whichever node `voms-proxy-init` was run on.
  `/tmp` is **not shared across LPC login nodes** — a proxy created on
  `cmslpc364` is invisible on `cmslpc347` and vice versa. Always confirm
  proxy + compute happen on the *same* node (`voms-proxy-info -all` on
  the node you're about to run from) rather than assuming a renewal
  elsewhere carries over.

**3. Second environment bug found: condor submission needs the Apptainer
container, not the plain conda env.** After the proxy fix, the DY2J
condor resubmission was first launched using the `zbb-btv` conda env
(the one used for local `iterative` sanity checks, see
`~/.claude/.../memory/btv_repo_setup.md`) — it crashed immediately on
`from lpcjobqueue import LPCCondorCluster` with
`ModuleNotFoundError: No module named 'htcondor'` (and `htcondor2`).
Checked: `htcondor` bindings exist system-wide only under
`/usr/lib64/python3.9/site-packages/htcondor2` (Python 3.9 build,
ABI-incompatible with the `zbb-btv` env's Python 3.10) and are not
installed anywhere inside the `zbb-btv` conda env itself. **This was true
on both `cmslpc364` and `cmslpc347`** — not node-specific, a genuine env
gap. The correct environment for anything touching condor (`dask/lpc`
executor) is the repo's own Apptainer wrapper:
```
./shell coffeateam/coffea-base-almalinux8:0.7.30-py3.10
```
which drops into a container whose `.bashrc` builds a shallow
`--system-site-packages` venv (`.env/`, already bootstrapped in this repo
— see `.gitignore`'s `.env/` entry) inheriting the container's own
matching `htcondor` bindings. **Rule of thumb going forward: local/
`iterative` testing → `zbb-btv` conda env is fine and lighter-weight;
anything with `--executor dask/lpc` → must run inside `./shell
coffeateam/coffea-base-almalinux8:0.7.30-py3.10`.** Confirmed via
`python -c "import htcondor"` inside the container before relaunching.

**4. DY2J resubmission, done right, succeeded cleanly.** Launched inside
the container, tmux session `qcd_sf_dy2j` on `cmslpc347`,
`--scaleout 8 --skipbadfiles --overwrite`, log `dy2j_submission.log`
(cleaned version without the `\r` progress-bar spam:
`dy2j_submission_clean.log`). Validation → cluster spin-up → processing →
save, **start to finish in under 8 minutes**, no stalls, no manual
intervention. Note: coffea's `run_uproot_job` progress bar goes through
**multiple sequential stages** (preprocessing, then processing), each
resetting its own bar to 0% — don't mistake a stage transition for a
restart/hang if you're watching a live log.

Cutflow (all 47 files, 44,484,852 total events):
```
Zee: trigger 9,155,157 → electron 2,366,467 → Zmass 2,235,117 → MET 1,896,648 → jet 99,115
Zmm: trigger 11,219,168 → muon 4,473,973 → Zmass 4,232,646 → MET 3,598,147 → jet 164,533
```
Both channels scale proportionally from an earlier 8-file local-iterative
test (same shape, ~6.3x the yield) — no sign of the Zmm bug from
`886b01a` recurring. Histogram overview plot
(`dy2j_condor_full_overview.png`, script `plot_hists_dy2j_full.py`):
Z candidate mass still peaks sharply at ~90 GeV, b-tagging discriminants
(ParticleNetMD Xbb, DeepTagMD ZbbvsQCD, DDBvL) all pile near 0 with the
QCD score rising toward 1 — correct, physically sane background behavior
for a DY+jets sample at full statistics.

**Next steps**: 47/2324 files validated. The remaining 15 datasets
(`metadata/QCD_sf_run2018_all.json` minus DY2J) have not been
resubmitted yet — held pending explicit go-ahead, since the whole point
of this session was not repeating the blind full-scale gamble that
deadlocked before. Given DY2J ran clean with the container fix + valid
proxy, the two known infra causes of prior failures are now resolved;
worth trying a bigger chunk (not necessarily all 16 at once) before
going straight back to full scale, per the original "test half the
sample first" plan below.

## STATUS AS OF 2026-09-01 08:15 CDT (superseded by above) — DEADLOCKED RUN LEFT ALIVE, DO NOT KILL WITHOUT RE-READING THIS

**Attempt 6 (`--scaleout 15 --skipbadfiles`, launched 2026-08-31 17:49:52
CDT) is deadlocked at 99% and has been deliberately left running,
untouched, per explicit user instruction** ("I will not kill and restart
now until you find a better solution"). Do not `condor_rm` these jobs or
Ctrl-C the tmux session without asking first — the user wants to
investigate further, possibly with someone attaching a debugger/inspecting
the live process, before it's torn down.

**How to find it right now**:
- Driver PID `851559` in tmux session `qcd_sf_submission` on `cmslpc364`
  (`ssh cmslpc364.fnal.gov`, `tmux attach -t qcd_sf_submission`).
- Condor jobs `85299054`–`85299068` (15 originally; 5 exited within minutes
  of launch — see below; 10 still show `JobStatus=2` running, on schedd
  `lpcschedd6.fnal.gov`, e.g. `condor_q -name lpcschedd6.fnal.gov
  85299054`).
- Log: `full_submission_2018.log` in this repo (shared storage, readable
  from any LPC node without SSH). Attempt 6's own content starts after raw
  line 146 (`tail -n +147 full_submission_2018.log | tr '\r' '\n'`).

**What happened, in order**:
1. Validation completed cleanly (16/16 samples, a handful of individual
   files dropped to known xrootd flakiness — see "xrootd flakiness"
   section below). Cluster came up, all 15 workers requested.
2. 5 of the 15 condor jobs (`85299063`, `85299065`–`68`) exited within ~2
   minutes of starting — their worker logs in
   `~/.lpcjobqueue_worker_logs/worker-<id>.0.out` are tiny (916–917 bytes),
   consistent with an early exit/preemption, not a crash mid-work. The
   other 10 kept running normally.
3. Processing proceeded through two dask stages (first stage hit 100% at
   16min35.8s cleanly), then stalled partway through the second stage.
   Progress climbed normally (1%→99%) up to roughly **2026-09-01 ~00:08–
   01:12 CDT** (6–7 hours after launch), then **froze at 99% and has not
   moved since** — confirmed by the dask progress-bar percentage in the
   log staying at 99% while its own elapsed-time counter kept ticking
   (seen at 13hr+ elapsed by the time this was caught).
4. Cross-check against `~/.lpcjobqueue_worker_logs/worker-<id>.0.out` for
   the 10 still-running jobs: every one of them stopped receiving new
   content at almost exactly the same minute, **~01:12–01:13 CDT** — a
   simultaneous, cluster-wide stop, not independent stragglers.

**Root-cause investigation (careful, evidence-based, done after Kerberos
was restored — see below)**:
- `condor_ssh_to_job -name lpcschedd6.fnal.gov <jobid>` into 4 of the 10
  "running" worker jobs (`85299054`, `85299058`, `85299061`, `85299064`):
  each `dask_worker` process's CPU time was **identical** before and after
  a 5-second wait, on all 4 checked. Zero compute happening, universally.
- Same check on the **driver process** (PID 851559 on `cmslpc364`): CPU
  time also identical before/after a 5s wait. The scheduler side (which
  runs in-process with the driver/client) is equally frozen.
- Node health on `cmslpc364` itself is fine: `uptime` shows 19 days
  continuous (no reboot), load average ~0.5 (not overloaded).
- **Conclusion**: this is a genuine, total, end-to-end deadlock across the
  whole dask distributed cluster (scheduler + all workers simultaneously
  idle), not a slow straggler task and not a resource/node problem. Given
  `--no-dashboard` was passed (from the existing `lpcjobqueue`-based
  command), there's no scheduler diagnostics page or scheduler-side log
  file to inspect further for *why* it deadlocked — this is the biggest
  gap for "digging deeper" next time (see Next steps).
- Coffea's `run_uproot_job` does not checkpoint partial results — the
  final histogram accumulate only happens once every task in the graph
  reports done, so **there is no way to extract partial output from this
  frozen state**. It either finishes on its own (seems very unlikely at
  this point, 7+ hours idle) or must be killed and rerun from scratch.

**Detour that ate a large chunk of the night: expired Kerberos ticket, NOT
a security block.** While the run was stalling, SSH to `cmslpc364`
started failing (`Host key verification failed` / earlier
`kex_exchange_identification: banner line 0: Not allowed at this time`).
Initially misattributed to our own polling frequency tripping a rate
limit — **that theory was wrong**. Actual cause: FNAL's SSH config
(`/etc/ssh/ssh_config.d/fnal_legacy.conf`) sets `GSSAPIKeyExchange yes`
for `*.fnal.gov`, so SSH normally authenticates via Kerberos and never
needs a `known_hosts` entry at all (confirmed: no entry for `cmslpc364`
existed there despite dozens of successful connections). Once the
Kerberos TGT expired (`klist` showed `krbtgt/FNAL.GOV` expiring
`08/31/2026 19:38:00`), GSSAPI auth silently stopped working and SSH fell
back to normal key exchange, which fails outright with `BatchMode=yes`
and no cached host key. **Fix**: user ran `kinit` in a separate
session/terminal — but this Bash tool's shell had `KRB5CCNAME` pointing at
the *old* ticket cache file (`/tmp/krb5cc_10024_XXXXCJzIYo`); the new
ticket landed in a different file (`/tmp/krb5cc_10024_XXXXgq0R7K`, found
via `ls -la /tmp/krb5cc_10024*` sorted by mtime). Had to
`export KRB5CCNAME=FILE:/tmp/krb5cc_10024_XXXXgq0R7K` explicitly before
SSH worked again. **If this happens again**: check `klist` first, and if
the ticket looks stale after a `kinit`, check `ls -la /tmp/krb5cc_10024*`
for a newer cache file rather than assuming the renewal failed.

**xrootd flakiness (separate, already-understood issue, not related to
the deadlock)**: scattered individual files across ≥4 datasets
(`DYJetsToLL_0J`, `DYJetsToLL_1J`, `DYJetsToLL_2J`, `ST_tW_top_5f...`, one
`EGamma_Run2018D` data file) fail with `XRootD error: [ERROR] Operation
expired` — confirmed via standalone retest (persistent, clean 60s
timeout) and DNS/TCP connectivity checks (both instant, ruling out our
network) that this is scattered storage-replica unavailability on the
grid, not our code/proxy/network. `--skipbadfiles` (added starting
attempt 5) correctly drops these individual files without crashing the
run — this part of the pipeline is working as intended and is NOT the
cause of tonight's deadlock.

**Next steps (for whoever picks this up)**:
1. **Do not touch the live deadlocked process** (`851559` / tmux
   `qcd_sf_submission` / condor jobs `85299054`-68) without checking with
   the user first — they explicitly want it left alone for further
   investigation before being killed.
2. **Dig deeper into the deadlock itself** before just retrying blindly a
   7th time at full scale:
   - Consider re-running with the scheduler/worker dashboards enabled
     (drop `--no-dashboard`, or patch `runner.py`'s `LPCCondorCluster`
     call) so there's an actual diagnostics UI to inspect if it happens
     again — right now we have zero visibility into *why* the scheduler
     and every worker froze at the same instant.
   - Check `distributed`/`dask` package versions in the container env
     (`/srv/.env` inside `./shell coffeateam/coffea-base-almalinux8:0.7.30-py3.10`)
     against known upstream issues — didn't get to this yet (avoided
     spinning up a second container instance to not risk touching the
     live one; do this in a **separate, fresh** container invocation, not
     inside the existing tmux session).
   - The exact timing correlation with the SSH/Kerberos/condor_q
     hiccups earlier in the night (all clustered in the very early
     morning hours) is suspicious but unconfirmed — worth checking if
     there's a broader FNAL network blip around 01:00-01:15 CDT on
     2026-09-01 that could have interrupted the scheduler's
     TCP connections to its workers without either side detecting the
     other as dead (a known hard case for TCP/heartbeat-based systems:
     a connection can go half-open and neither side notices without an
     application-level timeout).
3. **Scheduling note**: LPC EOS has a maintenance window **Tuesday 2026-09-02,
   ~8am-noon FNAL time** (per email to the user) — EOS will be fully
   inaccessible; other LPC/FNAL Tier 1 resources (condor, login nodes, NFS
   home/nobackup) expected unaffected. If any `/store/...` NanoAOD reads
   are served off LPC EOS, any data-processing attempt during that window
   will hard-fail on file access. **Do not launch a half-sample test or a
   full resubmission during that window** — do it before Tuesday 8am or
   after noon FNAL time. Investigating the deadlock's root cause (code,
   logs, package versions) doesn't need EOS and is safe to do anytime.
4. **User's suggested next validation step**: before committing to another
   multi-hour full-scale (all 16 samples, ~2324 files) attempt, run on
   **half the sample** (e.g. via a modified metadata JSON with half the
   datasets, or `--limit` set to roughly half the files per dataset) to
   confirm the histograms populate correctly end-to-end in a shorter,
   cheaper run, before re-attempting the full scale.
5. Once a successful run does complete, proceed to the original "Next
   steps once it finishes" further below, and revisit the
   plain-condor-batch-model alternative discussed earlier in the night
   (see "Comparing against the old ROOT-based workflow" section) given
   this is now the **second** distinct failure mode (after the single-bad-
   file crash) that a more resilient, smaller-blast-radius per-chunk
   condor submission model would have avoided or made much cheaper to
   recover from.

## STATUS AS OF 2026-08-31 13:44 CDT (superseded by above), for history

Attempt 3 (`--scaleout 50`, launched 10:36 CDT) validated fine and got its 50
condor jobs submitted around 11:23 CDT, but then sat at **50 idle / 0
running for over 3 hours** with zero movement. Diagnosis: NOT a bug in our
code — `condor_userprio`/`condor_q -allusers` showed the shared LPC pool
severely congested by other users (`acrobert` ~4159 idle jobs, `murtazas`
~2350 idle jobs system-wide; only ~209 jobs running pool-wide against ~3869
idle). Our request was just starved behind that backlog.

**Action taken**: sent Ctrl-C to the driver in the `qcd_sf_submission` tmux
session on `cmslpc364` — `lpcjobqueue`'s cluster teardown cleanly released
all 50 queued condor jobs on its own (no `condor_rm` needed, verified empty
afterward). Relaunched immediately as **attempt 4** in the same tmux
session with **`--scaleout 15`** (smaller ask, hoping to slot in around the
congestion better than 50) and switched to **`python -u`** (unbuffered
stdout) so progress is actually visible live in the tmux pane/log this time
— previously `python | tee` block-buffered everything so nothing appeared
until the buffer flushed or the process exited, making it hard to tell
progress from a hang.

Launched: 2026-08-31 13:43:47 CDT. Same command otherwise:
```
python -u runner.py --workflow QCD_sf --json metadata/QCD_sf_run2018_all.json --campaign 2018-UL --year 2018 --executor dask/lpc --scaleout 15 --overwrite
```

**Update**: `--scaleout 15` worked far better than 50 — all 15 workers went
idle→running within ~1 hour (vs. 3+ hours stuck at 0 running for the
50-worker ask). Confirms the earlier hypothesis: smaller resource asks slot
into a congested shared LPC pool much faster.

**Attempt 4 died at 64% (2h35min in)**: a single transient XRootD read
timeout (`OSError: XRootD error: [ERROR] Operation expired`) on one file —
`.../ST_tW_top_5f_inclusiveDecays_TuneCP5_13TeV-powheg-pythia8/.../
906D8960-EA2D-D345-A24D-D82003BF5601.root` — exhausted coffea's
`automatic_retries` and **killed the entire job**, losing all 2.5 hours of
progress. Root cause: `--skipbadfiles` was not passed (`runner.py` already
supports it, wired through at multiple call sites — just wasn't on the
command line), so one flaky file takes down the whole run instead of being
dropped and logged. This is also the biggest structural reason the old
ROOT/condor workflow (see "Comparing against the old ROOT-based workflow"
below) felt more resilient: its 18-jobs-per-dataset model means one bad
file only kills one small job, not a multi-hour combined run.

**Attempt 5** (current): same command +`--skipbadfiles`, launched 17:36:42
CDT in the same tmux session:
```
python -u runner.py --workflow QCD_sf --json metadata/QCD_sf_run2018_all.json --campaign 2018-UL --year 2018 --executor dask/lpc --scaleout 15 --skipbadfiles --overwrite
```

**Attempt 5 was stopped mid-validation** (user request: too many
`XRootD error: [ERROR] Operation expired` messages appearing during
validation — 9 files across `DYJetsToLL_0J`/`DYJetsToLL_1J` failed in a
short window, looked alarming, asked to stop and root-cause before
continuing). Sent Ctrl-C in tmux; driver took ~25s to actually exit (was
mid-blocking-XRootD-call, didn't respond to SIGINT until that call
returned) but did exit cleanly, no condor jobs left behind.

**Root-cause investigation (careful, before resubmitting anything)**:
1. Retried one of the exact failed files standalone → failed identically,
   clean 60.0s timeout. Confirmed **persistent**, not a blip that had
   already cleared.
2. Tested DNS + raw TCP connect to `cmsxrootd.fnal.gov:1094` from
   `cmslpc364` → both instant (DNS 27ms, TCP connect 1ms). Rules out
   network/firewall/DNS on our end.
3. Checked X509 proxy (`voms-proxy-info -all`) → valid, 167h remaining.
   Rules out proxy expiry as a cause of intermittent auth-related stalls.
4. Tested a file from a third, unrelated dataset (`DYJetsToLL_2J`) →
   opened fine in 1.9s.
5. Cross-referenced: attempt 4's mid-run failure (see above) was a
   *fourth* distinct dataset (`ST_tW_top_5f_inclusiveDecays`) with the
   identical error.

**Conclusion**: not our code, node, network, or proxy — a scattered subset
of specific files (so far confirmed across 3 MC datasets tonight) have
currently-unreachable storage-element replicas; the redirector itself
responds fine and serves other files normally. This is ordinary CMS grid
storage flakiness, exactly the class of failure `--skipbadfiles` (dropped
files during processing) and the existing validation logic (drops a sample
only if *zero* files remain valid) are designed to absorb. Decided (with
user) to resubmit rather than wait it out.

**Attempt 6** (current): identical to attempt 5, relaunched clean:
```
python -u runner.py --workflow QCD_sf --json metadata/QCD_sf_run2018_all.json --campaign 2018-UL --year 2018 --executor dask/lpc --scaleout 15 --skipbadfiles --overwrite
```
Launched 2026-08-31 ~17:53 CDT in the same `qcd_sf_submission` tmux session.

**Next step**: watch attempt 6 to completion. If it finishes, proceed to
the original "Next steps once it finishes" below — but also check the
`.coffea` output/log for how many files got skipped via `--skipbadfiles`
across ALL samples (not just the 4 datasets already known to have hit
flaky replicas tonight) and whether that meaningfully changes statistics
for any of the 16 samples. Once a successful run confirms everything
works end-to-end, commit/push if any code changed (nothing has this round
— only launch flags changed).

## Comparing against the old ROOT-based workflow

User pointed at the pre-existing ROOT/C++ analysis at
`/uscms/home/psrivast/nobackup/ZbExercize/CMSSW_14_0_6/src/Zb/CMSSW_14_0_6/src/ZbAnalysis_boosted`
(`SubmitToCondor/condor_run_*/condor_config.script`) to understand why it
felt faster to get running on LPC condor. Two differences found:

1. Its JDL sets `+LENGTH="SHORT"`, which routes jobs into the LPC pool's
   fast-turnover short-job class. Checked our current dask/lpc jobs'
   classads via `condor_q ... -l` — `LENGTH` is `undefined`;
   `lpcjobqueue`'s `LPCCondorCluster` never sets this classad, so our jobs
   get no such priority lane. (Not naively fixable: `LENGTH=SHORT` caps
   walltime at ~3h on LPC, but our dask workers are persistent for the
   whole multi-hour run — setting it would risk mid-run eviction.)
2. Bigger structural difference: the old workflow submits `Queue 18`
   ephemeral per-chunk jobs that each finish and exit — they can
   opportunistically backfill into any single freed slot on a busy pool.
   Our dask setup needs N workers to all be scheduled and held
   *concurrently* for the entire run duration, which is much harder to
   satisfy on a congested pool and is also why one bad file (see attempt 4
   above) can wipe out hours of collective progress at once.

Not acted on beyond `--skipbadfiles` (attempt 5) and the earlier
`--scaleout` reduction — a real fix for the "matches old workflow's speed"
ask would mean restructuring to short-lived per-chunk condor jobs, which is
a bigger change not yet requested.

## STATUS AS OF 2026-08-31 (superseded by above), for history

The 2026-08-30 21:42 CDT full-scale submission (see "2026-08-30 run: what
happened" below) died at 00:37 CDT after stalling — **not committed/pushed
yet**, but `runner.py` has been patched locally to fix the likely causes
before the next attempt:

1. **`cluster.adapt(minimum=args.scaleout)` had no `maximum`** for the
   `dask/lpc` executor path — despite asking for `--scaleout 50`, the
   scheduler log showed **305 workers** connected. Uncapped autoscale
   against a 19,028-task graph almost certainly overloaded the shared LPC
   condor pool and is the leading suspect for the mass "91 nanny workers
   did not shut down" stall. Fixed: now `cluster.adapt(minimum=args.scaleout,
   maximum=args.scaleout)`.
2. **`--workers`/`--memory`/`--disk` CLI flags were silently ignored for
   the `lpc` executor** — every worker ran with the `lpcjobqueue` package
   default (1 core / 2GB / 200MB) regardless of what was passed on the
   command line (the `condor`/`slurm` branches already wired these through;
   only `lpc` didn't). Last night's `--workers 3` had zero effect — every
   worker was single-threaded, more exposed to a slow/blocking synchronous
   xrootd read stalling its whole event loop (including its heartbeat).
   Fixed: `LPCCondorCluster(...)` now passes `cores=args.workers,
   memory=f"{args.memory}GB", disk=f"{args.disk}GB"`.
3. **No worker-level logs were ever kept** — `lpcjobqueue`'s default
   `log-directory` is `null`, so when workers died/hung there was nothing
   to inspect beyond scheduler-side messages. Fixed: `LPCCondorCluster(...)`
   now passes `log_directory=~/.lpcjobqueue_worker_logs` (must be a subpath
   of `~`, `/uscmst1b_scratch/lpc1/3DayLifetime`, or `/uscms_data` per
   `lpcjobqueue`'s own `schedd_safe_paths` check) so condor stdout/stderr/log
   for every worker job is transferred back on exit or eviction and
   available for post-mortem if this happens again.

**Deliberately NOT done**: did not try to move the driver itself off the
login node into a condor-submitted job. `lpcjobqueue`'s `schedd.py` submits
remotely via the `htcondor.Schedd` binding using the interactive-node condor
config (`/etc/condor/config.d/01_cmslpc_interactive`) — an execute/worker
node's sandbox isn't set up with that config or a forwarded x509 proxy, so a
nested condor-job driver would likely just fail to submit workers at all.
Running the driver interactively in `tmux` on a login node (`cmslpc364`) is
the standard, documented `lpcjobqueue` pattern; the working theory is that
fixing the uncapped autoscale (item 1) removes the runaway resource usage
that most plausibly got the process killed, without needing to relocate it.

**Next step**: re-run the full-scale submission with the patched
`runner.py` (same command as before — see "Reference command" further
down), watch `~/.lpcjobqueue_worker_logs` if problems recur, and reassess if
it stalls again. Not yet committed/pushed to `myfork` — do that once a
successful run confirms the fix.

## 2026-08-30 run: what happened (superseded by fixes above)

A full-scale HTCondor submission over all 16 2018 datasets (2324 files, no
`--limit`) is running unattended in `tmux` on **`cmslpc364.fnal.gov`**.

- **To reattach: `ssh cmslpc364.fnal.gov` specifically** (not the generic
  `cmslpc.fnal.gov`, which can round-robin to a different node and won't see
  this tmux session), then `tmux attach -t qcd_sf_submission`.
- Log (visible from any node, shared `nobackup`):
  `/uscms/home/psrivast/nobackup/BTVNanoCommissioning/full_submission_2018.log`
- Check condor jobs: `condor_q psrivast`
- Submission launched 2026-08-30 21:42:29 CDT (a first attempt at 21:06 crashed
  — see "Bug fixed tonight" below — this is the second, working attempt).
- Expected final output (once done):
  `hists_QCD_sf_QCD_sf_run2018_all/hists_QCD_sf_QCD_sf_run2018_all.coffea`
- **How to tell if it finished**: `grep SUBMISSION_FINISHED full_submission_2018.log`
  — prints `exit_code=0` on success. If the tmux pane/log just stops with no
  such line and no running process, it died unexpectedly — check the tail of
  the log for a Python traceback.
- As of last check: dataset validation passed (all 16/16 samples valid),
  cluster came up, dask progress bar was ticking (~1% at the 10-minute mark
  — this is a large run, expect it to take a while; there was no ETA
  established before this session ended).

### Next steps once it finishes
1. Confirm `exit_code=0` in the log.
2. Load the `.coffea` output, sanity check all 16 sample keys are present
   with real (non-trivial) statistics — `coffea.util.load(...)`.
3. Re-run `plot_stack_sample.py` (currently points at the `--limit`-based
   test output path — update the `REPO`/filename if the full-scale run wrote
   to a different directory than the test runs did) to get full-statistics
   stacked plots.
4. Commit/push the final `.coffea` + regenerated plots to `myfork` if useful,
   and decide whether/what to share with Hsin-Wei.

## Bug fixed tonight: resource leak in `runner.py` file validation

First full-scale attempt (21:06 CDT) crashed after ~33 min with exit_code=1.
Root cause: `validate_dataset_structure()` and `validate()` in `runner.py`
called `uproot.open(filename)` on each of 2324 remote xrootd files without
ever closing the handle, leaking XRootD reader threads. This produced
cascading `can't start new thread` errors (948 of 2324 files failed, and
6 of 16 datasets were dropped entirely), and later an `ImportError: ...
failed to map segment from shared object` when importing `htcondor` to
build the `LPCCondorCluster` — same exhausted process address space, just
hitting the dynamic linker instead of a thread spawn.

Fix: wrapped both `uproot.open()` call sites in `with` blocks so each file
handle is closed immediately after use. Committed and pushed:
`myfork/coffea_machine` commit `113a4fd`, "Fix resource leak in dataset file
validation". Verified: second attempt (21:42 CDT) passed validation with all
16/16 datasets, no thread errors, cluster came up cleanly.

## Repo / remotes quick reference

- Repo: `/uscms/home/psrivast/nobackup/BTVNanoCommissioning`
- `origin` = official `cms-btv-pog/BTVNanoCommissioning`, branch `master` —
  untouched, reference only.
- `hsinwei` = her fork `hsinweihsia/ZbAnalysis_boosted`, branch
  `coffea_machine` — informational only, we don't push here.
- `myfork` = **the user's own fork**, `git@github.com:Pranjal-Srivastava-2023/BTVNanoCommissioning.git`,
  branch `coffea_machine` — this is where all our work gets pushed, and it is
  currently up to date (as of commit `113a4fd`) with everything described
  here and in `WORKFLOW_GUIDE.md`.
- Local branch `coffea_machine` tracks `hsinwei/coffea_machine` for `git
  status` purposes (shows "ahead by N commits") but we push to `myfork`, not
  `hsinwei`.

## Environments (two, for different purposes)

1. **Interactive/local testing**: conda env `zbb-btv` at
   `/uscms_data/d3/psrivast/micromamba` — `source
   /uscms_data/d3/psrivast/micromamba/bin/activate zbb-btv`. Used for the
   earliest histogram-fix work (see "Earlier session" below).
2. **HTCondor submission** (what tonight's work used): Apptainer container
   via `./shell coffeateam/coffea-base-almalinux8:0.7.30-py3.10`
   (bootstrap.sh-generated). Its `.bashrc` auto-creates a venv at `.env/`
   inside the container. **Gotcha**: `pip` is an alias in `.bashrc` that
   doesn't expand in non-interactive/piped scripts — always use the explicit
   path `/srv/.env/bin/python -m pip install -e .` for the editable install,
   never bare `pip`. Full explanation in `WORKFLOW_GUIDE.md` section 4.

See `WORKFLOW_GUIDE.md` (in this repo) for the comprehensive writeup:
background, repo layout, environment setup, all fixes made, how to run at
scale on LPC condor, the dataset/cross-section setup, and the comparison
histograms.

## Data/analysis setup (built up over this multi-day session)

- **Fileset**: `metadata/QCD_sf_run2018_all.json` — 16 datasets (14 MC +
  EGamma_Run2018 + SingleMuon_Run2018), 2324 files, built from Hsin-Wei's
  `FileLists_NanoUL` via `scripts/build_2018_metadata.py`. Dataset keys are
  official CMS dataset names (parsed from each file's own xrootd path) for
  MC, `<PrimaryDataset>_Run2018` for data — required for the framework's
  `scaleSumW` cross-section lookup to work without `KeyError`s.
- **Cross sections**: `metadata/QCD_sf_xsections_2018.json` — a
  workflow-local override table sourced from Hsin-Wei's `config.ini`
  values, used instead of the framework's shared `helpers/xsection.py`
  because several entries there diverged substantially from her validated
  numbers (would make old-vs-new comparison plots inconsistent).
- **Fixed**: the known Zmm mass-window bug (`QCD_validation.py` compared
  against `Zee_mass` for both bounds; now correctly uses `Zmm_mass`).
- **Added**: 18 `cmp_*` comparison histograms in
  `utils/histogramming/histograms/qcd.py` + `QCD_validation.py`'s
  `fill_comparison_hists`, matching variables from Hsin-Wei's old
  ROOT-based `ZbAnalysis_boosted` workflow, with `region`
  (`Z_jet`/`Z_bjet`) and `channel` (`Zee`/`Zmm`) axes so Zee/Zmm stay
  distinguishable like in her old plots (this was explicitly requested
  after an initial version didn't split by channel).
- **Plotting**: `plot_stack_sample.py` — cross-section-scaled,
  physics-process-grouped stacked plots with data overlay. Currently built
  against the small `--limit`-based test run's output; will need path
  updates once full-scale output lands (see "Next steps" above).

## Earlier session (2026-08-25, kept for history)

Initial histogram-fix work happened directly on Hsin-Wei's checkout before
the fork/condor work started: fixed a latent `NameError` (`pruned_ev`
undefined), fixed `SelJet` wrongly reading AK4 `events.Jet.fields` instead
of AK8 `events.FatJet.fields`, fixed a shared-framework bug in
`histogrammer.py` where `histo_writter` unconditionally read
`SelJet.partonFlavour` (AK4-only field, crashes on `FatJet`), and populated
the previously-stub `qcd.py` histogram file. Verified against her reference
`output.log` cutflow. This is all now folded into and superseded by the
work described above, which is committed and pushed to `myfork`.
