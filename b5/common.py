"""b5 — utilitários comuns: log, JSONL, e as chamadas de LLM por CLI.

As chamadas ao Claude (cliente simulado, juiz, gerador de objetivos) passam
todas por :func:`chamar_llm`, que implementa o fallback do contrato:

1. ``claude -p`` (flags enxutas, ``--json-schema``);
2. se falhar por limite/erro: espera 30 s e tenta de novo UMA vez;
3. se falhar de novo: ``opencode run`` com o modelo grátis, pedindo SÓ o JSON,
   e parse robusto (primeiro objeto JSON do texto);
4. depois de 3 falhas SEGUIDAS do claude, fica 20 min direto no fallback.

Cada chamada devolve também QUEM respondeu (``modelo``), custo e duração, para
o registro por turno.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime

B5_DIR = os.path.dirname(os.path.abspath(__file__))
TMP_DIR = os.path.join(B5_DIR, ".tmp")

OPENCODE_MODEL = "opencode/muse-spark-1.3-contributor-free"
# Sem janela de console: o usuário reclamou de janelas piscando.
_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

_LOG_PATH = None
_log_lock = threading.Lock()


def set_log_path(path: str | None) -> None:
    global _LOG_PATH
    _LOG_PATH = path


def log(msg: str) -> None:
    linha = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {msg}"
    with _log_lock:
        try:
            print(linha, flush=True)
        except Exception:
            pass
        if _LOG_PATH:
            try:
                with open(_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(linha + "\n")
            except Exception:
                pass


def load_jsonl(path: str) -> list:
    out = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            try:
                out.append(json.loads(linha))
            except Exception:
                continue  # linha truncada por queda no meio da escrita
    return out


def append_jsonl(path: str, rec: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def write_json_atomic(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def extrair_json(texto: str):
    """Primeiro objeto JSON decodificável dentro de ``texto`` (ou None)."""
    if not texto:
        return None
    dec = json.JSONDecoder()
    for m in re.finditer(r"\{", texto):
        try:
            obj, _ = dec.raw_decode(texto[m.start():])
            if isinstance(obj, dict):
                return obj
        except Exception:
            continue
    return None


# --------------------------------------------------------------------- estado

_LIMITE_RE = re.compile(r"hit your .*limit|usage limit|rate_limit", re.I)


class EstadoFallback:
    """Contador de falhas seguidas do claude e janela de 20 min no fallback."""

    def __init__(self):
        self.falhas_seguidas = 0
        self.fallback_ate = 0.0
        self.n_fallbacks = 0
        self.n_claude = 0
        self.ultimo_modelo = {}  # papel -> modelo usado na última chamada

    def em_janela_fallback(self) -> bool:
        return time.time() < self.fallback_ate

    def registrar_falha(self) -> None:
        self.falhas_seguidas += 1
        if self.falhas_seguidas >= 3:
            self.fallback_ate = time.time() + 20 * 60
            self.falhas_seguidas = 0
            log("  !! 3 falhas seguidas do claude — 20 min direto no fallback (opencode)")

    def registrar_sucesso(self) -> None:
        self.falhas_seguidas = 0

    def resumo(self) -> dict:
        return {
            "n_claude": self.n_claude,
            "n_fallbacks": self.n_fallbacks,
            "em_janela_fallback": self.em_janela_fallback(),
            "fallback_ate": (datetime.fromtimestamp(self.fallback_ate).isoformat(timespec="seconds")
                             if self.fallback_ate else None),
            "ultimo_modelo": dict(self.ultimo_modelo),
        }


ESTADO_FALLBACK = EstadoFallback()


def _bin(nome: str) -> str:
    return shutil.which(nome) or nome


def _tmpfile(conteudo: str, sufixo: str) -> str:
    os.makedirs(TMP_DIR, exist_ok=True)
    fd, p = tempfile.mkstemp(suffix=sufixo, dir=TMP_DIR)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(conteudo)
    return p


def _chamar_claude(modelo: str, system: str, user: str, schema: dict, timeout: int) -> dict:
    """Uma tentativa. Devolve dict com ok/obj/erro/custo/duração/limite."""
    sp = _tmpfile(system, ".txt")
    cmd = [
        _bin("claude"), "-p", "--model", modelo, "--output-format", "json",
        "--tools", "", "--strict-mcp-config", "--setting-sources", "",
        "--no-session-persistence", "--system-prompt-file", sp,
        "--json-schema", json.dumps(schema, ensure_ascii=False),
    ]
    t0 = time.perf_counter()
    try:
        p = subprocess.run(cmd, input=user, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout,
                           creationflags=_NO_WINDOW, cwd=TMP_DIR)
    except subprocess.TimeoutExpired:
        return {"ok": False, "erro": f"timeout {timeout}s", "dur_s": round(time.perf_counter() - t0, 2)}
    except Exception as e:
        return {"ok": False, "erro": f"{type(e).__name__}: {e}", "dur_s": round(time.perf_counter() - t0, 2)}
    finally:
        try:
            os.remove(sp)
        except Exception:
            pass
    dur = round(time.perf_counter() - t0, 2)
    try:
        j = json.loads(p.stdout)
    except Exception:
        j = extrair_json(p.stdout) or {}
    result = str(j.get("result") or "")
    erro_txt = (p.stderr or "")[-400:]
    limite = bool(_LIMITE_RE.search(result) or _LIMITE_RE.search(erro_txt)
                  or j.get("api_error_status") == 429)
    obj = j.get("structured_output")
    if obj is None and result:
        obj = extrair_json(result)
    ok = p.returncode == 0 and not j.get("is_error") and not limite and isinstance(obj, dict)
    return {
        "ok": ok, "obj": obj if ok else None,
        "erro": None if ok else (f"exit={p.returncode} is_error={j.get('is_error')} "
                                 f"status={j.get('api_error_status')} limite={limite} "
                                 f"result={result[:200]!r} stderr={erro_txt[-200:]!r}"),
        "custo_usd": j.get("total_cost_usd"),
        "dur_s": dur,
        "tok_in": (j.get("usage") or {}).get("input_tokens", 0)
                  + (j.get("usage") or {}).get("cache_read_input_tokens", 0)
                  + (j.get("usage") or {}).get("cache_creation_input_tokens", 0),
        "tok_out": (j.get("usage") or {}).get("output_tokens", 0),
    }


def _chamar_opencode(system: str, user: str, schema: dict, timeout: int) -> dict:
    prompt = (
        f"{system}\n\n=====\n{user}\n\n=====\n"
        "IMPORTANTE: responda SOMENTE com UM objeto JSON válido (sem texto antes ou "
        "depois, sem markdown, sem usar ferramentas) que obedeça a este JSON Schema:\n"
        f"{json.dumps(schema, ensure_ascii=False)}"
    )
    t0 = time.perf_counter()
    os.makedirs(TMP_DIR, exist_ok=True)
    try:
        p = subprocess.run([_bin("opencode"), "run", "--model", OPENCODE_MODEL, "--pure"],
                           input=prompt, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, creationflags=_NO_WINDOW,
                           cwd=TMP_DIR)
    except subprocess.TimeoutExpired:
        return {"ok": False, "erro": f"opencode timeout {timeout}s", "dur_s": round(time.perf_counter() - t0, 2)}
    except Exception as e:
        return {"ok": False, "erro": f"opencode {type(e).__name__}: {e}", "dur_s": round(time.perf_counter() - t0, 2)}
    dur = round(time.perf_counter() - t0, 2)
    obj = extrair_json(p.stdout)
    faltando = [k for k in schema.get("required", []) if not isinstance(obj, dict) or k not in obj]
    ok = isinstance(obj, dict) and not faltando
    return {"ok": ok, "obj": obj if ok else None,
            "erro": None if ok else f"opencode exit={p.returncode} faltando={faltando} out={p.stdout[-300:]!r}",
            "custo_usd": 0.0, "dur_s": dur, "tok_in": None, "tok_out": None}


def chamar_llm(papel: str, modelo_claude: str, system: str, user: str, schema: dict,
               timeout: int = 300) -> dict:
    """Chamada com o fallback do contrato. Sempre devolve um dict:

    ``{ok, obj, modelo, tentativas:[...], custo_usd, dur_s, erro}``
    """
    est = ESTADO_FALLBACK
    tentativas = []
    if not est.em_janela_fallback():
        for i in range(2):
            r = _chamar_claude(modelo_claude, system, user, schema, timeout)
            est.n_claude += 1
            tentativas.append({"modelo": f"claude:{modelo_claude}", "ok": r["ok"], "erro": r.get("erro"),
                               "dur_s": r.get("dur_s"), "custo_usd": r.get("custo_usd")})
            if r["ok"]:
                est.registrar_sucesso()
                est.ultimo_modelo[papel] = f"claude:{modelo_claude}"
                return {"ok": True, "obj": r["obj"], "modelo": f"claude:{modelo_claude}",
                        "tentativas": tentativas, "custo_usd": r.get("custo_usd"),
                        "dur_s": r.get("dur_s"), "tok_in": r.get("tok_in"),
                        "tok_out": r.get("tok_out"), "erro": None}
            log(f"  claude[{papel}] falhou ({i + 1}/2): {str(r.get('erro'))[:200]}")
            est.registrar_falha()
            if est.em_janela_fallback():
                break
            if i == 0:
                time.sleep(30)
    est.n_fallbacks += 1
    r = _chamar_opencode(system, user, schema, timeout)
    tentativas.append({"modelo": f"opencode:{OPENCODE_MODEL}", "ok": r["ok"], "erro": r.get("erro"),
                       "dur_s": r.get("dur_s"), "custo_usd": 0.0})
    est.ultimo_modelo[papel] = f"opencode:{OPENCODE_MODEL}"
    return {"ok": r["ok"], "obj": r.get("obj"), "modelo": f"opencode:{OPENCODE_MODEL}",
            "tentativas": tentativas, "custo_usd": 0.0, "dur_s": r.get("dur_s"),
            "tok_in": None, "tok_out": None, "erro": r.get("erro")}
