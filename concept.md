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
