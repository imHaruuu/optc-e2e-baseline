#!/bin/bash
# Review muc 3: EVE 0.5B + kb_only tu worktree sach o commit e5f8c43 (code + KB cua commit).
PACK="E:/Code/optc-e2e-baseline/optc-explain-pack"; cd "$PACK"
PY="$PACK/.venv/Scripts/python.exe"
C="C:/Users/ADMIN/AppData/Local/Temp/claude/E--Code-optc-e2e-baseline--claude-worktrees-optc-file-analysis-305df4/e243e447-1dfe-46fa-8bac-a66d6be428f2/scratchpad/wt_e5f8c43/optc-explain-pack"
R="results/adgen/task13_commit_e5f8c43"
T="../P1/Output/data/splits/REAL_test_matched.jsonl"; DEV="../P1/Output/data/splits/LAB_dev_matched.jsonl"
L="$R/logs/progress.log"
log(){ echo "[$1] $2 $(date '+%F %T')" | tee -a "$L"; }
echo "commit $(git -C "$C" rev-parse HEAD) dirty=$(git -C "$C" status --porcelain | wc -l)" > "$R/logs/commit.txt"
for r in first specific alpha; do
  "$PY" "$C/eve.py" run --data "$T" --mode kb_only --kb_rule $r --out "$R/kb_only_${r}.jsonl" --progress 0 > "$R/logs/kb_only_$r.log" 2>&1
  log kb_only_$r "rc=$?"
done
for s in REAL:$T LAB_dev:$DEV; do
  n=${s%%:*}; d=${s#*:}
  "$PY" "$C/eve.py" run --data "$d" --model Qwen/Qwen2.5-0.5B-Instruct --mode eve --device cuda --out "$R/q05_${n}_eve.jsonl" --progress 100 > "$R/logs/q05_${n}_eve.log" 2>&1
  log q05_${n}_eve "rc=$?"
done
"$PY" "$C/eval_eve.py" --data "$T" --dev "$R/q05_LAB_dev_eve.jsonl" --out "$R/eval_commit.json" --results "$R/q05_REAL_eve.jsonl" "$R/kb_only_first.jsonl" "$R/kb_only_specific.jsonl" "$R/kb_only_alpha.jsonl" > "$R/logs/eval_commit.log" 2>&1
log eval "rc=$?"
log all "DONE"
