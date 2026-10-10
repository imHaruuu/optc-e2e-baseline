"""Review muc 1 + 2.
1) json_enum co trung majority do loi eval khong: so vector dung/sai theo mau, dem lai doc lap tu file data.
2) 0.5B free/json: vi sao khong ra technique (no_prediction) - phan loai + 10 output tho.
  python eval_parser_checks.py <outdir>
"""
import collections
import json
import random
import re
import sys

sys.path.insert(0, "E:/Code/optc-e2e-baseline/.claude/worktrees/optc-file-analysis-305df4/optc-explain-pack")
from eve import TECH_RE, get_ci, loads_lenient  # noqa: E402

OUT = sys.argv[1]
A = "results/adgen"
T = "../P1/Output/data/splits/REAL_test_matched.jsonl"
data = {json.loads(l)["sample_id"]: json.loads(l) for l in open(T, encoding="utf-8")}


def load(p):
    return [json.loads(l) for l in open(p, encoding="utf-8")]


# ---- 1. json_enum vs majority ----
res1 = []
for p, lim in [(f"{A}/stt39_anchored_json_enum/q05_REAL_json_enum.jsonl", None),
               (f"{A}/stt58b_cpu_latency/luot2_q05_cpu_json_enum.jsonl", None),
               (f"{A}/stt55_q7b/q7b_REAL_json_enum.jsonl", None),
               (f"{A}/stt39_anchored_json_enum/q15_REAL_json_enum.jsonl", None)]:
    try:
        rs = load(p)[:lim] if lim else load(p)
    except FileNotFoundError:
        continue
    m = [r for r in rs if data[r["sample_id"]].get("label") and data[r["sample_id"]].get("techniques_base")]
    gold = [{t[:5] for t in data[r["sample_id"]]["techniques_base"]} for r in m]
    freq = collections.Counter(t for g in gold for t in g)
    maj = freq.most_common(1)[0][0]
    hit = [int((r.get("technique") or "")[:5] in g) for r, g in zip(m, gold)]
    mh = [int(maj in g) for g in gold]
    res1.append({"file": p, "n_ttp": len(m), "majority": maj, "top3_gold": freq.most_common(3),
                 "hits": sum(hit), "majority_hits": sum(mh), "acc": round(sum(hit) / len(m), 4),
                 "acc_majority": round(sum(mh) / len(m), 4),
                 "same_per_sample_vector": hit == mh,
                 "both_hit": sum(a and b for a, b in zip(hit, mh)),
                 "hits_by_predicted_technique": dict(collections.Counter(r["technique"] for r, h in zip(m, hit) if h)),
                 "gold_label_mismatch_vs_data": sum(sorted(r.get("gold_techniques") or []) !=
                                                    sorted(data[r["sample_id"]].get("techniques_base") or []) for r in rs)})
json.dump(res1, open(f"{OUT}/json_enum_vs_majority.json", "w", encoding="utf-8"), indent=1)

# ---- 2. no_prediction o mode sinh ----
def why(r):
    obj, _ = loads_lenient(r["generation"])
    t = get_ci(obj, "technique")
    s = json.dumps(t) if t is not None else ""
    if obj is None:
        return "khong_parse_duoc_JSON"
    if t is None:
        return "JSON_khong_co_truong_technique"
    if TECH_RE.search(s):
        return "CO_ID_hop_le_trong_technique(loi_parser)"
    if re.search(r"T\d+", s):
        return "ID_T_sai_do_dai(T100,T12345)"
    if re.search(r"\d", s):
        return "chi_co_so_khong_co_T(10,456)"
    return "chi_co_ten_khong_co_ID"


res2, md = [], ["# Output tho cua mode sinh khi khong ra technique (alert malicious co nhan TTP)\n"]
for f in ["q05_REAL_json", "q05_REAL_free", "q15_REAL_json", "q15_REAL_free", "q7b_REAL_json", "q7b_REAL_free"]:
    rs = load(f"{A}/task03_gen_rerun/{f}.jsonl")
    m = [r for r in rs if r.get("label") and r.get("gold_techniques")]
    nop = [r for r in m if not r.get("technique")]
    c = collections.Counter(why(r) for r in nop)
    res2.append({"file": f, "n_ttp": len(m), "no_prediction": len(nop), "no_prediction_rate": round(len(nop) / len(m), 4),
                 "reasons": dict(c.most_common())})
    if f.startswith("q05"):
        random.seed(0)
        md.append(f"\n## {f} ({len(nop)}/{len(m)} khong ra technique)\n")
        for r in random.sample(nop, 5):
            md.append(f"\n### {r['sample_id']} - gold {r['gold_techniques']} - parse `{r['parse']}` - ly do: {why(r)}\n")
            md.append("```\n" + r["generation"][:900] + "\n```\n")
json.dump(res2, open(f"{OUT}/gen_no_prediction_breakdown.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
open(f"{OUT}/raw_outputs_q05_10.md", "w", encoding="utf-8").write("".join(md))
for x in res1:
    print(x["file"].split("/")[-1], x["acc"], x["acc_majority"], "same_vector", x["same_per_sample_vector"])
for x in res2:
    print(x["file"], x["no_prediction"], "/", x["n_ttp"], x["reasons"])
