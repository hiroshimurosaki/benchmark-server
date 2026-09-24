#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
b3 — prepara pacotes de julgamento para o juiz por SUBAGENTE.

Alternativa ao `judge_b3.py` (que precisa de ANTHROPIC_API_KEY). Aqui o juiz é
uma instância do Claude rodando como subagente; este script só monta a entrada
dela: um arquivo por lote, com a pergunta, o gabarito e as respostas de todos
os modelos ANONIMIZADAS e EMBARALHADAS.

O anonimato importa: sem ele o juiz ancora em nome de modelo. O embaralhamento
importa: sem ele ancora em posição. O mapa rótulo→modelo fica só aqui, no
`_mapa.json`, que o juiz não lê.

    python3 projetos/b3/runner/make_judge_packets.py --results results_b3.jsonl \
        --extra projetos/b3/results_groq.jsonl projetos/b3/results_cohere.jsonl projetos/b3/results_prod_mix.jsonl \
        --questions projetos/b2/questions_b2.jsonl --out projetos/b3/judge --lotes 5
"""

from __future__ import annotations

import argparse
import json
import os
import random
from collections import defaultdict


def load_jsonl(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def classificar_desfecho(r: dict) -> str:
    """Três desfechos, não dois.

    O `outcome` do runner só distingue respondeu/escalou/erro. Mas 25% das
    execuções fazem uma terceira coisa: devolvem um menu de desambiguação
    ("você quer saber sobre 1, 2 ou 3?") sem entregar resposta nem escalar.
    Isso conta como `answered`, e um juiz que só vê `answered` dá nota alta a
    quem entregou zero. A etapa `disambiguation` nos `stages` é a evidência.
    """
    if r.get("outcome") == "error":
        return "erro"
    if r.get("outcome") == "call_attendant":
        return "escalou_para_humano"
    if any(s.get("stage") == "disambiguation" for s in r.get("stages") or []):
        return "pediu_esclarecimento"
    return "respondeu"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", nargs="+", required=True)
    ap.add_argument("--questions", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--lotes", type=int, default=5)
    ap.add_argument("--seed", type=int, default=20260908)
    args = ap.parse_args()

    random.seed(args.seed)
    os.makedirs(args.out, exist_ok=True)

    questions = {q["id"]: q for q in load_jsonl(args.questions)}
    by_q = defaultdict(list)
    for path in args.results:
        if not os.path.exists(path):
            print(f"aviso: {path} não existe, ignorando")
            continue
        for r in load_jsonl(path):
            if r.get("outcome") != "error":
                by_q[r["id"]].append(r)

    ids = [qid for qid in questions if by_q.get(qid)]
    ids.sort()
    mapa = {}
    pacotes = []

    for qid in ids:
        rs = list(by_q[qid])
        random.shuffle(rs)
        rotulos = [f"R{i + 1:02d}" for i in range(len(rs))]
        mapa[qid] = {rot: r["model"] for rot, r in zip(rotulos, rs)}
        q = questions[qid]
        pacotes.append({
            "id": qid,
            "trilha": q.get("trilha", ""),
            "pergunta": q["input"],
            "modo_esperado": q.get("modo_esperado", "?"),
            "objetivos": q.get("objetivos", []),
            "proibicoes": q.get("proibicoes", []),
            "respostas": [
                {
                    "rotulo": rot,
                    "desfecho": classificar_desfecho(r),
                    "escalacao": r.get("escalation"),
                    "texto": (r.get("answer") or "").strip(),
                }
                for rot, r in zip(rotulos, rs)
            ],
        })

    n = max(1, args.lotes)
    tam = (len(pacotes) + n - 1) // n
    for i in range(0, len(pacotes), tam):
        lote = i // tam + 1
        p = os.path.join(args.out, f"lote_{lote:02d}.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(pacotes[i:i + tam], f, ensure_ascii=False, indent=1)
        print(f"{p}: {len(pacotes[i:i + tam])} perguntas, "
              f"{sum(len(x['respostas']) for x in pacotes[i:i + tam])} respostas")

    with open(os.path.join(args.out, "_mapa.json"), "w", encoding="utf-8") as f:
        json.dump(mapa, f, ensure_ascii=False, indent=1)
    print(f"\nmapa rótulo→modelo em {args.out}/_mapa.json (o juiz NÃO lê este arquivo)")
    print(f"total: {len(pacotes)} perguntas, "
          f"{sum(len(x['respostas']) for x in pacotes)} respostas a julgar")


if __name__ == "__main__":
    main()
