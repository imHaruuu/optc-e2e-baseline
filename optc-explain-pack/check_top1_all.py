"""Chay logic check_top1.py tren moi file .jsonl trong results/ -> check_top1_all.csv + .md
python check_top1_all.py <results dir> <out prefix>
"""
import csv
import json
import re
import sys
from pathlib import Path

KB = {"T1003", "T1036", "T1047", "T1055", "T1059", "T1218", "T1490", "T1543", "T1553", "T1574"}
TID = re.compile(r"T\d{4}")


def parents(value):
    if not value:
        return set()
    items = value if isinstance(value, (list, tuple)) else [value]
    return {m.group(0) for m in (TID.search(str(v)) for v in items) if m}


root = Path(sys.argv[1])
out = []
for f in sorted(root.rglob("*.jsonl")):
    rel = f.relative_to(root.parent).as_posix()
    try:
        rows = [json.loads(line) for line in open(f, encoding="utf-8") if line.strip()]
    except Exception as e:
        out.append({"file": rel, "status": f"loi doc: {type(e).__name__}"}); continue
    keys = set().union(*(r.keys() for r in rows if isinstance(r, dict))) if rows else set()
    if not rows or "technique" not in keys or "gold_techniques" not in keys:
        miss = [k for k in ("technique", "gold_techniques") if k not in keys]
        out.append({"file": rel, "alerts": len(rows), "status": "bo qua: thieu " + ",".join(miss) if rows else "rong"})
        continue
    named = sum(1 for r in rows if parents(r.get("technique")))
    labeled = [r for r in rows if parents(r.get("gold_techniques"))]
    hit = [bool(parents(r.get("technique")) & parents(r.get("gold_techniques"))) for r in labeled]
    scope = [h for r, h in zip(labeled, hit) if parents(r.get("gold_techniques")) & KB]
    out.append({"file": rel, "alerts": len(rows), "named": round(named / len(rows), 3),
                "n_labeled": len(hit), "hits": sum(hit),
                "top1": round(sum(hit) / len(hit), 3) if hit else None,
                "n_in_scope": len(scope), "top1_in_scope": round(sum(scope) / len(scope), 3) if scope else None,
                "status": "ok" if hit else "khong co alert co nhan"})

cols = ["file", "alerts", "named", "n_labeled", "hits", "top1", "n_in_scope", "top1_in_scope", "status"]
with open(sys.argv[2] + ".csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, cols); w.writeheader(); w.writerows(out)
ok = [r for r in out if r["status"] == "ok"]
rest = [r for r in out if r["status"] != "ok"]
fmt = lambda v: "" if v is None else (f"{v:.3f}" if isinstance(v, float) else str(v))
md = ["# TTP top-1 (check_top1.py) tren toan bo results/", "",
      f"{len(out)} file .jsonl; {len(ok)} file co du `technique` + `gold_techniques` va co alert co nhan; {len(rest)} file bo qua.",
      "So khop o muc ky thuat cha (T####). in scope = nhan dung thuoc 10 ky thuat KB v0.1.", "",
      "| file | alerts | named | n | hits | top-1 | n in-scope | top-1 in-scope |", "|---|---|---|---|---|---|---|---|"]
md += [f"| `{r['file']}` | " + " | ".join(fmt(r[c]) for c in cols[1:8]) + " |" for r in ok]
md += ["", "## File bo qua", "", "| file | alerts | ly do |", "|---|---|---|"]
md += [f"| `{r['file']}` | {fmt(r.get('alerts'))} | {r['status']} |" for r in rest]
Path(sys.argv[2] + ".md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(f"{len(out)} files, ok {len(ok)}, skipped {len(rest)}")
