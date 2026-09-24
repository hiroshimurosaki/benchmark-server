#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
b3 — benchmark do FLUXO REAL do Answer Service contra o servidor Ollama.

Responde às perguntas 1 e 2:
  Q1 "qual o melhor modelo?"        → resposta + desfecho por pergunta, julgados
                                      depois por `judge_b3.py` (Opus, no PC)
  Q2 "quanto tempo por pergunta?"   → wall time ponta a ponta do pipeline, com
                                      breakdown por etapa de LLM

Diferença para o b1/b2: aqui NÃO existe prompt de benchmark. O que roda é
`processor.answer_user_question` — contextualizador, verificador de relevância,
desambiguador, FAQ semântico (157 entradas reais), RAG sobre o FAISS real,
verificador de resposta e a escada de resgate. Uma pergunta dispara 3-4 chamadas
de LLM no caso comum e até ~20 no pior caso, e é isso que precisa caber no tempo
de resposta do WhatsApp.

Saída (`results_b3.jsonl`, append-only e resumível), um registro por
(pergunta × modelo):
    latency_s        wall time do pipeline inteiro
    n_llm_calls      quantas chamadas de LLM a pergunta custou
    stages[]         etapa, modelo, ttft, latência, tokens in/out, truncado
    outcome          answered | call_attendant | error
    escalation       motivo da escalação, quando houver
    used_rag         se a etapa de geração chegou a rodar (senão: FAQ/saudação)
    answer           texto entregue ao cliente

Uso no servidor:
    # no servidor, dentro do bundle ~/benchmark/b3 (montado por projetos/b3/runner/deploy_b3.sh):
    .venv/bin/python runner/run_b3.py --root . --models runner/models_b3.jsonl
    .venv/bin/python runner/run_b3.py --root . --models runner/models_b3.jsonl --limit 3   # smoke
    # no PC, a partir de projetos/b3 (o bundle local): --questions ../b2/questions_b2.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from datetime import datetime

# Imports locais. No repo: esta pasta + comum/. No bundle do servidor
# (~/benchmark/b3/runner) tudo fica achatado em runner/ e as outras pastas
# simplesmente não existem — por isso o `isdir`.
_AQUI = os.path.dirname(os.path.abspath(__file__))
_RAIZ = os.path.normpath(os.path.join(_AQUI, "..", "..", ".."))
for _p in (os.path.join(_RAIZ, "comum"), _AQUI):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)
import b3_env  # noqa: E402


LOGF = None


def log(msg: str) -> None:
    line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {msg}"
    print(line, flush=True)
    if LOGF:
        LOGF.write(line + "\n")
        LOGF.flush()


