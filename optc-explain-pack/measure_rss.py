"""Chay mot script Python (vd eve.py run) trong process rieng bang chinh interpreter hien tai, lay mau RSS bang psutil.
Chi chay file .py co that (khong nhan lenh shell tuy y).

  python measure_rss.py --out mem.json -- eve.py run --data T --model M --device cpu ...
  python measure_rss.py --out mem.json -- python eve.py run ...   # 'python' o dau duoc bo qua
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil


def tree_rss(p):
    rss = 0
    for q in [p] + p.children(recursive=True):
        try:
            rss += q.memory_info().rss
        except psutil.Error:
            pass
    return rss


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--interval", type=float, default=0.2)
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args(argv)
    cmd = a.cmd[1:] if a.cmd[:1] == ["--"] else a.cmd
    if cmd and Path(cmd[0]).name.lower().startswith("python") and Path(cmd[0]).suffix.lower() in ("", ".exe"):
        cmd = cmd[1:]
    if not cmd:
        ap.error("thieu script .py sau --")
    script = Path(cmd[0])
    if script.suffix.lower() != ".py" or not script.is_file():
        ap.error(f"'{cmd[0]}' khong phai file .py ton tai")
    cmd = [sys.executable, str(script.resolve()), *cmd[1:]]
    t0 = time.time()
    proc = subprocess.Popen(cmd, shell=False)
    p = psutil.Process(proc.pid)
    samples = []
    while proc.poll() is None:
        samples.append((round(time.time() - t0, 2), tree_rss(p)))
        time.sleep(a.interval)
    gb = [s[1] / 1e9 for s in samples] or [0.0]
    res = {"cmd": cmd, "returncode": proc.returncode, "wall_s": round(time.time() - t0, 1),
           "rss_peak_gb": round(max(gb), 3), "rss_mean_gb": round(sum(gb) / len(gb), 3),
           "rss_p50_gb": round(sorted(gb)[len(gb) // 2], 3), "n_samples": len(samples),
           "cpu_count_logical": psutil.cpu_count(), "ram_total_gb": round(psutil.virtual_memory().total / 1e9, 1)}
    Path(a.out).write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "cmd"}, indent=1))
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
