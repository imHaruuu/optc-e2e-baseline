"""CSV Pareto: do chinh xac TTP top-1 tren 266 alert (REAL_test_matched day du) + CI 95%, latency do tren CPU (100 alert dau)."""
import csv
import json
import sys

OUT = sys.argv[1]
A = "results/adgen"
# (ten, mode, model, file eval REAL day du, file ket qua REAL, file do latency CPU)
ROWS = [
    ("kb_only (no-model)", "kb_only", "", f"{A}/task09_kb_v2/eval_REAL_v1_vs_v2.json", "kb_only_first_REAL_v0.1.jsonl",
     f"{A}/task12_pareto_cpu/kb_only_first_cpu_first100.jsonl"),
    ("extractive (tfidf-lr)", "extractive", "tfidf-lr", f"{A}/stt57_extractive/eval_extractive.json", "extractive_REAL.jsonl",
     f"{A}/stt58b_cpu_latency/extractive_cpu_first100.jsonl"),
    ("eve (0.5B)", "eve", "Qwen/Qwen2.5-0.5B-Instruct", f"{A}/00_core/eval_q05.json", "q05_REAL_eve.jsonl",
     f"{A}/stt58b_cpu_latency/luot1_q05_cpu_eve.jsonl"),
    ("json_enum (0.5B)", "json_enum", "Qwen/Qwen2.5-0.5B-Instruct", f"{A}/stt58_pareto/eval_rq1.json", "q05_REAL_json_enum.jsonl",
     f"{A}/stt58b_cpu_latency/luot2_q05_cpu_json_enum.jsonl"),
    ("eve (1.5B)", "eve", "Qwen/Qwen2.5-1.5B-Instruct", f"{A}/task08_qwen3_06b/eval_qwen3_vs_q25.json", "q15_REAL_eve.jsonl",
     f"{A}/task04_cpu_15b/q15_cpu_eve.jsonl"),
    ("eve (7B)", "eve", "Qwen/Qwen2.5-7B-Instruct", f"{A}/stt55_q7b/eval_q7b.json", "q7b_REAL_eve.jsonl",
     f"{A}/stt58b_cpu_latency/luot3_q7b_cpu_eve.jsonl"),
    ("json_enum (7B)", "json_enum", "Qwen/Qwen2.5-7B-Instruct", f"{A}/stt55_q7b/eval_q7b.json", "q7b_REAL_json_enum.jsonl",
     f"{A}/stt58b_cpu_latency/luot4_q7b_cpu_json_enum.jsonl"),
]


def cpu_ms(path):
    lat = [json.loads(l).get("latency_ms", 0) for l in open(path, encoding="utf-8")]
    return sum(lat) / len(lat), len(lat)


pts = []
for name, mode, model, ev, res, cpu in ROWS:
    t = next(x for x in json.load(open(ev, encoding="utf-8")) if str(x["file"]).endswith(res))["ttp"]
    assert t["n"] == 266, (res, t["n"])
    ms, n_cpu = cpu_ms(cpu)
    pts.append({"name": name, "mode": mode, "model": model, "quality": t["acc_top1"], "latency_ms": round(max(ms, 0.01), 3),
                "ci_lo": t["acc_top1_ci"][0], "ci_hi": t["acc_top1_ci"][1], "n_ttp": t["n"], "n_cpu": n_cpu,
                "file": f"{ev}::{res}", "cpu_file": cpu})
for p in pts:
    p["pareto"] = not any(o is not p and o["latency_ms"] <= p["latency_ms"] and o["quality"] >= p["quality"]
                          and (o["latency_ms"] < p["latency_ms"] or o["quality"] > p["quality"]) for o in pts)
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["name", "mode", "model", "quality", "latency_ms", "pareto", "ci_lo", "ci_hi",
                                      "n_ttp", "n_cpu", "file", "cpu_file"])
    w.writeheader()
    w.writerows(pts)
for p in sorted(pts, key=lambda p: p["latency_ms"]):
    print(f'{p["name"]:24s} acc={p["quality"]:.3f} [{p["ci_lo"]:.3f},{p["ci_hi"]:.3f}] cpu={p["latency_ms"]:.1f}ms pareto={p["pareto"]}')
