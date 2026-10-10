"""task21: 5 luot cho cac model nho trong D:/hf_models/manifest.json (access ok), moi model mot thu muc rieng.
GPU (lan luot tung model): (1) EVE REAL + LAB_dev, (2) json_enum REAL, eval_eve; (3) random_in_c; (4) paired bootstrap.
Sau khi xong GPU cua TAT CA model: (5) CPU fp32 16 thread 100 alert dau (khong chay chung GPU).
Moi lenh eve.py boc bang hwmon.py run -> <model>/hw/<buoc>_<thoi diem>.hw.json. Chay lai duoc: buoc xong bo qua,
dang do -> --resume; OOM -> giam batch. Dung: python run_task21.py [--only slug ...] [--phase gpu|cpu|all]
"""
import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

PACK = Path("E:/Code/optc-e2e-baseline/optc-explain-pack")
W = Path("E:/Code/optc-e2e-baseline/.claude/worktrees/optc-file-analysis-305df4/optc-explain-pack")
PY = str(PACK / ".venv/Scripts/python.exe")
T = "../P1/Output/data/splits/REAL_test_matched.jsonl"
DEV = "../P1/Output/data/splits/LAB_dev_matched.jsonl"
KB1 = "results/_kb/tech_preconditions_v0.1.json"
KBF = "results/adgen/task09_kb_v2/kb_only_first_REAL_v0.1.jsonl"
Q05 = "results/adgen/00_core/q05_REAL_eve.jsonl"
R = PACK / "results/adgen/task21_small_models"
FP32_MAX_B = 2.7  # <= 2.7B: fp32 tren GPU; lon hon: bf16 (fp32 khong vua 16 GB VRAM)


def log(msg):
    line = f"[{datetime.datetime.now():%F %T}] {msg}"
    print(line, flush=True)
    with open(R / "logs/progress.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def nlines(p):
    return sum(1 for _ in open(p, encoding="utf-8")) if Path(p).exists() else 0


def eve(m, step, data, extra, want, gpu=True):
    d = R / m["slug"]
    out = d / f"{step}.jsonl"
    if (d / f"{step}.jsonl.summary.json").exists() and nlines(out) >= want:
        log(f"{m['slug']} {step} SKIP ({nlines(out)})")
        return 0
    bs = m["bs_gpu"] if gpu else m["bs_cpu"]
    while True:
        res = ["--resume"] if out.exists() else []
        cmd = [PY, str(W / "hwmon.py"), "run", "--out_dir", str(d / "hw"), "--tag", step, "--label", f"model={m['id']}",
               "--label", f"step={step}", "--label", f"device={'cuda' if gpu else 'cpu'}", "--label", f"batch={bs}",
               "--", str(W / "eve.py"), "run", "--data", data, "--model", m["path"], "--kb", KB1, "--out", str(out),
               "--batch_size", str(bs), "--progress", "50", *extra, *res]
        log(f"{m['slug']} {step} START bs={bs} ({nlines(out)}/{want})")
        with open(d / "logs" / f"{step}.log", "a", encoding="utf-8") as lg:
            rc = subprocess.run(cmd, cwd=PACK, stdout=lg, stderr=subprocess.STDOUT).returncode
        log(f"{m['slug']} {step} END rc={rc}")
        tail = (d / "logs" / f"{step}.log").read_text(encoding="utf-8", errors="replace")[-4000:].lower()
        if rc != 0 and "out of memory" in tail and bs > 1:
            bs //= 2
            log(f"{m['slug']} {step} OOM -> batch {bs}")
            continue
        return rc


def post(m):
    d = R / m["slug"]
    lg = lambda n: open(d / "logs" / f"{n}.log", "w", encoding="utf-8")  # noqa: E731
    steps = [("eval", [PY, str(W / "eval_eve.py"), "--data", T, "--dev", str(d / "LAB_dev_eve.jsonl"),
                       "--out", str(d / "eval.json"), "--results", str(d / "REAL_eve.jsonl"), str(d / "REAL_json_enum.jsonl")]),
             ("random_in_c", [PY, str(W / "random_in_c.py"), "--results", str(d / "REAL_eve.jsonl"),
                              "--out", str(d / "random_in_c.json")]),
             ("paired", [PY, str(W / "paired_bootstrap.py"), "--pair", f"eve={d / 'REAL_eve.jsonl'}", f"kb_first={KBF}",
                         "--pair", f"eve={d / 'REAL_eve.jsonl'}", f"q05_eve={Q05}", "--name", "REAL", "--kb", KB1,
                         "--out", str(d / "paired.json")])]
    for n, cmd in steps:
        with lg(n) as f:
            rc = subprocess.run(cmd, cwd=PACK, stdout=f, stderr=subprocess.STDOUT).returncode
        log(f"{m['slug']} {n} rc={rc}")


def models(only):
    out = []
    for x in json.loads(Path("D:/hf_models/manifest.json").read_text(encoding="utf-8")):
        if x["access"] != "ok":
            continue
        slug = x["run_dir"].split("__", 1)[1].lower().replace(".", "_").replace("-", "_")
        if only and slug not in only:
            continue
        fp32 = x["params_b"] <= FP32_MAX_B
        out.append({"id": x["id"], "path": f"D:/hf_models/{x['run_dir']}", "slug": slug, "params_b": x["params_b"],
                    "dtype_gpu": "float32" if fp32 else "bfloat16", "bs_gpu": 8 if fp32 else 4,
                    "bs_cpu": 8 if fp32 else 4})
    return sorted(out, key=lambda m: m["params_b"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--phase", choices=("gpu", "cpu", "all"), default="all")
    a = ap.parse_args()
    (R / "logs").mkdir(parents=True, exist_ok=True)
    ms = models(a.only)
    if not a.only:  # --only: giu models.json day du (build_task21.py doc no)
        (R / "models.json").write_text(json.dumps(ms, indent=1), encoding="utf-8")
    log(f"START phase={a.phase} {len(ms)} model: {', '.join(m['slug'] for m in ms)}")
    if a.phase in ("gpu", "all"):
        for m in ms:
            for sub in ("logs", "hw"):
                (R / m["slug"] / sub).mkdir(parents=True, exist_ok=True)
            g = ["--device", "cuda", "--dtype", m["dtype_gpu"]]
            ok = eve(m, "REAL_eve", T, ["--mode", "eve", *g], 1000) == 0
            ok &= eve(m, "LAB_dev_eve", DEV, ["--mode", "eve", *g], 400) == 0
            ok &= eve(m, "REAL_json_enum", T, ["--mode", "json_enum", *g], 1000) == 0
            if ok:
                post(m)
            else:
                log(f"{m['slug']} GPU FAIL - bo qua post, xem logs/")
    if a.phase in ("cpu", "all"):
        log("START CPU")
        for m in ms:
            (R / m["slug"] / "logs").mkdir(parents=True, exist_ok=True)
            eve(m, "cpu_eve", T, ["--mode", "eve", "--device", "cpu", "--dtype", "float32", "--threads", "16",
                                  "--limit", "100"], 100, gpu=False)
    log("ALL DONE")


if __name__ == "__main__":
    main()
