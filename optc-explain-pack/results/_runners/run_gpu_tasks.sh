#!/bin/bash
# task.docx viec 8, 9, 10, 3 (GPU). Chay lai duoc: buoc xong -> bo qua, buoc dang do -> --resume.
set +e
PACK="E:/Code/optc-e2e-baseline/optc-explain-pack"; cd "$PACK"
PY="$PACK/.venv/Scripts/python.exe"
W="E:/Code/optc-e2e-baseline/.claude/worktrees/optc-file-analysis-305df4/optc-explain-pack"
T="../P1/Output/data/splits/REAL_test_matched.jsonl"
ADGEN="../P1/Output/data/adgen-v2.jsonl"
ATK="results/attackdata/stt43/attackdata.jsonl"
DEV="results/adgen/00_core/q05_LAB_dev_eve.jsonl"
KB1="results/_kb/tech_preconditions_v0.1.json"
KB2="results/_kb/tech_preconditions_v0.2.json"
MAP="$W/attack_id_map_v15.json"
Q05="Qwen/Qwen2.5-0.5B-Instruct"; Q15="Qwen/Qwen2.5-1.5B-Instruct"; Q7="Qwen/Qwen2.5-7B-Instruct"; Q3="Qwen/Qwen3-0.6B"
mk(){ "$PY" newrun.py "$1" "$2" --reuse --note "$3"; }
PROG="results/_runners/progress_gpu_tasks.log"
log(){ echo "[$1] $2 $(date '+%F %T')" | tee -a "$PROG"; }

erun(){  # out data log args...
  out=$1; data=$2; lg=$3; shift 3
  want=$(grep -c . "$data"); have=$( [ -f "$out" ] && grep -c . "$out" || echo 0 )
  if [ -f "$out.summary.json" ] && [ "$have" -ge "$want" ]; then log "$(basename $out)" "SKIP ($have)"; return; fi
  res=""; [ -f "$out" ] && res="--resume"
  log "$(basename $out)" "START ($have/$want) $res"
  "$PY" "$W/eve.py" run --data "$data" --out "$out" --progress 100 $res "$@" >> "$lg" 2>&1
  log "$(basename $out)" "END rc=$?"
}
ev(){ out=$1; shift; "$PY" "$W/eval_eve.py" --data "$T" --dev "$DEV" --out "$out" --results "$@" > "${out%.json}.log" 2>&1; log "$(basename $out)" "eval rc=$?"; }

log all "START viec 8 9 10 3"

# ---- Viec 8: them ho SLM <= 1.5B (Qwen3-0.6B), KB v0.1 de so voi Qwen2.5 ----
R8=$(mk adgen task08_qwen3_06b "Viec 8: Qwen3-0.6B (ho Qwen3, enable_thinking=False) eve + json_enum, GPU fp32, KB v0.1")
erun "$R8/q3_06b_REAL_eve.jsonl" "$T" "$R8/logs/eve.log" --model "$Q3" --mode eve --device cuda --kb "$KB1"
erun "$R8/q3_06b_REAL_json_enum.jsonl" "$T" "$R8/logs/json_enum.log" --model "$Q3" --mode json_enum --device cuda --kb "$KB1"
ev "$R8/eval_qwen3_vs_q25.json" "$R8/q3_06b_REAL_eve.jsonl" "$R8/q3_06b_REAL_json_enum.jsonl" \
   results/adgen/00_core/q05_REAL_eve.jsonl results/adgen/stt39_anchored_json_enum/q05_REAL_json_enum.jsonl \
   results/adgen/stt42_q15/q15_REAL_eve.jsonl results/adgen/stt42_q15/q15_REAL_json_enum.jsonl

