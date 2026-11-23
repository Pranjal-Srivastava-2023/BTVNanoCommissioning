# Notes: Run 3 Z(→ℓℓ) + b / Z(→ℓℓ) + c ratio (`Zb_Zc_ratio` workflow)

Run 2 QCD_sf work is in `SESSION_NOTES.md`; this file is only the Run 3 ratio measurement.

## RESUME HERE (2026-11-22 night): MET > 50 study PHASE 2 DONE -- deck for the meeting 2026-11-23

DECK: hists_zbzc_run3_metvar/Summer22/slides_zbzc_metvar_Summer22.pdf (22 p.) + .pptx (cleaned, 20 p.).
Rebuild: python plot_zbzc_metvar.py (-> metvar/metvar.{txt,json} + 4 png); conclusions are hand-written in
hists_zbzc_run3_metvar/Summer22/metvar/findings.json; PYTHONPATH=$PWD python make_zbzc_metvar_slides_pdf.py
(+ ZBZC_PPTX=1 ZBZC_CLEAN=1 PYTHONPATH=$PWD:/uscms_data/d3/psrivast/pylibs_pptx for the pptx).
Run: 9 MC samples 20/20 files (PTLL-400 killed twice by the stall watchdog, OK on try 3). Checks exact: 'all' ==
run A met_pt_nm1 (diff 0), 0 of 2.8M Z events with |MET_all - framework MET| > 0.01 GeV.
RESULTS, data/MC at MET 50-100 (Zee / Zmm), all cuts except MET:
  nominal 0.70 / 0.69; no JER in MET for 2.65-2.964 0.81 / 0.82; 2.5-3.139 0.82 / 0.84 (Phase 1 predicted 0.83 / 0.86);
  soft & 2.5-3.139 0.80 / 0.82; pT<30 0.84 / 0.85; CorrT1METJet 0.77 / 0.75; no JER in MET 0.95 / 0.95; run B 0.96 / 0.96.
  MET < 50: 0.971 / 0.964 nominal -> 0.955 / 0.945 (fwd off) -> 0.944 / 0.937 (no JER in MET): with no JER data/MC is
  flat ~0.94-0.95 (shape described, ~5 % normalisation left). MET 100-200: too few events.
  MC b-tag/c-tag yield ratio change: L < 0.6 %, M +1.5..+2.7 % (Zee) / -0.6..-1.2 % (Zmm), T up to +1.5 % (Zee) /
  -3.1 +- 0.4 % (Zmm); data stat of the ratio 1.9/3.3/4.8 % (Zee), 1.1/1.8/2.7 % (Zmm) L/M/T.
  NOT fixed: recoil RMS(u_perp) at qT<10: data 13.9, MC nominal 17.0, no JER 15.7 GeV (MC still wider); recoil response
  <u_par+qT> data 1-2.5 GeV higher than every MC version (JER-independent).
Proposal on slides: keep recipe (run A) as nominal; MET-cut systematic on b/c = change to no-JER-in-MET for
2.5-3.139 (or no JER in MET, larger); ask JME about SF 1.60-1.64 for soft jets at 2.65-2.964; study recoil
(pileup, unclustered, 2022 v12 DY MET remark of the JME talk); other eras only if asked.

### (state while it was running)

Workflow Zb_Zc_ratio_metvar = run A (metxy + Z pT weights) + met_variants=True: MET_VARIANTS (all, noJERfwd,
noJERhighSF, noJERsoftfwd, noJERsoft, noJERcorrT1, noJER) filled side by side in metvar_nm1 (tag regions, as
met_pt_nm1) and metvar_recoil; common_shifts_metvar captures the framework's type-1 jets + JER factor from get_JER
and redoes the T1 sum; check metvar_check (1-file test: 'all' == framework MET, sum |diff| 1e-11). Analysis jets
nominal (smeared). Data not rerun: data have no JER -> every version = nominal; postprocess links run A data.
Launched 19:04 on cmslpc317: launch_zbzc_job.sh zbzc_run3_metvar Zb_Zc_ratio_metvar mc "DYto2L" + same with
"TTto2L2Nu WW WZ ZZ" (both -> logs_zbzc_run3_metvar/Summer22/driver_mc.log, need 2x ALL DONE); watchdog
ZBZC_RUN=zbzc_run3_metvar; postprocess_zbzc_metvar.sh (log logs_zbzc_run3_metvar/postprocess.log: N/N, links data).
To do after: comparison plots + data/MC table per version, deck (PDF + pptx), commit + push.

## RESUME HERE (2026-11-22): MET > 50 study Phase 1 -- which jets make the MC MET grow under JER (MC only)