def load_jsonl(path: str) -> list:
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def append_jsonl(path: str, rec: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def done_keys(path: str) -> set:
    keys = set()
    if os.path.exists(path):
        for r in load_jsonl(path):
            keys.add((r["id"], r["model"]))
    return keys


def tier_ok(q: dict, tier: str) -> bool:
    tiers = q.get("tiers") or ([q["tier"]] if q.get("tier") else [])
    return tier in tiers


# ------------------------------------------------------------------ observador

class StageRecorder:
    """Coleta uma linha por chamada de LLM, via `llm_provider.set_observer`."""

    def __init__(self):
        self.stages: list[dict] = []

    def __call__(self, stage: str, info: dict) -> None:
        self.stages.append({
            "stage": stage,
            "model": info.get("model", ""),
            "ttft_s": info.get("ttft_s"),
            "latency_s": info.get("total_s"),
            "tok_in": info.get("prompt_tokens", 0),
            "tok_out": info.get("completion_tokens", 0),
            "truncated": bool(info.get("truncated")),
        })

    def reset(self) -> None:
        self.stages = []

    def summary(self) -> dict:
        by_stage: dict[str, float] = {}
        for s in self.stages:
            by_stage[s["stage"]] = round(
                by_stage.get(s["stage"], 0.0) + (s["latency_s"] or 0.0), 3
            )
        return {
            "n_llm_calls": len(self.stages),
            "llm_s_total": round(sum(s["latency_s"] or 0.0 for s in self.stages), 3),
            "tok_in": sum(s["tok_in"] for s in self.stages),
            "tok_out": sum(s["tok_out"] for s in self.stages),
            "truncated_any": any(s["truncated"] for s in self.stages),
            "s_por_etapa": by_stage,
            "used_rag": any(s["stage"] == "Answer_generator" for s in self.stages),
        }


# ----------------------------------------------------------------------- warmup

def warm_model(model: str, base_url: str, timeout: int = 900) -> dict:
    """Carrega o modelo na memória antes de cronometrar qualquer pergunta.

    Sem isso a primeira pergunta de cada modelo carrega 5-40 GB do disco e a
    média fica envenenada. O tempo de load é reportado à parte — é dado útil
    para dimensionar `OLLAMA_KEEP_ALIVE` em produção.
    """
    from Answer_service.src.services.API.llm_provider import OllamaClient

    c = OllamaClient(base_url)
    t0 = time.perf_counter()
    try:
        out = c.chat(
            model=model, system_content="Responda apenas: ok.",
            user_content="ok", max_tokens=8, temperature=0.0, timeout=timeout,
        )
        return {"load_s": round(time.perf_counter() - t0, 2), "ok": True,
                "probe": (out.get("text") or "")[:40]}
    except Exception as e:
        return {"load_s": round(time.perf_counter() - t0, 2), "ok": False, "erro": str(e)[:200]}


# -------------------------------------------------------------------- pipeline

def run_one(pipeline, q: dict, model: str, rec: StageRecorder) -> dict:
    """Uma pergunta, ponta a ponta, pelo pipeline real."""
    from Answer_service.src.services.processor import reset_greeting_for_session

    # Sessão única por (modelo, pergunta): isola histórico e estado de saudação,
    # senão a resposta de uma pergunta contamina a próxima e os modelos não são
    # comparáveis entre si.
    phone = f"bench-{model.replace(':', '_')}-{q['id']}"
    reset_greeting_for_session(phone)
    rec.reset()

    body = q["input"]
    if q.get("historico"):
        body = q["input"]  # o pipeline lê histórico do disco, não do prompt

    t0 = time.perf_counter()
    err = None
    answer = ""
    escalation = None
    try:
        answer, _qa, _client, escalation_meta = pipeline(body, phone)
        escalation = getattr(escalation_meta, "reason", None) if escalation_meta else None
        if escalation is None and isinstance(escalation_meta, dict):
            escalation = escalation_meta.get("reason")
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        traceback.print_exc()
    latency = round(time.perf_counter() - t0, 3)

    answer = answer if isinstance(answer, str) else ""
    escalou = bool(escalation) or answer.strip() == "call_attendant"
    outcome = "error" if err else ("call_attendant" if escalou else "answered")

    return {
        "id": q["id"],
        "trilha": q.get("trilha", ""),
        "input": q["input"],
        "latency_s": latency,
        "outcome": outcome,
        "escalation": escalation,
        "answer": answer,
        "error": err,
        "stages": rec.stages,
        **rec.summary(),
    }


def main():
    global LOGF
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--org", default="oncorretor")
    ap.add_argument("--models", default="runner/models_b3.jsonl")
    ap.add_argument("--questions", default="b2/questions_b2.jsonl",
                    help="banco de perguntas (o b2 já tem objetivos/proibições)")
    ap.add_argument("--host", default="http://127.0.0.1:11434")
    ap.add_argument("--out", default="results_b3.jsonl")
    ap.add_argument("--limit", type=int, default=0, help="perguntas por modelo (0 = todas)")
    ap.add_argument("--only", default="", help="rodar só estes modelos (vírgula)")
    ap.add_argument("--num-ctx", type=int, default=8192)
    ap.add_argument("--all-questions", action="store_true",
                    help="ignora o tier e roda as 50 perguntas em todo modelo "
                         "(comparação direta; só vale porque o fluxo local se "
                         "mostrou rápido no smoke)")
    ap.add_argument("--provider", default="ollama", choices=["ollama", "groq"],
                    help="groq = linha de base com o provedor de produção atual")
    ap.add_argument("--repo", default="", help="caminho do repo rag-chatbot "
                    "(default: <root>/repo). Usado na linha de base do Groq.")
    ap.add_argument("--key-prefix", default="",
                    help="com --provider groq, restringe o pool a chaves com este "
                         "prefixo (GROQ_KEY_ ou COHERE_KEY_). Sem isso o pool é "
                         "misto e quem responde é a 1ª chave da ordem do .env — "
                         "que é como produção roda hoje, mas não isola o modelo.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    os.environ["OLLAMA_BASE_URL"] = args.host
    os.environ["OLLAMA_NUM_CTX"] = str(args.num_ctx)

    LOGF = open(os.path.join(root, "run_b3.log"), "a", encoding="utf-8")
    ctx = b3_env.bootstrap(bundle_root=root, org_id=args.org,
                           provider=args.provider, repo_dir=args.repo or None)
    log(f"=== START b3 org={ctx.org_id} ai={ctx.features.ai.enabled} "
        f"threshold={ctx.features.ai.confidence_threshold} corpus={ctx.n_corpus} "
        f"faq={ctx.n_faq} dtq={ctx.n_dtq} num_ctx={args.num_ctx} ===")

    from Answer_service.src.controllers.api_key_manager import ChangeApiKey
    from Answer_service.src.services.API import llm_provider
    from Answer_service.src.services.API.client_ai import ClientAI
    from Answer_service.src.services.API.qa_system import get_qa_system
    from Answer_service.src.services.processor import answer_user_question

    ChangeApiKey.load_api_keys()
    if args.key_prefix:
        nomes = [k for k in ChangeApiKey.API_KEY_NAMES_ORDER
                 if k.startswith(args.key_prefix)]
        if not nomes:
            log(f"FATAL: nenhuma chave com prefixo {args.key_prefix}")
            return 1
        ChangeApiKey.API_KEY_NAMES_ORDER = nomes
        ChangeApiKey.API_KEYS_DICT = {k: ChangeApiKey.API_KEYS_DICT[k] for k in nomes}
        ChangeApiKey.CURRENT_API_KEY_INDEX = 0
        os.environ["API_KEY"] = ChangeApiKey.API_KEYS_DICT[nomes[0]]
        log(f"pool restrito a {args.key_prefix}: {len(nomes)} chave(s)")

    recorder = StageRecorder()
    llm_provider.set_observer(recorder)

    verifier = ClientAI()
    client = verifier.create_client()
    if client is None:
        log("FATAL: cliente LLM não inicializou")
        return 1

    # O índice FAISS é o mesmo para todos os modelos — construir uma vez só.
    t0 = time.perf_counter()
    qa_system = get_qa_system(ctx.org_id, ctx.features)
    log(f"qa_system pronto em {time.perf_counter() - t0:.1f}s "
        f"(prep_chain={'ok' if qa_system is not None else 'None — RAG indisponível'})")

    susep = os.getenv("SUSEP_CODE", "12345678")
    # O pipeline DEVOLVE um client possivelmente novo: quando ele rotaciona a
    # chave (Groq ↔ Cohere), o client antigo passa a não bater com a
    # os.environ["API_KEY"] que `client_ai` relê a cada chamada. `ai_subscriber`
    # trata isso com `state.update_ai_components(client_updated)`
    # (ai_subscriber.py:897) — o harness precisa fazer o mesmo, senão a 1ª
    # rotação envenena todas as perguntas seguintes.
    live = {"client": client}

    def pipeline(body: str, phone: str):
        out = answer_user_question(
            body, phone, ctx.org_id, susep, live["client"], qa_system, verifier,
            True, ctx.who_am_i, ctx.prompts, ctx.features.ai.confidence_threshold,
        )
        if out[2] is not None:
            live["client"] = out[2]
        return out

    models = load_jsonl(os.path.join(root, args.models))
    if args.only:
        wanted = {m.strip() for m in args.only.split(",") if m.strip()}
        models = [m for m in models if m["name"] in wanted]
    questions = load_jsonl(os.path.join(root, args.questions))
    res_path = os.path.join(root, args.out)
    done = done_keys(res_path)

    planned = 0
    for m in models:
        name, tier = m["name"], m.get("tier", "barato")
        sel = questions if args.all_questions else [q for q in questions if tier_ok(q, tier)]
        if args.limit:
            sel = sel[:args.limit]
        sel = [q for q in sel if (q["id"], name) not in done]
        planned += len(sel)
        if not sel:
            log(f"--- {name}: nada a fazer (resume) ---")
            continue
        if args.dry_run:
            log(f"--- {name} (tier={tier}): {len(sel)} perguntas ---")
            continue

        if args.provider == "groq":
            os.environ["GROQ_MODEL"] = name
            w = {"load_s": 0.0, "ok": True}
        else:
            os.environ["OLLAMA_MODEL"] = name
            os.environ["OLLAMA_THINK"] = "true" if m.get("thinking") else "false"
        log(f"--- MODELO {name} (tier={tier}, thinking={bool(m.get('thinking'))}, "
            f"{len(sel)} perguntas) ---")

        if args.provider != "groq":
            w = warm_model(name, args.host)
        log(f"  warmup: load={w['load_s']}s ok={w['ok']} {w.get('erro', '')}")
        if not w["ok"]:
            for q in sel:
                append_jsonl(res_path, {
                    "id": q["id"], "model": name, "tier": tier,
                    "outcome": "error", "error": f"warmup: {w.get('erro')}",
                    "latency_s": None, "n_llm_calls": 0, "stages": [],
                })
            continue

        t_model = time.perf_counter()
        for i, q in enumerate(sel, 1):
            r = run_one(pipeline, q, name, recorder)
            r.update({
                "model": name, "tier": tier,
                "thinking": bool(m.get("thinking")),
                "model_load_s": w["load_s"],
                "quando": datetime.now().isoformat(timespec="seconds"),
            })
            append_jsonl(res_path, r)
            log(f"  [{i}/{len(sel)}] {q['id']} {r['outcome']:14s} "
                f"{r['latency_s']:7.2f}s  {r['n_llm_calls']} chamadas  "
                f"rag={r['used_rag']}  {'TRUNCADO' if r['truncated_any'] else ''}")
        log(f"  {name}: {len(sel)} perguntas em {time.perf_counter() - t_model:.0f}s")

    log(f"=== FIM. {'previstas' if args.dry_run else 'executadas'}: {planned} ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
