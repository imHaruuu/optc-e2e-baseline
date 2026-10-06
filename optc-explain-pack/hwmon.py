"""Theo doi phan cung khi chay mot script (CPU, RAM, dia, mang, GPU NVIDIA, va rieng cay tien trinh cua script).
Moi lan chay ghi MOT file rieng: <out_dir>/<tag>_<YYYYmmdd-HHMMSS>.hw.json (them --csv de co ban CSV cung ten).

  python hwmon.py run   --out_dir results/adgen/task21/qwen35_4b/hw --tag eve_REAL --label model=Qwen3.5-4B \
                        -- eve.py run --data ... --model ... --out ...
  python hwmon.py watch --out_dir hw --tag idle --duration 60        # chi theo doi he thong
  python hwmon.py watch --out_dir hw --tag eve --pid 1234            # gan vao tien trinh dang chay
  python hwmon.py show  hw/eve_REAL_20261006-170000.hw.json          # in bang tom tat

`run` chi chay file .py co that bang chinh interpreter hien tai ('python' o dau duoc bo qua), khong qua shell.
GPU doc tu `nvidia-smi --query-gpu ... -lms` (mot tien trinh nen); khong co nvidia-smi thi bo qua GPU.
"""
import argparse
import csv
import datetime
import json
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import psutil

SCHEMA = "hwmon/1"
GPU_FIELDS = [("utilization.gpu", "util_pct"), ("utilization.memory", "mem_bw_pct"), ("memory.used", "mem_used_mib"),
              ("temperature.gpu", "temp_c"), ("power.draw", "power_w"), ("clocks.sm", "sm_clock_mhz"),
              ("clocks.mem", "mem_clock_mhz"), ("fan.speed", "fan_pct"), ("pstate", "pstate")]
GPU_STATIC = ["index", "name", "driver_version", "memory.total", "power.limit", "pci.bus_id"]


def num(v):
    v = str(v).strip().replace("P", "")
    try:
        return float(v)
    except ValueError:
        return None


def cpu_name():
    if sys.platform == "win32":
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            return winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()
        except OSError:
            pass
    try:
        for line in open("/proc/cpuinfo", encoding="utf-8"):
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor()


