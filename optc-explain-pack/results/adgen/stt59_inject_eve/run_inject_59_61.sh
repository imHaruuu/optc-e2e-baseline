#!/bin/bash
# STT59-61: RQ4 injection. T = REAL_test_matched, M = Qwen2.5-0.5B, GPU float32 (giong ban sach).
# Chay lai duoc sau khi tat may: buoc da xong -> bo qua, buoc dang do -> --resume.
set +e
PACK="E:/Code/optc-e2e-baseline/optc-explain-pack"; cd "$PACK"
PY="$PACK/.venv/Scripts/python.exe"
T="../P1/Output/data/splits/REAL_test_matched.jsonl"
M="Qwen/Qwen2.5-0.5B-Instruct"
PAYLOADS="instruction claim_technique fake_fields keyword_stuffing"
D0=$("$PY" newrun.py adgen stt59_inject_data --reuse --note "data_inj_<p>.jsonl tu REAL_test_matched (dung chung STT59-61)")
R59=$("$PY" newrun.py adgen stt59_inject_eve --reuse --note "EVE thuong + kb_only first tren du lieu bi chen")
R60=$("$PY" newrun.py adgen stt60_inject_attested --reuse --note "EVE --attested_only: ban sach + ban bi chen")
R61=$("$PY" newrun.py adgen stt61_inject_json_enum --reuse --note "doi chung khong rang buoc json_enum")
CL_EVE="results/adgen/00_core/q05_REAL_eve.jsonl"
CL_JE="results/adgen/stt39_anchored_json_enum/q05_REAL_json_enum.jsonl"
CL_KB="results/adgen/00_core/kb_only_first.jsonl"
PROG="$R59/logs/progress_59_61.log"
log(){ echo "[$1] $2 $(date '+%F %T')" | tee -a "$PROG"; }

# eve run co bo qua/tiep tuc: $1=out $2=data $3=log, con lai = tham so eve.py
erun(){
  out=$1; data=$2; lg=$3; shift 3
  want=$(grep -c . "$data")
  have=$( [ -f "$out" ] && grep -c . "$out" || echo 0 )
  if [ -f "$out.summary.json" ] && [ "$have" -ge "$want" ]; then log "$(basename $out)" "SKIP (da du $have)"; return; fi
  res=""; [ -f "$out" ] && res="--resume"
  log "$(basename $out)" "START ($have/$want) $res"
  "$PY" eve.py run --data "$data" --out "$out" --progress 200 $res "$@" >> "$lg" 2>&1
  log "$(basename $out)" "END rc=$?"
}

log all "START STT59-61"
# 1. du lieu bi chen
for p in $PAYLOADS; do
  f="$D0/data_inj_$p.jsonl"
  [ -s "$f" ] || "$PY" inject.py make --data "$T" --out "$f" --payload $p | tee "$D0/logs/make_$p.json"
done
log make "data_inj xong"

# 5. kb_only (vai giay) -> STT59
for p in $PAYLOADS; do
  erun "$R59/kb_only_inj_$p.jsonl" "$D0/data_inj_$p.jsonl" "$R59/logs/kb_only_inj_$p.log" --mode kb_only --kb_rule first
  "$PY" inject.py compare --clean "$CL_KB" --injected "$R59/kb_only_inj_$p.jsonl" --out "$R59/inj_kb_only_$p.json" > /dev/null
done

# 2. EVE thuong -> STT59
for p in $PAYLOADS; do
  erun "$R59/q05_eve_inj_$p.jsonl" "$D0/data_inj_$p.jsonl" "$R59/logs/q05_eve_inj_$p.log" --model "$M" --mode eve --device cuda
  "$PY" inject.py compare --clean "$CL_EVE" --injected "$R59/q05_eve_inj_$p.jsonl" --out "$R59/inj_eve_$p.json" > /dev/null
done

# 3. EVE --attested_only (ban sach 1 lan + ban bi chen) -> STT60
erun "$R60/q05_REAL_eve_att.jsonl" "$T" "$R60/logs/q05_REAL_eve_att.log" --model "$M" --mode eve --attested_only --device cuda
for p in $PAYLOADS; do
  erun "$R60/q05_eve_att_inj_$p.jsonl" "$D0/data_inj_$p.jsonl" "$R60/logs/q05_eve_att_inj_$p.log" --model "$M" --mode eve --attested_only --device cuda
  "$PY" inject.py compare --clean "$R60/q05_REAL_eve_att.jsonl" --injected "$R60/q05_eve_att_inj_$p.jsonl" --out "$R60/inj_eve_att_$p.json" > /dev/null
done

# 4. doi chung json_enum -> STT61
for p in $PAYLOADS; do
  erun "$R61/q05_json_enum_inj_$p.jsonl" "$D0/data_inj_$p.jsonl" "$R61/logs/q05_json_enum_inj_$p.log" --model "$M" --mode json_enum --device cuda
  "$PY" inject.py compare --clean "$CL_JE" --injected "$R61/q05_json_enum_inj_$p.jsonl" --out "$R61/inj_json_enum_$p.json" > /dev/null
done
log all "ALL DONE"
