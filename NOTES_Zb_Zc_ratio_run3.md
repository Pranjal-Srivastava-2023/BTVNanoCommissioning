# Notes: Run 3 Z(→ℓℓ) + b / Z(→ℓℓ) + c ratio (`Zb_Zc_ratio` workflow)

Run 2 QCD_sf work is in `SESSION_NOTES.md`; this file is only the Run 3 ratio measurement.

## RESUME HERE (2026-10-29, ~03:15 CDT): pending decision on the Z pT weights

State when paused:
- Meeting deck (user's choice of content): hists_zbzc_compare/slides_zbzc_fixes_before_after.pdf, 9 pages
  (make_zbzc_fix_slides_pdf.py <before_dir>; before_dir = `git archive fb54afd hists_zbzc_run3 | tar -x -C <dir>`).
  Pages 2-5 Z mass, all campaigns: before/after = old vs per-electron smearing (52b72bf), from the
  28 Oct smearing test run (hists_zbzc_run3_smearfix). Width data/MC 0.90-0.95 -> 0.97-1.00; peak offset
  unchanged (Zee data +0.03-0.08 GeV, within EGM scale unc.). Pages 6-9 leading-lepton pT STACK plots,
  all campaigns: before = 2nd run fb54afd, after = 3rd run b48a524; exactly two changes between them:
  type-1 MET EmEF < 0.9 for v12 (1c3ce15) AND DY Z pT weights (8311570). The deck does not yet say
  explicitly what before/after is on each page type (user asked; offered to add a line).
- User doubts the Z pT reweighting ("are we even allowed to tinker with MC... clearly it hasn't worked").
  My answer: reweighting is common for MC used as a tool (bkg/eff, with syst), but here Z+jets IS the
  measurement (biases the comparison/ratio; normally handled by unfolding + model-dependence syst), the
  weights were derived inclusively before the jet cut but applied to Z+jet (first Z pT bin still 7-11% high
  in 2023, 22EE got worse), and circular for Zmm. Keep the two BUG fixes (smearing, T1 MET EmEF).
- PROPOSED, NOT DONE, awaiting user OK: (1) zpt_reweight default -> False in workflows/Zb_Zc_ratio.py
  (keep code as optional syst study); (2) one more small run with only the two bug fixes (~2 h, MC on one
  node, data on another via launch_zbzc_run3_node.sh, <= 4 jobs/node) -> clean "after" for all campaigns,
  separating the MET fix from the weights; then redo the stack pages of the deck.
- Also still open: 43-page decks' summary_zbzc_run3.json over-claims ("slope gone", "flat"); 2022 jet/MET
  excess (JER inputs); 23BPix Zee ~3% below Zmm (EGM question, not drafted); full condor run (ask first).

## (2026-10-29, 02:00 CDT): third small run

Where the data/MC slope in Z pT / lepton pT came from (study dbbad0a, diagnostics c8676d5):
1. DY generator Z pT shape, all campaigns, both channels, before any cut.
   Fix: DY Z pT weights from Z->mumu (derive_zbzc_zpt_weights.py ->
   src/BTVNanoCommissioning/data/ZbZc/zpt_weights_run3.json, workflow zpt_reweight=True, 8311570).
2. Electrons' own jets in type-1 MET (correction.py applied the JME EmEF < 0.9 cut only for
   NanoAODv15) -> fake MET, MET < 50 removes high-pT Z->ee data events (23BPix worst).
   Fix: calc_T1_MET applies EmEF < 0.9 also for Summer22/22EE/23/23BPix (1c3ce15, fork only).
3. 2022 only: MC has ~2x the MET > 50 tail and ~5% more >= 1 jet events. Without JER smearing
   (diag nojer) most of the MET tail goes away, not the jets. OPEN (2022 JER inputs, JRV2).

