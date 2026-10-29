#!/bin/bash
# one diag_zbzc_met.py job, two tries; log logs_zbzc_diag/<variant>_<campaign>_<dataset>.log
cd /uscms/home/psrivast/nobackup/BTVNanoCommissioning
export X509_USER_PROXY=/uscms/home/psrivast/x509up_u10024  # not set in ssh shells
source /uscms_data/d3/psrivast/micromamba/bin/activate zbb-btv
L=logs_zbzc_diag/$1_$2_${3%%_TuneCP5*}.log
for try in 1 2; do
  timeout 5400 python diag_zbzc_met.py $1 $2 $3 20 hists_zbzc_diag/$2 > $L 2>&1 && break
  echo "try $try failed rc=$?" >> logs_zbzc_diag/failed.log
done
echo "$(date +%T) $1 $2 ${3%%_TuneCP5*} $(grep -c 'DIAG DONE' $L)" >> logs_zbzc_diag/done.log
