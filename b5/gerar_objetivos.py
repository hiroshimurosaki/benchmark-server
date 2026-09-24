"""b5 — gera os objetivos de cliente UMA vez (antes da rodada) com Claude Opus.

Fonte: o documento da org perfeita (OnCorretor.txt) + faq_perfeita.json +
dtq_perfeita.json do repo do bot (só leitura). 6 lotes de 20 em paralelo, cada
lote com a sua cota de trilhas e uma faixa de tópicos de foco (reduz repetição
entre lotes). Depois: validação de campos, dedupe e ids estáveis.

Uso:
    python b5/gerar_objetivos.py            # gera b5/objetivos_b5.jsonl
    python b5/gerar_objetivos.py --lotes 1 --por-lote 3 --out b5/obj_teste.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import B5_DIR, chamar_llm, log  # noqa: E402

BOT_REPO = os.environ.get(
    "B5_BOT_REPO",
    r"C:\Users\fernando.murusaki\rag-chatbot\.claude\worktrees\e1-env-audit")
ORG_DIR = os.path.join(BOT_REPO, "scripts", "org_perfeita")

# Peso das trilhas (contrato) → cotas para 120 objetivos.
COTAS_120 = [
    ("faq_direta", 24), ("rag_documento", 24), ("multi_pergunta", 12),
    ("follow_up_contextual", 18), ("fora_do_escopo", 12), ("pede_atendente", 10),
    ("reclamacao_irritado", 8), ("confuso_digitacao", 8), ("saudacao_e_despedida", 4),
]
TRILHAS = [t for t, _ in COTAS_120]
ESTILOS = ["formal", "informal", "erros_digitacao", "audio_transcrito", "impaciente"]

SCHEMA_OBJ = {
    "type": "object",
    "properties": {
        "trilha": {"type": "string", "enum": TRILHAS},
        "persona": {
            "type": "object",
            "properties": {
                "nome": {"type": "string"},
                "tom": {"type": "string"},
                "estilo_escrita": {"type": "string", "enum": ESTILOS},
                "descricao": {"type": "string"},
            },
            "required": ["nome", "tom", "estilo_escrita", "descricao"],
        },
        "objetivo": {"type": "string"},
        "gabarito": {
            "type": "object",
            "properties": {
                "fatos": {"type": "array", "items": {"type": "string"}},
                "topicos": {"type": "array", "items": {"type": "integer"}},
                "faq_ids": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["fatos", "topicos", "faq_ids"],
        },
        "comportamento_esperado": {"type": "string",
                                   "enum": ["resolver", "escalar", "recusar_educadamente"]},
        "max_turnos": {"type": "integer", "minimum": 3, "maximum": 10},
        "susep": {"type": "string"},
    },
    "required": ["trilha", "persona", "objetivo", "gabarito", "comportamento_esperado",
                 "max_turnos", "susep"],
}
SCHEMA_LOTE = {"type": "object",
               "properties": {"objetivos": {"type": "array", "items": SCHEMA_OBJ}},
               "required": ["objetivos"]}

DESC_TRILHAS = {
    "faq_direta": "pergunta que uma entrada da FAQ responde diretamente (cite o id em faq_ids)",
    "rag_documento": "dúvida cuja resposta está no documento mas NÃO numa FAQ pronta (cite os tópicos)",
    "multi_pergunta": "o cliente faz 2-3 perguntas diferentes na mesma mensagem ou em sequência",
    "follow_up_contextual": "a 2ª/3ª pergunta só faz sentido com o histórico (ex.: 'e quanto custa isso?', 'e se eu quiser cancelar depois?')",
    "fora_do_escopo": "pede algo que o OnCorretor/atendimento não cobre (ex.: cotação de seguro, outra seguradora, assunto aleatório); esperado: recusar_educadamente ou escalar conforme o documento",
    "pede_atendente": "quer falar com um humano (direto ou depois de uma pergunta); esperado: escalar",
    "reclamacao_irritado": "reclamação/irritação (cobrança indevida, site fora do ar, demora); pode exigir escalar",
    "confuso_digitacao": "escreve de forma confusa, com erros de digitação, abreviações, sem pontuação",
    "saudacao_e_despedida": "começa só com saudação, faz algo simples e se despede/agradece (exercita os gates de abertura e encerramento)",
}

SYSTEM = """Você cria casos de teste para um benchmark de um chatbot de atendimento via WhatsApp do produto OnCorretor (sites e e-mails para corretores de seguro, parceria Porto Seguro).
Cada caso é um OBJETIVO de um cliente simulado: quem ele é (persona), o que quer resolver, e o gabarito que um juiz usará para conferir a conversa.
Regras:
- Tudo em português do Brasil.
- O gabarito deve vir SÓ do documento/FAQ/DTQ fornecidos: fatos corretos e verificáveis (valores, prazos, e-mails, passos), os NÚMEROS dos tópicos do documento (o número antes de ". – " no título do tópico) e os ids das entradas FAQ/DTQ relevantes (a chave, ex.: "03wfQqu9p3mk703V1kzP"). Nunca invente id nem fato.
- Entradas FAQ/DTQ cuja resposta é "call_attendant" significam que o bot deve ESCALAR para atendente nesse assunto → comportamento_esperado = "escalar".
- comportamento_esperado: "resolver" (o bot consegue responder com o material), "escalar" (precisa de humano: pedido explícito, caso que o material manda para atendente, problema técnico da conta), "recusar_educadamente" (fora do escopo, sem escalar).
- persona.estilo_escrita varia entre formal, informal, erros_digitacao, audio_transcrito (texto corrido sem pontuação, como transcrição de áudio), impaciente. Misture idades, profissões e jeitos.
- susep: um código de 6 a 8 dígitos (ex.: "1234567") OU "não sei" (em ~25% dos casos).
- max_turnos entre 3 e 10 (casos simples 3-4; follow-up/multi 5-8).
- Varie bastante: não repita o mesmo assunto entre casos do lote. objetivo em 1-3 frases, do ponto de vista do cliente (o que quer resolver e o que conta como resolvido)."""


def _topicos(texto: str) -> list:
    return [(int(m.group(1)), m.group(2).strip())
            for m in re.finditer(r"^(\d+)\. – (.+)$", texto, re.M)]


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", " ", s)


def _jaccard(a: str, b: str) -> float:
    ta, tb = set(_norm(a).split()), set(_norm(b).split())
    return len(ta & tb) / max(1, len(ta | tb))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lotes", type=int, default=6)
    ap.add_argument("--por-lote", type=int, default=20)
    ap.add_argument("--out", default=os.path.join(B5_DIR, "objetivos_b5.jsonl"))
    ap.add_argument("--modelo", default="opus")
    args = ap.parse_args()

    doc = open(os.path.join(ORG_DIR, "OnCorretor.txt"), encoding="utf-8").read()
    faq = json.load(open(os.path.join(ORG_DIR, "faq_perfeita.json"), encoding="utf-8"))
    dtq = json.load(open(os.path.join(ORG_DIR, "dtq_perfeita.json"), encoding="utf-8"))
    ids_validos = set(faq) | set(dtq)
    topicos = _topicos(doc)
    nums_validos = {n for n, _ in topicos}

    def compacto(d: dict) -> str:
        return "\n".join(f"{k} | {v.get('frase','')} | {str(v.get('resposta',''))[:260]}"
                         for k, v in d.items())

    material = (f"=== DOCUMENTO (OnCorretor.txt) ===\n{doc}\n\n"
                f"=== FAQ (id | frase | resposta) ===\n{compacto(faq)}\n\n"
                f"=== DTQ (id | frase | resposta) ===\n{compacto(dtq)}\n")

    # Cotas por lote: a lista de 120 trilhas distribuída em round-robin.
    total = args.lotes * args.por_lote
    fila = []
    for t, n in COTAS_120:
        fila += [t] * round(n * total / 120)
    fila = (fila + [TRILHAS[0]] * total)[:total]
    lotes = [fila[k::args.lotes] for k in range(args.lotes)]
    faixa = max(1, len(topicos) // args.lotes)

    def rodar(k: int) -> list:
        cotas = {t: lotes[k].count(t) for t in TRILHAS if lotes[k].count(t)}
        foco = topicos[k * faixa:(k + 1) * faixa] if k < args.lotes - 1 else topicos[k * faixa:]
        pedido = (
            material
            + f"\n=== PEDIDO (lote {k + 1}/{args.lotes}) ===\n"
            f"Gere exatamente {len(lotes[k])} objetivos, com estas quantidades por trilha:\n"
            + "\n".join(f"- {t}: {n} — {DESC_TRILHAS[t]}" for t, n in cotas.items())
            + "\n\nPara faq_direta/rag_documento/follow_up/multi_pergunta, PRIORIZE assuntos "
              "destes tópicos (foco deste lote, para não repetir outros lotes): "
            + ", ".join(f"{n}. {t}" for n, t in foco)
            + "\nDevolva no campo `objetivos`."
        )
        log(f"lote {k + 1}: pedindo {len(lotes[k])} ({cotas})")
        r = chamar_llm("gerador", args.modelo, SYSTEM, pedido, SCHEMA_LOTE, timeout=900)
        if not r["ok"]:
            log(f"lote {k + 1}: FALHOU — {r['erro']}")
            return []
        objs = r["obj"].get("objetivos") or []
        log(f"lote {k + 1}: {len(objs)} objetivos via {r['modelo']} "
            f"({r.get('dur_s')}s, US$ {r.get('custo_usd')})")
        for o in objs:
            o["_lote"] = k + 1
            o["_gerador"] = r["modelo"]
        return objs

    with ThreadPoolExecutor(max_workers=min(6, args.lotes)) as ex:
        brutos = [o for lote in ex.map(rodar, range(args.lotes)) for o in lote]

    # Validação + saneamento (nunca inventa: descarta o que for inválido).
    validos = []
    for o in brutos:
        try:
            if o["trilha"] not in TRILHAS or not str(o["objetivo"]).strip():
                continue
            gab = o["gabarito"]
            gab["faq_ids"] = [i for i in gab.get("faq_ids", []) if i in ids_validos]
            gab["topicos"] = [n for n in gab.get("topicos", []) if n in nums_validos]
            o["max_turnos"] = max(3, min(10, int(o["max_turnos"])))
            if o["comportamento_esperado"] not in ("resolver", "escalar", "recusar_educadamente"):
                continue
            validos.append(o)
        except Exception:
            continue

    unicos = []
    for o in validos:
        if any(_jaccard(o["objetivo"], u["objetivo"]) >= 0.7 for u in unicos):
            continue
        unicos.append(o)

    contador: dict = {}
    abrev = {"faq_direta": "faq", "rag_documento": "rag", "multi_pergunta": "multi",
             "follow_up_contextual": "follow", "fora_do_escopo": "fora",
             "pede_atendente": "atend", "reclamacao_irritado": "recl",
             "confuso_digitacao": "conf", "saudacao_e_despedida": "saud"}
    with open(args.out, "w", encoding="utf-8") as f:
        for o in unicos:
            a = abrev[o["trilha"]]
            contador[a] = contador.get(a, 0) + 1
            reg = {"id": f"{a}-{contador[a]:02d}", **o}
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
    log(f"brutos={len(brutos)} válidos={len(validos)} únicos={len(unicos)} → {args.out}")
    log("por trilha: " + json.dumps({t: sum(1 for o in unicos if o['trilha'] == t) for t in TRILHAS}))


if __name__ == "__main__":
    main()
