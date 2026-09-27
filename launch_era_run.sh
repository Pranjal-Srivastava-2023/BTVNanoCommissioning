#!/bin/bash
# Launch the per-dataset QCD_sf condor run for one era, detached, inside the
# Apptainer container. Usage: ./launch_era_run.sh <ERA>
# Outputs: hists_run<ERA>_mSD_SF/, logs_run<ERA>_mSD_SF/, logs_run<ERA>_mSD_SF_driver.log
ERA=$1
cd "$(dirname "$0")"
export COFFEA_IMAGE_FULL=$(realpath /cvmfs/unpacked.cern.ch/registry.hub.docker.com/coffeateam/coffea-base-almalinux8:0.7.30-py3.10)
export APPTAINER_BINDPATH=/uscmst1b_scratch,/cvmfs,/cvmfs/grid.cern.ch/etc/grid-security:/etc/grid-security,/etc/condor/config.d/01_cmslpc_interactive,/usr/local/bin/cmslpc-local-conf.py:/usr/local/bin/cmslpc-local-conf.py.orig,.cmslpc-local-conf:/usr/local/bin/cmslpc-local-conf.py
setsid nohup apptainer exec -B ${PWD}:/srv --pwd /srv $COFFEA_IMAGE_FULL /bin/bash -c "
source /srv/.bashrc >/dev/null 2>&1
python -c 'import BTVNanoCommissioning.utils.zb_old_sf as m; print(\"env ok\", m.__file__)'
ERA=$ERA OUTDIR=hists_run${ERA}_mSD_SF LOGDIR=logs_run${ERA}_mSD_SF ./submit_qcd_sf_per_dataset.sh
" > logs_run${ERA}_mSD_SF_driver.log 2>&1 < /dev/null &
echo "launched ERA=$ERA pid=$!"