Third small run (all 50 samples, first try, no stalls; MC on cmslpc364, data on cmslpc304 via
launch_zbzc_run3_node.sh): data/MC after the full selection, Z->ee / Z->mumu
| campaign | before (fb54afd) | now |
| Summer22 | 0.948 / 0.967 | 0.973 / 0.987 |
| Summer22EE | 0.969 / 0.985 | 0.995 / 1.006 |
| Summer23 | 0.965 / 0.985 | 0.985 / 0.999 |
| Summer23BPix | 0.941 / 0.988 | 0.978 / 1.012 |
2023: flat in Z pT and lepton pT. 2022: mild rising slope left after the jet cut (~0.95 below
30 GeV, 1.04-1.08 above 60-100 GeV), item 3. 23BPix leading-electron pT 200-300 GeV 0.61 -> 0.91.
Per-range numbers: hists_zbzc_run3/slope_check_run3.txt. Decks rebuilt with
summary_zbzc_run3.json (43 pages; corrections table has the MET cut and the Z pT weight row).

Open: 2022 jets/JER (item 3); 23BPix Z->ee ~3% below Z->mumu, mostly negative eta -> EGM
(2023D ID SFs; question not drafted yet); full condor run (ask user first); muon two-lepton
trigger SF; b/c-tag SFs. Gotchas: run <= 4 local jobs per 11.7 GB node; ssh shells lack
X509_USER_PROXY; scripts building the processor must pass isSyst=False (bool).

## RESUME HERE (2026-10-28, 17:15 CDT): second small Run 3 run done, decks rebuilt

Rerun of all four campaigns (data + MC, 20 files, VV incl. Summer22 WW) after these changes
(commits 52b72bf, 39fd67f, e2d86a4 + this one):
- EGM_shifts: one smearing random number per electron (was per event) -> Z->ee width now matches.
- load_lumi: year from the first two digits of the campaign (22EE/23BPix now read the cvmfs
  golden JSON; 23BPix loses 17 lumisections, -0.2% lumi).
- common_shifts: opt-in JME jet veto recipe (self.jetveto_jme in Zb_Zc_ratio): +3.5% Z->mumu
  events in data and MC alike.
- Zee trigger SF from both electrons (EGM data/MC Ele30 efficiencies); Zmm still leading muon
  (MUO gives no efficiencies). sumw_trigsf keeps the leading-only version.
- 19 new kinematic histograms + lepton eta-phi map; deck pages for them (43 pages per deck).
- Reads: many files switched to root://cmsdcadisk.fnal.gov//dcache/uscmsdisk/store/... in the
  metadata JSONs; Summer22 WW and 10 Summer23 EGamma0_C files are LOCAL copies under
  /uscms_data/d3/psrivast/zbzc_local/ (files.txt there has the /store paths). Every sample read
  all its files this time.

Data/MC after full selection (Zee / Zmm, stat ~0.01): 22 0.948/0.967, 22EE 0.969/0.985,
23 0.965/0.985, 23BPix 0.941/0.988. Zee went down 0.5-1.5% from the two-electron trigger SF.

Open:
1. 23BPix Zee deficit: data/MC by electron eta EE- 0.90, EB- 0.93, EB+ 0.95, EE+ 0.98 (muons flat).
   Before SFs Zee is 0.966. 2023D Tight-ID SFs are > 1 (1.01-1.02 per electron) vs 0.96-0.98 in
   2022. eleSFs == direct correctionlib (phi incl.); EGamma0/1 split is exactly 50%. EGM file year
   key "2023PromptD" in the 23DSep23 folder -> ask EGM.
2. Muon trigger SF from both muons needs MC efficiencies (derive from our DY MC?).
3. N PV shapes differ by channel: 20 data files = few runs; not representative (full run).
4. N jets >= 3: data 15-25% above MC (DY 2-jet FxFx), 0-jet bin data/MC ~1.08.
5. Note for Hsin-Wei (muSFs trigger clip line outside else, c7c65ae) drafted, not sent.

## 2026-10-28: Z->ee peak, electron smearing fix

Z->ee MC peak was 5-11% wider than data, with data looking slightly to the right. Cause:
`EGM_shifts` (utils/correction.py) drew `rng.normal(size=len(ele.pt))`, i.e. one random number
per EVENT, so both electrons of a pair were smeared together (m(ee) over-smeared). Fixed in our
fork only: one number per electron, seeded from the chunk's first event. Upstream master 38c34a8
has the same bug (not reported).

