#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
b3 / pergunta 1 — "qual o melhor modelo?"

Juiz Opus. Roda no PC do Fernando (o servidor não tem, nem deve ter, a chave
da Anthropic).

Três decisões de desenho que importam:

1. **Julga por pergunta, todos os modelos de uma vez.** 50 chamadas em vez de
   550. O juiz vê as N respostas lado a lado, o que torna a nota comparável
   entre modelos — julgar em isolamento produz notas que não se comparam.

2. **Os modelos são anonimizados e embaralhados** (A, B, C...) a cada pergunta.
   Sem isso o juiz ancora em nome de modelo e em posição.

3. **Escalar para atendente NÃO é erro por definição.** O fluxo documentado
   manda escalar quando a base não cobre a pergunta. O juiz recebe a fonte de
   verdade real e decide se, para AQUELA pergunta, escalar era a decisão certa.
   Sem isso o benchmark premiaria o modelo que mais inventa.

Sem ANTHROPIC_API_KEY, o caminho equivalente é o juiz por SUBAGENTE:
`build_fonte_verdade.py` → `make_judge_packets.py` → subagentes → `merge_judge.py`,
que produz o mesmo `scored_b3.json`.

Uso:
    set ANTHROPIC_API_KEY=...
    python projetos/b3/runner/build_fonte_verdade.py --data projetos/b3/data/oncorretor --out projetos/b3/judge/fonte_verdade.md
    env/Scripts/python.exe projetos/b3/runner/judge_b3.py \
        --results results_b3.jsonl --questions projetos/b2/questions_b2.jsonl \
        --corpus projetos/b3/judge/fonte_verdade.md --out scored_b3.json
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from collections import defaultdict

import anthropic

MODEL = "claude-opus-5"

SYSTEM_RUBRICA = """\
Você é o juiz de um benchmark que compara modelos de linguagem locais rodando \
o pipeline RAG de um chatbot de atendimento ao cliente da OnCorretor (SaaS para \
corretores de seguros SUSEP).

Você recebe, por pergunta:
  - a pergunta do cliente
  - os OBJETIVOS que uma boa resposta precisa cumprir
  - as PROIBIÇÕES que ela não pode violar
  - o MODO esperado (A = responde com o conteúdo; B = responde e sugere \
atendente; C = diz que não tem a informação nos documentos)
  - as respostas de vários modelos anônimos (A, B, C, ...), com o DESFECHO de \
cada uma

REGRA CENTRAL — escalar para atendente humano (`call_attendant`) NÃO é erro por \
definição. O fluxo do produto manda escalar quando a base não cobre a pergunta. \
Julgue assim:
  - se os OBJETIVOS são atendíveis pelos documentos e o modelo escalou → ERRO \
(escalação indevida): desfecho_apropriado = false
  - se a pergunta é adversarial, fora de domínio, ou a resposta não está nos \
documentos, e o modelo escalou ou recusou → CERTO: desfecho_apropriado = true
  - inventar uma resposta que não está nos documentos é a falha mais grave do \
benchmark, pior que escalar

Use a FONTE DE VERDADE fornecida (documentos + FAQ curado + tópicos designados para atendente humano) como única base sobre a OnCorretor. Um fato que só aparece no FAQ é válido — o pipeline responde por esse caminho também.

Responda SOMENTE com um objeto JSON, sem cercas de código e sem texto fora dele:

{"veredicto": [
  {"rotulo": "A",
   "objetivos_cumpridos": <int>,
   "proibicoes_violadas": <int>,
   "modo_detectado": "A"|"B"|"C"|"outro",
   "modo_ok": <bool>,
   "alucinacao": <bool>,
   "desfecho_apropriado": <bool>,
   "nota": <int 0-100>,
   "porque": "<no máximo 25 palavras>"}
]}

A `nota` pondera: objetivos cumpridos (40), ausência de alucinação (25), \
desfecho apropriado (20), sem violar proibições (10), modo correto (5).\
"""


def load_jsonl(path: str) -> list:
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def build_user_block(q: dict, entries: list[tuple[str, dict]]) -> str:
    p = [
        f"PERGUNTA DO CLIENTE: {q['input']}",
        f"TRILHA: {q.get('trilha', '')}",
        f"MODO ESPERADO: {q.get('modo_esperado', '?')}",
        "OBJETIVOS:",
    ]
    p += [f"  - {o}" for o in q.get("objetivos", [])] or ["  (nenhum)"]
    p.append("PROIBIÇÕES:")
    p += [f"  - {o}" for o in q.get("proibicoes", [])] or ["  (nenhuma)"]
    p.append("")
    p.append("RESPOSTAS A JULGAR:")
    for rotulo, r in entries:
        ans = (r.get("answer") or "").strip() or "(vazio)"
        p.append(f"--- {rotulo} | desfecho={r.get('outcome')} "
                 f"escalacao={r.get('escalation') or '-'} ---")
        p.append(ans)
    p.append("")
    p.append(f"Devolva o JSON com exatamente {len(entries)} veredictos, "
             f"um por rótulo, na ordem {', '.join(r for r, _ in entries)}.")
    return "\n".join(p)