Context (group meeting): "is JER already in NanoAOD / just keep JER off?". Checked on a DY file: NanoAOD Jet_pt and
PuppiMET have NO JER (Jet_pt = raw x JEC within 0.3-0.9 %, MC width = MC PtResolution, nano PuppiMET = our JEC-only
type-1). JME docs uploaded by the user (src/BTVNanoCommissioning/*.pdf: JER page, JEC page, Type-1 MET page +
Type1MET.pdf worked example, Type1METUnc.pdf, Nurfikri JME General 2 Feb 2026, Malucchi Run 3 MET performance):
the recipe smears every jet in the type-1 sum incl. CorrT1METJet, pT > 15 on the smeared pT -> run A IS the recipe.
Phase 1: python study_zbzc_met_jer_split.py hists_zbzc_run3_metsplit/Summer22 30,15,10,6,4 (65 DY files, ~15 min,
local, no batch; log logs_zbzc_metsplit/run.log) + python plot_zbzc_met_jer_split.py hists_zbzc_run3_metsplit/Summer22.
Same events, ~30 MET versions (smear only one jet class in the MET); simplified analysis selection (no SFs, see
SELECTION in the script). Output met_jer_split.{txt,json}, plots/met_jer_split_{zjet,z}.{png,pdf}.
RESULTS (Z+jet, all cuts except MET; MC MET 50-100 fraction with JER / without JER in the MET):
  all jets (run A) 1.37 Zee / 1.39 Zmm  (full runs: data/MC 0.697 -> 0.964, i.e. x1.38: reproduced)
  only |eta| 2.65-2.853 (JER SF 1.60) 1.18 / 1.20 = about half the effect from ONE SF bin; |eta| 2.5-3.0 1.21 / 1.25;
  mostly soft jets there (pT<30 & |eta|>2.5: 1.22 / 1.25); analysis-type jets (pT>30, |eta|<2.5) only 1.08 / 1.08.
  JER everywhere except |eta| 2.5-3.139: 1.16 / 1.12 -> expected data/MC ~0.83 / 0.86 (= 0.964 / that; not measured).
  JEC at raw pT (JME talk) vs muon-subtracted pT (framework): no change (1.368 vs 1.368). CorrT1METJet off: 1.24 / 1.25.
  JER SF (Summer22 JRV2, pT < 121): |eta| 2.5-2.65 1.22, 2.65-2.853 1.60, 2.853-2.964 1.64, 2.964-3.139 1.21, else 1.02-1.30.
Next = Phase 2 (needs user OK): one MC+data run filling several MET versions side by side (e.g. no JER in |eta|
2.5-3.139 in the MET, no JER for soft jets) to get the data/MC of each directly.

## Cuts / cutflow / yields deck of all latest setups (2026-11-17)

User asked for a separate deck with the cuts, cutflow and yields of everything in the latest decks. Tables:
python make_zbzc_yields.py hists_zbzc_run3_<setup>/Summer22 [<ref run dir>] for zpt, zpt_mupt30/mueta21/tauveto (ref zpt),
metxy (ref zpt), metxy_nojer/jermatched (ref metxy) -> <run>/Summer22/yields/yields.{txt,json} + compare_*.
Deck (10 p.): PYTHONPATH=$PWD python make_zbzc_cuts_yields_pdf.py --date "17 November 2026" (+ ZBZC_PPTX=1 for .pptx)
-> hists_zbzc_run3_summary/Summer22/slides_zbzc_cuts_yields_Summer22.{pdf,pptx}. FINAL / SUMMARY text by hand in script.
Same day, user: "more detailed, every cut, correction, SF, trigger, weight; don't assume people know" -> 11 description
pages added after the title (samples+normalisation+DY stitching, triggers/MET filters/jet veto/golden JSON, electrons,
muons, Z candidate+tau veto, jets JEC/JER/ID, type-1 MET + XY + JER variants, b tagging + WP table, every MC weight,
Z pT weight table, not applied). Facts from the workflow/selection/correction code and the cvmfs correctionlib keys.
Deck now 21 pages. Fixed: cuts table said run C changes the jets (only B does).
Key numbers: Z events data/MC 0.996/0.986 (ee/mm), >=1 jet 0.945/0.938 (B 0.961/0.952), final 0.971/0.963 base;
cut changes <= 0.003 inclusive, <= 0.009 Loose b-tag; B/C add 1.2-1.9 % MC after MET cut -> final 0.959/0.954 ee.

## Editable .pptx copies of the decks (2026-11-17), for Google Slides

Every deck built with zbzc_slides_common.Deck can also be written as an editable PowerPoint file: set ZBZC_PPTX=1
and add /uscms_data/d3/psrivast/pylibs_pptx (python-pptx + lxml, installed with pip --target, NOT in the zbb-btv env)
to PYTHONPATH. Same script, same --date; output = same name with .pptx. Text, bullets and coloured notes become text
boxes (Arial), tables become real tables, plots are pictures. Upload to Google Drive -> Open with Google Slides.
  ZBZC_PPTX=1 PYTHONPATH=$PWD:/uscms_data/d3/psrivast/pylibs_pptx python make_zbzc_btagL_slides_pdf.py --setup zpt --date "15 November 2026"
Built 2026-11-17 for the 6 latest decks (4 one-change b-tag decks, MET A/B, run C); slide counts = PDF page counts;
text-fit check with Liberation Sans (Arial metrics): no box needs more lines than in the PDF.
Not checked by eye in Google Slides yet (no LibreOffice render on the node).
CLEANED same day (user): ZBZC_CLEAN=1 drops zoomed-plot pages ('zoom' in title/subtitle), 'Analysis setup 1/2',
'Contents', 'How to read the numbers'; setup 2/2 is then titled 'Analysis setup: ...'; footers renumbered; b-tag
divider pages say '32 plots follow'. The committed .pptx are the CLEANED ones (b-tag 105 slides, MET 153, run C 16);
PDFs unchanged (full). Rebuild: ZBZC_PPTX=1 ZBZC_CLEAN=1 PYTHONPATH=$PWD:/uscms_data/d3/psrivast/pylibs_pptx python <deck script> ...

## RESUME HERE (2026-11-16 evening, RUN C done): JER in type-1 MET only for gen-matched jets

STATUS 2026-11-16 ~17:00: run C finished 15:37, postprocess 15:44; every log N/N (DY 20/20 x5, tt/WW/WZ/ZZ 20/20), 2x
"ALL DONE", no tracebacks. Deck (19 p.): PYTHONPATH=$PWD python make_zbzc_metc_slides_pdf.py ->
hists_zbzc_run3_metxy_jermatched/Summer22/slides_zbzc_metC_Summer22.pdf (setup slides via SETUP jer="abc").
RESULTS (data/MC all cuts except MET, MET 50-100, stat only): Zee A 0.697 / C 0.836 / B 0.964;
  Zmm A 0.687 / C 0.844 / B 0.961. C better in every Delta phi(MET, j1) bin, still below B.
  Z stage (no jet cut) Delta phi(MET, any-eta jet>15) at MET 50-100: A 0.50/0.49, C 0.66/0.67, B 0.72/0.72 (Zee/Zmm).
  Recoil RMS(u_perp) Z events qT<10: data 13.9, A 17.1, B 15.7, C 15.9 -> ~2 GeV extra MC width NOT from JER.
  Response u_par+qT identical in A/B/C (data 1-2.5 GeV higher).
  MC cutflow of C == A up to Zmass (jets identical); final data/MC (all weights) A 0.971/0.964, B 0.959/0.952,
  C 0.954/0.945; pT balance chi2/ndf A 40,110  B 58,144  C 45,125 (C's change = only MET-cut event selection).
  -> random smearing of jets without gen jet (incl. all CorrT1METJet) in T1 MET ~ half of the deficit; the other half
     from smearing of gen-matched jets in the MET (untested causes: JER SFs of soft/forward jets, genJetIdx matching
     vs JME dR<R/2 & 3 sigma, our T1 propagation vs JME recipe).
Proposed next (need user OK, nothing running): split the MET change from smearing by jet pT/|eta| (extra histo,
short run); check JER SF / matching; compare T1 propagation with JME recipe; unclustered/pileup part for the recoil.

## (earlier) RESUME HERE (2026-11-16, MET study): MET > 50 deficit, Delta phi + recoil + JER on/off, MET XY correction

STATUS 2026-11-16 ~14:30: DONE, pushed 325fb66 (+ this notes commit). Runs finished 13:49, every log N/N (DY 20/20
x5, tt/WW/WZ/ZZ 20/20 in both runs, Muon 12+8, EGamma 15+5), no non-zero exits. Deck 158 p.
RESULTS (data/MC all cuts except MET, MET 0-50 / 50-100 / 100-200, stat only):
  Zee  A (JER on) 0.971 / 0.697 / 0.917   B (JER off) 0.959 / 0.964 / 1.274+-0.17
  Zmm  A          0.964 / 0.687 / 0.750   B           0.952 / 0.961 / 1.022+-0.09
  -> JER smearing (as propagated to type-1 MET) causes most of the MET 50-100 deficit; fixed at every
     Delta phi(MET, j1). MET XY: data MET phi flatter (chi2/ndf 73->50 Zee, 108->75 Zmm), no effect on MET>50.
  NOT fixed by JER off: Z stage (no jet cut) Delta phi(MET, any-eta jet>15) data/MC 0.49 -> 0.72 only; recoil u_perp
     RMS in Z events at low qT MC still ~2 GeV wider (15.7 vs 13.9); recoil response u_par+qT 1.5-2.5 GeV larger in
     data (data recoil lower) in A and B. In Z+jet (all cuts except MET) B recoil width matches data within 0.5 GeV.
  JER off is NOT the fix: selected-jet pt_balance chi2/ndf worse (40->58 Zee, 110->144 Zmm), MET<50 data/MC -1.2 %,
     final raw data/MC 0.856->0.842 Zee, 0.914->0.898 Zmm.
  Hypothesis (untested): CorrT1METJet get Genpt=-1 (correction.py ~l.1133) and gen-unmatched Jet get genJetIdx=-1,
     so both get STOCHASTIC smearing that enters the type-1 MET sum. Proposed next one-change run: smear only
     gen-matched jets in the type-1 MET (keep smearing of the analysis jets). Ask the user before running.
RUN C (user OK 2026-11-16 14:10): zbzc_run3_metxy_jermatched = workflow Zb_Zc_ratio_metxy_jermatched (jer_met="matched":
  common_shifts_jermatched swaps get_JER; type-1 MET jets (no "jetId" field) get factor 1 where Genpt <= 0; analysis
  jets nominal). Direct test 20k raw DY PTLL-100 events: jets identical to nominal, MET>50 frac 40.2 % nominal /
  39.1 % matched / 37.3 % noJER. Launched 14:15 on cmslpc371 as TWO MC jobs (ZBZC_DSETS "DYto2L" and "TTto2L2Nu WW WZ
  ZZ", both write logs_zbzc_run3_metxy_jermatched/Summer22/driver_mc.log -> needs 2x "ALL DONE"); watchdog
  ZBZC_RUN=zbzc_run3_metxy_jermatched; postprocess_zbzc_met_c.sh (log logs_zbzc_run3_metxy_jermatched/postprocess.log)
  links run A data, plots, then ZBZC_MET_C=1 plot_zbzc_met_compare.py -> hists_zbzc_run3_metxy_jermatched/Summer22/
  met_compare/ (A/B/C). User closed the PC; on return: check postprocess.log N/N, then deck for C (to do: extend
  make_zbzc_met_slides_pdf.py or a short follow-up deck), commit + push with plots, give the PDF path.

User 2026-11-16: (1) check the "phi - 2pi" issue known from Run 2 -> Delta phi wrap IS applied (dphi() folds
|dphi| > pi to 2pi - |dphi|; coffea delta_phi wraps; T1 MET phi = arctan2 + fixPhiRange); cutvar outputs have 0
entries outside [0, pi] in dphi_met / stage_dphi_met / dphi_zj / dphi_ll / dphi_jj. Nothing to fix.
BUT the JME PuppiMET XY (phi-modulation) correction was NOT applied: met_xyCorrections_2022_2022.json.gz
(epochs 2022 / 2022EE, DATA / MC, input npvGood). Size: data (+0.3,+0.65) GeV at 15 PV .. (+0.9,+1.5) at 50 PV;
MC 0.2-0.6 GeV. User chose: apply it in BOTH runs; ONE MET deck comparing A and B.
(2) Delta phi study of MET > 50 with my suggestions (nojer + recoil), separate deck, 3-tagger deck style.
Code: workflow kwarg met_xy (MET_XY dict, MET.phi_noxy kept), new hists met_phi_nm1 (xy noXY/XY x metbin) and
recoil (sel Z / Z+jet x comp upar_qt / uperp x zpt bins), filled in every AK4 run. Workflows Zb_Zc_ratio_metxy
(zpt + met_xy) and Zb_Zc_ratio_metxy_nojer (+ jer_smear=False). 1-file test: data identical except 1 event over
the MET cut; noJER lowers MC MET>50 fraction (DY PTLL-100 Zee 13.5 -> 9.7 %).
Runs 2026-11-16 11:12 on cmslpc371: launch_zbzc_job.sh zbzc_run3_metxy (mc + data), zbzc_run3_metxy_nojer (mc);
watchdog logs_zbzc_run3_metxy/stall_watchdog_cmslpc371.log; postprocess_zbzc_met.sh (log
logs_zbzc_run3_metxy/postprocess.log: N/N per log, links A data into B, lumi.json from zpt, plots, compare).
Plots: ZBZC_RUN=<run> ZBZC_MET=1 python plot_zbzc_run3.py Summer22 -> plots/met/ (SLICES/LINEAR/CROP/RRANGE hooks);
python plot_zbzc_met_compare.py -> hists_zbzc_run3_metxy/Summer22/met_compare/ (overlays, recoil_*.png, json).
Deck: PYTHONPATH=$PWD python make_zbzc_met_slides_pdf.py -> hists_zbzc_run3_metxy/Summer22/slides_zbzc_met_Summer22.pdf
(158 pages; FINDINGS dict filled by hand after looking at the plots). Layout tested on 1-file outputs.

## (earlier) RESUME HERE (2026-11-16): one-change-per-deck b-tag decks (pT 26->30, |eta| 2.4->2.1, tau veto), Z pT weights ON

STATUS 2026-11-15 22:30: DONE, pushed 182e5f9 (code, plots, yields, 4 PDFs, 138 pages each). Session paused, continue 2026-11-16.
Results (no tag, data/MC Zee / Zmm, stat only): v2 0.949 / 0.943 -> zpt 0.971 / 0.963 (MC -2 %, data same);
mupt30: Zmm 0.961 (data and MC both -17.5 %); mueta21: Zmm 0.964 (both -12 %; tagged Zmm ~ -0.01);
tauveto 0.972 / 0.965 (both ~ -1 %). No cut moves data/MC beyond the stat. errors.
Plot fix in this round: log/zoom plots get extra headroom so the stat box clears the data; slope label range
clamped to the plotted range. Open: the user sent two images (3108x1764, 3885x2205) that Claude could not see;
ask for their content. Not pushed / local only: coffea outputs; test dir hists_zbzc_statboxtest (can be deleted).
Next: wait for user/advisor feedback on the 4 decks (and the images); nothing is running.

User 2026-11-15 evening: the cut-study deck (cutvar) was rejected (no DY+b/c/light split, VV not named) and the
nojer MET test was STOPPED by the user ("Stop everything now"); the metjer/metnojer runs were killed and are NOT to
be resumed unless asked. New request: decks EXACTLY in the format of
hists_zbzc_run3_v2/Summer22/slides_zbzc_btagL_3taggers_Summer22.pdf (8 Nov, Loose b-tag, PNet/DeepJet/RobustParT)
plus the statistics box, with Z pT weights ON, one change per deck:
  zpt          = v2 setup + Z pT weights (base / reference of the three below)
  zpt_mupt30   = muon pT > 30 (was 26; leading muon already > 35, so effectively the subleading muon)
  zpt_mueta21  = muon |eta| < 2.1 (was 2.4; user said 2.5 but muons stop at 2.4, so 2.1 is the tighter POG value)
  zpt_tauveto  = loose DeepTau veto (separate deck)
Workflows Zb_Zc_ratio_zpt / _zpt_mupt30 / _zpt_mueta21 / _zpt_tauveto (__init__.py; kwargs mu_eta_max, tau_veto;
mu_variants off). Data reuse: zpt data = v2 data (Z pT weights act on MC only); mupt30/mueta21 EGamma = v2 EGamma.
Runs 2026-11-15 19:22-21:26 (launch_zbzc_job.sh), all logs N/N, 0 ERROR lines.
Plots: ZBZC_RUN=zbzc_run3_<setup> ZBZC_TAG=<incl|btag_L|btagDeepJet_L|btagRobustParT_L> python plot_zbzc_run3.py Summer22
Deck:  PYTHONPATH=$PWD python make_zbzc_btagL_slides_pdf.py --setup <zpt|zpt_mupt30|zpt_mueta21|zpt_tauveto>
  -> hists_zbzc_run3_<setup>/Summer22/slides_zbzc_btagL_3taggers_Summer22_<setup>.pdf ("What changed" page 2 vs ref)

## RESUME HERE (2026-11-15): Zmm cut study + tau veto + Delta phi(MET) (Summer22, run zbzc_run3_cutvar)

STATUS 2026-11-15 evening: DONE. Run 14:30-17:28, all samples N/N (DY 20/20 x5, tt/WW/WZ/ZZ 20/20, Muon 12+8,
EGamma 15+5), no ERROR lines. Regression vs v2: all 54 common hists x 13 samples identical, sumw identical.
Deck: hists_zbzc_run3_cutvar/Summer22/slides_zbzc_cutvar_Summer22.pdf (176 p., make_zbzc_cutvar_pdf.py);
plots/table: hists_zbzc_run3_cutvar/Summer22/cutvar/ (plot_zbzc_cutvar.py; cutvar_table.txt).
Results (Zmm, stat only): no cut changes the slope: final pT(mumu) slope -1.6..-0.6 %/100 GeV (nominal -0.9+-1.2),
jet pT -2.8..-1.8 (nom -2.0+-1.7); overlays identical point by point (dip at pT(mumu) 25-50 everywhere).
Only MET cut moves data/MC: 0.960 (<40) 0.943 (<50) 0.932 (<60) 0.919 (none); others <= 0.002.
Tau veto: data -1.0 %, MC -1.2 %, data/MC 0.943 -> 0.945. Z stage slope -3.5+-0.8, muon variants -3.5..-3.1.
Delta phi: 0-jet Z events with a lepton-cleaned jet pT > 15 any eta: MC 49 % vs data 38 % (Zee 48 vs 37);
MET 50-100 0-jet: 70 % of MC has MET opposite that jet (dphi > 2.5), data/MC there 0.39 (Zee 0.40);
N-1 MET 50-100 Zmm: data/MC 0.52/0.63/0.78 vs dphi(MET,j1) <0.6/0.6-2.5/>2.5, 0.60/0.67/0.78 vs dphi(MET,Z):
deficit in every direction, smallest back-to-back. Reading (NOT proven): soft/forward MC jets too energetic
(JER smearing of unmatched jets?), fits 2026-10-28 nojer test. Next proposed: Delta phi + jany pT/eta with
nojer (diag_zbzc_met.py), then recoil u_par/u_perp. Await user/advisor.

User/advisor asks (2026-11-15): (a) MET > 50 deficit "thoroughly" -> START WITH Delta phi only; (b) does
RobustParT reduce it -> NO (answered from v2 outputs, see below); (c) change the CURRENT cuts one at a time,
staying at POG-like values, plots for all (many slides OK); MUONS ONLY, electron cuts untouched; (d) loose
tau veto (advisor 2026-11-08 item 3) as a variant; (e) statistics box on plots. N_jet 0-bin: dropped by user.
Code 0f3c281 (local commit, fork not pushed yet): MU_VARIANTS + sub30 lead30 mass76 mass81 met40 met60 noMET
jpt25 jpt40 jeta24 jidTight tauVeto (eta21 already there); muvar_jet_pt/jet_eta/met_pt; dphi_met (all cuts but
MET, obj j1 jmin z lep0 lep1 x metbin 0-50/50-100/100+) and stage_dphi_met (Z events, stage axis, obj z / jany =
leading lepton-cleaned jet pT > 15 any eta). Tau veto: DeepTau2018v2p5 VSjet>=Loose(4), VSe>=VVLoose(2),
VSmu>=VLoose(1), pT > 20, |eta| < 2.5, |dz| < 0.2, DM 0/1/10/11, dR > 0.4 from jet-cleaning leptons.
1-file test OK: muvar nominal == main Zmm exactly (MC + data); dphi totals == met_pt_nm1 / stage_z_pt;
tauVeto removes 0.3-0.9 %.
Run started 2026-11-15 14:30 on cmslpc352: ZBZC_RUN=zbzc_run3_cutvar ZBZC_JSON=logs_zbzc_run3_v2/
Zb_Zc_ratio_run3_Summer22_dyredir.json run_zbzc_run3.sh Summer22 mc|data -> hists_zbzc_run3_cutvar/Summer22/.
CHECK "Preprocessing 100% N/N" in every log (exit 0 can hide dropped files). 14:32 DY MLL-50 0ce05172 timed out
AGAIN even via cmsxrootd (19/19); file read fine 2 min later -> mc half killed + restarted 14:36, DY 20/20
(killed logs kept as *_killed_19of20.log). Muon_Run2022C 12/12 as in v2.
Deck: make_zbzc_cutvar_pdf.py (shared defs zbzc_cutvar_defs.py); FINDINGS / DPHI_FINDINGS are None placeholders
-> write them by hand after looking at the plots. Test deck on 1-file outputs: 176 pages, layout OK. Then: cp lumi.json from v2,
python plot_zbzc_cutvar.py hists_zbzc_run3_cutvar/Summer22 -> cutvar/ (table, var_*, ovl_*, dphi_*, stage_dphi_*),
deck (to write: make_zbzc_cutvar_pdf.py with zbzc_slides_common), push plots + PDF, give full PDF path.
Already known from v2 (met_pt_nm1 per tag region, MET 50-100 data/MC, Zmm): PNet/DeepJet/RobustParT agree at
the same WP (bL 0.70/0.70/0.74, bT 0.89/0.92/0.86, cL 0.65/0.66/0.66); deficit follows the DY+light share, not
the tagger. Z events with 0 selected jets: data/MC 1.13 (MET<25), 0.77, 0.42, 0.35 (75-100) -> MC MET too wide
even without jets (fits 2026-10-28 "nojer removes most of the 2022 MET tail").

## RESUME HERE (2026-11-09): continue editing the two decks of 2026-11-08 (Summer22 only)

Decks (last pushed dc402c9 on myfork/coffea_machine), rebuild in ~1-3 min, NO rerun needed:
- hists_zbzc_run3_v2/Summer22/slides_followup_2026-11-08_Summer22.pdf (25 p.)  <- python make_zbzc_followup_pdf.py
- hists_zbzc_run3_v2/Summer22/slides_zbzc_btagL_3taggers_Summer22.pdf (137 p.) <- python make_zbzc_btagL_slides_pdf.py
- shared layout, analysis-setup slides (2) and "how to read" slide: zbzc_slides_common.py (edit there for both decks)
- every number is parsed from the run outputs (muvar/, pu/, tagger_summary.txt, channels_summary.json, yields*.txt);
  never type numbers into the scripts. Check pages with pdftoppm -r 50 + montage before pushing.
User's slide rules (2026-11-08): self-explanatory, full sentences (question / what was done / found / meaning), define
every quantity, tests labelled "not applied" with the default row highlighted, setup slides in every deck, no
over-claiming (check plots before writing a claim), always give the full PDF path, push plots + PDFs.
Open items the user may ask for: SF up/down uncertainty band (needs a rerun with the variations), decisions on the
muon default and tagger/WP, full Summer22 dataset. Housekeeping: old-code worktree
/tmp/claude-10024/-uscms-homes-p-psrivast/18f64ed0-5088-442c-8ffc-6ac8d1cb40bd/scratchpad/oldcode (957d2d9) can be
removed with `git worktree remove --force <path>` (scratch dir may already be gone; then `git worktree prune`).

## RESUME HERE (2026-11-08): advisor's requests after the 237-page deck (Summer22 only)

Advisor (meeting 2026-11-08): (1) muon-channel discrepancy: trigger turn-on, eta cut, SFs, corrections,
Rochester? follow POG; suggested pT > 26, |eta| < 2.4; (2) other b/c taggers (L/M/T); (3) loose tau veto
(user: DROPPED for now); (4) why ee and mumu pileup differ; (5) ee legend had DY+b / DY+c swapped;
(6) MET plot up to ~200 GeV; (7) zoom on the high-statistics bins.

STATUS (evening): DONE. Two decks (user: slides must be self-explanatory; full setup slides; numbers parsed
from the output files; shared layout + setup/"how to read" slides in zbzc_slides_common.py):
- hists_zbzc_run3_v2/Summer22/slides_followup_2026-11-08_Summer22.pdf (25 p., make_zbzc_followup_pdf.py):
  every request as question / what was done / result / meaning; tests clearly marked "not applied".
  Replaces slides_zbzc_v2_Summer22.pdf and advisor_recommendations_2026-11-08.pdf (removed; in git history).
- hists_zbzc_run3_v2/Summer22/slides_zbzc_btagL_3taggers_Summer22.pdf (137 p., make_zbzc_btagL_slides_pdf.py):
  Loose b-tag, PNet / DeepJet / RobustParT, 42 explained plots per tagger. User does NOT want ~950-page all-regions.
User was confused by the muon test table ("you turned off pileup / Tight ID?"): tests are diagnostics only; the
default keeps everything. Say so explicitly on any slide with variants.
Next: show the advisor; decisions pending (keep pair trigger SF + pT > 26 as default? which tagger/WP?), then
the full dataset.

Run: ZBZC_RUN=zbzc_run3_v2 run_zbzc_run3.sh Summer22 mc|data (13:08-16:28) -> hists_zbzc_run3_v2/Summer22/.
FILE PROBLEM (exit code 0 hides it! check "Preprocessing 100% N/N" in every log): the runner's file validation
silently drops a file on an XRootD timeout. DY MLL-50 file 0ce05172-... is NOT readable from cmsdcadisk (fails
even with 300 s), but the same LFN reads fine via root://cmsxrootd.fnal.gov/ -> rerun with
logs_zbzc_run3_v2/Zb_Zc_ratio_run3_Summer22_dyredir.json (only that URL changed). EGamma_Run2022D lost
002aaeb4-... once (transient) -> plain rerun. rerun_missing_files_v2.sh, logs driver_fix.log. All 20/20 now.
Checks: check_zbzc_v2_regression.py PASSED: Zee 237 hists x 13 samples identical to hists_zbzc_run3_tag,
sumw identical; muvar prev == old Zmm per sample (data 65259); muvar nominal == new main Zmm.

Results (stat. only, 20 files):
- Zmm data/MC 0.966 -> 0.943 (Zee 0.949): pair trigger SF +2.75% MC, pT > 26 -0.3%. Z stage: Zee 0.995,
  Zmm 0.986. Channels agree at every stage (compare_zbzc_v2_channels.py -> channels_summary.{txt,json}).
- muvar_table.txt: no muon choice changes the pT(mumu) slope (final -1.0..-0.3, Z -3.8..-3.0 %/100 GeV).
  trigMatch vs pair formula: -0.8% (final), -0.5% (Z). |eta| 2.0-2.4 leading muon 0.964 vs barrel 0.998
  at Z stage (trigMatch 0.940): OPEN.
- Slope: same fit on 3 runs: ge1j (DY Z pT weights ON) Zmm +4.4+-1.3; deck run (weights off) -0.7+-1.2;
  v2 -0.8+-1.2. So the +4.4 came from the weights; no significant slope after the selection now. Before
  jet/MET cuts both channels fall (Zee -2.1+-1.2, Zmm -3.5+-0.8) = DY generator Z pT. Dip at pT(ll)
  30-60 GeV (0.92) in both: OPEN. Deficit after cuts: MC excess with jets (0 jet MET<50: 1.04, final 0.95)
  and MET>50 (0.41-0.69): OPEN, common to both channels.
- Pileup: mean PU of lumisections: EGamma 32.84, Muon 33.56, full 33.76. Mean-shift check (data-MC mean
  N(PV) vs dPU x 0.69): Zee -0.57 vs -0.64, Zmm -0.14 vs -0.14 -> sampling explains ee vs mumu.
  Bin-by-bin reweighting (zbzc_pu_closure.py part 2) OVERSHOOTS (Zmm gets a slope) -> not used.
- Taggers (summarize_zbzc_taggers.py -> tagger_summary.txt): similar purity at same WP; b-tag tag ratios
  within 1.7 sigma; c-tag mean tag ratio PNet 0.978, DeepJet 1.025, RobustParT 1.042 (max 2.4 sigma).
Tau veto: not done (user: postponed). Coffea outputs (73 MB) not committed, as for the tag run.

What was found / changed (details in the code docstrings):
- Legend (5): stack order was per channel by yield, so b/c swapped when their sizes swap. Now one
  stack order for both channels + fixed legend order (plot_zbzc_run3.py). Old regions replotted.
- Muon SS (Run 3 Rochester) IS applied (muonSS loaded for Summer22, MUO_shifts). |eta| < 2.4 already.
- MUO muon_Z.json (updated 2026-06-18) now has nominal_DATAeff / nominal_MCeff for IsoMu24 (signed
  eta x pT >= 26). Our Zmm used the leading-muon SF only although either muon can fire -> MC ~2.75%
  too LOW. New nominal (POG): pair formula as for Zee + both muons pT > 26 (SF range). NOTE: this
  LOWERS Zmm data/MC by ~2.7% (towards Zee), it does not bring it to 1.
- mu_variants: muvar_* hists, one change each (prev, trigLead, sub25, lead26, eta21, trigMatch, noSS,
  noTrigSF, noIDIsoSF, noPU) at stage Z and final -> compare_zbzc_muvar.py.
- Taggers: DeepJet (btagDeepFlav*) + RobustParT (btagRobustParTAK4*) L/M/T with own BTV SFs
  (same SF ranges as PNet); regions btagDeepJet_L ... ctagRobustParT_T; PNet names unchanged.
- met_pt_nm1 (all cuts but MET, 0-200, all regions); *_zoom.png plots (linear y, ratio 0.8-1.2).
- Pileup (4): brilcalc --byls: the 20-file EGamma lumisections have less high pileup than the full
  2022 C-D profile the MC is weighted to (EGamma/full 0.77 at PU 42-46, 0.41 at 46-50; Muon 1.04/0.86)
  -> likely the Zee N(PV) slope. Closure (MC reweighted per channel via pu_ntrue_npv): zbzc_pu_closure.py.
- 1-file regression (old 957d2d9 worktree vs new, same files): Zee 39 hists identical; muvar prev ==
  old Zmm exactly; muvar nominal == new main; met_nm1 < 50 == met_pt; pu_ntrue_npv total == npv.

## RESUME HERE (2026-11-05 evening): work on the slide contents of the b/c-tag deck

Deck: hists_zbzc_run3_tag/Summer22/slides_zbzc_tag_Summer22.pdf (237 pages, made by
make_zbzc_tag_slides_pdf.py; contents p. 2, intro p. 3-5, then 7 regions x (1 summary + 32 plots), summary p. 237).
Plan for tonight: go through the contents with the user and modify (text, order, which plots, parton plots?).
Rebuild: `python make_zbzc_tag_slides_pdf.py` (~45 s, no rerun needed; numbers on intro/section pages are typed
in the script from yields*.txt). Open items: SF up/down bands (needs rerun), other campaigns.

### How the Loose tagging is applied (what to say if asked)

Short: "Official BTV ParticleNet Loose working point for Summer22 on the leading jet; MC corrected with the BTV
fixed-working-point SFs for the jet's true flavour."

Details:
- Only the leading AK4 jet is tagged (pT > 30, |eta| < 2.5, tight ID, dR > 0.4 from the leptons).
- b-tag Loose: PNet B > 0.047. c-tag Loose: CvL > 0.054 and CvB > 0.181. Official Summer22 values, read at run
  time from the BTV correctionlib files (particleNet_wp_values in
  /cvmfs/cms-griddata.cern.ch/cat/metadata/BTV/Run3-22CDSep23-Summer22-NanoAODv12/latest/{b,c}tagging.json.gz),
  not chosen by us. Same for M and T. b-tag and c-tag are separate selections; a jet can pass both.
- Data: no correction. MC: tagged jet weighted by the BTV SF for its hadron flavour. b-tag: particleNet_comb
  (b, c), particleNet_light (udsg). c-tag: particleNet_wc (c), particleNet_tnp (b), particleNet_light (udsg).
- Only tagged events are plotted, so the event weight is just that jet's SF; no MC tagging-efficiency maps needed
  (those are only needed when jets that fail the tag are reweighted too).
- Jets outside the SF range: pT and |eta| clipped to the edge (c-tag SFs: |eta| < 2.4; pT < 200 c, < 300 b).
- Check that it works: tagged fraction data vs MC agrees within 1-2% (b-tag L, Zmm: 17.9% MC, 17.6% data).
- Uncertainties: NOT yet. Central SF only, stat. errors only. SF up/down is the next step.
- Why M and T too: Loose c-tag keeps 92% of light jets (not a charm selection); Medium ~20% c, Tight ~50% c.
- How BTV defines the WPs: b-tag L/M/T = ~10% / 1% / 0.1% light mistag (arXiv:2412.05863, 2608.18331).
  Our DY Z+jet (Zmm, SFs applied): light pass 11.4% / 1.3% / 0.27%, b pass 91% / 83% / 68%. c-tag WPs are points
  in the CvL-CvB plane; exact BTV targets NOT confirmed - don't claim them. Tight CvB (0.259) is looser than
  Medium (0.306), so c-tag Tight is not a subset of Medium. c-tag pass rates (b / c / light):
  L 27 / 96 / 92%, M 21 / 69 / 25%, T 17 / 45 / 3.3%.

## 2026-11-05: Summer22 kinematics with b- and c-tagged leading jet (advisor's request)

Advisor: all kinematic plots with the POG corrections and SFs, plus b-tagged and c-tagged versions.
Changes in Zb_Zc_ratio: JME MET filters added (were missing; remove 0.1-0.5% of events); Z pT
weights now OFF by default (not a POG correction, decision of 29 Oct); new "tag" axis on all
final-selection histograms and n_jet: incl, btag_<WP>, ctag_<WP> for WP = L, M, T (leading AK4
jet; PNet B > WP, or CvL > WP and CvB > WP; cuts from the BTV correctionlib files). MC tagged
events carry the BTV fixed-WP SF of the leading jet for its hadron flavour (btag: particleNet_comb
for b/c, particleNet_light for udsg; ctag: particleNet_wc c, particleNet_tnp b, particleNet_light
udsg; pT/|eta| clipped to the SF range). Only tagged events are plotted, so no MC efficiency maps.
Advisor asked for Loose; the test showed Loose c-tag ~ inclusive, so M and T are stored too (user).
Run: ZBZC_RUN=zbzc_run3_tag run_zbzc_run3.sh Summer22 mc|data (20 files/sample, 13:49-16:02, no
retries), postprocess_zbzc_tag.sh; plots ZBZC_TAG=<region> plot_zbzc_run3.py ->
hists_zbzc_run3_tag/Summer22/plots_<region>/, yields_<region>.txt (+ mean SF per flavour, overlap).
Data lumisections identical to the main run, so hists_zbzc_run3/Summer22/lumi.json is used.

Yields (DY flavour fractions are of the total MC; eff = region / inclusive):

| region | ch | MC | data | data/MC | DY+b | DY+c | DY+l | tt | eff MC | eff data |
|---|---|---|---|---|---|---|---|---|---|---|
| incl   | Zee | 19841 | 18833 | 0.949 +- 0.012 |  3.8% |  8.0% | 87.4% | 0.4% | 1     | 1     |
| incl   | Zmm | 67588 | 65259 | 0.966 +- 0.009 |  4.2% |  8.1% | 87.0% | 0.4% | 1     | 1     |
| btag_L | Zee |  3356 |  3179 | 0.947 +- 0.031 | 20.7% | 23.0% | 54.1% | 1.7% | 0.169 | 0.169 |
| btag_L | Zmm | 12076 | 11485 | 0.951 +- 0.021 | 21.5% | 20.9% | 55.6% | 1.6% | 0.179 | 0.176 |
| ctag_L | Zee | 17737 | 16523 | 0.932 +- 0.013 |  1.1% |  8.7% | 89.7% | 0.2% | 0.894 | 0.877 |
| ctag_L | Zmm | 60521 | 57554 | 0.951 +- 0.009 |  1.3% |  8.7% | 89.6% | 0.2% | 0.895 | 0.882 |
| btag_M | Zee |  1164 |  1117 | 0.960 +- 0.053 | 55.1% | 22.1% | 17.8% | 4.5% | 0.059 | 0.059 |
| btag_M | Zmm |  4040 |  3794 | 0.939 +- 0.036 | 59.0% | 16.9% | 19.4% | 4.3% | 0.060 | 0.058 |
| ctag_M | Zee |  5545 |  5203 | 0.938 +- 0.023 |  2.9% | 20.2% | 76.2% | 0.3% | 0.279 | 0.276 |
| ctag_M | Zmm | 19346 | 18394 | 0.951 +- 0.017 |  3.1% | 19.5% | 76.7% | 0.3% | 0.286 | 0.282 |
| btag_T | Zee |   640 |   643 | 1.004 +- 0.074 | 82.9% |  5.4% |  4.5% | 6.8% | 0.032 | 0.034 |
| btag_T | Zmm |  2370 |  2139 | 0.902 +- 0.045 | 82.0% |  4.8% |  6.7% | 6.1% | 0.035 | 0.033 |
| ctag_T | Zee |  1508 |  1381 | 0.916 +- 0.043 |  8.2% | 49.4% | 41.1% | 0.7% | 0.076 | 0.073 |
| ctag_T | Zmm |  4933 |  4579 | 0.928 +- 0.033 |  9.6% | 50.2% | 38.9% | 0.7% | 0.073 | 0.070 |

- Tagged fraction agrees between data and MC within ~1-2% (relative) in every region: the SFs work.
  ctag_L is 1-1.5% lower in data (0.877-0.882 vs 0.894-0.895).
- Inclusive data/MC dropped from 0.973 / 0.987 (b48a524, Z pT weights on) to 0.949 / 0.966: MC up
  by ~2.3% / 2.1% with the weights off (MET filters cut data and MC alike, 0.1-0.5%). Every tagged region sits at about that same level (stat. errors only, no SF uncertainties yet).
- Loose c-tag keeps ~89% of events and is ~90% light: not useful as a c selection. Medium c-tag gives
  ~20% DY+c, Tight ~50%. b-tag purity: L ~21%, M ~55-59%, T ~82% DY+b.
- Deck: hists_zbzc_run3_tag/Summer22/slides_zbzc_tag_Summer22.pdf (make_zbzc_tag_slides_pdf.py, 237 pages: intro,
  then all 32 plots per region full size, contents on p. 2; Z + >= 1 jet).
- Not done yet: SF up/down bands; other campaigns.

## 2026-11-02: Summer22 Z + exactly 1 jet vs Z + >= 1 jet (advisor's question)

Two Summer22 reruns, 10 GeV bins in z_pt / lep0_pt / lhe_vpt, Z pT weights still ON (decision below still
pending): `ZBZC_RUN=zbzc_run3_ge1j` (Zb_Zc_ratio) and `ZBZC_RUN=zbzc_run3_1j ZBZC_WF=Zb_Zc_ratio_1jet`
(new njet_exact=1 option). ~13:20 an LPC reboot killed both during TTto2L2Nu; resumed only TT/WW/WZ/ZZ with
resume_zbzc_njet_bkg.sh (NB: relaunch stall_watchdog_zbzc_run3.sh with the drivers on any resume).
ge1j yields.txt is identical to b48a524 Summer22. Postprocess: postprocess_zbzc_njet.sh.
Comparison: hists_zbzc_run3_1j/Summer22/compare_ge1j/ (compare_zbzc_njet_slope.py). The slope fit first used
data-based errors (e ~ r), which pulls the line towards downward-fluctuating low-count bins (Zee 1j lep1_pt
gave -42 %/100 GeV); fixed to expected errors sqrt(MC + var)/MC, empty data bins included as 0.
Slopes (%/100 GeV, ge1j -> 1j): Zmm z_pt +4.4+-1.3 -> +0.7+-1.7, lep0 +6.2+-2.2 -> +2.5+-3.0,
lep1 +20.5+-5.5 -> +1.3+-7.6; Zee z_pt +4.8+-2.0 -> +3.0+-2.7, lep0 +9.7+-3.5 -> +9.1+-4.8.
=> muons: slope consistent with zero in Z + 1 jet (comes from N_jet >= 2 events); electrons: no clear change,
1j errors larger. 1j is ~80% of ge1j, so the two are strongly correlated. Eta-phi by N_jet:
hists_zbzc_run3_ge1j/Summer22/etaphi_nj_summary.txt, chi2/ndf ~1 in every map (the summary only lists cells
beyond 3 sigma, which hid this:) two cells are low in BOTH the 1-jet and the 2-jet maps (disjoint events):
Zee eta 0-0.5, phi 1.26-1.88: 0.82+-0.07 (1j), 0.61+-0.10 (2j); Zmm eta 0.5-1.0, phi -3.14..-2.51: 0.90+-0.06,
0.65+-0.08. >= 3 jets data/MC ~0.79-0.80 (MC too high).
Deck: hists_zbzc_run3_1j/Summer22/slides_zbzc_njet_Summer22.pdf (make_zbzc_njet_slides_pdf.py, 9 pages).

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