Test: `run_zbzc_run3_smearfix.sh <c>` reran DY + ttbar (20 files) into `hists_zbzc_run3_smearfix/`;
`python compare_zee_smearfix.py` -> `<c>/z_mass_smearfix.png`, `zee_smearfix_summary.txt`.
Zee sigma data/MC old -> new: 22 0.951 -> 0.986, 22EE 0.936 -> 1.003, 23 0.944 -> 1.004,
23BPix 0.900 -> 0.971. Peak offset data - MC unchanged: +0.05/+0.07/+0.03/+0.08 GeV (<= 0.09%),
inside the EGM scale uncertainty (0.05-0.15% barrel per electron); data scale correction itself
is applied (+0.95% per electron on a 2023D file). Zmm unchanged (control). Zee yields unchanged,
so 23BPix Zee 0.95 vs Zmm 0.99 is NOT explained by the smearing.

## RESUME HERE (2026-10-26, 17:30 CDT): small Run 3 data/MC run finished, decks done

All 50 samples done, post-processing done, everything committed and pushed (3d6121d).
Decks: `hists_zbzc_run3/<campaign>/slides_zbzc_run3_<campaign>.pdf` (23 pages each), rebuilt with
`python make_zbzc_run3_slides_pdf.py <campaign> --summary summary_zbzc_run3.json`. New pages: data
DAS names + lumi, golden JSON source/check, MC DAS processing strings, corrections/SFs table (POG files
and keys), POG recommendations vs us (2 pages), Hsin-Wei's merge.

Data/MC after full selection (Zee / Zmm): Summer22 0.96/0.96, 22EE 0.98/0.99, 23 0.97/0.99,
23BPix 0.95/0.99 (stat ~0.01). Four samples lost one file to an XRootD timeout (22EE DY MLL-50,
23 DY PTLL-100/600, 23 EGamma0 C); lumi and sumw only count what was read, so it stays consistent.

Open items found (not fixed):
1. `load_lumi` (utils/correction.py) builds `Collisions{campaign[-2:]}` -> "CollisionsEE"/"Collisionsix"
   for Summer22EE/Summer23BPix, so they use the repo golden JSON copies = pre-2026-tracker-review
   versions. 15/6634 Summer23BPix LS no longer golden, 0 in 22EE. Fix: use campaign[6:8].
2. Z->ee peak 1.5-4% wider (RMS) in MC than data in all campaigns (largest 23BPix); muons fine.
   23BPix Zee data/MC 0.95 vs Zmm 0.99 -> look at electron SFs/smearing there.
3. Still pending from before: JME-style jet veto, two-electron (trigger-matched) trigger SF,
   muSFs trigger clip bug in Hsin-Wei's code (tell her), WW missing in Summer22.
4. 2026-10-26 evening: n_jet (n_fj for AK8) is now filled for Z events BEFORE the jet cut
   (fill_njet; 0-jet MC = flav l / pflav none), all other histos still after the full selection.
   Current hists_zbzc_run3 outputs predate this (0 bin empty, the deck says so); next run fills it.
   Tested on 1 Muon0_Run2023D + 1 DY PTLL-100 file: n_jet total = cutflow MET step, n>=1 = jet_pt.

## (earlier) RESUME HERE (2026-10-26, 15:50 CDT): first Run 3 data/MC run in progress

**Goal (group go-ahead after the meeting):** small interactive run, MC and data together, for
Run3Summer22 (2022 C–D), Run3Summer22EE (2022 E–G), Run3Summer23 (2023 C) and Run3Summer23BPix
(2023 D): coffea files, cutflow, the usual plots and a deck. 20 files per MC sample (DY in pT(ℓℓ)
bins plus inclusive, TTto2L2Nu, WW, WZ, ZZ) and 20 data files per channel per campaign.

**Done today (commits 58cdde0 … this one):**
- Merged Hsin-Wei's latest `coffea_machine` (21599c0, Run 2 UL electron SFs + eleSFs reset fix)
  as 58cdde0; kept our QCD_validation.py / selection.py / histogrammer.py (validated Run 2 code).
  Her `muSFs` refactor breaks the muon-trigger branch (26 GeV clip overwritten, `pt_min` unset);
  not used by us, to be reported to her.