# ---- Viec 9: KB v0.2 (T1036/T1553/T1047 viet lai) ----
R9=$(mk adgen task09_kb_v2 "Viec 9: KB v0.2 vs v0.1 - kbstats, kb_only (first/specific/alpha), EVE 0.5B; AD-GEN REAL + attack_data")
for v in 1 2; do
  KBV=$([ $v = 1 ] && echo "$KB1" || echo "$KB2")
  [ -s "$R9/kbstats_adgen_v0.$v.json" ] || "$PY" "$W/eve.py" kbstats --data "$ADGEN" --kb "$KBV" --out "$R9/kbstats_adgen_v0.$v.json" > "$R9/logs/kbstats_adgen_v0.$v.log" 2>&1
  [ -s "$R9/kbstats_attackdata_v0.$v.json" ] || "$PY" "$W/eve.py" kbstats --data "$ATK" --kb "$KBV" --out "$R9/kbstats_attackdata_v0.$v.json" > "$R9/logs/kbstats_attackdata_v0.$v.log" 2>&1
  for r in first specific alpha; do
    erun "$R9/kb_only_${r}_REAL_v0.$v.jsonl" "$T" "$R9/logs/kb_only.log" --mode kb_only --kb_rule $r --kb "$KBV"
    erun "$R9/kb_only_${r}_attackdata_v0.$v.jsonl" "$ATK" "$R9/logs/kb_only.log" --mode kb_only --kb_rule $r --kb "$KBV"
  done
done
log kbstats "xong"
erun "$R9/q05_REAL_eve_v0.2.jsonl" "$T" "$R9/logs/eve_v0.2.log" --model "$Q05" --mode eve --device cuda --kb "$KB2"
erun "$R9/q05_attackdata_eve_v0.2.jsonl" "$ATK" "$R9/logs/eve_atk_v0.2.log" --model "$Q05" --mode eve --device cuda --kb "$KB2"
ev "$R9/eval_REAL_v1_vs_v2.json" results/adgen/00_core/q05_REAL_eve.jsonl "$R9/q05_REAL_eve_v0.2.jsonl" \
   "$R9"/kb_only_*_REAL_v0.1.jsonl "$R9"/kb_only_*_REAL_v0.2.jsonl
"$PY" "$W/eval_eve.py" --data "$ATK" --out "$R9/eval_attackdata_v1_vs_v2.json" --results results/attackdata/stt43/q05_attackdata_eve.jsonl \
   "$R9/q05_attackdata_eve_v0.2.jsonl" "$R9"/kb_only_*_attackdata_v0.1.jsonl "$R9"/kb_only_*_attackdata_v0.2.jsonl > "$R9/logs/eval_attackdata.log" 2>&1
log task09 "eval xong"

# ---- Viec 10: payload thich ung vao field attested (KB v0.1, so voi STT59-61) ----
R10=$(mk adgen task10_inject_adaptive "Viec 10: payload thich ung vao Image (attested): attested_rename, attested_instruction; KB v0.1")
for p in attested_rename attested_instruction; do
  D="$R10/data_inj_$p.jsonl"
  [ -s "$D" ] || "$PY" "$W/inject.py" make --data "$T" --out "$D" --payload $p > "$R10/logs/make_$p.json"
  erun "$R10/kb_only_inj_$p.jsonl" "$D" "$R10/logs/kb_only.log" --mode kb_only --kb_rule first --kb "$KB1"
  erun "$R10/q05_eve_inj_$p.jsonl" "$D" "$R10/logs/eve_$p.log" --model "$Q05" --mode eve --device cuda --kb "$KB1"
  erun "$R10/q05_eve_att_inj_$p.jsonl" "$D" "$R10/logs/eve_att_$p.log" --model "$Q05" --mode eve --attested_only --device cuda --kb "$KB1"
  erun "$R10/q05_json_enum_inj_$p.jsonl" "$D" "$R10/logs/json_enum_$p.log" --model "$Q05" --mode json_enum --device cuda --kb "$KB1"
  "$PY" "$W/inject.py" compare --clean "$R9/kb_only_first_REAL_v0.1.jsonl" --injected "$R10/kb_only_inj_$p.jsonl" --out "$R10/inj_kb_only_$p.json" > /dev/null
  "$PY" "$W/inject.py" compare --clean results/adgen/00_core/q05_REAL_eve.jsonl --injected "$R10/q05_eve_inj_$p.jsonl" --out "$R10/inj_eve_$p.json" > /dev/null
  "$PY" "$W/inject.py" compare --clean results/adgen/stt60_inject_attested/q05_REAL_eve_att.jsonl --injected "$R10/q05_eve_att_inj_$p.jsonl" --out "$R10/inj_eve_att_$p.json" > /dev/null
  "$PY" "$W/inject.py" compare --clean results/adgen/stt39_anchored_json_enum/q05_REAL_json_enum.jsonl --injected "$R10/q05_json_enum_inj_$p.jsonl" --out "$R10/inj_json_enum_$p.json" > /dev/null
