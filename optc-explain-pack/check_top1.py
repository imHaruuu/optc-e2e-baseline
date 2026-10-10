import json
import re
import sys

KB = {"T1003", "T1036", "T1047", "T1055", "T1059", "T1218", "T1490", "T1543", "T1553", "T1574"}
TID = re.compile(r"T\d{4}")


def parents(value):
    if not value:
        return set()
    items = value if isinstance(value, (list, tuple)) else [value]
    return {m.group(0) for m in (TID.search(str(v)) for v in items) if m}


rows = [json.loads(line) for line in open(sys.argv[1], encoding="utf-8") if line.strip()]
named = sum(1 for r in rows if parents(r.get("technique")))
labeled = [r for r in rows if parents(r.get("gold_techniques"))]
hit = [bool(parents(r.get("technique")) & parents(r.get("gold_techniques"))) for r in labeled]
scope = [h for r, h in zip(labeled, hit) if parents(r.get("gold_techniques")) & KB]
print(f"alerts {len(rows)}, name a technique {named / len(rows):.3f}")
print(f"top-1 {sum(hit) / len(hit):.3f} (n = {len(hit)})")
print(f"in scope {sum(scope) / len(scope):.3f} (n = {len(scope)})")