- `Zb_Zc_ratio`: all four campaigns, data + MC, framework `common_shifts` (JEC/JER + type-1
  PuppiMET, lepton scale/smearing, jet veto map), leading-lepton trigger SF (IsoMu24 /
  HLT_SF_Ele30_TightID), cutflow all → lumi_slice → jetveto → trigger …; `lhe_vpt` only when LHE exists.
- Scripts: `make_zbzc_run3_fileset.py`, `run_zbzc_run3.sh <c> mc|data`, `run_zbzc_run3_vv.sh`,
  `stop_mc_at_vv.sh`, `rerun_zbzc_run3.sh`, `stall_watchdog_zbzc_run3.sh`, `zbzc_lumi.py`,
  `plot_zbzc_run3.py <c>|all`, `make_zbzc_run3_slides_pdf.py`, `postprocess_zbzc_run3.sh`.
- Normalization: brilcalc on the processed golden-JSON lumisections, per channel (Muon vs EGamma
  PDs see different lumisections). 2023 uses only Muon0/EGamma0: the two halves split every
  lumisection's events ~50/50, so their lumi is ×0.5. Each lumisection sits in one file (DAS check).
- Preliminary Summer22 (all data, all DY; tt̄/VV missing): data/MC 0.968 ± 0.013 (Z→ee, 0.39 fb⁻¹),
  0.970 ± 0.009 (Z→μμ, 0.74 fb⁻¹); Z peak, jet pT/η, PNet B shapes agree. Plots in
  `hists_zbzc_run3/Summer22/plots/` (to be regenerated by the post-processing).

**Running on cmslpc333 (detached, survive logout):** 45/50 samples done at 15:45. Left: Summer22
WW; Summer22EE DY PTLL-400 (rerun), PTLL-600, TTto2L2Nu, WZ, ZZ. Summer23 and Summer23BPix are
complete. `postprocess_zbzc_run3.sh` waits for the 12 driver logs to say ALL DONE and every
`rerun_*.log` to say RERUN DONE, then runs `zbzc_lumi.py`, `plot_zbzc_run3.py` for each campaign
and a draft deck per campaign (summary page empty). Log: `logs_zbzc_run3/postprocess.log`.
`stall_watchdog_zbzc_run3.sh` kills runners with < 5 s CPU in 10 min (drivers retry).

**On resume:**
1. `cat logs_zbzc_run3/postprocess.log logs_zbzc_run3/stall_watchdog.log`; list failed tries with
   `grep -H exit logs_zbzc_run3/*/driver_*.log logs_zbzc_run3/*/rerun_*.log | grep -v 'exit 0'`.
   A sample whose 3 tries all failed: `./rerun_zbzc_run3.sh <campaign> <dataset>`, then rerun
   `zbzc_lumi.py` / plots / deck by hand.
2. Decided (user, 2026-10-26): keep the campaigns separate, no combined 2022+2023 output.
   Post-processing makes plots, yields and a draft deck per campaign
   (`hists_zbzc_run3/<campaign>/slides_zbzc_run3_<campaign>.pdf`).
3. Look at the plots/yields, write the summary JSON (plain sentences + conclusion box), rerun
   `python make_zbzc_run3_slides_pdf.py all --summary <json>`, commit outputs and push.

**Gotchas from today:**
- The cmsxrootd.fnal.gov redirector sometimes sends reads to far sites and they hang (retries can
  stall again). Files on T1_US_FNAL_Disk read fast via
  `root://cmsdcadisk.fnal.gov//dcache/uscmsdisk/store/...`; the Summer22EE DY PTLL-400/600 and
  TTto2L2Nu entries in `metadata/Zb_Zc_ratio_run3_Summer22EE.json` now use that path (same files).
  The VV samples are not on FNAL disk.
- `timeout` runs its child in a new process group: killing the driver's group leaves the runner.
- brilcalc works on LPC only through the container: `apptainer -s exec --env
  PYTHONPATH=/home/bril/.local/lib/python3.10/site-packages
  /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/cms-cloud/brilws-docker:latest brilcalc ...`.
