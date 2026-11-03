#!/bin/bash
# LNBI S1: the whole free-server window in one command (run from the worktree root).
#   bash SPATIAL/run_window_s1.sh
# Order: thermal test -> criterion -> GPU 3x5 -> CPU control 3x5 -> concordance.
# Each repetition waits until the preflight passes (load1 <= 3, no foreign process > 50%).
set -uo pipefail
cd "$(dirname "$0")/.."
S=SPATIAL/run_spatial_v2_server.sh
R=SPATIAL/results_v2
mkdir -p $R
echo "window start $(date -Iseconds)"
if [ ! -f $R/thermal/thermal_eval.json ]; then
    bash $S thermal || { echo "thermal: machine not free"; exit 3; }
    python3 SPATIAL/scripts/s1_thermal_eval.py $R/thermal > $R/thermal/thermal_eval.json
    rc=$?; cat $R/thermal/thermal_eval.json
    [ $rc -ne 0 ] && { echo "THERMAL CRITERION FAILED: stop, the PI decides the thread count"; exit 10; }
fi
echo "gpu start $(date -Iseconds)";  bash $S gpu || { echo "gpu failed rc=$?"; exit 4; }
echo "cpu start $(date -Iseconds)";  bash $S cpu || { echo "cpu failed rc=$?"; exit 5; }
echo "compare start $(date -Iseconds)"; bash $S compare > $R/compare.log 2>&1; echo "compare rc=$?"
echo "window end $(date -Iseconds)"
