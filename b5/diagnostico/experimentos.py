"""Passo 2 do diagnóstico: experimentos de correção (C1–C4, C6 e combinações) nos
turnos que falharam, restaurando o estado exato da sessão antes de cada turno
(snapshot gravado pelo replay). Só o pipeline (answer_user_question + guard) roda —
os gates não, porque os turnos-alvo já passaram deles. C5 (gate) é simulado aqui
também: a pergunta que chegou ANTES da SUSEP é processada logo depois dela.

Nada do código do bot é alterado: tudo por monkeypatch/parâmetro (diag_common).

Uso: python experimentos.py --configs base,C1_070,... [--c5]
Saída: resultados/experimentos.jsonl (uma linha por turno × config); o juiz roda à
parte (julgar.py) para a GPU ficar só com o bot.
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diag_common as dc  # noqa: E402

RES = os.path.join(dc.DIAG_DIR, "resultados")
MULTI = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Prompt de geração enxuto (C6) — entra pelo MESMO caminho que a org já tem no
# Firestore (prompts.answer_system), aqui só em memória.
ANSWER_ENXUTO = """{who_am_I}

Contexto dos documentos base (única fonte de verdade):
{context}

Como responder:
1. Encontre no contexto o trecho que trata do assunto da pergunta (considere sinônimos:
   pagamento = cobrança = mensalidade; adesão = contratação; domínio = endereço do site).
2. Responda usando as informações desse trecho, com as palavras e valores do documento,
   de forma direta, cordial e curta (até ~150 palavras, parágrafos curtos ou lista).
3. Se a pergunta tiver várias partes, responda cada parte que o contexto cobre; para a que não
   cobre, diga em uma linha que não tem essa informação.
4. Não invente nada que não esteja no contexto. Não confirme itens específicos (cartão, PIX,
   um aplicativo, uma integração) que não aparecem no contexto.
5. Só se NENHUM trecho tratar do assunto responda exatamente:
   "Desculpe, não tenho essa informação nos meus documentos. 😕"
6. Não ofereça atendente humano e não peça dados sensíveis. Não repita a pergunta.