- POG pages (SSO) saved as PDFs in `~/nobackup/pog_docs/` (outside git, never push). Findings: our
  JEC tags, muon Tight ID + PFIsoTight, hadronFlavour and PNet branches match the recommendations.
  PNet c-tagging has fixed-WP SFs only (no shape SFs) for 2022/2023, which matters for a CvL–CvB
  template fit. Offline estimates (one chunk): a JME-style jet veto keeps ~4–5% more Z→μμ events
  than the framework's any-jet veto (data/MC shift ≤ 0.3%); the two-electron trigger SF raises the
  Z→ee MC by 1.1–1.9% vs the leading-electron SF. Neither applied yet.

## (earlier) RESUME HERE (end of session 2026-10-12)

**Where things stand:** the workflow runs on AK4 jets (the group-meeting decision of
2026-10-11) and labels each jet with both hadronFlavour and partonFlavour. Only the
1-file-per-sample MC test exists so far. Everything is committed and pushed to
`myfork/coffea_machine` (`6e0b7e3` before this notes commit); nothing is running.

**Look at first:**
- `hists_zbzc_ak4_test/test_zbzc_ak4/slides_zbzc_ak4_summer22_test.pdf`: 30-page AK4 deck
  (setup, cutflow, yields, AK8 vs AK4, kinematics, PNet taggers, hadron vs parton flavour,
  pileup check p. 29, N_jet at 1 vs 20 files p. 30)
- `hists_zbzc_ak4_20files/merged/`: 20-files-per-sample run (plots, `yields.txt`) and its 30-page deck
  `slides_zbzc_ak4_summer22_20files.pdf` (page 8 = 1 file vs 20 files instead of AK8 vs AK4)
- `hists_zbzc_ak4_test/test_zbzc_ak4/yields.txt`: cutflows, raw and scaled yields under
  both flavour definitions, and the migration tables
- `hists_zbzc_test/test_zbzc/`: the older AK8 test (deck, notes `NOTES_zbzc_run3.txt`)

**Next steps, roughly in order:**
1. Full-statistics MC run over all DY files (condor). The test shows that the inclusive
   sample (pT(ℓℓ) < 100 GeV) gives 87–89% of the scaled yield from ~12% of the raw events,
   so low-pT MC statistics will limit us. The runner needs a timeout and automatic retry
   (see "Gotchas").
2. Corrections still missing: trigger SFs, jet veto maps, AK4 JEC/JER, b/c-tag SFs.
3. b/c-tag strategy: PNet working points (correctionlib) or a template fit, for example
   in the CvL–CvB plane. c tagging is harder: many true c jets sit in the light-jet corner
   (low CvL).
4. Decide the truth definition for the ratio: hadronFlavour (BTV standard) or
   partonFlavour. They agree for b and differ by ~1 percentage point for c (see results).
5. Add data (2022 C–D) and other backgrounds (ttbar, dibosons), then extract σ(Z+b)/σ(Z+c).

**2026-10-17/18:** both 2026-10-14 questions are answered (pileup confirmed; the bumps disappear
with 20 files per sample). Left: merge N_jet ≥ 5 + MC stat bands, then the full run.

**2026-10-14:** the group asked about the AK4 jet-multiplicity plots (no
"no parton" jets above N_jet = 3; bumps at N_jet = 6 for Z→ee and N_jet = 8 for Z→μμ). The
answers and to-do list are in "Group questions on the AK4 jet-multiplicity plots" below.

**Open questions for the group:**
- hadronFlavour or partonFlavour as the reference truth for Z+c?
- Leading jet only, or every jet in the event? (Leading only for now.)
- Keep the AK8 boosted version as a cross-check, or drop it?

## Timeline

| Date | What | Commits |
|---|---|---|
| 2026-10-07 | New AK8 boosted workflow `Zb_Zc_ratio` on Summer22 DY→ℓℓ, 1-file test, AK8 deck | `2ecd95e` … `560edb6` |
| 2026-10-11 | Group meeting: switch to AK4. AK4 is now the default, AK8 kept as `Zb_Zc_ratio_AK8` | `f8748a6`, `8baed0b` |
| 2026-10-11 | AK4 slides PDF with AK8 vs AK4 comparison | `d2024f2` |
| 2026-10-12 | partonFlavour labels next to hadronFlavour, deck pages 21–28 | `d817f67`, `6e0b7e3` |
| 2026-10-14 | Group questions on the N_jet plots answered (low-statistics MC artefacts), to-dos noted | `a05510c` |
| 2026-10-17 | GenJet-match counters: partonFlavour-0 leading jets are pileup; deck page 29 | `31ba6bc`, `03f9bd3` |
| 2026-10-18 | 20 files per sample: N_jet bumps gone; deck page 30 | |

