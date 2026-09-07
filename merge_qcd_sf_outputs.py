"""Merge per-dataset QCD_sf .coffea outputs into one combined file.

Each `runner.py --only <dataset>` run writes a `{dataset: {histograms...}}`
dict to its own file. Since no dataset key appears in more than one file,
combining is a plain dict union -- no bin-level histogram addition needed.
"""
import argparse
import glob

from coffea.util import load, save

DEFAULT_PATTERNS = [
    "hists_QCD_sf_QCD_sf_run2018_all/hists_QCD_sf_QCD_sf_run2018_all_*.coffea",
    "hists_DY2J_condor_rebin/hists_QCD_sf_QCD_sf_run2018_DY2J/hists_QCD_sf_QCD_sf_run2018_DY2J.coffea",
]
DEFAULT_OUTPUT = "hists_QCD_sf_QCD_sf_run2018_all/hists_QCD_sf_QCD_sf_run2018_all.coffea"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--pattern",
        action="append",
        default=None,
        help="Glob pattern for input .coffea files; may be given multiple times. "
        "Defaults to the per-dataset split outputs plus the DY2J validation output.",
    )
    args = parser.parse_args()
    patterns = args.pattern or DEFAULT_PATTERNS

    files = []
    for pattern in patterns:
        files.extend(sorted(glob.glob(pattern)))
    if not files:
        raise SystemExit(f"No input files matched patterns: {patterns}")

    merged = {}
    for f in files:
        out = load(f)
        overlap = set(out) & set(merged)
        if overlap:
            raise SystemExit(f"Dataset key(s) {overlap} appear in more than one input file "
                              f"(offending file: {f}) -- refusing to merge, check for a "
                              f"duplicate/re-submitted run.")
        merged.update(out)
        print(f"{f}: {list(out.keys())}")

    print(f"\nMerged {len(files)} file(s) into {len(merged)} dataset key(s):")
    for k in merged:
        print(f"  {k}")

    save(merged, args.output)
    print(f"\nSaved combined output to {args.output}")
