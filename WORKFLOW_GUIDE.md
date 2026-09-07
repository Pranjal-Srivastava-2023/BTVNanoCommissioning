# QCD_sf Boosted Z(bb) Workflow — Setup & Usage Guide

This documents the current state of the boosted Z(bb)+jet (`QCD_sf`) analysis
setup on this branch: what was broken and fixed, and how to run the workflow
both interactively and at scale on LPC HTCondor.

## 1. Background

This is a boosted Z(bb)+jet commissioning analysis built on
[BTVNanoCommissioning](https://github.com/cms-btv-pog/BTVNanoCommissioning),
developed by Hsin-Wei Hsia (GitHub: `hsinweihsia`). It selects AK8 `FatJet`
candidates plus a Zee or Zmm dilepton candidate, requiring at least one
subjet pair on the jet (a "boosted" Z+jet topology, as opposed to the
resolved AK4 dijet case).

The workflow is called `QCD_sf` on the command line and maps to the
`NanoProcessor` class in
[`src/BTVNanoCommissioning/workflows/QCD_validation.py`](src/BTVNanoCommissioning/workflows/QCD_validation.py)
(see the mapping in `workflows/__init__.py`).

## 2. Repository layout

- `origin` → official upstream, `cms-btv-pog/BTVNanoCommissioning`, branch `master` — not touched by this work.
- `hsinwei` → Hsin-Wei's fork `hsinweihsia/ZbAnalysis_boosted`, branch `coffea_machine` — the branch this work builds on.
- This fork's `coffea_machine` branch — a personal copy pushed here for visibility/review; not (yet) merged back anywhere.

## 3. Environment (interactive / local running)

For running directly on an LPC interactive node (no batch system), there is a
conda/micromamba environment already set up with the pinned dependency
versions this repo needs (`coffea==0.7.31`, `correctionlib==2.7.0`, etc., see
`setup.cfg`). Activate it and install the repo in editable mode:

```bash
source <path-to-your-conda>/bin/activate <your-env-name>
cd BTVNanoCommissioning
pip install -e .
```

Reference command (validated to reproduce a known-good cutflow exactly):

```bash
python runner.py --workflow QCD_sf --json metadata/test_Zb.json \
  --campaign 2018-UL --year 2018 --executor iterative --overwrite --noHist
```

`metadata/test_Zb.json` is a minimal one-dataset, one-file fileset used for
fast local testing. `--noHist` skips histogram filling and just runs the
cutflow (useful for quickly checking selection logic via the `print()`
statements in the processor).

## 4. What was fixed in this branch

Histograms had never actually been run before (all prior testing used
`--noHist`, which masked that the histogram path was fully broken). Three
things were fixed:

1. **`QCD_validation.py`** — built a proper `pruned_ev` for the array/histogram
   writer (previously undefined — this was a latent `NameError`). It now
   attaches `SelJet` from `events.FatJet` (previously incorrectly pulled from
   `events.Jet`, the AK4 collection), `njet`, derived `tau21`/`tau32`, and a
   merged per-event `dilep` candidate (whichever of Zee/Zmm fired).
2. **`utils/histogramming/histogrammer.py`** (shared framework file, affects
   *all* workflows) — `histo_writter` unconditionally read
   `SelJet.partonFlavour`, which AK4 jets have but AK8 `FatJet` does not. This
   would crash any boosted-jet workflow. Now falls back to `hadronFlavour`
   alone when `partonFlavour` isn't present.
3. **`utils/histogramming/histograms/qcd.py`** — was a stub (`return {}`).
   Populated with boosted Z→bb variables confirmed to exist in the sample's
   actual `FatJet` branches: `msoftdrop`, `tau21`/`tau32` (derived), `n2b1`,
   `deepTagMD_ZbbvsQCD`, `particleNetMD_Xbb`/`particleNetMD_QCD`,
   `btagDDBvLV2`, plus `dilep_mass` (the framework's generic 4-vector code
   doesn't auto-produce `_mass` for non-jet objects like the merged `dilep`
   candidate, so it's added explicitly).

Cutflow `print()` statements were also added for the jet-selection, Zee, and
Zmm stages, layered on top of the electron/muon cutflow print that already
existed, to make the selection logic easier to follow when running with
`--executor iterative`.

**Known bug, not fixed (flag to Hsin-Wei):** in `QCD_validation.py`, the Zmm
mass window cut reads:

```python
req_Zmm_mass = ak.fill_none((Zmm_mass >= 71) & (Zee_mass <= 111), False)
```

This compares against `Zee_mass` instead of `Zmm_mass` for the upper bound
(looks like a copy-paste slip), which makes the Zmm channel yield exactly 0
selected events in the test sample. This is a selection-logic call left for
Hsin-Wei to decide on, not fixed as part of this work.

## 5. Running at scale on LPC HTCondor (`dask/lpc`)

`runner.py` already supports several batch/distributed executors out of the
box (see `--executor` choices in `scaleout_parser`), including `dask/lpc` —
a custom executor for LPC's HTCondor pool built on
[CoffeaTeam/lpcjobqueue](https://github.com/CoffeaTeam/lpcjobqueue). This was
never actually exercised on this branch before; this section documents how it
was set up and validated.

### 5.1 What lpcjobqueue is and why it's needed

`lpcjobqueue` is a `dask-jobqueue` plugin providing `LPCCondorCluster`, used
in `runner.py`'s `dask/lpc` branch. It handles LPC-specific restrictions:
worker nodes can't share your home directory or install packages themselves,
so instead of a normal shared-filesystem setup, it:

- Ships your Python virtualenv to each condor job (`ship_env=True`).
- Ships your source tree via `transfer_input_files`.
- Runs each condor job inside the same Apptainer/Singularity image you
  develop in, with HTCondor's own Singularity support auto-binding each
  job's scratch directory to `/srv` inside the container — the same
  convention used for your own interactive container session, so absolute
  paths like `/srv/.env` and `/srv/src` resolve identically on the submit
  side and on every worker.

This container-based approach is separate from (and does not replace) the
`zbb-btv` conda env used for interactive/local running in Section 3 — the two
are independent environments for two different execution modes.

### 5.2 One-time setup (already done in this branch, regenerate if needed)

These files were generated by `lpcjobqueue`'s own `bootstrap.sh` and are
already committed at the repo root: `bootstrap.sh`, `shell`, `.bashrc`,
`.cmslpc-local-conf`. If you ever need to regenerate them from scratch:

```bash
curl -sL -O https://raw.githubusercontent.com/CoffeaTeam/lpcjobqueue/main/bootstrap.sh
bash bootstrap.sh
```

This writes `shell` (the Apptainer container launcher) and `.bashrc` (sets up
a lightweight virtualenv at `.env/` on first use). `.env/` is **not**
committed to git — it's a generated, regenerable virtualenv (~5 MB of
symlinks/site-packages), listed in `.gitignore` alongside `.local/` (an
auto-generated Jupyter kernelspec, harmless but also not meant to be
versioned).

### 5.3 Entering the container and installing the analysis package

```bash
cd BTVNanoCommissioning
./shell coffeateam/coffea-base-almalinux8:0.7.30-py3.10
```

This pulls the specified image from CVMFS and drops you into a shell with
the repo root bind-mounted at `/srv`. **Image choice matters**: this repo
pins `coffea==0.7.31` exactly, but `setup.cfg` also requires
`python_requires = <3.11`. The only `0.7.31` prebuilt image available is
`py3.11`, which is incompatible with that constraint — so use the closest
`py3.10` image (`0.7.30-py3.10` above) and let `pip` upgrade coffea to
`0.7.31` inside the venv; it's a pure-Python bump and works cleanly on top of
that image.

On first entry, `.bashrc` auto-creates `.env/` and installs `lpcjobqueue`
into it. You then need to install this repo's own package into that same
venv:

```bash
/srv/.env/bin/python -m pip install -e . -q
```

**Important — use the explicit path, not the bare `pip` command.** The
`.bashrc` defines `alias pip="python -m pip"`, but bash aliases only expand
in *interactive* shells. If you pipe commands into `./shell` non-interactively
(e.g. via a heredoc for scripting/automation), the alias silently doesn't
expand, and a bare `pip install -e .` falls through to a different `pip` on
`$PATH` — typically the container's system pip, which (since the real system
site-packages aren't writable) silently falls back to installing into your
**host home directory** (`~/.local/lib/python3.X/site-packages`) instead of
`.env/`. This is a real trap: the install appears to succeed with no error,
`import BTVNanoCommissioning` even works locally (since `~/.local` is on
Python's default search path), but the analysis package is now invisible to
`ship_env` (which only ships `.env/`), so every condor worker fails with
`ModuleNotFoundError: No module named 'BTVNanoCommissioning'`. It's also a
latent hazard for any *other* Python environment on the same account, since
`~/.local` is picked up by any interpreter with `site.ENABLE_USER_SITE=True`
(e.g. a conda env) unless it happens to already provide the same module
itself. If this happens, `rm -rf ~/.local` and reinstall using the full path
above.

Verify the install landed in the right place:

```bash
find /srv/.env/lib/python3.10/site-packages -maxdepth 1 -iname "*BTVNano*"
/srv/.env/bin/python -c "import BTVNanoCommissioning, lpcjobqueue; print('ok')"
```

### 5.4 Grid proxy

`LPCCondorCluster` needs a valid VOMS proxy to read files over xrootd and to
authenticate job submission:

```bash
voms-proxy-init --voms cms --valid 192:00
voms-proxy-info -all   # check timeleft
```

### 5.5 Submitting a job

From inside the container shell, with the venv installed as above:

```bash
cd /srv
python runner.py --workflow QCD_sf --json metadata/test_Zb.json \
  --campaign 2018-UL --year 2018 --executor dask/lpc \
  --scaleout 1 --overwrite
```

- `--scaleout N` is the minimum number of condor worker jobs `dask` will keep
  running (`cluster.adapt(minimum=args.scaleout)` in `runner.py`); it will
  scale up further under load.
- The command blocks on `"Waiting for at least one worker..."` until
  HTCondor actually schedules and starts a worker — this can take anywhere
  from under a minute to several minutes depending on pool load and image
  pull time. This is normal.
- **Cutflow `print()` statements do not appear in this log.** Under
  `--executor iterative`, everything runs in your own process, so `print()`
  inside the processor shows up directly. Under `dask/lpc`, the actual
  per-chunk processing happens on remote condor workers — their stdout goes
  to each worker's own condor log in its scratch directory on the schedd, not
  back to your terminal. Use `--executor iterative` (with `--limit` to keep
  it fast) for interactively debugging selection logic, and `dask/lpc` for
  unattended bulk histogram production.

This was validated end-to-end with a real single-dataset submission: a
condor worker started, imported the shipped package successfully, and
completed the full dataset with exit code 0.

## 6. Scaling to multiple datasets

`metadata/test_Zb.json` only contains one sample with one file — it's a
minimal smoke-test fileset, not the production dataset list. The JSON schema
is simple:

```json
{
  "SampleName1": ["root://.../file1.root", "root://.../file2.root", ...],
  "SampleName2": ["root://.../file1.root", ...]
}
```

To run this workflow on the real analysis samples, build a metadata JSON
listing every dataset and its constituent files (e.g. via a DAS query or
whatever fileset-building convention Hsin-Wei's analysis already uses
elsewhere in this repo's `metadata/` directory), then point `--json` at it
and drop `--limit`. Everything else about the `dask/lpc` invocation in
Section 5.5 stays the same — the executor and scaling machinery don't care
how many datasets/files are in the JSON, only the `--scaleout` value you
choose for how many parallel condor workers to use.

`metadata/QCD_sf_run2018_all.json` is exactly this for the full 2018 UL
dataset list — **16 datasets, 2324 files** (14 MC + `EGamma_Run2018` +
`SingleMuon_Run2018`; an earlier draft of this guide said 21/2826, which
was stale/wrong), built by `scripts/build_2018_metadata.py` from
Hsin-Wei's `FileLists_NanoUL` text files.

**Status as of 2026-09-07: this has been run at full scale, successfully,
for every dataset.** See Section 6.1 below for how, and `SESSION_NOTES.md`
/ `concept.md` for the full narrative. `--json metadata/QCD_sf_run2018_all.json`
with `--only <dataset>` (not a bare full-JSON submission — see 6.1) is now
the validated way to reproduce this.

### 6.1 Per-dataset submission (the resilient way to run this at scale)

The first attempts at running all 16 datasets submitted them as a single
combined `dask/lpc` job (`--json metadata/QCD_sf_run2018_all.json` with no
`--only`). This works, but is fragile: dask/lpcjobqueue has a recurring
deadlock (cluster and all workers simultaneously freeze at ~99% complete,
cause still unknown — no dashboard was ever enabled to diagnose it further)
that, in a combined run, wipes out the *entire* multi-hour job when it hits,
since coffea's accumulator only writes output once every task in the graph
reports done — there's no partial-result recovery.

Following a suggestion from Hsin-Wei, the fix isn't to avoid the deadlock
(root cause still unknown) but to shrink its blast radius: submit each
dataset as its own **independent** job, using the `--only <dataset>` flag
`runner.py` already has (`runner.py:373` — filters `sample_dict` down to one
dataset *before* validation touches any files, so it's a fully isolated run,
own dask cluster, own condor jobs, own output file). No new metadata JSON
files needed.

```bash
python -u runner.py --workflow QCD_sf \
  --json metadata/QCD_sf_run2018_all.json \
  --campaign 2018-UL --year 2018 \
  --executor dask/lpc --scaleout 8 \
  --only <dataset-name> --skipbadfiles --overwrite
```

Two helper scripts (repo root) wrap this:
- **`submit_qcd_sf_per_dataset.sh`** — loops over dataset keys sequentially,
  one `--only` job at a time, logging each to `logs_qcd_sf_split/<dataset>.log`
  and a running `logs_qcd_sf_split/summary.log`. On a hang, kill the current
  job (`SIGINT` — tears the cluster down cleanly, confirmed via `condor_q`)
  and either let the loop continue to the next dataset or retry the killed
  one on its own; either way, no other dataset's job is affected.
- **`merge_qcd_sf_outputs.py`** — combines the per-dataset `.coffea` outputs
  back into the single file `plot_stack_sample.py`/`plot_full_overview.py`
  expect (`hists_QCD_sf_QCD_sf_run2018_all/hists_QCD_sf_QCD_sf_run2018_all.coffea`).
  Safe as a plain dict union (asserted, not just assumed): each dataset is
  its own disjoint top-level key in the workflow's output
  (`{dataset: {histograms...}}`), so no bin-level histogram addition is
  needed and no double-counting risk exists as long as each dataset's file
  is only merged once.

**Result of the actual full run** (2026-09-06/07): 13 of 16 datasets
succeeded cleanly on the first `--only` submission. 3
(`DYJetsToLL_0J`, `DYJetsToLL_1J`, `TTToSemiLeptonic`) hit the deadlock —
confirmed via the same method as the original combined-run deadlock
(`condor_ssh_to_job` into a worker, compare CPU time before/after a short
wait — identical means genuinely frozen, not just slow), killed cleanly,
retried individually, all 3 succeeded on retry (10-76 minutes each). Total
wall time for the full 16-dataset run: roughly 9 hours across two
sequential submission passes, almost entirely condor-queue/processing time
rather than debugging. **New finding from this run**: the deadlock is not
tied to combined-run scale — it recurred on single, isolated dataset jobs
too, so whatever causes it is a dask/lpcjobqueue-level issue independent of
job size. Root cause is still unknown.

## 7. Comparison histograms (old ROOT workflow vs. this one)

Hsin-Wei's original analysis (before this coffea port) was a C++/ROOT
framework at `ZbAnalysis_boosted` (`src/Plots.cxx`, `src/ZbSelection.cxx`),
producing a fixed set of control plots per lepton channel (Zee/Zmm) and jet
category (inclusive vs. b-tagged). To let the two workflows be compared
directly, this branch reproduces the same 18 variables as coffea histograms,
prefixed `cmp_` and added in
[`utils/histogramming/histograms/qcd.py`](src/BTVNanoCommissioning/utils/histogramming/histograms/qcd.py),
filled by `fill_comparison_hists()` in
[`workflows/QCD_validation.py`](src/BTVNanoCommissioning/workflows/QCD_validation.py):

| Histogram | Meaning |
|---|---|
| `cmp_pt_lep0` / `cmp_eta_lep0` | Leading lepton of whichever Z candidate fired |
| `cmp_pt_lep1` / `cmp_eta_lep1` | Subleading lepton |
| `cmp_mass_zcand` | Dilepton (Z candidate) mass, full 0–300 GeV range |
| `cmp_pt_zcand` | Dilepton pt |
| `cmp_pt_fj` / `cmp_eta_fj` | Leading AK8 jet kinematics |
| `cmp_n_fj` | AK8 jet multiplicity |
| `cmp_pt_sub0/1`, `cmp_eta_sub0/1`, `cmp_phi_sub0/1`, `cmp_mass_sub0/1` | The two subjets of the leading AK8 jet, via coffea's built-in `FatJet.subjets` cross-reference |
| `cmp_dr_subjets` | ΔR between the two subjets |

**Region axis instead of separate histogram sets.** The old workflow produced
entirely separate histograms per jet category (`*_Z_jet` vs. `*_Z_bjet`
files). Here, every `cmp_*` histogram instead carries a `region` axis with
two values:
- `"Z_jet"` — all selected events, no b-tag requirement (filled always)
- `"Z_bjet"` — the same events, additionally passing the "loose" ParticleNetMD
  Xbb-vs-QCD working point on the leading jet:
  `particleNetMD_Xbb / (particleNetMD_Xbb + particleNetMD_QCD) >= 0.9172`
  (the 2018 value from the old workflow's `Configs/inputParameters.txt`;
  other years' values are in `pnet_loose_wp` in `QCD_validation.py`)

Slice either region out of a saved `.coffea` file with
`h[{"region": "Z_jet"}]` / `h[{"region": "Z_bjet"}]`.

These are filled by a dedicated method rather than through the shared
`histo_writter` dispatcher in `utils/histogramming/histogrammer.py`, since
that dispatcher has no concept of a region axis and is shared across every
workflow in the repo — adding region-axis support there would risk changing
behavior for other analyses. `cmp_*` names were deliberately chosen to avoid
substrings (`jet`, `dilep`, `btag`, ...) that dispatcher matches on, so it
passes over them as a no-op instead of misfiring.

**One correctness fix vs. the old code, not a reproduction of it:** `Plots.cxx`
has a bug where `phi_sub0`/`eta_sub0` (and the `sub1` equivalents) are filled
with each other's values swapped
(`h_phi_sub0->Fill(SubJ1.m_lvec.Eta(), w)`, `h_eta_sub0->Fill(SubJ1.m_lvec.Phi(), w)`
— lines 338–339 of `Plots.cxx`). `cmp_phi_sub0`/`cmp_eta_sub0` here are filled
correctly. Worth flagging to Hsin-Wei, since it means the old workflow's
"phi_sub0" plots are actually showing eta, and vice versa.

## 8. Plotting and known analysis-level issues

Three plotting scripts (repo root), all pointed at the merged combined
output and needing no arguments:

- **`plot_stack_sample.py`** — targeted plots: Z-candidate mass (`Z_jet` vs
  `Z_bjet` side by side, and separately split by Zee/Zmm channel), leading
  AK8 jet pT, ParticleNetMD Xbb score.
- **`plot_full_overview.py`** — a 15-panel grid covering every key
  kinematic/substructure variable (masses, pTs, tau21/tau32/N2, ΔR between
  subjets, η, jet multiplicity), same xsec-scaling/grouping treatment.
- Both stack by physics-process group (`DY+jets`/`ttbar`/`Single top`/
  `Diboson`/`ZH`, xsec × luminosity / `sumw` scaled) with a `Data` overlay
  (`EGamma_Run2018` + `SingleMuon_Run2018`, unscaled).

**Standing style conventions for these scripts** (established 2026-09-07,
keep going forward, don't revert):
- **Log-scale y-axis** on every panel — linear scale hid the sub-dominant
  backgrounds almost completely under DY+jets.
- **x-axis cropped to the actually-populated range** per histogram (e.g.
  `m_ll` to 70–110 GeV, jet pT starting at the real 200 GeV cut) rather than
  each histogram's wider default axis definition — avoids blank
  zero-content padding.
- **A Data/MC ratio sub-panel below every stack** (70/30 height split,
  black error-bar markers, horizontal line at 1, y-axis labeled
  "Data/MC") — matches the convention used by the old ROOT-based
  `ZbAnalysis_boosted` analysis's own plots (confirmed by inspecting its
  saved `TCanvas` macros, e.g.
  `SubmitToCondor/condor_output_mSD/*/*.C`). Implemented via nested
  matplotlib `GridSpec`s (`outer_cell.subgridspec(2, 1, height_ratios=[3,
  1])`) rather than a single `Axes` per panel; ratio uncertainty combines
  data and MC statistical uncertainty in quadrature via each histogram's
  tracked `.variances()`.
- The `region` axis on `cmp_*` histograms must be **selected**
  (`region="Z_jet"`), never **summed** — `Z_bjet` is a strict *subset* of
  `Z_jet` (same events plus the tag requirement), not an exclusive
  category, so summing both double-counts every b-tagged event. (This was
  a real bug in an early version of `plot_full_overview.py`, since fixed.)

**Known open issue: no scale factors are applied anywhere in `QCD_sf`.**
`QCD_validation.py:83` has `self.SF_map = load_SF(...)` **commented out**,
so `weight_manager()` (`utils/correction.py:3924`) receives `SF_map=None`
and returns immediately after adding only `genWeight` to every MC event's
weight. Concretely disabled: pileup reweighting, muon/electron
ID-iso-trigger SFs, b-tagging SFs — all fully implemented elsewhere in the
framework (`puwei`, `muSFs`, `eleSFs`, `btagSFs`), just not wired into this
workflow. No golden-JSON/certified-lumi mask is applied to data either.
This is the concrete root cause of the ~16% MC-over-data normalization gap
found when comparing scaled yields, and shows up clearly as a systematic
offset in every Data/MC ratio panel. Top-pT reweighting for `ttbar` is only
partially applied — folded into the `sumw` normalization denominator
(`utils/correction.py:3975`), not into the actual per-event histogram-fill
weight. **Not fixed** — flagged as a decision for Hsin-Wei, since it
changes the physics normalization; would also need confirming the 2018-UL
correction JSONs exist before enabling.

## 9. Files added by this setup

| File | Purpose |
|---|---|
| `bootstrap.sh` | Upstream lpcjobqueue script that generates `shell`/`.bashrc`/`.cmslpc-local-conf` |
| `shell` | Launches the Apptainer container with the repo bind-mounted at `/srv` |
| `.bashrc` | Container shell rc file; creates/activates `.env/` on first use |
| `.cmslpc-local-conf` | Helper used by the container bind-mount config for local condor config discovery |
| `.env/` (gitignored) | Generated virtualenv — `lpcjobqueue` + this repo, editable-installed |
| `SESSION_NOTES.md` | Narrative notes from the histogram-fix session and the full-scale run |
| `concept.md` | Mechanics explainers (how variables get filled, etc.) plus a status summary for sharing with Hsin-Wei |
| `submit_qcd_sf_per_dataset.sh` | Sequential per-dataset `--only` submission wrapper (see Section 6.1) |
| `merge_qcd_sf_outputs.py` | Combines per-dataset `.coffea` outputs into the single merged file the plotting scripts expect |
| `plot_stack_sample.py`, `plot_full_overview.py` | The two plotting scripts described in Section 8 |
| `cutflow_full_16dataset_run.log` | Full cutflow (general + Zee + Zmm chains) dumped from the merged `.coffea` output, all 16 datasets |
| `fix_qcd_histograms.patch` | `git diff` of the histogram fix, for sharing outside this fork if needed |
| `output.log`, `output_with_hist.log` | Cutflow logs from `--executor iterative` runs (before/after histogram fix) |
| `plot_hists.py`, `qcd_hists_overview.png` | Quick-look plot of the filled histograms and the script that made it (early, single-sample; superseded by Section 8's scripts for the full run) |

**Note on `.coffea` output files**: the actual histogram data
(`hists_QCD_sf_QCD_sf_run2018_all/`, 16 individual + 1 merged file, 12MB
total) is **not** committed — excluded by this repo's existing
`.gitignore` rules (`*.coffea`, `hists_*`). It currently exists only on
local LPC `nobackup` disk. Regenerate the merge anytime with
`python3 merge_qcd_sf_outputs.py` as long as the per-dataset outputs are
still present; re-running the full per-dataset submission from scratch
(Section 6.1) is the fallback if they aren't.
