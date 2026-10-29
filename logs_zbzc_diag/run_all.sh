#!/bin/bash
# run every line of jobs.txt through one.sh, 4 at a time (8 ran the 11.7 GB node out of memory); ALL DONE marker at the end
cd /uscms/home/psrivast/nobackup/BTVNanoCommissioning
xargs -P 4 -L 1 logs_zbzc_diag/one.sh < logs_zbzc_diag/jobs.txt
echo "$(date +%T) ALL DONE" >> logs_zbzc_diag/done.log
