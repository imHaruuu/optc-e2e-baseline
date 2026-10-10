"""check_top1 chi tren lan chay MOI NHAT cua moi cau hinh (cung mode/model/kb_rule/du lieu/KB -> giu file moi nhat).
Doc check_top1_all.csv (tu check_top1_all.py), bo cac file da bi chay lai -> check_top1_latest.csv + .md
python check_top1_latest.py check_top1_all.csv check_top1_latest
"""
import csv
import sys
from pathlib import Path

A, T9, T13, T18 = "results/adgen/", "results/adgen/task09_kb_v2/", "results/adgen/task13_commit_e5f8c43/", \
    "results/adgen/task18_kb_field_control/"
# file cu -> (file thay the, ly do)
REPLACED = {
    **{f"{A}00_core/{n}.jsonl": (f"{T13}{n}.jsonl", "chay lai o commit e5f8c43 (04/10)")
       for n in ("q05_REAL_eve", "q05_LAB_dev_eve", "kb_only_alpha", "kb_only_specific")},
    f"{A}00_core/kb_only_first.jsonl": (f"{T18}kb_only_v0.1_orig_REAL.jsonl", "kb_only first v0.1 REAL, ban moi nhat"),
    f"{T13}kb_only_first.jsonl": (f"{T18}kb_only_v0.1_orig_REAL.jsonl", "kb_only first v0.1 REAL, chay sau 28 phut"),
    f"{T9}kb_only_first_REAL_v0.1.jsonl": (f"{T18}kb_only_v0.1_orig_REAL.jsonl", "cung cau hinh, moi hon"),
    f"{T9}kb_only_first_REAL_v0.2.jsonl": (f"{T18}kb_only_v0.2_orig_REAL.jsonl", "cung cau hinh, moi hon"),
    f"{T9}kb_only_first_attackdata_v0.1.jsonl": (f"{T18}kb_only_v0.1_orig_attackdata.jsonl", "cung cau hinh, moi hon"),
    f"{T9}kb_only_first_attackdata_v0.2.jsonl": (f"{T18}kb_only_v0.2_orig_attackdata.jsonl", "cung cau hinh, moi hon"),
    f"{T9}kb_only_alpha_REAL_v0.1.jsonl": (f"{T13}kb_only_alpha.jsonl", "cung cau hinh, moi hon"),
    f"{T9}kb_only_specific_REAL_v0.1.jsonl": (f"{T13}kb_only_specific.jsonl", "cung cau hinh, moi hon"),
    f"{A}stt40_json_free/q05_REAL_json.jsonl": (f"{A}task03_gen_rerun/q05_REAL_json.jsonl", "task03: parser moi, 384 token"),
    f"{A}stt40_json_free/q05_REAL_free.jsonl": (f"{A}task03_gen_rerun/q05_REAL_free.jsonl", "task03: parser moi, 384 token"),
    f"{A}stt38_kb_only_nontrivial/kb_only_nontrivial_specific.jsonl":
        (f"{A}task07_paired_ci/kb_only_specific_nontrivial_v0.1.jsonl", "cung cau hinh, moi hon"),
    "results/attackdata/stt43/kb_only_attackdata.jsonl": (f"{T9}kb_only_specific_attackdata_v0.1.jsonl", "cung cau hinh, moi hon"),
    "results/attackdata/stt43/kb_only_attackdata_alpha.jsonl": (f"{T9}kb_only_alpha_attackdata_v0.1.jsonl", "cung cau hinh, moi hon"),
    "results/attackdata/stt43/kb_only_attackdata_first.jsonl": (f"{T18}kb_only_v0.1_orig_attackdata.jsonl", "cung cau hinh, moi hon"),
    f"{A}task04_cpu_15b/q15_cpu_eve_contended.jsonl": (f"{A}task04_cpu_15b/q15_cpu_eve.jsonl", "lan do bi nhieu, da do lai"),
}
OLD_PREFIX = ("results/_superseded/", "results/6_3-ketqua/")  # + file nam thang o results/: ban cu truoc khi sap xep lai

rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
keep, drop = [], []
for r in rows:
    f = r["file"]
    if r["status"] != "ok":
        continue
    if f.count("/") == 1 or f.startswith(OLD_PREFIX):
        drop.append((f, "-", "ban cu (README: khong dung cho so lieu moi)"))
    elif f in REPLACED:
        drop.append((f, *REPLACED[f]))
    else:
        keep.append(r)
names = {r["file"] for r in keep}
assert all(new in names for _, new, _ in drop if new != "-"), [n for _, n, _ in drop if n != "-" and n not in names]

cols = ["file", "alerts", "named", "n_labeled", "hits", "top1", "n_in_scope", "top1_in_scope"]
with open(sys.argv[2] + ".csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, cols, extrasaction="ignore"); w.writeheader(); w.writerows(keep)
md = ["# TTP top-1 (check_top1.py) - chi lan chay moi nhat", "",
      f"{len(keep)} file (moi cau hinh mode/model/kb_rule/du lieu/KB giu 1 file moi nhat); bo {len(drop)} file cu hoac da chay lai.",
      "So khop o muc ky thuat cha (T####). in scope = nhan dung thuoc 10 ky thuat KB v0.1.", "",
      "| file | alerts | named | n | hits | top-1 | n in-scope | top-1 in-scope |", "|---|---|---|---|---|---|---|---|"]
md += [f"| `{r['file'].removeprefix('results/')}` | " + " | ".join(f"{float(r[c]):.3f}" if "." in r[c] else r[c] for c in cols[1:]) + " |" for r in keep]
md += ["", "## File bo (cu hoac da chay lai)", "", "| file bo | thay bang | ly do |", "|---|---|---|"]
md += [f"| `{a.removeprefix('results/')}` | `{b.removeprefix('results/')}` | {c} |" for a, b, c in drop]
Path(sys.argv[2] + ".md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(f"keep {len(keep)}, drop {len(drop)}")