<PORTAL_DIRECTIVE>
{help_portal_directive}
</PORTAL_DIRECTIVE>
(Se a diretiva acima estiver vazia, ignore-a. Não a aplique a cobrança/cancelamento.)"""

CONFIGS = {
    "base": dc.Config("base"),
    "base2": dc.Config("base2"),
    "C1_070": dc.Config("C1_070", limiar_faq=0.70),
    "C1_065": dc.Config("C1_065", limiar_faq=0.65),
    "C2_multi": dc.Config("C2_multi", embedder=MULTI, limiar_faq=None),  # limiar via --limiar-multi
    "C3_top10": dc.Config("C3_top10", top_n=10, piso=0),
    "C4_aceita": dc.Config("C4_aceita", verif_modo="aceita_nao_modo_c"),
    "C4_relax": dc.Config("C4_relax", verif_modo="relaxado"),
    "C6_prompt": dc.Config("C6_prompt"),
    "C1+C3+C4": dc.Config("C1+C3+C4", limiar_faq=0.70, top_n=10, piso=0, verif_modo="relaxado"),
    "C2+C3+C4": dc.Config("C2+C3+C4", embedder=MULTI, top_n=10, piso=0, verif_modo="relaxado"),
    "C2+C3+C4+C6": dc.Config("C2+C3+C4+C6", embedder=MULTI, top_n=10, piso=0, verif_modo="relaxado"),
    "C3+C6": dc.Config("C3+C6", top_n=10, piso=0),
    "C1+C3+C6": dc.Config("C1+C3+C6", limiar_faq=0.70, top_n=10, piso=0),
    "C2+C3+C6": dc.Config("C2+C3+C6", embedder=MULTI, top_n=10, piso=0),
}
CONFIGS.update({
    "C7_ambiguo": dc.Config("C7_ambiguo", ambiguo_so_curto=True),
    "C8_opcao": dc.Config("C8_opcao", parse_opcao=True),
    "C3+C6+C7+C8": dc.Config("C3+C6+C7+C8", top_n=10, piso=0, ambiguo_so_curto=True, parse_opcao=True),
    "C2+C3+C6+C7+C8": dc.Config("C2+C3+C6+C7+C8", embedder=MULTI, top_n=10, piso=0,
                                ambiguo_so_curto=True, parse_opcao=True),
    "C1+C3+C6+C7+C8": dc.Config("C1+C3+C6+C7+C8", limiar_faq=0.70, top_n=10, piso=0,
                                ambiguo_so_curto=True, parse_opcao=True),
})
USA_C6 = {"C3+C6+C7+C8", "C2+C3+C6+C7+C8", "C1+C3+C6+C7+C8", "C6_prompt", "C2+C3+C4+C6", "C3+C6", "C1+C3+C6", "C2+C3+C6"}


def alvos() -> list:
    return json.load(open(os.path.join(RES, "alvos.json"), encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", default="base")
    ap.add_argument("--limiar-multi", type=float, default=0.75)
    ap.add_argument("--c5", action="store_true", help="roda a simulação do gate (C5)")
    ap.add_argument("--c5-configs", default="base")
    ap.add_argument("--saida", default=os.path.join(RES, "experimentos.jsonl"))
    a = ap.parse_args()

    from bot_env import Bot
    bot = Bot(dc.ORG, os.path.join(dc.DIAG_DIR, "memory_exp"))
    dc.instalar(bot)
    prompts_orig = bot.org_cfg.prompts.answer_system
    feitos = set()
    if os.path.exists(a.saida):
        feitos = {(r["config"], r["alvo"]) for r in dc.jl(a.saida)}

    def rodar(nome, lista, tipo):
        cfg = CONFIGS[nome]
        if cfg.embedder and cfg.limiar_faq is None:
            cfg.limiar_faq = a.limiar_multi
        dc.aplicar_config(cfg)
        bot.org_cfg.prompts.answer_system = ANSWER_ENXUTO if nome in USA_C6 else prompts_orig
        t_cfg = time.perf_counter()
        for al in lista:
            chave = f"{tipo}:{al['conversa_id']}:T{al['n']}"
            if (nome, chave) in feitos:
                continue
            chat = f"exp-{al['conversa_id']}@c.us"
            dc.restaurar(bot, chat, al["snapshot"])
            dc.CAP.reset(al["gabarito"])
            try:
                r = dc.pipeline(bot, al["pergunta"], chat)
                erro = None
            except Exception as e:  # noqa: BLE001
                r, erro = {"texto": "", "escalou": True, "latencia_s": None}, f"{type(e).__name__}: {e}"
            etapas = [(e["etapa"], e["dur_s"]) for e in dc.CAP.eventos if e["tipo"] == "llm"]
            rag = [e for e in dc.CAP.eventos if e["tipo"] == "rag"]
            rec = {"config": nome, "alvo": chave, "tipo": tipo, "conversa_id": al["conversa_id"],
                   "n": al["n"], "pergunta": al["pergunta"], **r, "erro": erro, "etapas": etapas,
                   "rag_saidas": [x["saida"][:300] for x in rag],
                   "gab_no_contexto": [x["gab_no_contexto"] for x in rag],
                   "limiar": dc.limiar_efetivo(bot),
                   "eventos": dc.CAP.eventos if nome == "base" else None}
            with open(a.saida, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"[{nome}] {chave} escalou={r['escalou']} {r.get('latencia_s')}s "
                  f"{(r.get('texto') or '')[:80]!r}", flush=True)
        print(f"== {nome} {tipo} {time.perf_counter() - t_cfg:.0f}s", flush=True)

    lista = alvos()
    for nome in filter(None, a.configs.split(",")):
        rodar(nome, lista if nome.startswith("base") else [x for x in lista if x["falhou"]], "falha")
    if a.c5:
        c5 = json.load(open(os.path.join(RES, "alvos_c5.json"), encoding="utf-8"))
        for nome in filter(None, a.c5_configs.split(",")):
            rodar(nome, c5, "c5")


if __name__ == "__main__":
    main()
