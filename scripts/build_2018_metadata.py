#!/usr/bin/env python
"""Build a runner.py-compatible metadata JSON for the QCD_sf 2018 samples
from Hsin-Wei's pre-built NanoAODUL file lists.

Normalizes the file lists' `root:://host///store/...` URLs (extra colon,
extra slash) to the standard `root://host//store/...` form -- uproot/coffea
otherwise fail to open them with FileNotFoundError.

Dataset keys are renamed from the short FileLists_NanoUL filenames to names
the framework's cross-section/stacking machinery
(helpers/xs_scaler.py:scaleSumW, scripts/plotdataMC.py) actually recognizes:
- MC samples are renamed to their official CMS dataset name, parsed directly
  out of each file's own xrootd path -- this must exactly match a
  "process_name" entry in helpers/xsection.py or xsection_13TeV.py, or
  scaleSumW raises a KeyError.
- Data samples are renamed to include "Run" (e.g. EGamma_DATA_2018 ->
  EGamma_Run2018), which is scaleSumW's check for "this is real data, don't
  scale it by a cross-section". All run eras (A/B/C/D) stay combined under
  one key -- nothing downstream needs per-era granularity here.
"""
import argparse
import glob
import json
import os
import re

URL_FIX = re.compile(r"^root:+//+")
MC_NAME_RE = re.compile(r"^root:+//[^/]+/+store/mc/[^/]+/([^/]+)/NANOAODSIM/")
DATA_PRIMARY_RE = re.compile(r"^root:+//[^/]+/+store/data/[^/]+/([^/]+)/NANOAOD/")


def normalize(url):
    return URL_FIX.sub("root://", url.strip(), count=1)


def rename(sample, first_file_url):
    if "DATA" in sample:
        m = DATA_PRIMARY_RE.match(first_file_url)
        if not m:
            raise ValueError(f"Could not parse primary dataset name from {first_file_url}")
        return f"{m.group(1)}_Run2018"
    m = MC_NAME_RE.match(first_file_url)
    if not m:
        raise ValueError(f"Could not parse official dataset name from {first_file_url}")
    return m.group(1)


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
        short_name = os.path.basename(path)[: -len(".txt")]
        if any(ex in short_name for ex in excludes):
            print(f"{short_name}: excluded")
            continue
        with open(path) as f:
            files = [normalize(line) for line in f if line.strip()]
        sample = rename(short_name, files[0])
        if sample in fdict:
            raise ValueError(
                f"{short_name} renamed to '{sample}', which already exists "
                f"(from a different short name) -- files would be silently merged"
            )
        fdict[sample] = files
        print(f"{short_name:35s} -> {sample:60s} {len(files)} files")

    with open(args.output, "w") as f:
        json.dump(fdict, f, indent=2)

    total_files = sum(len(v) for v in fdict.values())
    print(f"\nWrote {len(fdict)} datasets, {total_files} files -> {args.output}")


if __name__ == "__main__":
    main()
