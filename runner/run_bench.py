#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orquestrador dos benchmarks b1 (tool-call) e b2 (RAG) via Ollama.
Roda no servidor (Debian, python3 stdlib only — sem dependências externas).

FLUXO:
  Para cada modelo (loop externo, pra carregar cada modelo só uma vez):
    para cada variante de thinking (on/off, se o modelo suporta):
      b1: perguntas do subconjunto do tier -> protocolo de 2 turnos
      b2: perguntas do subconjunto do tier -> 1 turno
  Cada resposta é anexada na hora em results_b1.jsonl / results_b2.jsonl (crash-safe).
  Reexecução: pula (id, model, thinking, bench) já presentes (resume).
  Todo request e troca de modelo é logado em run.log.

ENTRADAS (mesma pasta, ver --root):
  models.jsonl   : {"name","tier","thinking"}  name = tag Ollama (ex.: bench-q4b)
  ../b1/questions_b1.jsonl, ../b1/schema_b1.json
  ../b2/questions_b2.jsonl, ../b2/kb_oncorretor.md
  prompts/b1_system.txt   (system do b1, com {today} {dataLastDay} {small_sample_limit})
  prompts/b2_system.txt   (system do b2, com {context})

SAÍDAS: ../results_b1.jsonl, ../results_b2.jsonl, run.log

Uso:
  python3 run_bench.py --root . --host http://localhost:11434 [--bench b1,b2] [--dry-run]