def parse_json(text: str) -> dict:
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        i, j = t.find("{"), t.rfind("}")
        if i >= 0 and j > i:
            return json.loads(t[i:j + 1])
        raise


def judge_question(client, corpus: str, q: dict, results: list[dict],
                   effort: str) -> list[dict]:
    order = list(results)
    random.shuffle(order)
    rotulos = [chr(ord("A") + i) for i in range(len(order))]
    entries = list(zip(rotulos, order))

    with client.messages.stream(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": effort},
        system=[
            {"type": "text", "text": SYSTEM_RUBRICA},
            # A fonte de verdade é idêntica nas 50 chamadas: cacheada, custa
            # ~10% a partir da segunda. É o que torna viável julgar tudo com Opus.
            {"type": "text",
             "text": "FONTE DE VERDADE DA ONCORRETOR:\n\n" + corpus,
             "cache_control": {"type": "ephemeral"}},
        ],
        messages=[{"role": "user", "content": build_user_block(q, entries)}],
    ) as stream:
        msg = stream.get_final_message()

    if msg.stop_reason == "refusal":
        raise RuntimeError(f"juiz recusou: {getattr(msg.stop_details, 'category', '?')}")

    text = "".join(b.text for b in msg.content if b.type == "text")
    data = parse_json(text)
    by_rotulo = {v["rotulo"]: v for v in data["veredicto"]}

    out = []
    for rotulo, r in entries:
        v = by_rotulo.get(rotulo)
        if v is None:
            continue
        v = dict(v)
        v.pop("rotulo", None)
        out.append({"id": q["id"], "model": r["model"], **v})
    usage = msg.usage
    return out, {
        "in": usage.input_tokens,
        "cache_read": getattr(usage, "cache_read_input_tokens", 0) or 0,
        "cache_write": getattr(usage, "cache_creation_input_tokens", 0) or 0,
        "out": usage.output_tokens,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results_b3.jsonl")
    ap.add_argument("--questions", default="projetos/b2/questions_b2.jsonl")
    # Precisa ser a fonte de verdade COMPLETA (documento + FAQ + tópicos de
    # atendente), não só o documento: fatos que existem apenas no FAQ seriam
    # julgados como alucinação. Gere com `build_fonte_verdade.py`.
    ap.add_argument("--corpus", default="projetos/b3/judge/fonte_verdade.md")
    ap.add_argument("--out", default="scored_b3.json")
    ap.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    ap.add_argument("--limit", type=int, default=0, help="julgar só as N primeiras perguntas")
    ap.add_argument("--seed", type=int, default=20260908)
    args = ap.parse_args()

    random.seed(args.seed)
    client = anthropic.Anthropic()

    with open(args.corpus, encoding="utf-8") as f:
        corpus = f.read()

    questions = {q["id"]: q for q in load_jsonl(args.questions)}
    by_q: dict[str, list] = defaultdict(list)
    for r in load_jsonl(args.results):
        if r.get("outcome") != "error":
            by_q[r["id"]].append(r)

    # Resume: não re-julga o que já está no arquivo de saída.
    scored: list[dict] = []
    if os.path.exists(args.out):
        with open(args.out, encoding="utf-8") as f:
            scored = json.load(f).get("veredictos", [])
    done = {(v["id"], v["model"]) for v in scored}

    ids = [qid for qid in questions if qid in by_q]
    if args.limit:
        ids = ids[:args.limit]

    custo = {"in": 0, "cache_read": 0, "cache_write": 0, "out": 0}
    for n, qid in enumerate(ids, 1):
        pend = [r for r in by_q[qid] if (qid, r["model"]) not in done]
        if not pend:
            continue
        try:
            vs, u = judge_question(client, corpus, questions[qid], pend, args.effort)
        except Exception as e:
            print(f"[{n}/{len(ids)}] {qid} FALHOU: {type(e).__name__}: {e}", flush=True)
            continue
        scored.extend(vs)
        for k in custo:
            custo[k] += u[k]
        media = sum(v["nota"] for v in vs) / max(len(vs), 1)
        print(f"[{n}/{len(ids)}] {qid}: {len(vs)} respostas julgadas, "
              f"nota média {media:.1f}", flush=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"modelo_juiz": MODEL, "effort": args.effort,
                       "custo_tokens": custo, "veredictos": scored},
                      f, ensure_ascii=False, indent=1)

    # $5/MTok in, $25/MTok out; leitura de cache ~10% do input, escrita ~1.25x.
    usd = (custo["in"] * 5 + custo["cache_write"] * 6.25
           + custo["cache_read"] * 0.5 + custo["out"] * 25) / 1_000_000
    print(f"\nOK -> {args.out} | {len(scored)} veredictos | "
          f"tokens {custo} | custo estimado US$ {usd:.2f}")


if __name__ == "__main__":
    sys.exit(main())
