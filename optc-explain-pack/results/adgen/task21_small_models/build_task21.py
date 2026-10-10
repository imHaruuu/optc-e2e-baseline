"""Tong hop task21 (moi model mot thu muc con <slug>/) -> SUMMARY.md, summary.json, figures_data.csv, hw_index.csv.
Model chua chay du (thieu eval.json) duoc ghi trang thai, khong vao bang. Chay: python build_task21.py <thu muc task21>
"""
import csv
import json
import sys
from pathlib import Path

R = Path(sys.argv[1])
STEPS = ("REAL_eve", "LAB_dev_eve", "REAL_json_enum", "cpu_eve")


def f3(x):
    return "-" if x is None else f"{x:.3f}"


def ci(c):
    return "-" if not c else f"[{c[0]:.3f}, {c[1]:.3f}]"


def pct(x):
    return "-" if x is None else f"{100 * x:.1f}%"


def nlines(p):
    return sum(1 for _ in open(p, encoding="utf-8")) if p.exists() else 0


def hw_step(d, step):
    """Cac lan chay cua 1 buoc (ke ca lan OOM): tong wall, so lan, batch cuoi; thong so phan cung lay tu lan thanh cong."""
    runs = []
    for f in sorted((d / "hw").glob(f"{step}_*.hw.json")):
        h = json.loads(f.read_text(encoding="utf-8"))
        if h["run"].get("wall_s") is None and h.get("samples"):  # tien trinh bi kill: lay t_s mau cuoi
            h["run"]["wall_s"] = h["samples"][-1][0]
        runs.append((f, h))
    if not runs:
        return None, []
    idx = [{"file": str(f.relative_to(R)).replace("\\", "/"), "step": step, "batch": h["run"]["labels"].get("batch"),
            "device": h["run"]["labels"].get("device"), "start": h["run"]["start"], "end": h["run"].get("end"),
            "wall_s": h["run"].get("wall_s"), "returncode": h["run"].get("returncode"),
            "n_samples": h["run"].get("n_samples"), "status": h["run"].get("status")} for f, h in runs]
    ok = [(f, h) for f, h in runs if h["run"].get("returncode") == 0]
    f, h = max(runs, key=lambda x: x[1]["run"].get("wall_s") or 0)  # lan chay dai nhat = dai dien
    s = h["summary"]
    g = lambda k, st="max": (s.get(k) or {}).get(st)  # noqa: E731
    wall = h["run"].get("wall_s") or 0
    pw = g("gpu0_power_w", "mean")
    agg = {"ok": bool(ok), "attempts": len(runs), "wall_s_total": round(sum(r["wall_s"] or 0 for r in idx), 1),
           "wall_s_final": wall, "batch_final": h["run"]["labels"].get("batch"),
           "gpu_mem_peak_gib": None if g("gpu0_mem_used_mib") is None else round(g("gpu0_mem_used_mib") / 1024, 2),
           "gpu_util_mean": None if g("gpu0_util_pct", "mean") is None else round(g("gpu0_util_pct", "mean"), 1),
           "gpu_power_mean_w": None if pw is None else round(pw, 1),
           "gpu_energy_wh": None if pw is None else round(pw * wall / 3600, 1),
           "proc_rss_peak_gb": g("proc_rss_gb"), "proc_cpu_mean_pct": g("proc_cpu_pct", "mean"),
           "ram_used_peak_gb": g("ram_used_gb"), "hw_file": str(f.relative_to(R)).replace("\\", "/")}
    return agg, idx


