#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coletor leve de telemetria do servidor (uma amostra por chamada, append em sysmon.jsonl).
Roda em loop durante o benchmark, ex.:
  while true; do python3 sysmon.py --out ~/benchmark/sysmon.jsonl; sleep 20; done

Cada linha:
{ "t": "2026-08-19T16:40:00", "ram_used_gib": 12.3, "ram_total_gib": 62.0,
  "vram_used_gib": 20.1, "vram_total_gib": 64.0, "cpu_pct": 45.2,
  "loaded_model": "bench-q4b:latest", "processor": "100% GPU" }
Só stdlib. Nada aqui derruba o run se falhar (best-effort, campos viram null).
"""
import argparse, json, os, glob, subprocess, time
from datetime import datetime


def read_mem():
    """RAM usada/total em GiB via /proc/meminfo (MemTotal - MemAvailable)."""
    try:
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":")
                info[k.strip()] = int(v.strip().split()[0])  # kB
        total = info["MemTotal"] / 1024 / 1024
        avail = info.get("MemAvailable", info.get("MemFree", 0)) / 1024 / 1024
        return round(total - avail, 2), round(total, 2)
    except Exception:
        return None, None


def read_vram():
    """VRAM usada/total (GiB) via sysfs amdgpu."""
    def g(pat):
        for p in glob.glob(pat):
            try:
                return int(open(p).read().strip())
            except Exception:
                pass
        return None
    used = g("/sys/class/drm/card*/device/mem_info_vram_used")
    total = g("/sys/class/drm/card*/device/mem_info_vram_total")
    to_g = lambda x: round(x / 1024 / 1024 / 1024, 2) if x is not None else None
    return to_g(used), to_g(total)


def read_cpu_pct(interval=0.4):
    """% de CPU agregada via delta de /proc/stat."""
    def snap():
        with open("/proc/stat") as f:
            parts = f.readline().split()[1:]
        vals = list(map(int, parts))
        idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
        return sum(vals), idle
    try:
        t1, i1 = snap()
        time.sleep(interval)
        t2, i2 = snap()
        dt, di = t2 - t1, i2 - i1
        return round(100.0 * (dt - di) / dt, 1) if dt else None
    except Exception:
        return None


def read_ollama_ps():
    """(loaded_model, processor) do 'ollama ps'; None se nada carregado."""
    try:
        out = subprocess.run(["ollama", "ps"], capture_output=True, text=True,
                             timeout=10).stdout.strip().splitlines()
        if len(out) < 2:
            return None, None
        # cabecalho: NAME ID SIZE PROCESSOR UNTIL ; pega 1a linha de dados
        row = out[1]
        name = row.split()[0]
        # PROCESSOR costuma conter "GPU"/"CPU"; extrai o trecho com esses tokens
        proc = None
        low = row
        import re
        m = re.search(r"(\d+%?\s*(/\s*\d+%)?\s*(CPU|GPU)(/(CPU|GPU))?)", low)
        if m:
            proc = m.group(1).strip()
        elif "GPU" in low:
            proc = "GPU"
        elif "CPU" in low:
            proc = "CPU"
        return name, proc
    except Exception:
        return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="../sysmon.jsonl")
    args = ap.parse_args()
    ram_u, ram_t = read_mem()
    vram_u, vram_t = read_vram()
    cpu = read_cpu_pct()
    model, proc = read_ollama_ps()
    rec = {"t": datetime.now().isoformat(timespec="seconds"),
           "ram_used_gib": ram_u, "ram_total_gib": ram_t,
           "vram_used_gib": vram_u, "vram_total_gib": vram_t,
           "cpu_pct": cpu, "loaded_model": model, "processor": proc}
    with open(args.out, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps(rec, ensure_ascii=False))


if __name__ == "__main__":
    main()
