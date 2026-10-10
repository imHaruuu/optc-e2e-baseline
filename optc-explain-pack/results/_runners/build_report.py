"""Gom so lieu task.docx (viec 1-12) vao mot thu muc + SUMMARY.md + summary.json, roi nen 7z."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

R = Path("E:/Code/optc-e2e-baseline/optc-explain-pack/results")
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("E:/Code/optc-e2e-baseline/optc-explain-pack/task_results_2026-10-04")
A = R / "adgen"
K = R / "attackdata"
J = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
f3 = lambda x: "-" if x is None else (f"{x:.3f}" if isinstance(x, float) else str(x))
pc = lambda x: "-" if x is None else f"{100 * x:.1f}%"
ms = lambda x: "-" if x is None else f"{x:.0f}"

# viec -> (thu muc nguon, danh sach file/glob can lay)
COPY = {
    "task01_attackdata_desc": (K / "task01_desc", ["*.json", "run.json"]),
    "task02_silver_gold": (K / "task02_silver_gold", ["*.json"]),
    "task03_gen_rerun": (A / "task03_gen_rerun", ["eval_*.json", "*.summary.json", "run.json"]),
    "task04_cpu_15b": (A / "task04_cpu_15b", ["*.json"]),
    "task05_11_conformal_route": (A / "task05_conformal_route", ["*.json"]),
    "task06_json_enum_check": (A / "task06_json_enum_check", ["*.json"]),
    "task07_paired_ci": (A / "task07_paired_ci", ["ci_*.json", "run.json"]),
    "task08_qwen3_06b": (A / "task08_qwen3_06b", ["eval_*.json", "*.summary.json", "run.json"]),
    "task09_kb_v2": (A / "task09_kb_v2", ["eval_*.json", "kbstats_*.json", "run.json"]),
    "task10_inject_adaptive": (A / "task10_inject_adaptive", ["inj_*.json", "*.summary.json", "run.json"]),
    "task12_pareto_cpu": (A / "task12_pareto_cpu", ["eval_cpu_all.json", "pareto_cpu.png", "pareto_cpu.svg", "pareto_cpu_mpl.csv", "run.json"]),
}


def ttp_row(t):
    tt, v, e = t.get("ttp") or {}, t.get("verdict") or {}, t.get("evidence") or {}
    return (Path(t["file"]).stem, t.get("mode"), (t.get("model") or "-").rsplit("/", 1)[-1], f3(tt.get("acc_top1")),
            str(tt.get("acc_top1_ci") or "-"), f3(tt.get("acc_top1_in_scope")), f3(v.get("auc")),
            f3(e.get("entailment_ok")), ms((t.get("latency") or {}).get("mean_ms")))


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


EVAL_HEAD = ["file", "mode", "model", "TTP top-1", "CI 95%", "in-scope", "verdict AUC", "entail", "ms/alert"]
md, S = ["# Ket qua task.docx (viec 1-12)", "",
         "Tap mac dinh: REAL_test_matched (1000 alert, 266 alert malicious co nhan TTP), LAB -> REAL. "
         "GPU = RTX 5070 Ti; CPU = Ryzen 9 9950X (fp32, 16 thread). KB v0.1 tru khi ghi ro (viec 9 do v0.2).", ""], {}


def section(title, body):
    md.extend([f"## {title}", "", body, ""])


# Viec 1
d = J(K / "task01_desc/attackdata_stats_kb_v0.1.json")
S["task01"] = {k: d[k] for k in ("n_alerts", "by_label_source", "n_techniques", "events_per_alert", "kb", "overlap_real_test")}
top = ", ".join(f"{t} {n}" for t, n in list(d["technique_distribution"].items())[:8])
section("Viec 1 - Mo ta attack_data", "\n".join([
    f"- Nguon: {d['source']['repo']} (nhan technique tu .yml, muc file). {d['n_alerts']} alert "
    f"(tree {d['by_label_source'].get('tree')}, rare {d['by_label_source'].get('rare')}), {d['n_techniques']} technique, "
    f"{d['n_subtechniques']} sub-technique; event/alert median {d['events_per_alert']['median']}.",
    f"- Phan bo technique (top 8): {top}.",
    f"- KB v0.1: kb_scope {pc(d['kb']['kb_scope'])}, C(E) khac rong {pc(d['kb']['nonempty_C_rate'])}, "
    f"kb_recall_in_scope {pc(d['kb']['kb_recall_in_scope'])}.",
    f"- Trung REAL test: {d['overlap_real_test']['n_shared_techniques']} technique chung; "
    f"{pc(d['overlap_real_test']['share_alerts_with_technique_seen_in_real'])} alert co technique da xuat hien trong REAL; "
    f"trung nguyen van {d['overlap_real_test']['exact_text_duplicates_with_real']}."]))

# Viec 2
d = J(K / "task02_silver_gold/silver_gold.json")
g = J(K / "task02_silver_gold/eval_gold_field.json")
S["task02"] = {k: {x: d[k][x] for x in ("n", "n_with_gold", "gold_coverage", "agree_any", "cohen_kappa")} for k in ("all", "tree", "rare")}
rows = [(k, d[k]["n"], d[k]["n_with_gold"], pc(d[k]["gold_coverage"]), pc(d[k]["agree_any"]), f3(d[k]["cohen_kappa"]))
        for k in ("tree", "rare", "all")]
grows = [(Path(t["file"]).stem, t["evidence"].get("gold_n"), f3(t["evidence"].get("gold_field_precision")),
          f3(t["evidence"].get("gold_field_recall")), f3(t["evidence"].get("gold_technique_acc"))) for t in g]
section("Viec 2 - Silver (.yml) vs gold (atomic test trong cay tien trinh)",
        table(["nhom", "n", "co gold", "do phu gold", "khop", "Cohen kappa"], rows) +
        "\n\ngold_field P/R (eval_eve --gold, gold.jsonl 150 mau do 7B gan -> chi la silver):\n\n" +
        table(["he thong", "n gold", "field P", "field R", "technique acc"], grows))

# Viec 3
p3 = A / "task03_gen_rerun"
ev3 = [t for f in sorted(p3.glob("eval_*_gen.json")) for t in J(f)]
rows = []
for t in ev3:
    e = t["evidence"]
    rows.append((Path(t["file"]).stem, f3(t["ttp"].get("acc_top1")), pc(t["ttp"].get("no_prediction_rate")),
                 pc(e.get("generated_valid_technique_id")), pc(e.get("generated_evidence_fabricated")),
                 pc(e.get("generated_no_parseable_evidence")), ms(t["latency"].get("mean_ms"))))
S["task03"] = [dict(zip(["file", "ttp_top1", "no_pred", "valid_id", "fabricated", "no_parseable_ev", "ms"], r)) for r in rows]
section("Viec 3 - free / json chay lai (parser moi, max_new_tokens 384, --attack_map v15.1)",
        table(["file", "TTP top-1", "khong du doan", "ID hop le", "evidence bia", "khong parse duoc evidence", "ms/alert"], rows) +
        "\n\nParser cu lay nham ID technique tu duong dan trong evidence (vd atomics\\T1087.002) -> so cu bi thoi phong.")

# Viec 4
m = J(A / "task04_cpu_15b/mem_q15_cpu_eve.json")
s4 = J(A / "task04_cpu_15b/q15_cpu_eve.jsonl.summary.json")
S["task04"] = {"latency_ms_mean": s4["latency_ms_mean"], "latency_ms_p90": s4["latency_ms_p90"],
               "rss_peak_gb": m["rss_peak_gb"], "rss_mean_gb": m["rss_mean_gb"], "n": s4["n"]}
section("Viec 4 - Qwen2.5-1.5B tren CPU (eve, 100 alert dau)",
        f"Latency trung binh {s4['latency_ms_mean']:.0f} ms, p90 {s4['latency_ms_p90']:.0f} ms; RSS dinh {m['rss_peak_gb']} GB, "
        f"trung binh {m['rss_mean_gb']} GB (fp32, batch 8, max_len 4096). Lan do bi nhieu (_contended) cho so gan nhu bang.")

# Viec 5 + 11
c = J(A / "task05_conformal_route/conformal_q05.json")
r = J(A / "task05_conformal_route/conformal_route.json")
S["task11_ess"] = c["weight_stats"]
rows = [(k, x["alpha"], x["rule"], pc(x["escalate_rate"]), f3(x["acc_kept_small"]), f3(x["acc_escalated_small"]),
         f3(x["acc_escalated_big"]), f3(x["acc_system"]), x["recovered_by_big"], x["harmed_by_big"],
         ms(x["latency_ms_mean_system"])) for k in ("unweighted", "weighted") for x in r[k]]
S["task05"] = {"baselines": r["baselines"], "routes": rows}
crow = [(k, x["alpha"], f3(x["coverage_inscope"]), x["target_inscope"], f3(x["avg_set_size_inscope"]), x["bound_holds"])
        for k in ("unweighted", "weighted") for x in c[k]]
ws = c["weight_stats"]
section("Viec 5 - Dinh tuyen conformal (giu 0.5B / escalate 7B)",
        f"Chi dung 0.5B: acc {r['baselines']['small_only']['acc']}, {r['baselines']['small_only']['latency_ms_mean']} ms; "
        f"chi dung 7B: acc {r['baselines']['big_only']['acc']}, {r['baselines']['big_only']['latency_ms_mean']} ms.\n\n" +
        table(["quantile", "alpha", "luat", "escalate", "acc giu (0.5B)", "acc escalate 0.5B", "acc escalate 7B",
               "acc he thong", "7B sua dung", "7B lam sai", "ms/alert"], rows))
section("Viec 11 - Effective sample size (conformal weighted)",
        f"calib n = {ws['calib_n']}, ESS = {ws['calib_ess']:.1f} (ty le {ws['calib_ess_ratio']:.3f}); w in [{ws['calib_w_min']:.3f}, "
        f"{ws['calib_w_max']:.3f}], w test trung binh {ws['test_mean']:.2f}.\n\n" +
        table(["quantile", "alpha", "coverage in-scope", "muc tieu", "|set| TB", "bound dung"], crow))

# Viec 6
d = J(A / "task06_json_enum_check/json_enum_check.json")
rows = [(Path(x["file"]).stem, x["n"], x["n_ok"], x["duplicates"], x["missing"], x["n_distinct_pred"], x["top_pred"],
         pc(x["top_pred_share"]), f3(x["pred_entropy_bits"]), f3(x["ttp_acc_top1"])) for x in d]
S["task06"] = rows
section("Viec 6 - Kiem tra json_enum", table(["file", "n", "du n", "trung", "thieu", "so nhan du doan", "nhan nhieu nhat",
                                               "ty le", "entropy (bit)", "TTP top-1"], rows))

# Viec 7
rows = []
for f in sorted((A / "task07_paired_ci").glob("ci_*.json")):
    d = J(f)
    for cmp_ in d["comparisons"]:
        x = cmp_.get("all") or {}
        a, b = cmp_["a"]["name"], cmp_["b"]["name"]
        rows.append((d["name"], f"{a} - {b}", x.get("n"), f3(x.get(f"acc_{a}")), str(x.get(f"ci_{a}")), f3(x.get(f"acc_{b}")),
                     str(x.get(f"ci_{b}")), f3(x.get("diff")), str(x.get("diff_ci")), f3(x.get("p_mcnemar_exact"))))
S["task07"] = rows
section("Viec 7 - Bootstrap CI ghep cap (10000 lan) + McNemar", table(
    ["tap", "so sanh", "n", "acc A", "CI A", "acc B", "CI B", "chenh", "CI chenh", "p McNemar"], rows))

# Viec 8
ev = J(A / "task08_qwen3_06b/eval_qwen3_vs_q25.json")
S["task08"] = [ttp_row(t) for t in ev]
section("Viec 8 - Them ho SLM: Qwen3-0.6B", table(EVAL_HEAD, [ttp_row(t) for t in ev]) +
        "\n\nLatency do o cac thoi diem tai GPU khac nhau, khong so sanh toc do giua model.")

# Viec 9
rows = []
for ds in ("adgen", "attackdata"):
    a1, a2 = J(A / f"task09_kb_v2/kbstats_{ds}_v0.1.json"), J(A / f"task09_kb_v2/kbstats_{ds}_v0.2.json")
    for t in ("T1036", "T1553", "T1047"):
        p1, p2 = a1["per_technique"].get(t) or {}, a2["per_technique"].get(t) or {}
        rows.append((ds, t, p1.get("n_gold"), pc(p1.get("recall")), pc(p2.get("recall")), pc(p1.get("precision_mal")),
                     pc(p2.get("precision_mal")), pc(p1.get("benign_fire")), pc(p2.get("benign_fire"))))
S["task09_kbstats"] = rows
ev = J(A / "task09_kb_v2/eval_REAL_v1_vs_v2.json") + J(A / "task09_kb_v2/eval_attackdata_v1_vs_v2.json")
section("Viec 9 - KB v0.2 (T1036 / T1553 / T1047 viet lai)",
        table(["tap", "technique", "n gold", "recall v0.1", "recall v0.2", "prec v0.1", "prec v0.2", "benign fire v0.1",
               "benign fire v0.2"], rows) + "\n\nEVE / kb_only tren REAL_test_matched va attack_data:\n\n" +
        table(EVAL_HEAD, [ttp_row(t) for t in ev]))

# Viec 10
rows = []
for p in ("attested_rename", "attested_instruction"):
    for s in ("eve", "eve_att", "json_enum", "kb_only"):
        x = J(A / f"task10_inject_adaptive/inj_{s}_{p}.json")
        rows.append((p, s, x["n"], pc(x["verdict_flip_rate"]), pc(x["mal_to_benign_rate"]), pc(x["technique_change_rate"]),
                     pc(x["kb_candidates_change_rate"]), pc(x["technique_change_via_unattested_rate"])))
S["task10"] = rows
section("Viec 10 - Payload thich ung vao field attested (Image)", table(
    ["payload", "he thong", "n", "verdict lat", "mal->benign", "TTP doi", "C(E) doi", "doi qua field khong attested"], rows) +
    "\n\nattested_rename = doi ten binary thanh powershell.exe; attested_instruction = cau lenh du trong ten thu muc.")

# Viec 12
ev = J(A / "task12_pareto_cpu/eval_cpu_all.json")
S["task12"] = [ttp_row(t) for t in ev]
section("Viec 12 - Pareto chi latency CPU (100 alert dau, 33 co nhan TTP)",
        table(EVAL_HEAD, [ttp_row(t) for t in ev]) + "\n\nHinh: task12_pareto_cpu/pareto_cpu.png")

if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
for name, (src, pats) in COPY.items():
    dst = OUT / name
    dst.mkdir()
    for pat in pats:
        for f in sorted(src.glob(pat)):
            shutil.copy2(f, dst / (f.name if f.name != "run.json" else "run_info.json"))
(OUT / "SUMMARY.md").write_text("\n".join(md), encoding="utf-8")
(OUT / "summary.json").write_text(json.dumps(S, indent=1, ensure_ascii=False), encoding="utf-8")
arc = OUT.with_suffix(".7z")
arc.unlink(missing_ok=True)
subprocess.run(["C:/Program Files/7-Zip/7z.exe", "a", "-t7z", "-mx=9", "-bso0", "-bsp0", str(arc), str(OUT)], check=True)
print("wrote", arc, sum(1 for _ in OUT.rglob("*") if _.is_file()), "files")
