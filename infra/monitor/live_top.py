#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor ao vivo do servidor: uma barra de blocos para RAM e outra para VRAM
(1 ■ = 1 GiB, cor = dono), tabela por dono embaixo, modelos carregados e usuários.
Usa a tela alternativa do terminal (como o htop) e corta na altura da janela,
então não rola nem empilha frames.

O monitor_servidor.bat copia este arquivo para o servidor e abre com ssh -tt
(o tty é o que permite saber o tamanho da janela):
  scp live_top.py HOST:.live_top.py && ssh -tt HOST "python3 -u ~/.live_top.py"
Teste sem tty:  ssh HOST "python3 - --once" < live_top.py

Só stdlib. Tudo best-effort: o que não der para ler fica de fora.
Limite: os modelos rodam no processo do usuário `ollama`; o dono atribuído é quem
abriu conexão com a :11434 desde que o modelo foi carregado.
"""
import argparse, getpass, glob, json, os, pwd, shutil, subprocess, sys, time, urllib.request
from datetime import datetime

GIB = 1024 ** 3
OLLAMA = "http://127.0.0.1:11434"
ME = getpass.getuser()
CLK = os.sysconf("SC_CLK_TCK")
NCPU = os.cpu_count() or 1

B, DIM, RST = "\033[1m", "\033[2m", "\033[0m"
RED, YEL, GRN = "\033[31m", "\033[33m", "\033[32m"


def meminfo():
    info = {}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":")
                info[k] = int(v.split()[0]) * 1024
    except Exception:
        pass
    return info


def gpu_mem():
    """(vram_used, vram_total, gtt_used, gtt_total) em bytes via sysfs amdgpu.
    Na APU (memória unificada) o ROCm usa VRAM (fatia reservada) + GTT (RAM do sistema)."""
    def g(name):
        for p in glob.glob(f"/sys/class/drm/card*/device/{name}"):
            try:
                return int(open(p).read())
            except Exception:
                pass
        return None
    return (g("mem_info_vram_used"), g("mem_info_vram_total"),
            g("mem_info_gtt_used"), g("mem_info_gtt_total"))


def cpu_total():
    with open("/proc/stat") as f:
        v = list(map(int, f.readline().split()[1:]))
    return sum(v), v[3] + v[4]


def procs():
    """{pid: (uid, rss_bytes, cpu_ticks, comm)} de todos os processos visíveis."""
    out = {}
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            with open(f"/proc/{d}/stat") as f:
                s = f.read()
            comm = s[s.index("(") + 1:s.rindex(")")]
            rest = s[s.rindex(")") + 2:].split()
            ticks = int(rest[11]) + int(rest[12])      # utime + stime
            rss = int(rest[21]) * 4096                 # páginas -> bytes
            uid = os.stat(f"/proc/{d}").st_uid
            out[int(d)] = (uid, rss, ticks, comm)
        except Exception:
            pass
    return out


def uname(uid, cache={}):
    if uid not in cache:
        try:
            cache[uid] = pwd.getpwuid(uid).pw_name
        except Exception:
            cache[uid] = str(uid)
    return cache[uid]


def ollama_models():
    """Lista de modelos carregados via /api/ps; None se o Ollama não responder."""
    try:
        with urllib.request.urlopen(OLLAMA + "/api/ps", timeout=2) as r:
            return json.load(r).get("models", [])
    except Exception:
        return None


def ollama_clients():
    """{usuario: n_conexoes} abertas contra a porta 11434 (lado cliente).
    O dono do socket está na coluna uid de /proc/net/tcp — funciona sem root."""
    port = f"{11434:04X}"
    count = {}
    for path in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            with open(path) as f:
                next(f)
                for line in f:
                    c = line.split()
                    remote, state, uid = c[2], c[3], int(c[7])
                    if remote.endswith(":" + port) and state == "01":  # ESTABLISHED
                        u = uname(uid)
                        count[u] = count.get(u, 0) + 1
        except Exception:
            pass
    return count


def other_llms(ps):
    """Servidores de LLM fora do Ollama (ex.: llama-server em Docker):
    [(pid, user, alias, modelo, ctx, 'Docker'|'processo')].
    O /proc/PID/cmdline é legível por todos, então pega até os de root/containers."""
    res = []
    for pid, (uid, rss, ticks, comm) in ps.items():
        if comm not in ("llama-server", "vllm", "text-generation", "koboldcpp"):
            continue
        try:
            argv = open(f"/proc/{pid}/cmdline").read().split("\0")
        except Exception:
            continue

        def arg(*names):
            for n in names:
                if n in argv and argv.index(n) + 1 < len(argv):
                    return argv[argv.index(n) + 1]
            return ""
        path = arg("-m", "--model")
        if uname(uid) == "ollama" or "/blobs/sha256-" in path:
            continue                                   # runner do próprio Ollama
        try:
            where = "Docker" if "docker" in open(f"/proc/{pid}/cgroup").read() else "processo"
        except Exception:
            where = "processo"
        res.append((pid, uname(uid), arg("--alias", "-a") or comm, os.path.basename(path) or "?",
                    arg("-c", "--ctx-size"), where))
    return res


def sessions():
    """{usuario: {origens}} de quem está logado (who)."""
    try:
        lines = subprocess.run(["who"], capture_output=True, text=True, timeout=3).stdout.splitlines()
    except Exception:
        return {}
    res = {}
    for ln in lines:
        p = ln.split()
        if not p:
            continue
        origin = ln[ln.find("(") + 1:ln.find(")")] if "(" in ln else "local"
        res.setdefault(p[0], set()).add(origin)
    return res


def until(expires):
    """'expires_at' do Ollama -> 'descarrega em 3m12s'."""
    try:
        exp = datetime.fromisoformat(expires[:26] + expires[-6:] if "." in expires else expires)
        secs = int((exp - datetime.now(exp.tzinfo)).total_seconds())
        if secs > 10 ** 7:
            return "fica carregado"
        return f"descarrega em {secs // 60}m{secs % 60:02d}s" if secs > 0 else "descarregando"
    except Exception:
        return ""


# --- cores -----------------------------------------------------------------
# Cor = dono; cada dono tem uma família (tom normal = processos, tom claro = modelo).
def c256(n):
    return f"\033[38;5;{n}m"


ME_FAM = (34, 82)                                     # verde = você
OTHER_FAMS = [(170, 213), (33, 117), (178, 228), (37, 87), (160, 210)]  # magenta, azul, amarelo, ciano, vermelho
DOCKER_FAM = (166, 214)                               # laranja = LLM em Docker
SYS_COL, CACHE_COL, FREE_COL = c256(246), c256(238), c256(238)
KIND = {"proc": "processos", "model": "modelo", "cache": "cache de disco"}
_fams = {}
_ollama_users = set()     # quem conversou com o Ollama desde que os modelos atuais subiram


def color_of(owner, kind="proc"):
    if kind == "cache":
        return CACHE_COL
    if owner == "sistema":
        return SYS_COL
    if owner == ME:
        fam = ME_FAM
    elif owner.startswith("docker"):
        fam = DOCKER_FAM
    else:
        if owner not in _fams:
            _fams[owner] = OTHER_FAMS[len(_fams) % len(OTHER_FAMS)]
        fam = _fams[owner]
    return c256(fam[1] if kind == "model" else fam[0])


def pct_col(frac):
    return RED if frac > 0.85 else YEL if frac > 0.6 else GRN


# --- barra de blocos ---------------------------------------------------------
def rank(key):
    """Ordem na barra e na tabela: você, outros usuários, Docker, sistema, cache."""
    owner, kind = key
    grp = (0 if owner == ME else 3 if owner == "sistema" else 4 if kind == "cache"
           else 2 if owner.startswith("docker") else 1)
    return (grp, owner, ("proc", "model", "cache").index(kind))


def blocks(parts, total):
    """parts: {(dono, tipo): bytes} -> ({(dono, tipo): nº de blocos}, n).
    1 bloco = 1 GiB; arredonda pelo maior resto para a soma bater."""
    n = max(int(round(total / GIB)), 1)
    keys = sorted(parts, key=rank)
    raw = {k: max(parts[k], 0) / total * n for k in keys}
    out = {k: int(r) for k, r in raw.items()}
    spare = int(round(sum(raw.values()))) - sum(out.values())
    for k in sorted(keys, key=lambda k: raw[k] - out[k], reverse=True)[:max(spare, 0)]:
        out[k] += 1
    return out, n


def bar(title, parts, total, used, width):
    """Uma linha: título + barra (■ ocupado, ■ apagado = cache, · livre)."""
    counts, n = blocks(parts, total)
    cells = []
    for k in sorted(parts, key=rank):
        cells += [f"{color_of(*k)}■"] * counts[k]
    cells = cells[:n] + [f"{FREE_COL}·"] * (n - len(cells))
    frac = used / total if total else 0
    head = f"{B}{title}{RST} {pct_col(frac)}{used / GIB:5.1f}/{total / GIB:4.0f} GiB {frac:4.0%}{RST}  "
    room = max(width - 26, 10)                        # quebra em mais linhas só se a janela for estreita
    rows = [cells[i:i + room] for i in range(0, n, room)]
    L = [head + "".join(rows[0]) + RST]
    L += [" " * 26 + "".join(r) + RST for r in rows[1:]]
    return L, counts, n


def render(interval, width, height, as_json=False):
    t0, i0 = cpu_total()
    p0 = procs()
    time.sleep(interval)
    t1, i1 = cpu_total()
    p1 = procs()
    dt = (t1 - t0) or 1
    cpu_pct = 100.0 * (dt - (i1 - i0)) / dt
    wall_ticks = interval * CLK

    mi = meminfo()
    total, avail = mi.get("MemTotal", 1), mi.get("MemAvailable", 0)
    cache = mi.get("Cached", 0) + mi.get("Buffers", 0)
    vu, vt, gu, gt = gpu_mem()
    api = ollama_models()
    models = api or []
    clients = ollama_clients()
    sess = sessions()
    others = other_llms(p1)

    # dono dos modelos do Ollama = quem conversou com ele desde que foram carregados
    global _ollama_users
    if not models:
        _ollama_users = set()
    _ollama_users |= set(clients)
    humans = sorted(u for u in _ollama_users if u != "ollama")
    model_owner = humans[0] if len(humans) == 1 else (" + ".join(humans) if humans else "ollama (sem cliente)")

    # RSS e CPU por usuário Linux
    per = {}
    for pid, (uid, rss, ticks, comm) in p1.items():
        d = per.setdefault(uname(uid), [0, 0.0, 0])
        d[0] += rss
        if pid in p0:
            d[1] += (ticks - p0[pid][2]) / wall_ticks / NCPU * 100
        d[2] += 1

    # ---- RAM: você / cada usuário logado / modelos Ollama / sistema / cache ----
    logged = set(sess) | {ME}
    ram, accounted = {}, 0
    for u, (rss, _, _) in per.items():
        if u in logged and u != "root" and rss > 0:
            ram[(u, "proc")] = rss
            accounted += rss
    # memória de GPU dos modelos Ollama: nesta APU o ROCm aloca na GTT (RAM do
    # sistema emprestada à GPU); só o excedente cairia na VRAM reservada
    ollama_gpu = sum(m.get("size_vram", 0) for m in models)
    ollama_gtt = min(ollama_gpu, gu or 0)
    ollama_vram = ollama_gpu - ollama_gtt
    if models:                                        # sem modelo, o daemon do Ollama é "sistema"
        ram[(model_owner, "model")] = per.get("ollama", [0])[0] + ollama_gtt
        accounted += ram[(model_owner, "model")]
    used = max(total - avail, 0)
    ram[("sistema", "proc")] = max(used - accounted, 0)
    ram[("cache", "cache")] = min(cache, avail)

    # ---- VRAM: modelos Ollama na GPU / LLM em Docker / resto ----
    vram = {}
    if vt:
        if ollama_vram:
            vram[(model_owner, "model")] = ollama_vram
        rest = max((vu or 0) - ollama_vram, 0)
        if others:
            vram[("docker: " + ", ".join(sorted({o[2] for o in others})), "model")] = rest
        else:
            vram[("sistema", "proc")] = rest

    if as_json:
        # resumo para o ícone da bandeja (uma linha por amostra, valores em GiB)
        g = lambda b: round(b / GIB, 2)
        print(json.dumps({
            "t": datetime.now().strftime("%H:%M:%S"), "host": os.uname().nodename, "cpu": round(cpu_pct, 1),
            "me": ME, "model_owner": model_owner if models else None,
            "ram": {"total": g(total), "used": g(used), "cache": g(cache),
                    "parts": {f"{o}|{k}": g(b) for (o, k), b in ram.items() if b >= 0.05 * GIB}},
            "vram": {"total": g(vt or 0), "used": g(vu or 0),
                     "parts": {f"{o}|{k}": g(b) for (o, k), b in vram.items() if b >= 0.05 * GIB}},
            "models": [{"name": m.get("name"), "gib": g(m.get("size", 0)), "owner": model_owner,
                        "gpu": bool(m.get("size_vram"))} for m in models],
            "docker": [o[2] for o in others],
            "people": {u: {"gib": g(per.get(u, [0])[0]), "cpu": round(per.get(u, [0, 0])[1], 1),
                           "from": sorted(sess.get(u, []))} for u in sorted(logged - {"root"})},
            "ollama_up": api is not None,
        }, ensure_ascii=False), flush=True)
        return

    # ---- cabeçalho + barras ----
    L = []
    load = open("/proc/loadavg").read().split()[0]
    L.append(f"{B}{os.uname().nodename}{RST}  {datetime.now():%H:%M:%S}  CPU {pct_col(cpu_pct / 100)}{cpu_pct:.0f}%{RST}"
             f" de {NCPU} · load {load} · você = {ME}   {DIM}1 ■ = 1 GiB · Ctrl+C sai{RST}")
    L.append("")
    rl, rc, rn = bar("RAM ", ram, total, used, width)
    L += rl
    vc, vn = {}, 0
    if vt:
        vl, vc, vn = bar("VRAM", vram, vt, vu or 0, width)
        L += vl
    L.append("")

    # ---- tabela única: uma linha por (dono, tipo), colunas RAM e VRAM ----
    L.append(f"{DIM}   {'dono':<34} {'tipo':<15} {'RAM':>15}   {'VRAM':>15}{RST}")

    def cell(parts, counts, n, k):
        if k not in parts or parts[k] < 0.05 * GIB:
            return f"{DIM}{'—':>15}{RST}"
        return f"{counts.get(k, 0):>2}/{n} {parts[k] / GIB:5.1f} GiB"

    for k in sorted(set(ram) | set(vram), key=rank):
        if max(ram.get(k, 0), vram.get(k, 0)) < 0.05 * GIB:
            continue
        owner, kind = k
        name = f"você ({ME})" if owner == ME else ("cache (liberável)" if kind == "cache" else owner)
        col = color_of(*k)
        L.append(f" {col}■ {name[:34]:<34}{RST} {DIM}{KIND[kind]:<15}{RST} "
                 f"{col}{cell(ram, rc, rn, k)}{RST}   {col}{cell(vram, vc, vn, k)}{RST}")
    free_r = max(total - sum(ram.values()), 0)
    free_v = max(vt - (vu or 0), 0) if vt else 0
    L.append(f" {FREE_COL}·{RST} {'livre':<34} {'':<15} "
             f"{rn - min(sum(rc.values()), rn):>2}/{rn} {free_r / GIB:5.1f} GiB   "
             + (f"{vn - min(sum(vc.values()), vn):>2}/{vn} {free_v / GIB:5.1f} GiB" if vt else ""))
    if gt:
        L.append(f"   {DIM}GTT (RAM emprestada à GPU): {(gu or 0) / GIB:.1f} de {gt / GIB:.1f} GiB — já contada na RAM{RST}")
    L.append("")

    # ---- LLMs rodando ----
    L.append(f"{B}Modelos{RST}" + ("" if api is not None else f"  {RED}Ollama não respondeu{RST}"))
    for m in models:
        size, sv = m.get("size", 0), m.get("size_vram", 0)
        where = "GPU" if size and sv >= size else "CPU" if not sv else f"{sv / size:.0%} GPU"
        col = color_of(model_owner, "model")
        L.append(f" {col}■ Ollama  {m.get('name', '?'):<28} {size / GIB:5.1f} GiB{RST}  {where}  "
                 f"dono {col}{model_owner}{RST}  {DIM}{until(m.get('expires_at', ''))}{RST}")
    if api is not None and not models:
        L.append(f"   {DIM}Ollama: nenhum modelo carregado{RST}")
    if clients:
        L.append("   requisições no Ollama agora: " + ", ".join(f"{color_of(u)}{u}{RST} ({n})"
                                                            for u, n in sorted(clients.items())))
    for pid, u, alias, model, ctx, where in others:
        c = f"ctx {int(ctx) // 1024}k" if ctx.isdigit() else ""
        col = color_of("docker", "model") if where == "Docker" else ""
        L.append(f" {col}■ {where:<7} {alias:<15} {model[:40]:<40}{RST} {DIM}{c} · {u}{RST}")
    L.append("")

    # ---- pessoas ----
    L.append(f"{B}Pessoas{RST}  {DIM}{'RAM GiB':>30} {'CPU %':>6}  sessões{RST}")
    for u in sorted(logged - {"root"}, key=lambda u: (u != ME, u)):
        rss, cpu, _ = per.get(u, [0, 0.0, 0])
        name = f"{u} (você)" if u == ME else u
        L.append(f" {color_of(u)}■ {name:<28}{RST} {rss / GIB:8.2f} {cpu:6.1f}  "
                 f"{DIM}{', '.join(sorted(sess.get(u, [])))}{RST}")

    # corta na altura da janela e limpa o resto de cada linha (sem piscar, sem rolar)
    L = L[:height - 1]
    out = "\033[H" + "".join(ln + "\033[K\n" for ln in L) + "\033[J"
    sys.stdout.write(out)
    sys.stdout.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=float, default=2.0)
    ap.add_argument("--once", action="store_true", help="uma amostra e sai (teste)")
    ap.add_argument("--json", action="store_true", help="uma linha JSON por amostra (alimenta o ícone da bandeja)")
    a = ap.parse_args()
    tty = sys.stdout.isatty() and not a.once and not a.json
    if tty:
        sys.stdout.write("\033[?1049h\033[?25l")     # tela alternativa + esconde cursor
    try:
        while True:
            size = shutil.get_terminal_size((120, 60))
            render(a.interval, size.columns, size.lines if tty else 999, a.json)
            if a.once:
                break
    except KeyboardInterrupt:
        pass
    finally:
        if tty:
            sys.stdout.write("\033[?25h\033[?1049l")  # devolve a tela normal
            sys.stdout.flush()


if __name__ == "__main__":
    main()