done
log task10 "xong"

# ---- Viec 5 + 11: conformal (co ESS) tren LAB_calib cua bo split nay, dinh tuyen 0.5B -> 7B ----
LABC="../P1/Output/data/splits/LAB_calib.jsonl"
R5=$(mk adgen task05_conformal_route "Viec 5 + 11: EVE 0.5B tren LAB_calib, conformal weighted (+ESS), dinh tuyen giu 0.5B / escalate 7B")
erun "$R5/q05_LAB_calib_eve.jsonl" "$LABC" "$R5/logs/eve_calib.log" --model "$Q05" --mode eve --device cuda --kb "$KB1"
"$PY" "$W/conformal.py" --calib "$R5/q05_LAB_calib_eve.jsonl" --test results/adgen/00_core/q05_REAL_eve.jsonl --weighted \
   --calib_data "$LABC" --test_data "$T" --out "$R5/conformal_q05.json" > "$R5/logs/conformal.log" 2>&1
"$PY" "$W/conformal_route.py" --calib "$R5/q05_LAB_calib_eve.jsonl" --test results/adgen/00_core/q05_REAL_eve.jsonl \
   --big results/adgen/stt55_q7b/q7b_REAL_eve.jsonl --weighted --calib_data "$LABC" --test_data "$T" \
   --out "$R5/conformal_route.json" > "$R5/logs/route.log" 2>&1
log task05 "xong"

# ---- Viec 7 (phu tro): kb_only cung code/KB v0.1 tren REAL_nontrivial ----
NT="../P1/Output/data/splits/REAL_nontrivial.jsonl"
R7=$(mk adgen task07_paired_ci "Viec 7: bootstrap CI ghep cap EVE vs kb_only (REAL / nontrivial / gold), CI cho 7B")
for r in first specific; do
  erun "$R7/kb_only_${r}_nontrivial_v0.1.jsonl" "$NT" "$R7/logs/kb_only.log" --mode kb_only --kb_rule $r --kb "$KB1"
done
log task07 "kb_only nontrivial xong"

# ---- Viec 3: free + json, parser moi, max_new_tokens 384, --attack_map, 0.5B/1.5B/7B (KB v0.1) ----
R3=$(mk adgen task03_gen_rerun "Viec 3: free/json chay lai voi parser moi, max_new_tokens 384, --attack_map v15.1; 0.5B/1.5B fp32, 7B bf16; KB v0.1")
for m in q05 q15 q7b; do
  case $m in q05) M=$Q05; X="";; q15) M=$Q15; X="";; q7b) M=$Q7; X="--dtype bf16 --batch_size 2";; esac
  for mode in json free; do
    erun "$R3/${m}_REAL_${mode}.jsonl" "$T" "$R3/logs/${m}_${mode}.log" --model "$M" --mode $mode --device cuda \
         --max_new_tokens 384 --attack_map "$MAP" --kb "$KB1" $X
  done
  ev "$R3/eval_${m}_gen.json" "$R3/${m}_REAL_json.jsonl" "$R3/${m}_REAL_free.jsonl"
done
log all "ALL DONE"
