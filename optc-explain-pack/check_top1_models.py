"""Bang so sanh model (lan chay moi nhat) tu check_top1_latest.csv -> check_top1_models.csv + .md
python check_top1_models.py check_top1_latest.csv check_top1_models
"""
import csv
import sys
from pathlib import Path

A, T21 = "results/adgen/", "results/adgen/task21_small_models/"
# (model, ho, tham so B tu manifest safetensors, {cot: file})
MODELS = [
    ("ERNIE-4.5-0.3B-PT", "Baidu", 0.36, "ernie_4_5_0_3b_pt"),
    ("Qwen2.5-0.5B-Instruct", "Qwen", 0.49, {"REAL_eve": "task13_commit_e5f8c43/q05_REAL_eve",
        "REAL_json_enum": "stt39_anchored_json_enum/q05_REAL_json_enum", "LAB_dev_eve": "task13_commit_e5f8c43/q05_LAB_dev_eve",
        "cpu100_eve": "stt58b_cpu_latency/luot1_q05_cpu_eve", "REAL_free": "task03_gen_rerun/q05_REAL_free",
        "REAL_json": "task03_gen_rerun/q05_REAL_json"}),
    ("Qwen3-0.6B", "Qwen", 0.75, {"REAL_eve": "task08_qwen3_06b/q3_06b_REAL_eve",
        "REAL_json_enum": "task08_qwen3_06b/q3_06b_REAL_json_enum"}),
    ("EXAONE-4.0-1.2B", "LG", 1.28, "exaone_4_0_1_2b"),
    ("OLMo-2-0425-1B-Instruct", "AllenAI", 1.48, "olmo_2_0425_1b_instruct"),
    ("Qwen2.5-1.5B-Instruct", "Qwen", 1.54, {"REAL_eve": "stt42_q15/q15_REAL_eve", "REAL_json_enum": "stt42_q15/q15_REAL_json_enum",
        "cpu100_eve": "task04_cpu_15b/q15_cpu_eve", "REAL_free": "task03_gen_rerun/q15_REAL_free",
        "REAL_json": "task03_gen_rerun/q15_REAL_json"}),
    ("DeepSeek-R1-Distill-Qwen-1.5B", "DeepSeek", 1.78, "deepseek_r1_distill_qwen_1_5b"),
    ("Youtu-LLM-2B", "Tencent", 1.96, "youtu_llm_2b"),
    ("MiniCPM5-2B", "OpenBMB", 2.52, {"REAL_eve": "task20_other_family/minicpm5_2b/mc5_REAL_eve",
        "REAL_json_enum": "task20_other_family/minicpm5_2b/mc5_REAL_json_enum",
        "LAB_dev_eve": "task20_other_family/minicpm5_2b/mc5_LAB_dev_eve", "cpu100_eve": "task20_other_family/minicpm5_2b/mc5_cpu_eve"}),
    ("LFM2.5-2.6B", "LiquidAI", 2.70, "lfm2_5_2_6b"),
    ("AI21-Jamba2-3B", "AI21", 3.03, "ai21_jamba2_3b"),
    ("K2-Horizon-3.7B", "IFM", 5.06, {"REAL_eve": "task20_other_family/k2_horizon_3_7b/k2h_REAL_eve",
        "REAL_json_enum": "task20_other_family/k2_horizon_3_7b/k2h_REAL_json_enum",
        "LAB_dev_eve": "task20_other_family/k2_horizon_3_7b/k2h_LAB_dev_eve", "cpu100_eve": "task20_other_family/k2_horizon_3_7b/k2h_cpu_eve"}),
    ("Qwen2.5-7B-Instruct", "Qwen", 7.62, {"REAL_eve": "stt55_q7b/q7b_REAL_eve", "REAL_json_enum": "stt55_q7b/q7b_REAL_json_enum",
        "cpu100_eve": "stt58b_cpu_latency/luot3_q7b_cpu_eve", "REAL_free": "task03_gen_rerun/q7b_REAL_free",
        "REAL_json": "task03_gen_rerun/q7b_REAL_json"}),
]
BASE = [("kb_only first (khong model)", "-", None, {"REAL_eve": "task18_kb_field_control/kb_only_v0.1_orig_REAL",
            "cpu100_eve": "task12_pareto_cpu/kb_only_first_cpu_first100"}),
        ("extractive (khong model)", "-", None, {"REAL_eve": "stt57_extractive/extractive_REAL",
            "cpu100_eve": "stt58b_cpu_latency/extractive_cpu_first100"})]
COLS = [("REAL_eve", "EVE REAL (n=266/166)"), ("REAL_json_enum", "json_enum REAL"), ("LAB_dev_eve", "EVE LAB_dev (n=136/97)"),
        ("cpu100_eve", "EVE CPU-100 (n=33/19)"), ("REAL_free", "free REAL"), ("REAL_json", "json REAL")]

res = {r["file"]: r for r in csv.DictReader(open(sys.argv[1], encoding="utf-8"))}
f3 = lambda v: f"{float(v):.3f}"


def files(spec):
    if isinstance(spec, str):  # thu muc task21
        return {"REAL_eve": f"{T21}{spec}/REAL_eve", "REAL_json_enum": f"{T21}{spec}/REAL_json_enum",
                "LAB_dev_eve": f"{T21}{spec}/LAB_dev_eve", "cpu100_eve": f"{T21}{spec}/cpu_eve"}
    return {k: A + v for k, v in spec.items()}


out = []
for name, org, pb, spec in MODELS + BASE:
    row = {"model": name, "org": org, "params_b": pb}
    for k, _ in COLS:
        f = files(spec).get(k)
        r = res.get(f + ".jsonl") if f else None
        if f and not r and not f.endswith("/cpu_eve"):
            raise SystemExit(f"thieu {f}")
        if r:
            row.update({f"{k}_top1": f3(r["top1"]), f"{k}_hits": r["hits"], f"{k}_n": r["n_labeled"],
                        f"{k}_in_scope": f3(r["top1_in_scope"]), f"{k}_file": r["file"]})
    out.append(row)

keys = ["model", "org", "params_b"] + [f"{k}_{s}" for k, _ in COLS for s in ("top1", "hits", "n", "in_scope", "file")]
with open(sys.argv[2] + ".csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, keys); w.writeheader(); w.writerows(out)
cell = lambda r, k: f"{r[k + '_top1']} / {r[k + '_in_scope']}" if k + "_top1" in r else "-"
md = ["# So sanh model - TTP top-1 (check_top1.py, lan chay moi nhat)", "",
      "Moi o: **top-1 toan bo / top-1 trong pham vi KB** (10 ky thuat KB v0.1), so khop o muc ky thuat cha.",
      "REAL = REAL_test_matched 1000 alert (266 co nhan TTP, 166 trong KB). CPU-100 = 100 alert dau. KB v0.1. Xep theo so tham so.", "",
      "| model | to chuc | tham so (B) | " + " | ".join(h for _, h in COLS) + " |", "|---" * (3 + len(COLS)) + "|"]
md += [f"| {r['model']} | {r['org']} | {'' if r['params_b'] is None else r['params_b']} | "
       + " | ".join(cell(r, k) for k, _ in COLS) + " |" for r in out]
md += ["", "## File nguon (goc `results/`)", "", "| model | cot | file |", "|---|---|---|"]
md += [f"| {r['model']} | {k} | `{r[k + '_file'].removeprefix('results/')}` |" for r in out for k, _ in COLS if k + "_file" in r]
Path(sys.argv[2] + ".md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("\n".join(md[:7 + len(out)]))
