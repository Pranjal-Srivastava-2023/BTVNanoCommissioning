#!/usr/bin/env python
"""Build a runner.py-compatible metadata JSON for the QCD_sf 2018 samples
from Hsin-Wei's pre-built NanoAODUL file lists.

Normalizes the file lists' `root:://host///store/...` URLs (extra colon,
extra slash) to the standard `root://host//store/...` form -- uproot/coffea
otherwise fail to open them with FileNotFoundError.
"""
import argparse
import glob
import json
import os
import re

URL_FIX = re.compile(r"^root:+//+")


def normalize(url):
    return URL_FIX.sub("root://", url.strip(), count=1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--filelists-dir",
        required=True,
        help="Directory containing the per-dataset *.txt file lists",
    )
    parser.add_argument("--year", default="2018", help="Year suffix to match, e.g. 2018")
    parser.add_argument("--output", required=True, help="Output metadata JSON path")
    parser.add_argument(
        "--exclude",
        default="",
        help="Comma-separated substrings; any dataset filename containing one is skipped "
        "(e.g. 'DY_madgraphMLM-herwig7_MC,DY_minnlo_MC')",
    )
    args = parser.parse_args()

    excludes = [e.strip() for e in args.exclude.split(",") if e.strip()]
    pattern = os.path.join(args.filelists_dir, f"*_{args.year}.txt")
    fdict = {}
    for path in sorted(glob.glob(pattern)):
        sample = os.path.basename(path)[: -len(".txt")]
        if any(ex in sample for ex in excludes):
            print(f"{sample}: excluded")
            continue
        with open(path) as f:
            files = [normalize(line) for line in f if line.strip()]
        fdict[sample] = files
        print(f"{sample}: {len(files)} files")

    with open(args.output, "w") as f:
        json.dump(fdict, f, indent=2)

    total_files = sum(len(v) for v in fdict.values())
    print(f"\nWrote {len(fdict)} datasets, {total_files} files -> {args.output}")


if __name__ == "__main__":
    main()
