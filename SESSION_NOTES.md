# Session notes: QCD_sf boosted Zbb — LPC condor scale-up

Working with senior postdoc Hsin-Wei Hsia (GitHub: hsinweihsia) on her
boosted Z(bb)+jet analysis, `QCD_sf` workflow, built on BTVNanoCommissioning.

## STATUS AS OF 2026-08-31, READ THIS FIRST

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