## How to run

```bash
cd ~/nobackup/BTVNanoCommissioning
source /uscms_data/d3/psrivast/micromamba/bin/activate zbb-btv   # VOMS proxy needed for xrootd

# 1-file-per-sample test (~1 min when xrootd behaves)
timeout 900 python runner.py --wf Zb_Zc_ratio --json metadata/Zb_Zc_ratio_Summer22_DY_test.json \
    --year 2022 --campaign Summer22 --executor iterative \
    --outputdir hists_zbzc_ak4_test --output test_zbzc_ak4.coffea --overwrite
# AK8 version: --wf Zb_Zc_ratio_AK8

python plot_zbzc.py hists_zbzc_ak4_test/test_zbzc_ak4/test_zbzc_ak4.coffea          # plots + yields.txt
python make_zbzc_ak4_slides_pdf.py hists_zbzc_ak4_test/test_zbzc_ak4 hists_zbzc_test/test_zbzc   # deck
                                         # (adds the 1-vs-20-files N_jet page if the 20-file output exists)

# 20 files per sample (~23 min locally, one runner call per sample with timeout + 3 retries)
./run_zbzc_ak4_20files.sh                # per-sample outputs in hists_zbzc_ak4_20files/zbzc_ak4_20files/
# merge them (dict union, keys are datasets) into hists_zbzc_ak4_20files/merged/zbzc_ak4_20files.coffea, then
python plot_zbzc.py hists_zbzc_ak4_20files/merged/zbzc_ak4_20files.coffea
python make_zbzc_ak4_slides_pdf.py hists_zbzc_ak4_20files/merged --nfiles 20   # 20-file deck
python compare_njet_zbzc.py hists_zbzc_ak4_test/test_zbzc_ak4/test_zbzc_ak4.coffea "1 file / sample" \
    hists_zbzc_ak4_20files/merged/zbzc_ak4_20files.coffea "20 files / sample" hists_zbzc_ak4_20files/merged/plots
```

Full fileset: `metadata/Zb_Zc_ratio_Summer22_DY.json` (built by `make_zbzc_fileset.py`).
Cross sections and lumi: `metadata/Zb_Zc_ratio_xsections_Summer22.json`.

## Files

| File | Role |
|---|---|
| `src/BTVNanoCommissioning/workflows/Zb_Zc_ratio.py` | Processor; `jet="AK4"` (default) or `"AK8"` |
| `src/BTVNanoCommissioning/workflows/__init__.py` | Registers `Zb_Zc_ratio` (AK4) and `Zb_Zc_ratio_AK8` |
| `plot_zbzc.py` | Stacked plots (hadron and parton flavour; smallest flavour at the bottom of the log stack, lower panel = flavour fraction per bin, since 2026-10-18), 2D tagger map, migration matrix, `yields.txt`; detects AK4 or AK8 |
| `make_zbzc_ak4_slides_pdf.py` | AK4 deck; reads numbers from the coffea files |
| `make_zbzc_slides_pdf.py` | AK8 deck (numbers typed in) |
| `make_zbzc_fileset.py` | Builds the DY fileset from DAS |

## Analysis setup (AK4)

- **MC:** Summer22 (2022 C–D, pre-EE), NanoAODv12, DY→ℓℓ amc@NLO FxFx (`DYto2L-2Jets_MLL-50`),
  inclusive + PTLL-100/200/400/600, stitched on LHE pT(ℓℓ) (the PTLL-X samples are inclusive
  above X). Lumi 7.98 fb⁻¹ (brilcalc check still pending). Not Zto2Q.