"""
import argparse, json, os, sys, time, urllib.request, urllib.error
from datetime import datetime

# --------------------------------------------------------------- infra HTTP/log

LOGF = None
def log(msg):
    line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {msg}"
    print(line, flush=True)
    if LOGF:
        LOGF.write(line + "\n"); LOGF.flush()

def ollama_chat(host, model, messages, think=None, num_predict=512, timeout=1800):
    """Chama /api/chat com stream=true. Retorna (texto, ttft_s, total_s, eval_count).
    think: None (default), True ou False -> repassa opção 'think' do Ollama."""
    body = {"model": model, "messages": messages, "stream": True,
            "options": {"num_predict": num_predict, "temperature": 0}}
    if think is not None:
        body["think"] = think
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(host + "/api/chat", data=data,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time(); ttft = None; text = []; eval_count = 0
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        for raw in resp:
            raw = raw.strip()
            if not raw:
                continue
            obj = json.loads(raw)
            msg = obj.get("message", {})
            chunk = msg.get("content", "")
            if chunk:
                if ttft is None:
                    ttft = time.time() - t0
                text.append(chunk)
            if obj.get("done"):
                eval_count = obj.get("eval_count", 0)
    total = time.time() - t0
    if ttft is None:
        ttft = total
    return "".join(text), round(ttft, 3), round(total, 3), eval_count

# --------------------------------------------------------------- carga de dados

def load_jsonl(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out

def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def done_keys(path):
    """Chaves (id, model, thinking) já feitas, pra resume."""
    keys = set()
    if os.path.exists(path):
        for r in load_jsonl(path):
            keys.add((r["id"], r["model"], bool(r.get("thinking"))))
    return keys

def append_jsonl(path, rec):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

# --------------------------------------------------------------- prompts b1

def b1_system(root, schema):
    tpl = read_text(os.path.join(root, "prompts", "b1_system.txt"))
    a = schema["anchors"]
    return (tpl.replace("{today}", a["today"])
               .replace("{dataLastDay}", a["dataLastDay"])
               .replace("{small_sample_limit}", str(a["SMALL_SAMPLE_LIMIT"])))

B1_TOOLCALL_INSTR = (
    "\n\nVocê tem estas tools (não invente outras):\n"
    "- get_access_stats(from, to)  # datas YYYY-MM-DD inclusivas\n"
    "- get_reservations(from, to, area?)\n"
    "- get_person_history(name, limit?)\n"
    "Para ESTA mensagem, responda APENAS com um JSON de chamada de tool, sem texto extra:\n"
    '{\"tool\": \"<nome>\", \"args\": { ... }}\n'
    "Se o pedido não puder/dever ser atendido por nenhuma tool, responda {\"tool\": null, \"args\": {}}."
)

def run_b1_item(host, model, think, sys_prompt, q):
    gab = q["gabarito"]
    # Orcamento maior quando thinking esta ligado: o raciocinio consome tokens antes
    # de o modelo emitir o 'content' final; com budget curto o content sai vazio
    # (bug pego no smoke: phaseA vazia com think=True). think None/False -> budget curto.
    napA = 1024 if think else 256
    napB = 1536 if think else 512
    # Turno A: pedir a tool-call
    msgs = [{"role": "system", "content": sys_prompt + B1_TOOLCALL_INSTR},
            {"role": "user", "content": q["user"]}]
    rawA, ttftA, totA, ecA = ollama_chat(host, model, msgs, think=think, num_predict=napA)
    # Turno B: devolver mock e pedir a resposta final
    mock = gab.get("mock_result") or {}
    msgs += [{"role": "assistant", "content": rawA},
             {"role": "user", "content":
              "Resultado da tool (JSON): " + json.dumps(mock, ensure_ascii=False) +
              "\nAgora produza a resposta final. Sua mensagem final deve ser APENAS um JSON: "
              '{\"answer\": \"<2 a 4 frases>\", \"highlights\": [\"<achado>\", \"<achado>\"]}'}]
    rawB, ttftB, totB, ecB = ollama_chat(host, model, msgs, think=think, num_predict=napB)
    return {
        "phaseA": {"raw": rawA, "ttft_s": ttftA, "latency_s": totA, "tokens_out": ecA},
        "phaseB": {"raw": rawB, "ttft_s": ttftB, "latency_s": totB, "tokens_out": ecB},
    }

# --------------------------------------------------------------- prompts b2

def b2_system(root, kb):
    tpl = read_text(os.path.join(root, "prompts", "b2_system.txt"))
    return tpl.replace("{context}", kb)

def run_b2_item(host, model, think, sys_prompt, q):
    user = q["input"]
    if q.get("historico"):
        user = ("<CONTEXTO_ANTERIOR>" + q["historico"] + "</CONTEXTO_ANTERIOR>\n"
                "<PERGUNTA_ATUAL>" + q["input"] + "</PERGUNTA_ATUAL>")
    msgs = [{"role": "system", "content": sys_prompt},
            {"role": "user", "content": user}]
    raw, ttft, tot, ec = ollama_chat(host, model, msgs, think=think, num_predict=512)
    return {"answer_raw": raw, "ttft_s": ttft, "latency_s": tot, "tokens_out": ec}

# --------------------------------------------------------------- loop principal

def tier_ok(q, tier):
    return tier in q.get("tiers", []) or tier in (q.get("tier") and [q["tier"]] or [])

def main():
    global LOGF
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--host", default="http://localhost:11434")
    ap.add_argument("--bench", default="b1,b2")
    ap.add_argument("--models", default="models.jsonl",
                    help="arquivo de modelos (ex.: models_smoke.jsonl)")
    ap.add_argument("--limit", type=int, default=0,
                    help="max perguntas por (modelo, thinking, bench); 0 = todas (smoke usa ex. 5)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    benches = args.bench.split(",")
    LOGF = open(os.path.join(root, "run.log"), "a", encoding="utf-8")
    log(f"=== START run_bench root={root} host={args.host} bench={benches} "
        f"models={args.models} limit={args.limit} dry={args.dry_run} ===")

    models = load_jsonl(os.path.join(root, args.models))
    # Carrega so o que o(s) bench(es) selecionado(s) precisam.
    schema = q_b1 = q_b2 = kb = sysA = sysB = None
    if "b1" in benches:
        schema = json.load(open(os.path.join(root, "..", "b1", "schema_b1.json"), encoding="utf-8"))
        q_b1 = load_jsonl(os.path.join(root, "..", "b1", "questions_b1.jsonl"))
        sysA = b1_system(root, schema)
    if "b2" in benches:
        q_b2 = load_jsonl(os.path.join(root, "..", "b2", "questions_b2.jsonl"))
        kb = read_text(os.path.join(root, "..", "b2", "kb_oncorretor.md"))
        sysB = b2_system(root, kb)
    res_b1 = os.path.join(root, "..", "results_b1.jsonl")
    res_b2 = os.path.join(root, "..", "results_b2.jsonl")
    done_b1 = done_keys(res_b1)
    done_b2 = done_keys(res_b2)

    total_calls = 0
    for m in models:
        name, tier = m["name"], m["tier"]
        think_variants = [False, True] if m.get("thinking") else [None]
        log(f"--- MODELO {name} (tier={tier}, thinking={m.get('thinking')}) ---")
        for think in think_variants:
            tflag = bool(think)
            # b1
            if "b1" in benches:
                sel = [q for q in q_b1 if tier_ok(q, tier)]
                if args.limit:
                    sel = sel[:args.limit]
                for q in sel:
                    if (q["id"], name, tflag) in done_b1:
                        continue
                    total_calls += 1
                    if args.dry_run:
                        continue
                    try:
                        r = run_b1_item(args.host, name, think, sysA, q)
                        rec = {"id": q["id"], "model": name, "tier": tier, "thinking": tflag,
                               "error": None, **r}
                    except Exception as e:
                        rec = {"id": q["id"], "model": name, "tier": tier, "thinking": tflag,
                               "error": str(e), "phaseA": {"raw": ""}, "phaseB": None}
                        log(f"  ERRO b1 {q['id']} {name} think={tflag}: {e}")
                    append_jsonl(res_b1, rec)
                    log(f"  b1 {q['id']} {name} think={tflag} ok")
            # b2
            if "b2" in benches:
                sel = [q for q in q_b2 if tier_ok(q, tier)]
                if args.limit:
                    sel = sel[:args.limit]
                for q in sel:
                    if (q["id"], name, tflag) in done_b2:
                        continue
                    total_calls += 1
                    if args.dry_run:
                        continue
                    try:
                        r = run_b2_item(args.host, name, think, sysB, q)
                        rec = {"id": q["id"], "model": name, "tier": tier, "thinking": tflag,
                               "error": None, **r}
                    except Exception as e:
                        rec = {"id": q["id"], "model": name, "tier": tier, "thinking": tflag,
                               "error": str(e), "answer_raw": "", "ttft_s": None, "latency_s": None}
                        log(f"  ERRO b2 {q['id']} {name} think={tflag}: {e}")
                    append_jsonl(res_b2, rec)
                    log(f"  b2 {q['id']} {name} think={tflag} ok")

    log(f"=== FIM. chamadas {'previstas' if args.dry_run else 'executadas'}: {total_calls} ===")

if __name__ == "__main__":
    main()
