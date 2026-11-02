#!/bin/bash
# resume after the 2026-11-02 ~13:20 LPC reboot: only the MC samples the Summer22
# ge1j / 1j reruns had not finished (data + DY done); appends to driver_mc.log so
# postprocess_zbzc_njet.sh sees "ALL DONE" as usual.
# usage: ./resume_zbzc_njet_bkg.sh <ge1j|1j>
R=$1; WF=Zb_Zc_ratio; [ "$R" = 1j ] && WF=Zb_Zc_ratio_1jet
cd "$(dirname "$0")"
source /uscms_data/d3/psrivast/micromamba/bin/activate zbb-btv
export X509_USER_PROXY=/uscms/home/psrivast/x509up_u10024
JSON=metadata/Zb_Zc_ratio_run3_Summer22.json
OUT=hists_zbzc_run3_$R/Summer22; LOG=logs_zbzc_run3_$R/Summer22
echo "$(date +%T) RESUME after node reboot on $(hostname -s)" >> $LOG/driver_mc.log
for ds in TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8 WW_TuneCP5_13p6TeV_pythia8 WZ_TuneCP5_13p6TeV_pythia8 ZZ_TuneCP5_13p6TeV_pythia8; do
  for try in 1 2 3; do
    echo "$(date +%T) $ds try $try" >> $LOG/driver_mc.log
    timeout 14400 python runner.py --wf $WF --json $JSON --year 2022 --campaign Summer22 \
      --executor iterative --limit 20 --only $ds --outputdir $OUT --output zbzc_run3.coffea \
      --overwrite > $LOG/${ds%%_TuneCP5*}.log 2>&1
    rc=$?; echo "$(date +%T) $ds exit $rc" >> $LOG/driver_mc.log
    [ $rc -eq 0 ] && break
  done
done
echo "$(date +%T) ALL DONE" >> $LOG/driver_mc.log