models = json.loads((R / "models.json").read_text(encoding="utf-8"))
out, flat, hw_index, status = {}, [], [], []
t3, t4, t5, tg, t7 = [], [], [], [], []
for m in models:
    d, name = R / m["slug"], m["id"].split("/")[1]
    counts = {s: nlines(d / f"{s}.jsonl") for s in STEPS}
    hw = {}
    for s in STEPS:
        agg, idx = hw_step(d, s)
        if agg:
            hw[s] = agg
            hw_index += [{"slug": m["slug"], **r} for r in idx]
    done = (d / "eval.json").exists() and (d / "paired.json").exists() and (d / "random_in_c.json").exists()
    status.append(f"| {name} | {m['params_b']} | {m['dtype_gpu']} | "
                  + " | ".join(str(counts[s]) for s in STEPS) + f" | {'xong' if done else ('dở dang' if any(counts.values()) else 'chưa chạy')} |")
    rec = {"id": m["id"], "slug": m["slug"], "params_b": m["params_b"], "dtype_gpu": m["dtype_gpu"],
           "counts": counts, "hw": hw, "complete_gpu": done}
    out[m["slug"]] = rec
    if not done:
        continue
    ev = json.loads((d / "eval.json").read_text(encoding="utf-8"))
    e = next(x for x in ev if x["mode"] == "eve")
    j = next((x for x in ev if x["mode"] == "json_enum"), None)
    et, ee, ev_v = e["ttp"], e.get("evidence") or {}, e.get("verdict") or {}
    jt = (j or {}).get("ttp") or {}
    rc = json.loads((d / "random_in_c.json").read_text(encoding="utf-8"))[0]
    pb = json.loads((d / "paired.json").read_text(encoding="utf-8"))
    rec.update(eve={"ttp": et, "evidence": ee, "verdict": ev_v, "latency": e.get("latency")},
               json_enum={"ttp": jt, "evidence": (j or {}).get("evidence"), "latency": (j or {}).get("latency")},
               random_in_c=rc, paired=pb)
    t3.append(f"| {name} | {f3(et['acc_top1'])} {ci(et.get('acc_top1_ci'))} | {f3(et.get('acc_top1_in_scope'))} | "
              f"{f3(ee.get('entailment_ok'))} | {f3(ee.get('minimal_ok'))} | {pct(et.get('undetermined_rate'))} | "
              f"{f3(jt.get('acc_top1'))} {ci(jt.get('acc_top1_ci'))} | {f3(ev_v.get('auc'))} {ci(ev_v.get('auc_ci'))} |")
    row = {"slug": m["slug"], "model": m["id"], "params_b": m["params_b"], "dtype_gpu": m["dtype_gpu"],
           "eve_top1": et["acc_top1"], "eve_top1_lo": et["acc_top1_ci"][0], "eve_top1_hi": et["acc_top1_ci"][1],
           "eve_top1_in_scope": et.get("acc_top1_in_scope"), "eve_entailment": ee.get("entailment_ok"),
           "eve_minimal": ee.get("minimal_ok"), "eve_undetermined": et.get("undetermined_rate"),
           "json_enum_top1": jt.get("acc_top1"), "json_enum_top1_lo": (jt.get("acc_top1_ci") or [None])[0],
           "json_enum_top1_hi": (jt.get("acc_top1_ci") or [None, None])[1],
           "json_enum_entailment": ((j or {}).get("evidence") or {}).get("entailment_ok"),
           "verdict_auc": ev_v.get("auc"), "verdict_auc_lo": (ev_v.get("auc_ci") or [None])[0],
           "verdict_auc_hi": (ev_v.get("auc_ci") or [None, None])[1],
           "eve_gpu_latency_ms": (e.get("latency") or {}).get("mean_ms"),
           "json_enum_gpu_latency_ms": ((j or {}).get("latency") or {}).get("mean_ms")}
    for cmp in pb["comparisons"]:
        p, a, b = cmp["all"], cmp["a"]["name"], cmp["b"]["name"]
        t4.append(f"| {name} | {b} | {p['n']} | {f3(p[f'acc_{a}'])} | {f3(p[f'acc_{b}'])} | {p['diff']:+.4f} | "
                  f"{ci(p['diff_ci'])} | {p[f'only_{a}_correct']} / {p[f'only_{b}_correct']} | {p['p_mcnemar_exact']:.3f} |")
        row.update({f"vs_{b}_diff": p["diff"], f"vs_{b}_diff_lo": p["diff_ci"][0], f"vs_{b}_diff_hi": p["diff_ci"][1],
                    f"vs_{b}_only_model": p[f"only_{a}_correct"], f"vs_{b}_only_ref": p[f"only_{b}_correct"],
                    f"vs_{b}_p_mcnemar": p["p_mcnemar_exact"]})
    gc = rc["C_ge_2"]
    t5.append(f"| {name} | {gc['n']} | {f3(gc['acc_system'])} | {f3(gc['acc_random_expected'])} {ci(gc['acc_random_ci95'])} | "
              f"{gc['p_random_ge_system']:.3f} | {f3(gc['oracle_in_C'])} |")
    row.update(c2_n=gc["n"], c2_acc=gc["acc_system"], c2_random=gc["acc_random_expected"], c2_p=gc["p_random_ge_system"],
               c2_oracle=gc["oracle_in_C"])
    for s in ("REAL_eve", "LAB_dev_eve", "REAL_json_enum"):
        h = hw.get(s) or {}
        tg.append(f"| {name} | {s} | {h.get('attempts', '-')} | {h.get('batch_final', '-')} | "
                  f"{(h.get('wall_s_total') or 0) / 60:.1f} | {h.get('gpu_mem_peak_gib', '-')} | {h.get('gpu_util_mean', '-')} | "
                  f"{h.get('gpu_power_mean_w', '-')} | {h.get('gpu_energy_wh', '-')} | {h.get('proc_rss_peak_gb', '-')} |")
        row.update({f"{s}_wall_min": round((h.get("wall_s_total") or 0) / 60, 2), f"{s}_batch": h.get("batch_final"),
                    f"{s}_gpu_mem_peak_gib": h.get("gpu_mem_peak_gib"), f"{s}_gpu_util_mean": h.get("gpu_util_mean"),
                    f"{s}_gpu_energy_wh": h.get("gpu_energy_wh")})
    c = d / "cpu_eve.jsonl"
    if counts["cpu_eve"] >= 100:
        lat = sorted(json.loads(x)["latency_ms"] for x in open(c, encoding="utf-8"))
        h = hw.get("cpu_eve") or {}
        cpu = {"n": len(lat), "mean_ms": sum(lat) / len(lat), "p50_ms": lat[len(lat) // 2],
               "p90_ms": lat[int(0.9 * (len(lat) - 1))], "rss_peak_gb": h.get("proc_rss_peak_gb")}
        rec["cpu"] = cpu
        t7.append(f"| {name} | {cpu['n']} | {cpu['mean_ms']:.0f} | {cpu['p50_ms']:.0f} | {cpu['p90_ms']:.0f} | "
                  f"{f3(cpu['rss_peak_gb'])} |")
        row.update(cpu_mean_ms=cpu["mean_ms"], cpu_p50_ms=cpu["p50_ms"], cpu_p90_ms=cpu["p90_ms"],
                   cpu_rss_peak_gb=cpu["rss_peak_gb"])
    flat.append(row)

run = json.loads((R / "run.json").read_text(encoding="utf-8")) if (R / "run.json").exists() else {}
md = ["# task21: các SLM nhỏ (≤ ~5B) trên REAL_test_matched\n",
      "REAL_test_matched (1000 alert, 266 có nhãn TTP), KB v0.1. GPU RTX 5070 Ti 16 GB; CPU Ryzen 9 9950X; transformers 5.17, torch 2.11.",
      "dtype GPU: fp32 nếu ≤ 2.7B tham số, bf16 nếu lớn hơn. OOM → runner tự giảm batch (kết quả không đổi, chỉ đổi tốc độ).",
      f"Code: git {run.get('git', '?')}; từ EXAONE trở đi thêm 7f1e7c9 (giới hạn bộ nhớ CUDA 92%, chỉ ảnh hưởng tốc độ).",
      "Dừng theo yêu cầu sau AI21-Jamba2-3B: 11 model còn lại chưa chạy; lượt CPU (Bảng 7) mới đo ERNIE-4.5-0.3B (07/10).",
      "Đường dẫn và cấu trúc file: xem TREE.md. Số liệu phẳng cho vẽ hình: figures_data.csv; chuỗi thời gian phần cứng: hw_index.csv → *.hw.json.\n",
      "## Trạng thái (số dòng kết quả)\n",
      "| model | tham số (B) | dtype GPU | REAL_eve | LAB_dev_eve | REAL_json_enum | cpu_eve | trạng thái |",
      "|---|---|---|---|---|---|---|---|", *status,
      "\n## Bảng 3 (RQ1)\n",
      "| model | EVE TTP top-1 [CI 95%] | trong phạm vi KB | entailment | minimal | không xác định | json_enum TTP top-1 [CI 95%] | verdict AUC (EVE) [CI 95%] |",
      "|---|---|---|---|---|---|---|---|", *t3,
      "\n## Bảng 4 (RQ2) – CI ghép cặp, bootstrap 10 000 + McNemar exact\n",
      "kb_first = kb_only first (task09, KB v0.1); q05_eve = Qwen2.5-0.5B EVE (00_core).\n",
      "| model | so với | n | acc model | acc đối chứng | chênh | CI chênh | chỉ model đúng / chỉ đối chứng đúng | p McNemar |",
      "|---|---|---|---|---|---|---|---|---|", *t4,
      "\n## Bảng 5 (RQ2) – so với chọn ngẫu nhiên trong C(E), nhóm \\|C\\| ≥ 2\n",
      "| model | n | EVE | ngẫu nhiên [CI 95%] | p | trần (gold ∈ C) |", "|---|---|---|---|---|---|", *t5,
      "\n## Chi phí GPU (hwmon)\n",
      "Số lần = số lần chạy kể cả lần OOM; thời gian = tổng mọi lần; các cột phần cứng lấy từ lần chạy dài nhất.",
      "EXAONE REAL_eve: 999 alert đầu chạy khi VRAM tràn sang RAM hệ thống (trước 7f1e7c9), tiến trình bị dừng tay rồi "
      "chạy tiếp 1 alert; thời gian và phần cứng của bước này phản ánh lúc tràn.\n",
      "| model | bước | số lần | batch cuối | thời gian (phút) | VRAM đỉnh (GiB) | GPU util TB (%) | công suất TB (W) | năng lượng (Wh) | RAM tiến trình đỉnh (GB) |",
      "|---|---|---|---|---|---|---|---|---|---|", *tg,
      "\n## Bảng 7 (chi phí) – CPU fp32 16 thread, 100 alert đầu\n"]
md += (["| model | n | latency TB (ms) | p50 (ms) | p90 (ms) | RAM đỉnh (GB) |", "|---|---|---|---|---|---|", *t7]
       if t7 else ["Chưa chạy (dừng theo yêu cầu trước pha CPU)."])
md.append("")
(R / "SUMMARY.md").write_text("\n".join(md), encoding="utf-8")
(R / "summary.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
for fn, rows in (("figures_data.csv", flat), ("hw_index.csv", hw_index)):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(R / fn, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
print(f"{len(flat)}/{len(models)} model day du GPU -> {R / 'SUMMARY.md'}, summary.json, figures_data.csv, hw_index.csv")