- **Z selection** (shared with AK8):
  - Triggers: Ele30_WPTight_Gsf (ee) / IsoMu24 (μμ)
  - Two tight leptons, pT > 25 GeV, leading > 35 GeV, opposite sign
  - 71 < m(ℓℓ) < 111 GeV, PuppiMET < 50 GeV
- **Jet:** leading AK4 PUPPI jet with pT > 30 GeV, |η| < 2.5, tight-lepton-veto ID (framework
  `jet_id`, with the NanoAODv12 jetId fix), ΔR > 0.4 from leptons. No Z pT cut.
- **Weights:** genWeight × pileup × lepton ID/iso/reco SFs (correctionlib). No trigger SF yet.
- **Truth labels** (both on every histogram):
  - `flav` from hadronFlavour: b (5), c (4), l. NanoAOD AK4 jets have no hadron counts,
    so there is no bb/cc split.
  - `pflav` from |partonFlavour|: b, c, uds (1–3), g (21), none (0).
  - `nevt_flav` and `nevt_migration` hold the raw counts.
- **Taggers histogrammed** (no cut yet): PNet B, CvL, CvB, and CvL vs CvB.

## Results so far (1 file per sample; statistics only)

| | Z→ee | Z→μμ |
|---|---|---|
| raw events selected | 21,367 | 33,106 |
| b fraction: hadron / parton | 4.2% / 4.1% | 4.5% / 4.7% |
| c fraction: hadron / parton | 10.6% / 11.6% | 8.3% / 8.5% |
| gluon share of all jets (parton) | 28.6% | 30.7% |

- 99% of hadron-b jets and 92% of hadron-c jets have the same partonFlavour.
- Hadron-light jets split into 64% uds and 34% gluon.
- 1.4% of hadron-light jets carry a c or b parton with no matching hadron. This is why the
  parton c fraction comes out higher.
- With AK8 (boosted, pT > 200 GeV) the same files gave only 1,440 / 2,121 events, and the
  Z→μμ b yield was negative (one negative-weight inclusive event; see
  `hists_zbzc_test/test_zbzc/NOTES_zbzc_run3.txt`). AK4 has no negative yields.
- Small negative entries (−0.1%) in the migration matrix are NLO negative weights.

## Group questions on the AK4 jet-multiplicity plots (2026-10-14)

Answers come from `hists_zbzc_ak4_test/test_zbzc_ak4/test_zbzc_ak4.coffea` (1 file per
sample). N_eff = (Σw)²/Σw², the number of MC events a bin is effectively built from.
Plots: `plots/n_jet.png`, `plots/n_jet_parton.png`.

**Q1: Why is the "no parton (0)" category missing in `n_jet_parton.png` above N_jet = 3?**
- The stack colours each event by its *leading* jet's flavour, while the x axis counts *all* jets.
- Only 20 raw events have a leading jet with partonFlavour 0 (8 Z→ee, 12 Z→μμ), 0.3–0.5% of
  the scaled yield. All are hadron-light, have pT 30–50 GeV (two at 70–100), and almost all come
  from the inclusive sample (one from PTLL-100). They fall in N_jet = 1–2 (Z→ee) and 1–3 (Z→μμ).
- Interpretation: soft pileup or underlying-event jets just above 30 GeV. They lead only when no
  hard matrix-element jet is present, which happens in low-multiplicity, low-pT(ℓℓ) events.
  At higher N_jet a hard parton-matched jet leads.
- **Verified 2026-10-17: they are pileup.** All 20 (8 Z→ee, 12 Z→μμ) have `Jet_genJetIdx = -1`,
  so no GenJet (pT > 10 GeV) lies within ΔR 0.4. Every leading jet with a b, c, uds or g parton
  label has a GenJet match, except 0.0–0.5% of them (raw). Workflow counters `nevt_genmatch` /
  `sumw_genmatch`; table at the end of `yields.txt`.
  - Leading jets with no GenJet match: 36 raw in Z→ee (0.17%), 55 in Z→μμ (0.17%). Most are
    parton-labelled gluon (20 and 37), not "none". So partonFlavour 0 picks out only part of
    the pileup. Pileup jets near a soft ISR/UE gluon get a parton label but still no GenJet.
  - All are hadron-light apart from a single hadron-c jet (Z→ee), and none are hadron-b, so
    pileup does not touch the b yield. Scaled, the unmatched fraction is 1.9% (Z→ee) and 1.3% (Z→μμ).
    That is larger than the raw fraction because the events sit in the high-weight inclusive sample,
    so it is statistically poor until the full MC run.
  - 20 files per sample (2026-10-18, `hists_zbzc_ak4_20files/merged/yields.txt`) confirms it:
    395 of 399 partonFlavour-0 leading jets (99%) have no GenJet. A few unmatched parton-b / c
    leading jets now appear (11 b, 40 c in 2.3M; 0.01–0.03% raw). The scaled unmatched fraction
    is stable at 1.75% (Z→ee) and 1.74% (Z→μμ), so ~1.7% of the low-pT-dominated scaled yield
    has a pileup leading jet, nearly all light (gluon-labelled jets: 3.5–3.7% unmatched).

