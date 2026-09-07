# Concepts

Running notes explaining *how* pieces of this workflow actually work, for
personal reference. Written up as questions get asked during development,
newest entry at the bottom. These are explanations of mechanics, not status
updates — see `SESSION_NOTES.md` for what happened and when.

---

## How does the code know how to calculate softdrop mass (and similar jet variables)?

Short answer: **it doesn't calculate it** — softdrop mass is read directly
from a branch that's already in the NanoAOD file, computed centrally by CMS
during official NanoAOD production (the soft-drop grooming algorithm runs
upstream, long before this analysis code ever touches the file). Same story
for `pt`, `eta`, `phi`, `n2b1`, the ParticleNetMD/DeepTagMD tagger scores,
and `btagDDBvLV2` — all pre-computed branches on the NanoAOD `FatJet`
collection, just being *read*, not calculated.

A couple of variables genuinely **are** computed by our own code:
`tau21`/`tau32`. In
[`QCD_validation.py:480-487`](src/BTVNanoCommissioning/workflows/QCD_validation.py#L480-L487):
```python
pruned_ev["SelJet", "tau21"] = ak.where(
    pruned_ev.SelJet.tau1 > 0,
    pruned_ev.SelJet.tau2 / pruned_ev.SelJet.tau1,
    ...
)
```
`tau1`/`tau2`/`tau3` themselves *are* raw NanoAOD branches (N-subjettiness
values from central production) — we just take the ratio.

### Two separate concerns: booking vs. filling

- **Booking** (bin edges/ranges) happens in
  [`utils/histogramming/histograms/qcd.py`](src/BTVNanoCommissioning/utils/histogramming/histograms/qcd.py).
  This only defines the empty histogram shape — it doesn't touch any actual
  event data.
- **Filling** (putting real numbers into those bins) happens generically in
  [`histo_writter` in `histogrammer.py`](src/BTVNanoCommissioning/utils/histogramming/histogrammer.py#L271-L296).
  It loops over every booked histogram name and, for anything containing
  `"jet"`, does:
  ```python
  h.fill(syst, flatten(flav), flatten(sel_jet[histname.replace(f"jet{i}_", "")]), weight=weight)
  ```
  For `histname = "jet0_msoftdrop"`, this strips the `"jet0_"` prefix,
  leaving `"msoftdrop"`, and does `sel_jet["msoftdrop"]` — i.e. it looks up
  a field on `pruned_ev.SelJet` (the selected leading AK8 jet, sliced from
  `events.FatJet` in
  [`QCD_validation.py:477`](src/BTVNanoCommissioning/workflows/QCD_validation.py#L477))
  by that exact string. `SelJet` is just a slice of the original `FatJet`
  collection, so it carries every original NanoAOD branch along with it —
  that's why `sel_jet["msoftdrop"]` just works with no extra code needed.

**Why this matters practically**: the naming convention `jet0_<fieldname>`
isn't cosmetic — it's literally how the generic dispatcher knows which
NanoAOD (or derived) field to pull for a given histogram. A histogram in
`qcd.py` has to be named exactly `jet0_msoftdrop`, `jet0_tau21`, etc. for
this to work; rename the key and the dispatcher no longer finds a matching
field, and it silently won't get filled.

---

## What did we actually do to get the full 16-dataset run finished? (summary for Hsin-Wei, 2026-09-07)

This is a status summary rather than a mechanics explanation (normally
that belongs in `SESSION_NOTES.md`), kept here as the one-stop writeup to
share externally.

**1. Restructured the submission to be resilient (Hsin-Wei's suggestion)**
- Split the single combined 16-dataset condor job into 16 independent
  per-dataset jobs, using `runner.py`'s existing `--only <dataset>` flag —
  no new metadata files needed, since it filters the existing combined
  JSON before validation touches any files.
- Added two small scripts to the repo: `submit_qcd_sf_per_dataset.sh`
  (sequential per-dataset submission) and `merge_qcd_sf_outputs.py`
  (recombines the per-dataset outputs into one file, safe merge since
  each dataset is a disjoint key).
- Result: **13 of 14** remaining datasets succeeded cleanly on the first
  pass. 3 (`DYJetsToLL_0J`, `DYJetsToLL_1J`, `TTToSemiLeptonic`) hit the
  same dask/lpcjobqueue deadlock seen before — but this time it was
  isolated to just those jobs and didn't affect anything else. All 3
  succeeded on a simple retry.

**2. Key new finding: the deadlock isn't scale-related**
- Previously assumed the earlier deadlock was tied to running all 16
  datasets together in one huge job.
- It recurred on single, isolated dataset jobs too — so it's some kind of
  dask/lpcjobqueue-level issue independent of job size. Root cause still
  unknown (no dashboards were ever enabled to see why it freezes).

**3. All 16 datasets now complete and merged**
- Final combined output: 16/16 dataset keys, all with sensible
  non-trivial statistics (from `ZZ` at 3.2M raw events up to
  `EGamma_Run2018` at 1.38B raw events).
- Full cutflow (general + Zee-specific + Zmm-specific chains, per
  dataset) is saved to `cutflow_full_16dataset_run.log` in the repo.

**4. Regenerated plots — three deliverables**
- `plot_stack_sample.py` — targeted Z-mass, jet pT, and Xbb-score
  stacked plots, `Z_jet` (inclusive) vs `Z_bjet` (b-tagged) side by
  side.
- `plot_full_overview.py` (new) — a 15-panel grid covering all the key
  kinematic/substructure variables, xsec-scaled and stacked by physics
  process (DY+jets/ttbar/single top/diboson/ZH), with data overlay.
- All plots switched to **log-scale y-axis** — linear scale was hiding
  ttbar/single-top/diboson/ZH almost completely under DY+jets; log-scale
  shows all of them clearly, including in the b-tagged region where they
  become much more comparable to DY.
- Cropped x-axis ranges to where events actually populate (e.g. `m_ll`
  to 70-110 GeV, jet pT starting at the real 200 GeV cut) — removes
  blank padding that was showing up as odd hatched bars.

**5. Confirmed `Z_bjet` is a real b-tagged region**
- `pnet_leading >= 0.9172` (ParticleNetMD Xbb-vs-QCD "loose" WP for
  2018-UL, sourced from Hsin-Wei's old ROOT workflow's config) —
  genuinely tagger-selected, not just a label.
- Found and fixed a double-counting bug: the overview grid was summing
  `Z_jet + Z_bjet` together for most variables, but `Z_bjet` is a
  *subset* of `Z_jet`, not a separate category — so b-tagged events were
  being counted twice. Fixed; verified numerically (the correction
  matched the independently-computed `Z_bjet`-only yield exactly).

**6. Important open issue: no scale factors are applied anywhere in `QCD_sf`**
- Found the root cause of MC running ~16% high vs. data overall:
  `QCD_validation.py:83` has `self.SF_map = load_SF(...)`
  **commented out**. This means every MC event's weight is just raw
  `genWeight` — no pileup reweighting, no muon/electron
  ID-iso-trigger SFs, no b-tagging SFs, and no golden-JSON/certified-lumi
  filtering on data either.
- The framework already has all of these (`puwei`, `muSFs`, `eleSFs`,
  `btagSFs`) fully implemented — they're just not wired into this
  specific workflow.
- This is especially relevant for the `Z_bjet` plots, since the missing
  b-tag SF is an extra normalization gap on top of the general one.
- **Not fixed yet** — flagged as a decision that should go through
  Hsin-Wei first, since it changes the physics normalization.

**7. Further plot refinements (same day, after the above)**
- Cropped every plot's x-axis range to where events actually populate
  (measured directly against the merged output) — several histogram
  axes were defined wider than the selection populates, showing as
  blank hatched padding at the edges.
- Found and fixed a `region`-axis double-counting bug in
  `plot_full_overview.py`: it was summing `Z_jet + Z_bjet` together for
  most variables, but `Z_bjet` is a strict *subset* of `Z_jet`, not a
  separate category, so b-tagged events were being counted twice.
  Verified the fix numerically.
- **Added a Data/MC ratio panel below every stacked plot**, in both
  plotting scripts. Matches the old ROOT-based `ZbAnalysis_boosted`
  analysis's own convention (checked its saved canvas macros directly):
  70/30 top/bottom split, black error-bar ratio markers, horizontal
  line at 1, "Data/MC" y-axis label. The ratio panels make the
  missing-SF normalization gap (item 6 above) directly visible as a
  systematic offset in almost every panel.

**8. Everything is committed and pushed**
- All code, session notes, and plots are on `myfork/coffea_machine`
  (9 commits: `5037179` → `a953577`).
- One caveat: the actual `.coffea` histogram output files (16 individual
  + 1 merged, 12MB total) are excluded from git by this repo's existing
  conventions (`*.coffea`/`hists_*` in `.gitignore`), so they currently
  only exist on local LPC disk — not shared automatically.
