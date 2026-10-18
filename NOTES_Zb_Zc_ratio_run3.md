# Notes: Run 3 Z(→ℓℓ) + b / Z(→ℓℓ) + c ratio (`Zb_Zc_ratio` workflow)

Run 2 QCD_sf work is in `SESSION_NOTES.md`; this file is only the Run 3 ratio measurement.

## RESUME HERE (end of session 2026-10-12)

**Where things stand:** the workflow runs on AK4 jets (the group-meeting decision of
2026-10-11) and labels each jet with both hadronFlavour and partonFlavour. Only the
1-file-per-sample MC test exists so far. Everything is committed and pushed to
`myfork/coffea_machine` (`6e0b7e3` before this notes commit); nothing is running.

**Look at first:**
- `hists_zbzc_ak4_test/test_zbzc_ak4/slides_zbzc_ak4_summer22_test.pdf`: 30-page AK4 deck
  (setup, cutflow, yields, AK8 vs AK4, kinematics, PNet taggers, hadron vs parton flavour,
  pileup check p. 29, N_jet at 1 vs 20 files p. 30)
- `hists_zbzc_ak4_20files/merged/`: 20-files-per-sample run (plots, `yields.txt`)
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
| `plot_zbzc.py` | Stacked plots (hadron and parton flavour), 2D tagger map, migration matrix, `yields.txt`; detects AK4 or AK8 |
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