**Q2: Why does N_jet peak at 6 for Z→ee and at 8 for Z→μμ?**
Neither bump is physics. Each is one or two high-weight MC events in a nearly empty bin.
- Z→ee, N_jet = 6 (802) is more than N_jet = 5 (563): 785 of it is the inclusive sample with
  N_eff = 1.7 (about 2 events), while N_jet = 5 holds 1 inclusive event (462).
- Z→μμ, N_jet = 8 (19.7) is more than N_jet = 7 (2.4): N_jet = 8 is 1 PTLL-100 event (16.3), and
  N_jet = 7 nearly cancels: a PTLL-200 negative-weight event (−3.5) plus a PTLL-400 event (+5.9).
  Z→μμ N_jet = 6 (630) > N_jet = 5 (433) the same way: 589 of it is 1 inclusive event.
- Per-event weights differ a lot: one inclusive event is about 300–600 events at 7.98 fb⁻¹,
  a PTLL event about 0.1–20. This is the same low-pT statistics problem as in "Next steps" item 1.
- **Checked 2026-10-18 with 20 files per sample** (`hists_zbzc_ak4_20files/merged/`, deck page 30,
  `plots/n_jet_stats_compare.png` + `.txt`). Both bumps are gone: Z→ee N_jet = 6 802 → 46,
  Z→μμ N_jet = 6 630 → 108 and N_jet = 8 19.7 → 0.0. Both spectra fall smoothly up to N_jet = 7,
  and Z→μμ out to 9. One new single-event point: Z→ee N_jet = 8 = 34 (N_eff 1.1), a single
  inclusive-sample event (31.6). N_jet ≥ 6 is still N_eff ≲ 3 and needs the full run. The
  inclusive sample is the limit: 20 files give 39k / 69k selected events (Z→ee / Z→μμ) against
  74k–370k for each PTLL sample, and all 525 inclusive files would give ~26× more.

**To do from these questions:**
- [ ] Merge N_jet ≥ 5 into one last bin and draw MC statistical uncertainty bands on the stacks.
- [x] genJet-match check for partonFlavour-0 leading jets: confirmed pileup (2026-10-17).
- [ ] Optionally fill N_jet with every jet's flavour, not only the leading jet's.
- [x] Recheck with more MC: 20 files per sample removes both bumps (2026-10-18).
- [ ] Recheck the N_jet ≥ 6 tail after the full-statistics MC run.

## Gotchas

- **xrootd stalls:** reads sometimes hang indefinitely. `--executor futures` hung for more
  than 28 min. One `iterative` run also hung for more than 9 min, and the identical rerun
  finished in 36 s. Always wrap runs in `timeout`, log to a file rather than piping into
  `| tail` (which hides progress), and retry. Condor jobs will need retries.
- **Framework bug, not fixed (shared code):** `utils/correction.py` `eleSFs` resets the SF
  product inside the per-electron loop, so only the last electron's SF is kept. Our workflow
  works around it by calling the SFs once per lepton. To be reported upstream.
- `FatJet_jetId` is fine for |η| < 2.7 in NanoAODv12 but absent in v15 (2024). The AK4 jetId
  fix is handled by the framework's `jet_id`.
- Fork status: `myfork/coffea_machine` is 3 commits behind `hsinwei/coffea_machine`.
  Not merged, and no PR opened yet.
