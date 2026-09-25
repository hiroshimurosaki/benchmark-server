"""Passo 1 do diagnóstico: reexecuta as 22 conversas da b5 com as MESMAS mensagens
do cliente (não dinâmico), pelo mesmo ``Bot.turno`` da b5, com as sondas de
``diag_common`` ligadas. Grava por turno: saída, etapas instrumentadas, snapshot do
estado da sessão ANTES do turno (para os experimentos restaurarem) e se a
reexecução divergiu do texto original.

Uso: python b5/diagnostico/replay.py [--ids faq-12,rag-10]
"""

import argparse
import difflib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diag_common as dc  # noqa: E402

RES = os.path.join(dc.DIAG_DIR, "resultados")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", default="")
    ap.add_argument("--saida", default=os.path.join(RES, "replay.jsonl"))
    a = ap.parse_args()
    os.makedirs(RES, exist_ok=True)

    from bot_env import Bot
    bot = Bot(dc.ORG, os.path.join(dc.DIAG_DIR, "memory"))
    dc.instalar(bot)
    print(json.dumps(bot.resumo_config(), ensure_ascii=False), flush=True)
    obj = dc.objetivos()
    conversas = dc.jl(os.path.join(dc.B5_DIR, "resultados", "conversas.jsonl"))
    ids = set(filter(None, a.ids.split(",")))
    feitos = {(r["conversa_id"], r["n"]) for r in dc.jl(a.saida)} if os.path.exists(a.saida) else set()

    import Answer_service.src.services.processor as proc
    for c in conversas:
        if ids and c["id"] not in ids:
            continue
        if any(k[0] == c["id"] for k in feitos):
            continue
        chat = f"diag-{c['id']}@c.us"
        bot.nova_sessao(chat)
        proc._awaiting_disambiguation.pop(chat, None)
        proc._negative_feedback_count.pop(chat, None)
        estado = {}
        gab = obj[c["id"]]["gabarito"]
        t_conv = time.perf_counter()
        for t in c["transcricao"]:
            snap = dc.snapshot(bot, chat)
            dc.CAP.reset(gab)
            r = bot.turno(t["texto_cliente"], chat, estado)
            orig = t.get("texto_bot") or ""
            novo = r.get("texto_bot") or ""
            rec = {
                "conversa_id": c["id"], "n": t["n"], "texto_cliente": t["texto_cliente"],
                "orig": {"texto_bot": orig, "fonte": t.get("fonte"), "escalou": t.get("escalou"),
                         "motivo": t.get("motivo_escalonamento"), "confianca": t.get("confianca"),
                         "latencia_s": t.get("latencia_s"),
                         "etapas": [(e["stage"], e.get("tok_out")) for e in t.get("etapas") or []]},
                "replay": {k: r.get(k) for k in ("texto_bot", "fonte", "escalou", "motivo_escalonamento",
                                                 "confianca", "entrada_id", "gate", "erro", "latencia_s")},
                "replay_etapas": [(e["stage"], e.get("tok_out"), e.get("latency_s")) for e in r["etapas"]],
                "similaridade_texto": round(difflib.SequenceMatcher(None, orig, novo).ratio(), 3),
                "eventos": dc.CAP.eventos,
                "snapshot": snap,
            }
            with open(a.saida, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"{c['id']} T{t['n']} orig={t.get('fonte')}/{t.get('escalou')} "
                  f"replay={r.get('fonte')}/{r.get('escalou')} sim={rec['similaridade_texto']} "
                  f"{r.get('latencia_s')}s {r.get('erro') or ''}", flush=True)
        print(f"== {c['id']} {time.perf_counter() - t_conv:.0f}s", flush=True)


if __name__ == "__main__":
    main()
