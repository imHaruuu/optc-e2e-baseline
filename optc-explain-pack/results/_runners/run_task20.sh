#!/bin/bash
# Ho SLM khac: K2-Horizon-3.7B (IFM, code rieng da doc, ghim revision) + MiniCPM5-2B (openbmb, Llama).
# 5 luot / model: (1) EVE REAL + LAB_dev, (2) json_enum REAL, eval_eve; (3) random_in_c; (4) paired bootstrap;
# (5) CPU fp32 16 thread 100 alert dau qua measure_rss. Moi model mot thu muc con: $R/<model>/ (+ logs/). Chay lai duoc: buoc xong -> bo qua, dang do -> --resume.
set +e
PACK="E:/Code/optc-e2e-baseline/optc-explain-pack"; cd "$PACK"
PY="$PACK/.venv/Scripts/python.exe"
W="E:/Code/optc-e2e-baseline/.claude/worktrees/optc-file-analysis-305df4/optc-explain-pack"
T="../P1/Output/data/splits/REAL_test_matched.jsonl"; DEV="../P1/Output/data/splits/LAB_dev_matched.jsonl"
KB1="results/_kb/tech_preconditions_v0.1.json"
KBF="results/adgen/task09_kb_v2/kb_only_first_REAL_v0.1.jsonl"; Q05="results/adgen/00_core/q05_REAL_eve.jsonl"
R=$(bash results/_runners/newrun_wt.sh adgen task20_other_family --reuse --note "Ho SLM khac: K2-Horizon-3.7B (bf16 GPU / fp32 CPU, trust_remote_code, revision d6e5432) + MiniCPM5-2B (fp32); KB v0.1; 5 luot/model")
PROG="$R/logs/progress.log"
log(){ echo "[$1] $2 $(date '+%F %T')" | tee -a "$PROG"; }
erun(){  # out data log args...
  out=$1; data=$2; lg=$3; shift 3
  want=$(grep -c . "$data"); [ -n "$LIMIT" ] && want=$LIMIT
  have=$( [ -f "$out" ] && grep -c . "$out" || echo 0 )
  if [ -f "$out.summary.json" ] && [ "$have" -ge "$want" ]; then log "$(basename $out)" "SKIP ($have)"; return; fi
  res=""; [ -f "$out" ] && res="--resume"
  log "$(basename $out)" "START ($have/$want) $res"
  "$PY" "$W/eve.py" run --data "$data" --out "$out" --kb "$KB1" --progress 50 $res "$@" >> "$lg" 2>&1
  log "$(basename $out)" "END rc=$?"
}
log all "START GPU"
for spec in "mc5|openbmb/MiniCPM5-2B|--dtype float32 --batch_size 8" "k2h|IFM/K2-Horizon-3.7B|--dtype bfloat16 --batch_size 2 --trust_remote_code --revision d6e5432c59637093c0e125e791d89ea4a0b53559"; do
  IFS='|' read -r tag M X <<< "$spec"; LIMIT=""
  case $tag in mc5) D="$R/minicpm5_2b";; k2h) D="$R/k2_horizon_3_7b";; esac; mkdir -p "$D/logs"
  erun "$D/${tag}_REAL_eve.jsonl" "$T" "$D/logs/${tag}_REAL_eve.log" --model "$M" --mode eve --device cuda $X
  erun "$D/${tag}_LAB_dev_eve.jsonl" "$DEV" "$D/logs/${tag}_LAB_dev_eve.log" --model "$M" --mode eve --device cuda $X
  erun "$D/${tag}_REAL_json_enum.jsonl" "$T" "$D/logs/${tag}_REAL_json_enum.log" --model "$M" --mode json_enum --device cuda $X
  "$PY" "$W/eval_eve.py" --data "$T" --dev "$D/${tag}_LAB_dev_eve.jsonl" --out "$D/eval_${tag}.json" \
     --results "$D/${tag}_REAL_eve.jsonl" "$D/${tag}_REAL_json_enum.jsonl" > "$D/logs/eval_${tag}.log" 2>&1; log "eval_${tag}" "rc=$?"
  "$PY" "$W/random_in_c.py" --results "$D/${tag}_REAL_eve.jsonl" --out "$D/random_in_c_${tag}.json" > "$D/logs/random_in_c_${tag}.log" 2>&1; log "random_in_c_${tag}" "rc=$?"
  "$PY" "$W/paired_bootstrap.py" --pair "${tag}_eve=$D/${tag}_REAL_eve.jsonl" "kb_first=$KBF" --pair "${tag}_eve=$D/${tag}_REAL_eve.jsonl" "q05_eve=$Q05" \
     --name REAL --kb "$KB1" --out "$D/paired_${tag}.json" > "$D/logs/paired_${tag}.log" 2>&1; log "paired_${tag}" "rc=$?"
done
log all "START CPU"
for spec in "mc5|openbmb/MiniCPM5-2B|" "k2h|IFM/K2-Horizon-3.7B|--trust_remote_code --revision d6e5432c59637093c0e125e791d89ea4a0b53559"; do
  IFS='|' read -r tag M X <<< "$spec"
  case $tag in mc5) D="$R/minicpm5_2b";; k2h) D="$R/k2_horizon_3_7b";; esac; out="$D/${tag}_cpu_eve.jsonl"
  if [ -f "$out.summary.json" ]; then log "${tag}_cpu_eve" "SKIP"; continue; fi
  rm -f "$out"; log "${tag}_cpu_eve" "START"
  "$PY" "$W/measure_rss.py" --out "$D/mem_${tag}_cpu_eve.json" -- "$W/eve.py" run --data "$T" --model "$M" --mode eve --kb "$KB1" \
     --device cpu --dtype float32 --threads 16 --limit 100 --progress 10 $X --out "$out" > "$D/logs/${tag}_cpu_eve.log" 2>&1
  log "${tag}_cpu_eve" "END rc=$?"
done
log all "ALL DONE"
