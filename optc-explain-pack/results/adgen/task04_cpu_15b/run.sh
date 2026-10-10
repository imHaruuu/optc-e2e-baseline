#!/bin/bash
cd E:/Code/optc-e2e-baseline/optc-explain-pack
PY=E:/Code/optc-e2e-baseline/optc-explain-pack/.venv/Scripts/python.exe
W="E:/Code/optc-e2e-baseline/.claude/worktrees/optc-file-analysis-305df4/optc-explain-pack"
R=results/adgen/task04_cpu_15b
$PY $W/measure_rss.py --out $R/mem_q15_cpu_eve.json -- $PY $W/eve.py run --data ../P1/Output/data/splits/REAL_test_matched.jsonl --model Qwen/Qwen2.5-1.5B-Instruct --mode eve --kb results/_kb/tech_preconditions_v0.1.json --device cpu --dtype float32 --threads 16 --limit 100 --progress 10 --out $R/q15_cpu_eve.jsonl > $R/logs/q15_cpu_eve.log 2>&1
echo "DONE rc=$?" >> $R/logs/q15_cpu_eve.log
