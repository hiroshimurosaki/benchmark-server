"""Monta os alvos dos experimentos a partir da rodada ORIGINAL da b5.

* ``alvos.json``    — todo turno do bot que NÃO foi gate (fonte rag/faq/escalonamento),
  com o estado da sessão ANTES do turno reconstruído do histórico ORIGINAL
  (``b5/resultados/memory``, truncado nas mensagens anteriores ao turno), o context
  da sessão e os candidatos de desambiguação pendentes vindos do replay (o original
  não os guarda), a nota do juiz Opus para o turno e se falhou.
* ``alvos_c5.json`` — C5: conversas cujo 1º turno foi engolido pelo gate de
  opening_question; a "pergunta" é a mensagem que chegou ANTES da SUSEP, processada
  com o estado logo depois da resposta à SUSEP.
"""
import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diag_common as dc  # noqa: E402

R5 = os.path.join(dc.B5_DIR, "resultados")
RES = os.path.join(dc.DIAG_DIR, "resultados")

obj = dc.objetivos()
conversas = {c["id"]: c for c in dc.jl(os.path.join(R5, "conversas.jsonl"))}
jul = {j["id"]: j["veredito"] for j in dc.jl(os.path.join(R5, "julgamentos.jsonl"))}
smap = json.load(open(os.path.join(R5, "memory", "session_map.json"), encoding="utf-8"))
replay = {(r["conversa_id"], r["n"]): r for r in dc.jl(os.path.join(RES, "replay.jsonl"))}


def hist_orig(cid):
    sid = smap[f"{dc.ORG}:{conversas[cid]['chat_id']}"]
    return json.load(open(os.path.join(R5, "memory", f"{sid}.json"), encoding="utf-8"))


def snap_para(cid, n):
    h = hist_orig(cid)
    rp = replay.get((cid, n))
    snap_rp = (rp or {}).get("snapshot") or {}
    hh = copy.deepcopy(h)
    hh["messages"] = h["messages"][: 2 * (n - 1)]
    if snap_rp.get("hist"):
        hh["context"] = snap_rp["hist"].get("context", {})
    prev = conversas[cid]["transcricao"][n - 2] if n >= 2 else None
    prev_disamb = bool(prev and prev.get("fonte") == "rag"
                       and (prev.get("texto_bot") or "").lstrip().startswith(("Pra te ajudar", "Boa tarde! 😊\n\nPra te ajudar",
                                                                               "Bom dia! 😊\n\nPra te ajudar")))
    # houve turno de pipeline antes? (saudação única por sessão)
    greeted = any(not (t.get("fonte") or "").startswith("gate:") for t in conversas[cid]["transcricao"][: n - 1])
    return {"hist": hh, "awaiting": snap_rp.get("awaiting") if prev_disamb else None,
            "greeted": greeted, "negfb": None}, prev_disamb


alvos, c5 = [], []
for cid, c in conversas.items():
    notas = {q["turno"]: q.get("nota") for q in jul[cid].get("qualidade_por_turno", [])}
    for t in c["transcricao"]:
        if (t.get("fonte") or "").startswith("gate:"):
            continue
        snap, prev_disamb = snap_para(cid, t["n"])
        nota = notas.get(t["n"])
        falhou = bool(t.get("escalou")) or (nota is not None and nota <= 4)
        alvos.append({"conversa_id": cid, "n": t["n"], "pergunta": t["texto_cliente"],
                      "gabarito": obj[cid]["gabarito"], "trilha": c["trilha"],
                      "comportamento_esperado": c["comportamento_esperado"],
                      "orig": {"texto_bot": t.get("texto_bot"), "fonte": t.get("fonte"),
                               "escalou": t.get("escalou"), "motivo": t.get("motivo_escalonamento"),
                               "latencia_s": t.get("latencia_s"), "nota_juiz": nota},
                      "falhou": falhou, "prev_disamb": prev_disamb, "snapshot": snap})
    tr = c["transcricao"]
    # C5: T1 e T2 engolidos pelo gate e T1 tinha conteúdo (não só saudação)
    if len(tr) >= 2 and tr[0].get("gate") == "opening_question" and tr[1].get("gate") == "opening_question":
        snap, _ = snap_para(cid, 3) if len(tr) >= 3 else (None, None)
        if snap is None:
            continue
        c5.append({"conversa_id": cid, "n": 2, "pergunta": tr[0]["texto_cliente"],
                   "gabarito": obj[cid]["gabarito"], "trilha": c["trilha"],
                   "comportamento_esperado": c["comportamento_esperado"],
                   "orig": {"t3_fonte": tr[2].get("fonte"), "t3_escalou": tr[2].get("escalou")},
                   "falhou": True, "snapshot": snap})

json.dump(alvos, open(os.path.join(RES, "alvos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(c5, open(os.path.join(RES, "alvos_c5.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"alvos={len(alvos)} (falharam={sum(a['falhou'] for a in alvos)}; "
      f"reply de desambiguação={sum(a['prev_disamb'] for a in alvos)})  c5={len(c5)}")
