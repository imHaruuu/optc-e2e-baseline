#!/bin/bash
# Review muc c: clause doi chung cheo field. KB v0.1 / v0.2 x {orig, anyfield, cross0..2} x {REAL, attack_data}.
PACK="E:/Code/optc-e2e-baseline/optc-explain-pack"; cd "$PACK"
PY="$PACK/.venv/Scripts/python.exe"
W="E:/Code/optc-e2e-baseline/.claude/worktrees/optc-file-analysis-305df4/optc-explain-pack"
T="../P1/Output/data/splits/REAL_test_matched.jsonl"; ATK="results/attackdata/stt43/attackdata.jsonl"
R=$(bash results/_runners/newrun_wt.sh adgen task18_kb_field_control --note "Review muc c: clause doi chung cheo field - KB v0.1/v0.2 x {orig, anyfield, cross0-2}; kbstats + kb_only first tren REAL va attack_data")
L="$R/logs/progress.log"
for kv in v0.1 v0.2; do
  K="results/_kb/tech_preconditions_$kv.json"; D="$R/kb_$kv"
  "$PY" "$W/kb_field_control.py" --kb "$K" --data "$T" "$ATK" --outdir "$D" > "$R/logs/variants_$kv.log" 2>&1
  cp "$K" "$D/kb_orig.json"
  for var in orig anyfield cross0 cross1 cross2; do
    for s in REAL:$T attackdata:$ATK; do
      n=${s%%:*}; d=${s#*:}
      "$PY" "$W/eve.py" kbstats --kb "$D/kb_$var.json" --data "$d" --out "$R/kbstats_${kv}_${var}_$n.json" > /dev/null 2>> "$R/logs/errors.log"
      "$PY" "$W/eve.py" run --mode kb_only --kb_rule first --kb "$D/kb_$var.json" --data "$d" --progress 0 \
        --out "$R/kb_only_${kv}_${var}_$n.jsonl" > /dev/null 2>> "$R/logs/errors.log"
      echo "[$kv $var $n] rc=$? $(date '+%T')" | tee -a "$L"
    done
  done
done
"$PY" "$W/eval_eve.py" --data "$T" --out "$R/eval_REAL.json" --results "$R"/kb_only_*_REAL.jsonl > "$R/logs/eval_REAL.log" 2>&1
"$PY" "$W/eval_eve.py" --data "$ATK" --out "$R/eval_attackdata.json" --results "$R"/kb_only_*_attackdata.jsonl > "$R/logs/eval_attackdata.log" 2>&1
echo "DONE $(date '+%T')" | tee -a "$L"
