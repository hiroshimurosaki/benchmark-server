"""Sonda de contaminação: o Answer_generator devolve 'RELEVANTE'/'IRRELEVANTE'/'AMBIGUO'
(tokens dos classificadores) em ~45% das chamadas, e na maioria das vezes o MESMO token
que a chamada aux anterior acabou de devolver. Hipótese: vazamento de estado entre
requisições no Ollama (qwen3.6 = família qwen35moe, atenção híbrida/recorrente + cache
de prefixo).

Teste: mesma chamada de geração (prompt de produção, pergunta do faq-12, contexto que
contém o tópico 30 "Não há multa de cancelamento"), precedida de uma chamada aux que
devolve um token marcador (BANANA / IRRELEVANTE / RELEVANTE). Se a geração devolver o
marcador, é contaminação do servidor, não do prompt. Controle: a mesma geração com um
nonce no começo do system (quebra o reaproveitamento de prefixo).
Chama o Ollama direto (/api/chat), mesmas opções do bot. ~30 chamadas curtas.
"""
import json
import os
import sys
import time
import uuid

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diag_common as dc  # noqa: E402
from bot_env import Bot  # noqa: E402

bot = Bot(dc.ORG, os.path.join(dc.DIAG_DIR, "memory"))
from Answer_service.src.utils.prompt import (ANSWER_PROMPT_SYSTEM, DEFAULT_WHO_AM_I,  # noqa: E402
                                             VERIFICATION_PROMPT_SYSTEM)

URL = "http://127.0.0.1:11434/api/chat"
M = "qwen3.6:35b-a3b"
Q = "queria cancelar a adesão que fiz hoje de manhã, vai ter multa ou alguma cobrança?"
info = bot.qa_system.invoke({"query": Q, "who_am_I": DEFAULT_WHO_AM_I})
SYS_GEN = ANSWER_PROMPT_SYSTEM.format(who_am_I=DEFAULT_WHO_AM_I, context=info["context"],
                                      help_portal_directive=bot.org_cfg.prompts.help_portal_directive or "")


def chat(system, user, temp, n_pred, keep_prefix=True):
    body = {"model": M, "stream": False, "think": False,
            "options": {"num_ctx": 8192, "temperature": temp, "num_predict": n_pred},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    t0 = time.perf_counter()
    r = requests.post(URL, json=body, timeout=300).json()
    return r["message"]["content"].strip(), round(time.perf_counter() - t0, 2), r.get("prompt_eval_count")


def aux(marcador):
    if marcador in ("RELEVANTE", "IRRELEVANTE", "AMBIGUO"):
        s = VERIFICATION_PROMPT_SYSTEM.format(who_am_I=DEFAULT_WHO_AM_I)
        u = {"RELEVANTE": "PERGUNTA:\nComo altero o logo do meu site?",
             "IRRELEVANTE": "PERGUNTA:\nQuem ganhou a copa de 1970?",
             "AMBIGUO": "PERGUNTA:\nsite"}[marcador]
    else:
        s, u = f"Responda exatamente a palavra {marcador} e nada mais.", "Qual é a palavra?"
    return chat(s, u, 0.0, 20)


res = []
for rep in range(3):
    for marc in ("BANANA", "IRRELEVANTE", "RELEVANTE", "AMBIGUO", None):
        a = aux(marc) if marc else ("(sem aux)", 0, 0)
        g = chat(SYS_GEN, Q, 0.3, 1024)
        gn = chat(f"[req {uuid.uuid4().hex}]\n" + SYS_GEN, Q, 0.3, 1024)
        rec = {"rep": rep, "aux_marcador": marc, "aux_saida": a[0], "gen": g[0][:160], "gen_s": g[1],
               "gen_prompt_eval": g[2], "gen_nonce": gn[0][:160], "gen_nonce_prompt_eval": gn[2]}
        res.append(rec)
        print(json.dumps(rec, ensure_ascii=False), flush=True)
json.dump(res, open(os.path.join(dc.DIAG_DIR, "resultados", "sonda_eco.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
