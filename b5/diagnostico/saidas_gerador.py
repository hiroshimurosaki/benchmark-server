"""Classifica as saídas cruas do Answer_generator (base dos experimentos + replay) e
relaciona com a última saída de LLM aux anterior no mesmo turno."""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diag_common as dc  # noqa: E402

RES = os.path.join(dc.DIAG_DIR, "resultados")
TOK = {"RELEVANTE", "IRRELEVANTE", "AMBIGUO", "CALL_ATTENDANT", "SAUDACAO", "ATENDENTE"}
c = Counter()
eco = Counter()
for arq in ("experimentos.jsonl", "replay.jsonl"):
    for r in dc.jl(os.path.join(RES, arq)):
        ev = r.get("eventos") or []
        ultimo_aux = None
        for e in ev:
            if e["tipo"] == "llm":
                ultimo_aux = e["saida"].strip().upper()
            elif e["tipo"] == "rag":
                s = (e["saida"] or "").strip()
                if s.upper() in TOK:
                    k = "token_classificador"
                    eco["igual_ao_aux_anterior" if s.upper() == ultimo_aux else f"diferente(aux={ultimo_aux})"] += 1
                elif "não tenho essa informação" in s.lower():
                    k = "MODO_C"
                else:
                    k = "resposta"
                hist = "com_hist" if "<CONTEXTO_ANTERIOR>" in e["rag_query"] else "sem_hist"
                c[(arq, hist, k)] += 1
                c[(arq, hist, "ctx_tem_gab" if e["gab_no_contexto"] else "ctx_sem_gab", k)] += 1
for k, v in sorted(c.items()):
    print(k, v)
print("eco:", dict(eco))
