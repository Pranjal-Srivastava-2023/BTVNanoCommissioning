# Session notes: QCD_sf boosted Zbb — LPC condor scale-up

Working with senior postdoc Hsin-Wei Hsia (GitHub: hsinweihsia) on her
boosted Z(bb)+jet analysis, `QCD_sf` workflow, built on BTVNanoCommissioning.

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
