#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
b3 — leaderboard e respostas às 3 perguntas do benchmark.

Roda no servidor (durante o run, para acompanhar) ou no PC (depois, junto com
`scored_b3.json` do juiz Opus). Sem dependência externa.

    python3 runner/report_b3.py --results results_b3.jsonl \
        [--scored scored_b3.json] [--index index_bench.json] [--json relatorio_b3.json]
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict


def load_jsonl(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def pct(n, d):
    return 100.0 * n / d if d else 0.0


def quantil(xs, q):
    if not xs:
        return 0.0
    s = sorted(xs)
    i = min(int(q * (len(s) - 1) + 0.5), len(s) - 1)
    return s[i]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results_b3.jsonl")
    ap.add_argument("--scored", default="")
    ap.add_argument("--index", default="")
    ap.add_argument("--json", default="")
    ap.add_argument("--models", default="", help="models_b3.jsonl — habilita o "
                    "bloco de progresso (quanto falta, ETA) no --json")
    ap.add_argument("--n-perguntas", type=int, default=50)
    args = ap.parse_args()

    rows = load_jsonl(args.results)
    notas = defaultdict(list)
    extras = defaultdict(Counter)
    if args.scored and os.path.exists(args.scored):
        blob = json.load(open(args.scored, encoding="utf-8"))
        for v in blob.get("veredictos", []):
            notas[v["model"]].append(v["nota"])
            extras[v["model"]]["alucinacao"] += bool(v.get("alucinacao"))
            extras[v["model"]]["desfecho_ruim"] += (not v.get("desfecho_apropriado", True))
            extras[v["model"]]["proibicao"] += int(v.get("proibicoes_violadas") or 0)
            extras[v["model"]]["modo_ok"] += bool(v.get("modo_ok"))

    by_model = defaultdict(list)
    for r in rows:
        by_model[r["model"]].append(r)

    linhas = []
    for model, rs in by_model.items():
        ok = [r for r in rs if r.get("outcome") != "error"]
        lat = [r["latency_s"] for r in ok if r.get("latency_s")]
        calls = [r.get("n_llm_calls", 0) for r in ok]
        esc = sum(1 for r in ok if r.get("outcome") == "call_attendant")
        trunc = sum(1 for r in ok if r.get("truncated_any"))
        tok_out = sum(r.get("tok_out", 0) for r in ok)
        llm_s = sum(r.get("llm_s_total", 0) or 0 for r in ok)
        n = len(notas[model])
        linhas.append({
            "model": model,
            "n": len(rs),
            "erros": len(rs) - len(ok),
            "nota": round(sum(notas[model]) / n, 1) if n else None,
            "s_medio": round(sum(lat) / len(lat), 1) if lat else None,
            "s_p50": round(quantil(lat, 0.50), 1),
            "s_p95": round(quantil(lat, 0.95), 1),
            "chamadas": round(sum(calls) / len(calls), 1) if calls else 0,
            "escalou_%": round(pct(esc, len(ok)), 1),
            "truncou_%": round(pct(trunc, len(ok)), 1),
            "tok_s": round(tok_out / llm_s, 1) if llm_s else 0,
            "aluc_%": round(pct(extras[model]["alucinacao"], n), 1) if n else None,
            "desf_ruim_%": round(pct(extras[model]["desfecho_ruim"], n), 1) if n else None,
            "load_s": (rs[0].get("model_load_s") if rs else None),
        })

    linhas.sort(key=lambda x: (-(x["nota"] or -1), x["s_medio"] or 9e9))

    print("\n" + "=" * 118)
    print("b3 — PIPELINE RAG REAL NO SERVIDOR   (nota = juiz Opus; s = pipeline "
          "ponta a ponta, não uma chamada de LLM)")
    print("=" * 118)
    hdr = ("modelo", "n", "err", "nota", "s_med", "s_p50", "s_p95", "cham",
           "escalou%", "trunc%", "tok/s", "aluc%", "desf_ruim%", "load_s")
    fmt = "{:<22}{:>4}{:>5}{:>7}{:>7}{:>7}{:>7}{:>6}{:>10}{:>8}{:>7}{:>7}{:>12}{:>8}"
    print(fmt.format(*hdr))
    print("-" * 118)
    for x in linhas:
        print(fmt.format(
            x["model"][:22], x["n"], x["erros"],
            "-" if x["nota"] is None else x["nota"],
            "-" if x["s_medio"] is None else x["s_medio"],
            x["s_p50"], x["s_p95"], x["chamadas"], x["escalou_%"], x["truncou_%"],
            x["tok_s"],
            "-" if x["aluc_%"] is None else x["aluc_%"],
            "-" if x["desf_ruim_%"] is None else x["desf_ruim_%"],
            "-" if x["load_s"] is None else x["load_s"],
        ))

    # --- distribuição de etapas (onde o tempo mora) -------------------------
    etapa_s = Counter()
    etapa_n = Counter()
    for r in rows:
        for s in r.get("stages") or []:
            etapa_s[s["stage"]] += s.get("latency_s") or 0
            etapa_n[s["stage"]] += 1
    if etapa_n:
        print("\nONDE O TEMPO MORA (todas as execuções somadas)")
        print("{:<24}{:>10}{:>12}{:>12}".format("etapa", "chamadas", "s totais", "s/chamada"))
        for st, tot in etapa_s.most_common():
            print("{:<24}{:>10}{:>12.1f}{:>12.2f}".format(
                st, etapa_n[st], tot, tot / etapa_n[st]))

    # --- motivos de escalação ----------------------------------------------
    motivos = Counter(r.get("escalation") for r in rows
                      if r.get("outcome") == "call_attendant")
    if motivos:
        print("\nPOR QUE ESCALOU")
        for k, v in motivos.most_common():
            print(f"  {k or '(sem motivo registrado)':<26} {v}")

    # --- pergunta 3 ---------------------------------------------------------
    if args.index and os.path.exists(args.index):
        idx = json.load(open(args.index, encoding="utf-8"))
        print("\nBANCO VETORIAL (pergunta 3)")
        print("{:>7}{:>10}{:>9}{:>12}{:>12}{:>11}".format(
            "escala", "KB", "chunks", "embed+idx s", "TOTAL s", "ms/chunk"))
        vistos = set()
        for m in idx["runs"]:
            if m["scale"] in vistos:
                continue
            vistos.add(m["scale"])
            iguais = [x for x in idx["runs"] if x["scale"] == m["scale"]]
            med = lambda k: sum(x[k] for x in iguais) / len(iguais)  # noqa: E731
            print("{:>7}{:>10.1f}{:>9}{:>12.2f}{:>12.2f}{:>11.2f}".format(
                m["scale"], m["bytes"] / 1024, m["chunks_final"],
                med("embed_index_s"), med("build_total_s"), med("ms_por_chunk")))

    # --- progresso do run (alimenta o modo ao vivo do dashboard) -----------
    progresso = None
    if args.models and os.path.exists(args.models):
        roster = [m["name"] for m in load_jsonl(args.models)]
        alvo = len(roster) * args.n_perguntas
        feitos = len(rows)
        # ETA por modelo já concluído: quanto cada um custou de verdade.
        concl = [m for m in roster if len(by_model.get(m, [])) >= args.n_perguntas]
        seg_por_resposta = None
        somas = [sum(r.get("latency_s") or 0 for r in by_model[m]) for m in concl]
        if somas:
            seg_por_resposta = sum(somas) / (len(concl) * args.n_perguntas)
        atual = next((m for m in roster
                      if 0 < len(by_model.get(m, [])) < args.n_perguntas), None)
        faltam = alvo - feitos
        progresso = {
            "modelos_total": len(roster),
            "modelos_concluidos": len(concl),
            "modelo_atual": atual,
            "respostas_feitas": feitos,
            "respostas_alvo": alvo,
            "pct": round(pct(feitos, alvo), 1),
            "pendentes": [m for m in roster if len(by_model.get(m, [])) < args.n_perguntas],
            # ETA é extrapolação pelos modelos já concluídos. A verbosidade varia
            # MUITO entre modelos (llama3.1:8b foi 6× o qwen2.5:7b), então isto é
            # ordem de grandeza, não promessa.
            "eta_s_estimado": round(faltam * seg_por_resposta) if seg_por_resposta else None,
            "atualizado_em": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        }
        print(f"\nPROGRESSO {feitos}/{alvo} ({progresso['pct']}%) | "
              f"modelo atual: {atual or '-'} | "
              f"faltam {len(progresso['pendentes'])} modelo(s)"
              + (f" | ETA ~{progresso['eta_s_estimado'] // 60} min"
                 if progresso["eta_s_estimado"] else ""))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"leaderboard": linhas,
                       "etapas": {k: {"n": etapa_n[k], "s": round(v, 1)}
                                  for k, v in etapa_s.items()},
                       "escalacoes": dict(motivos),
                       "progresso": progresso}, f, ensure_ascii=False, indent=1)
        print(f"\njson -> {args.json}")


if __name__ == "__main__":
    main()
