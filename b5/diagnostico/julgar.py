"""Juiz dos experimentos: a resposta do bot naquele turno está correta segundo o gabarito?

``claude -p --model sonnet`` (flags enxutas, via b5/common.chamar_llm, com fallback
opencode). Resposta escalada não vai ao juiz (conta como "escalou"). Cache por
(texto da pergunta, texto da resposta) para não julgar duas vezes a mesma saída.

Uso: python julgar.py [--arq resultados/experimentos.jsonl] [--workers 4]
Saída: resultados/julgamentos_exp.jsonl
"""
import argparse
import hashlib
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diag_common as dc  # noqa: E402
from common import chamar_llm  # noqa: E402

RES = os.path.join(dc.DIAG_DIR, "resultados")

SCHEMA = {
    "type": "object",
    "properties": {
        "veredito": {"type": "string", "enum": ["correta", "parcial", "errada"]},
        "alucinou": {"type": "boolean"},
        "justificativa": {"type": "string"},
    },
    "required": ["veredito", "alucinou", "justificativa"],
}

SYSTEM = """Você avalia UMA resposta de um bot de suporte (OnCorretor) a UMA mensagem de cliente.
Você recebe o objetivo do cliente, os fatos do gabarito (a verdade da base de conhecimento), o
texto das FAQ de referência, as últimas mensagens da conversa e a resposta do bot.

veredito:
- "correta": a resposta atende o que o cliente pediu NESTA mensagem, com informação coerente com
  o gabarito/FAQ (não precisa cobrir todos os fatos do objetivo, só o que foi perguntado agora).
  Se o assunto for fora do escopo do OnCorretor, "correta" = recusa educada dizendo com o que o
  bot pode ajudar.
- "parcial": responde parte do que foi pedido, ou responde certo mas genérico demais para agir.
- "errada": não responde (menu de opções / pedido de esclarecimento para uma pergunta clara,
  "não tenho essa informação"), responde outro assunto ou contradiz o gabarito.
alucinou: true se afirma algo que contradiz o gabarito ou inventa procedimento/valor/caminho
que não está no gabarito nem na FAQ.
Responda só o JSON."""


def carregar_faq():
    from bot_env import SA_PATH, BUCKET  # noqa: F401
    import firebase_admin
    from firebase_admin import credentials, firestore
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(SA_PATH))
    db = firestore.client()
    out = {}
    for col in ("faq", "dtq"):
        for d in db.collection("orgs").document(dc.ORG).collection(col).stream():
            x = d.to_dict() or {}
            out[d.id] = {"frase": x.get("frase", ""), "resposta": x.get("resposta", "")}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arq", default=os.path.join(RES, "experimentos.jsonl"))
    ap.add_argument("--saida", default=os.path.join(RES, "julgamentos_exp.jsonl"))
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()

    faq = carregar_faq()
    obj = dc.objetivos()
    alvos = {f"falha:{x['conversa_id']}:T{x['n']}": x for x in
             json.load(open(os.path.join(RES, "alvos.json"), encoding="utf-8"))}
    alvos.update({f"c5:{x['conversa_id']}:T{x['n']}": x for x in
                  json.load(open(os.path.join(RES, "alvos_c5.json"), encoding="utf-8"))})
    feitos = {}
    if os.path.exists(a.saida):
        for r in dc.jl(a.saida):
            feitos[r["hash"]] = r
    lock = threading.Lock()
    pend = []
    for r in dc.jl(a.arq):
        if r["escalou"]:
            continue
        h = hashlib.sha1((r["alvo"] + "\n" + (r["texto"] or "")).encode("utf-8")).hexdigest()
        if h not in feitos:
            pend.append((h, r))
    uniq = {}
    for h, r in pend:
        uniq.setdefault(h, r)
    print(f"a julgar: {len(uniq)}", flush=True)

    def julgar(item):
        h, r = item
        al = alvos[r["alvo"]]
        o = obj[r["conversa_id"]]
        msgs = (al["snapshot"]["hist"] or {}).get("messages", [])[-4:]
        conversa = "\n".join(f"{m['sender']}: {m['message'][:400]}" for m in msgs)
        refs = "\n".join(f"- FAQ {i}: P: {faq.get(i, {}).get('frase', '?')} | R: {faq.get(i, {}).get('resposta', '?')}"
                         for i in o["gabarito"].get("faq_ids", []))
        user = (f"OBJETIVO DO CLIENTE: {o['objetivo']}\n"
                f"COMPORTAMENTO ESPERADO: {o['comportamento_esperado']}\n"
                f"FATOS DO GABARITO:\n" + "\n".join(f"- {f}" for f in o["gabarito"]["fatos"]) +
                f"\nFAQ DE REFERÊNCIA:\n{refs or '(nenhuma)'}\n\n"
                f"ÚLTIMAS MENSAGENS ANTES DESTA:\n{conversa or '(nenhuma)'}\n\n"
                f"MENSAGEM DO CLIENTE AGORA: {r['pergunta']}\n\nRESPOSTA DO BOT:\n{r['texto']}")
        res = chamar_llm("juiz_exp", "sonnet", SYSTEM, user, SCHEMA, timeout=240)
        rec = {"hash": h, "alvo": r["alvo"], "ok": res["ok"], "modelo": res.get("modelo"),
               **(res.get("obj") or {})}
        with lock:
            with open(a.saida, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(r["alvo"], rec.get("veredito"), rec.get("modelo"), flush=True)

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(julgar, uniq.items()))


if __name__ == "__main__":
    main()