def system_info(smi):
    vm, sw, fr = psutil.virtual_memory(), psutil.swap_memory(), psutil.cpu_freq()
    info = {"os": f"{platform.system()} {platform.release()} ({platform.version()})", "python": platform.python_version(),
            "cpu": cpu_name(), "cpu_physical_cores": psutil.cpu_count(logical=False),
            "cpu_logical_cores": psutil.cpu_count(), "cpu_freq_max_mhz": fr.max if fr else None,
            "ram_total_gb": round(vm.total / 1e9, 2), "swap_total_gb": round(sw.total / 1e9, 2), "gpus": []}
    for mod in ("torch", "transformers"):
        try:
            info[mod] = __import__(mod).__version__
        except Exception:
            info[mod] = None
    try:
        import torch
        info["torch_cuda"] = torch.version.cuda if torch.cuda.is_available() else None
    except Exception:
        info["torch_cuda"] = None
    if smi:
        out = subprocess.run([smi, f"--query-gpu={','.join(GPU_STATIC)}", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=20).stdout
        for line in out.strip().splitlines():
            v = [x.strip() for x in line.split(",")]
            info["gpus"].append({"index": int(v[0]), "name": v[1], "driver": v[2], "mem_total_mib": num(v[3]),
                                 "power_limit_w": num(v[4]), "pci_bus_id": v[5]})
    return info


class GpuReader(threading.Thread):
    """Doc lien tuc `nvidia-smi -lms`, giu gia tri moi nhat cho tung GPU."""

    def __init__(self, smi, interval_ms):
        super().__init__(daemon=True)
        self.latest, self.lock = {}, threading.Lock()
        self.proc = subprocess.Popen([smi, f"--query-gpu=index,{','.join(f for f, _ in GPU_FIELDS)}",
                                      "--format=csv,noheader,nounits", f"-lms={interval_ms}"],
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)

    def run(self):
        for line in self.proc.stdout:
            v = [x.strip() for x in line.split(",")]
            if len(v) != len(GPU_FIELDS) + 1:
                continue
            with self.lock:
                self.latest[int(v[0])] = {k: num(x) for (_, k), x in zip(GPU_FIELDS, v[1:])}

    def snapshot(self):
        with self.lock:
            return {i: dict(d) for i, d in self.latest.items()}

    def stop(self):
        self.proc.terminate()


class Sampler:
    def __init__(self, root_pid, n_gpu, per_core):
        self.root = psutil.Process(root_pid) if root_pid else None
        self.procs, self.per_core, self.n_gpu = {}, per_core, n_gpu
        self.cols = ["t_s", "cpu_pct", "cpu_core_max_pct", "cpu_freq_mhz", "ram_used_gb", "ram_pct", "swap_used_gb",
                     "disk_read_mbps", "disk_write_mbps", "net_recv_mbps", "net_sent_mbps"]
        if self.root:
            self.cols += ["proc_cpu_pct", "proc_rss_gb", "proc_vms_gb", "proc_threads", "proc_count",
                          "proc_read_mb", "proc_write_mb"]
        for i in range(n_gpu):
            self.cols += [f"gpu{i}_{k}" for _, k in GPU_FIELDS]
        if per_core:
            self.cols += [f"core{i}_pct" for i in range(psutil.cpu_count())]
        psutil.cpu_percent(percpu=True)
        self.last_t, self.last_disk, self.last_net = time.time(), psutil.disk_io_counters(), psutil.net_io_counters()

    def tree(self):
        if not self.root:
            return []
        try:
            ps = [self.root] + self.root.children(recursive=True)
        except psutil.Error:
            return []
        out = []
        for p in ps:
            if p.pid not in self.procs:
                self.procs[p.pid] = p
                try:
                    p.cpu_percent(None)
                except psutil.Error:
                    pass
            out.append(self.procs[p.pid])
        return out

    def sample(self, t0, gpu):
        now = time.time()
        dt = max(now - self.last_t, 1e-6)
        cores = psutil.cpu_percent(percpu=True)
        vm, sw, fr = psutil.virtual_memory(), psutil.swap_memory(), psutil.cpu_freq()
        dk, nt = psutil.disk_io_counters(), psutil.net_io_counters()
        row = {"t_s": round(now - t0, 2), "cpu_pct": round(sum(cores) / len(cores), 1),
               "cpu_core_max_pct": max(cores), "cpu_freq_mhz": fr.current if fr else None,
               "ram_used_gb": round((vm.total - vm.available) / 1e9, 3), "ram_pct": vm.percent,
               "swap_used_gb": round(sw.used / 1e9, 3),
               "disk_read_mbps": round((dk.read_bytes - self.last_disk.read_bytes) / dt / 1e6, 2) if dk else None,
               "disk_write_mbps": round((dk.write_bytes - self.last_disk.write_bytes) / dt / 1e6, 2) if dk else None,
               "net_recv_mbps": round((nt.bytes_recv - self.last_net.bytes_recv) / dt / 1e6, 3),
               "net_sent_mbps": round((nt.bytes_sent - self.last_net.bytes_sent) / dt / 1e6, 3)}
        self.last_t, self.last_disk, self.last_net = now, dk, nt
        if self.root:
            cpu = rss = vms = thr = rd = wr = 0.0
            ps = self.tree()
            for p in ps:
                try:
                    with p.oneshot():
                        cpu += p.cpu_percent(None)
                        mi = p.memory_info()
                        rss, vms, thr = rss + mi.rss, vms + mi.vms, thr + p.num_threads()
                        io = p.io_counters()
                        rd, wr = rd + io.read_bytes, wr + io.write_bytes
                except psutil.Error:
                    pass
            row.update(proc_cpu_pct=round(cpu, 1), proc_rss_gb=round(rss / 1e9, 3), proc_vms_gb=round(vms / 1e9, 3),
                       proc_threads=thr, proc_count=len(ps), proc_read_mb=round(rd / 1e6, 1),
                       proc_write_mb=round(wr / 1e6, 1))
        for i in range(self.n_gpu):
            g = gpu.get(i, {})
            for _, k in GPU_FIELDS:
                row[f"gpu{i}_{k}"] = g.get(k)
        if self.per_core:
            for i, c in enumerate(cores):
                row[f"core{i}_pct"] = c
        return [row.get(c) for c in self.cols]


def summarize(cols, rows):
    out = {}
    for j, c in enumerate(cols):
        if c == "t_s":
            continue
        v = sorted(r[j] for r in rows if isinstance(r[j], (int, float)))
        if not v:
            continue
        out[c] = {"mean": round(sum(v) / len(v), 3), "min": v[0], "p50": v[len(v) // 2],
                  "p95": v[min(len(v) - 1, int(0.95 * (len(v) - 1)))], "max": v[-1]}
    return out


def out_path(out_dir, tag, start):
    out_dir.mkdir(parents=True, exist_ok=True)
    base = f"{tag}_{start:%Y%m%d-%H%M%S}"
    p, k = out_dir / f"{base}.hw.json", 1
    while p.exists():
        p, k = out_dir / f"{base}-{k}.hw.json", k + 1
    return p


def write(path, doc, cols, rows, csv_too):
    doc["summary"] = summarize(cols, rows)
    doc["columns"], doc["samples"] = cols, rows
    doc["run"]["n_samples"] = len(rows)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)
    if csv_too:
        with open(path.with_suffix("").with_suffix(".csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(rows)


def monitor(a, child=None, pid=None, command=None):
    smi = shutil.which("nvidia-smi")
    start = datetime.datetime.now()
    path = out_path(Path(a.out_dir), a.tag, start)
    info = system_info(smi)
    gpu = GpuReader(smi, int(a.interval * 1000)) if smi and info["gpus"] else None
    if gpu:
        gpu.start()
    root = child.pid if child else pid
    sm = Sampler(root, len(info["gpus"]) if gpu else 0, a.per_core)
    labels = dict(kv.split("=", 1) for kv in a.label)
    doc = {"schema": SCHEMA, "system": info,
           "run": {"tag": a.tag, "labels": labels, "command": command, "cwd": os.getcwd(), "pid": root,
                   "start": start.isoformat(timespec="seconds"), "end": None, "wall_s": None, "returncode": None,
                   "status": "running", "interval_s": a.interval}}
    print(f"[hwmon] ghi vao {path}", file=sys.stderr, flush=True)
    t0, rows, last_flush, status = time.time(), [], time.time(), "done"
    try:
        while True:
            rows.append(sm.sample(t0, gpu.snapshot() if gpu else {}))
            if child is not None and child.poll() is not None:
                break
            if pid and not psutil.pid_exists(pid):
                break
            if a.duration and time.time() - t0 >= a.duration:
                break
            if time.time() - last_flush >= a.flush_every:
                write(path, doc, sm.cols, rows, False)
                last_flush = time.time()
            time.sleep(a.interval)
    except KeyboardInterrupt:
        status = "interrupted"
        if child is not None:
            child.terminate()
    finally:
        if gpu:
            gpu.stop()
        if child is not None:
            child.wait()
        end = datetime.datetime.now()
        doc["run"].update(end=end.isoformat(timespec="seconds"), wall_s=round(time.time() - t0, 1),
                          returncode=child.returncode if child is not None else None, status=status)
        write(path, doc, sm.cols, rows, a.csv)
        print(f"[hwmon] {status}: {len(rows)} mau, {doc['run']['wall_s']} s -> {path}", file=sys.stderr, flush=True)
    return doc["run"]["returncode"] or 0


def cmd_run(a, ap):
    cmd = a.cmd[1:] if a.cmd[:1] == ["--"] else a.cmd
    if cmd and Path(cmd[0]).name.lower().startswith("python") and Path(cmd[0]).suffix.lower() in ("", ".exe"):
        cmd = cmd[1:]
    if not cmd:
        ap.error("thieu script .py sau --")
    script = Path(cmd[0])
    if script.suffix.lower() != ".py" or not script.is_file():
        ap.error(f"'{cmd[0]}' khong phai file .py ton tai")
    full = [sys.executable, str(script.resolve()), *cmd[1:]]
    child = subprocess.Popen(full, shell=False)
    sys.exit(monitor(a, child=child, command=full))


def cmd_watch(a, ap):
    if a.pid and not psutil.pid_exists(a.pid):
        ap.error(f"khong co tien trinh {a.pid}")
    if not a.pid and not a.duration:
        print("[hwmon] khong co --duration: Ctrl+C de dung", file=sys.stderr)
    monitor(a, pid=a.pid, command=None)


def cmd_show(a, ap):
    d = json.loads(Path(a.file).read_text(encoding="utf-8"))
    r, s, si = d["run"], d["summary"], d["system"]
    print(f"{r['tag']}  {r['start']} -> {r['end']}  {r['wall_s']} s  status={r['status']} rc={r['returncode']}  "
          f"{r['n_samples']} mau / {r['interval_s']} s")
    print(f"{si['cpu']} ({si['cpu_physical_cores']}C/{si['cpu_logical_cores']}T), RAM {si['ram_total_gb']} GB, "
          + ", ".join(f"GPU{g['index']} {g['name']} {g['mem_total_mib']:.0f} MiB" for g in si["gpus"]))
    if r.get("labels"):
        print("labels:", r["labels"])
    print(f"{'chi so':24s} {'mean':>10s} {'p50':>10s} {'p95':>10s} {'max':>10s}")
    for k, v in s.items():
        if k.startswith("core"):
            continue
        print(f"{k:24s} {v['mean']:>10.2f} {v['p50']:>10.2f} {v['p95']:>10.2f} {v['max']:>10.2f}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="sub", required=True)
    for name in ("run", "watch"):
        p = sub.add_parser(name)
        p.add_argument("--out_dir", required=True)
        p.add_argument("--tag", required=True, help="ten ngan cho lan chay (dung trong ten file)")
        p.add_argument("--label", action="append", default=[], help="key=value ghi vao run.labels (lap lai duoc)")
        p.add_argument("--interval", type=float, default=1.0, help="giay giua 2 mau")
        p.add_argument("--flush_every", type=float, default=60.0, help="ghi tam file moi N giay (khong mat khi treo)")
        p.add_argument("--per_core", action="store_true", help="luu % tung core")
        p.add_argument("--csv", action="store_true", help="ghi them ban CSV cac mau")
        if name == "run":
            p.add_argument("cmd", nargs=argparse.REMAINDER)
        else:
            p.add_argument("--pid", type=int, default=None)
            p.add_argument("--duration", type=float, default=None)
    p = sub.add_parser("show")
    p.add_argument("file")
    a = ap.parse_args(argv)
    if a.sub == "run":
        a.duration = None
        cmd_run(a, ap)
    elif a.sub == "watch":
        cmd_watch(a, ap)
    else:
        cmd_show(a, ap)


if __name__ == "__main__":
    main()
