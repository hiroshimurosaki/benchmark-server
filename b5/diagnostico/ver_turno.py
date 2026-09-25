"""Mostra os eventos instrumentados de um turno (replay.jsonl ou experimentos.jsonl, config base).
Uso: ver_turno.py ARQ conversa n [config]"""
import json
import sys

arq, cid, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
cfg = sys.argv[4] if len(sys.argv) > 4 else "base"
for x in open(arq, encoding="utf-8"):
    r = json.loads(x)
    if r["conversa_id"] != cid or r["n"] != n:
        continue
    if "config" in r:
        if r["config"] != cfg or r.get("tipo") != "falha":
            continue
        print("CLIENTE:", r["pergunta"])
        print("SAIDA FINAL:", repr((r.get("texto") or "")[:500]), "escalou", r["escalou"], r["etapas"])
    else:
        print("CLIENTE:", r["texto_cliente"])
        print("ORIG:", json.dumps(r["orig"], ensure_ascii=False)[:600])
        print("REPLAY:", json.dumps(r["replay"], ensure_ascii=False)[:600], r["replay_etapas"])
    for e in r.get("eventos") or []:
        if e["tipo"] == "llm":
            print(f"\n--- LLM {e['etapa']} ({e['dur_s']}s)")
            print("  USER:", e["user"][-700:].replace("\n", " | "))
            print("  SAIDA:", repr(e["saida"][:500]))
        elif e["tipo"] == "semantic_lookup":
            d = e["diag"]
            print(f"\n--- LOOKUP q={e['query'][:150]!r} best={e['melhor_score']} {e['melhor_frase']!r}")
            print("   top3_faq:", [(t["score"], t["frase"][:50]) for t in d["top3_faq"]], "gab:", d["gab_faq"])
        elif e["tipo"] == "rag":
            print(f"\n--- RAG q={e['rag_query'][-250:]!r}")
            print("  faiss:", e["headers_faiss"][:8])
            print("  ctx:", e["headers_contexto"], "pos_gab_faiss", e["pos_gab_faiss"][:3],
                  "pos_gab_rerank", e["pos_gab_rerank"][:3], "no_ctx", e["gab_no_contexto"])
            print("  SAIDA:", repr(e["saida"][:500]))
