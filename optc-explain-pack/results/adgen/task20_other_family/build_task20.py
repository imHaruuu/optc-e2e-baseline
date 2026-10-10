"""Tong hop task20 (moi model mot thu muc con: minicpm5_2b/, k2_horizon_3_7b/) (K2-Horizon-3.7B, MiniCPM5-2B) thanh bang 3/4/5/7 -> SUMMARY.md + summary.json."""
import json
import sys
from pathlib import Path

R = Path(sys.argv[1])
MODELS = [("mc5", "MiniCPM5-2B", "openbmb/MiniCPM5-2B", "fp32 GPU / fp32 CPU", "minicpm5_2b"),
          ("k2h", "K2-Horizon-3.7B", "IFM/K2-Horizon-3.7B @d6e5432", "bf16 GPU / fp32 CPU", "k2_horizon_3_7b")]


def f3(x):
    return "-" if x is None else f"{x:.3f}"


def ci(c):
    return "-" if not c else f"[{c[0]:.3f}, {c[1]:.3f}]"


def pct(x):
    return "-" if x is None else f"{100 * x:.1f}%"


out = {}
t3, t4, t5, t7 = [], [], [], []
for tag, name, hf, dt, sub in MODELS:
    D = R / sub
    ev = {Path(x["file"]).name: x for x in json.loads((D / f"eval_{tag}.json").read_text(encoding="utf-8"))}
    e, j = ev[f"{tag}_REAL_eve.jsonl"], ev[f"{tag}_REAL_json_enum.jsonl"]
    et, ee, jt = e["ttp"], e.get("evidence") or {}, j["ttp"]
    rc = json.loads((D / f"random_in_c_{tag}.json").read_text(encoding="utf-8"))[0]
    pb = json.loads((D / f"paired_{tag}.json").read_text(encoding="utf-8"))
    rows = [json.loads(l) for l in open(D / f"{tag}_cpu_eve.jsonl", encoding="utf-8")]
    lat = sorted(r["latency_ms"] for r in rows)
    mem = json.loads((D / f"mem_{tag}_cpu_eve.json").read_text(encoding="utf-8"))
    cpu = {"n": len(lat), "mean_ms": sum(lat) / len(lat), "p50_ms": lat[len(lat) // 2],
           "p90_ms": lat[int(0.9 * (len(lat) - 1))], "rss_peak_gb": mem["rss_peak_gb"],
           "rss_mean_gb": mem["rss_mean_gb"], "wall_s": mem["wall_s"]}
    out[tag] = {"model": hf, "dtype": dt, "eve": {"ttp": et, "evidence": ee, "verdict": e.get("verdict")},
                "json_enum": {"ttp": jt}, "random_in_c": rc, "paired": pb, "cpu": cpu}
    t3.append(f"| {name} | {f3(et['acc_top1'])} {ci(et.get('acc_top1_ci'))} | {f3(et.get('acc_top1_in_scope'))} | "
              f"{f3(ee.get('entailment_ok'))} | {f3(ee.get('minimal_ok'))} | {pct(et.get('undetermined_rate'))} | "
              f"{f3(jt['acc_top1'])} {ci(jt.get('acc_top1_ci'))} | {f3((e.get('verdict') or {}).get('auc'))} |")
    for cmp in pb["comparisons"]:
        p, a, b = cmp["all"], cmp["a"]["name"], cmp["b"]["name"]
        t4.append(f"| {name} | {b} | {p['n']} | {f3(p[f'acc_{a}'])} | {f3(p[f'acc_{b}'])} | {p['diff']:+.4f} | "
                  f"{ci(p['diff_ci'])} | {p[f'only_{a}_correct']} / {p[f'only_{b}_correct']} | {p['p_mcnemar_exact']:.3f} |")
    g = rc["C_ge_2"]
    t5.append(f"| {name} | {g['n']} | {f3(g['acc_system'])} | {f3(g['acc_random_expected'])} {ci(g['acc_random_ci95'])} | "
              f"{g['p_random_ge_system']:.3f} | {f3(g['oracle_in_C'])} |")
    t7.append(f"| {name} | {cpu['n']} | {cpu['mean_ms']:.0f} | {cpu['p50_ms']:.0f} | {cpu['p90_ms']:.0f} | "
              f"{cpu['rss_peak_gb']:.2f} |")

md = [f"# Họ SLM khác: K2-Horizon-3.7B, MiniCPM5-2B\n",
      "REAL_test_matched (1000 alert, 266 có nhãn TTP), KB v0.1. GPU RTX 5070 Ti; CPU Ryzen 9 9950X fp32 16 thread, 100 alert đầu.",
      "K2-Horizon: `--trust_remote_code --revision d6e5432` (code đã đọc), bf16 trên GPU (fp32 cần ~20 GB > 16 GB VRAM), fp32 trên CPU; khối `<ifm|think>` được đóng rỗng (tương đương enable_thinking=False). MiniCPM5: enable_thinking=False.\n",
      "## Bảng 3 (RQ1)\n",
      "| model | EVE TTP top-1 [CI 95%] | trong phạm vi KB | entailment | minimal | không xác định | json_enum TTP top-1 [CI 95%] | verdict AUC (EVE) |",
      "|---|---|---|---|---|---|---|---|", *t3,
      "\n## Bảng 4 (RQ2) – CI ghép cặp, bootstrap 10 000 + McNemar exact\n",
      "| model | so với | n | acc model | acc đối chứng | chênh | CI chênh | chỉ model đúng / chỉ đối chứng đúng | p McNemar |",
      "|---|---|---|---|---|---|---|---|---|", *t4,
      "\n## Bảng 5 (RQ2) – so với chọn ngẫu nhiên trong C(E), nhóm \\|C\\| ≥ 2\n",
      "| model | n | EVE | ngẫu nhiên [CI 95%] | p | trần (gold ∈ C) |", "|---|---|---|---|---|---|", *t5,
      "\n## Bảng 7 (chi phí) – CPU, 100 alert đầu\n",
      "| model | n | latency TB (ms) | p50 (ms) | p90 (ms) | RAM đỉnh (GB) |", "|---|---|---|---|---|---|", *t7, ""]
(R / "SUMMARY.md").write_text("\n".join(md), encoding="utf-8")
(R / "summary.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print("\n".join(md))
