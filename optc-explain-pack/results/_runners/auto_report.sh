#!/bin/bash
B=E:/Code/optc-e2e-baseline/optc-explain-pack
P=$B/results/_runners/progress_gpu_tasks.log
until grep -q "ALL DONE" $P; do sleep 60; done
cd $B && PYTHONIOENCODING=utf-8 $B/.venv/Scripts/python.exe $B/results/_runners/build_report.py $B/task_results_2026-10-04 > $B/results/_runners/build_report.log 2>&1
echo "REPORT rc=$? $(date '+%F %T')" >> $P
