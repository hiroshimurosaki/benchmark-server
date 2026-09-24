#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
b3 — monta a FONTE DE VERDADE que o juiz usa.

Por que não basta o corpus: o pipeline responde por DOIS caminhos — o FAQ
semântico (157 entradas, atalho sem LLM) e o RAG sobre o documento. Fatos que
existem só no FAQ (ex.: "10 contas de e-mail com 5 GB cada" não aparece no
`OnCorretor.txt`) seriam julgados como alucinação se o juiz visse só o corpus.

O DTQ entra como lista de TÓPICOS que a própria org marcou para atendimento
humano — serve para o juiz não penalizar escalação legítima. (O DTQ não está
ligado ao pipeline hoje; ver PLANO.md. Isso não muda o que é resposta certa.)

    python3 runner/build_fonte_verdade.py --data b3/data/oncorretor \
        --out b3/judge/fonte_verdade.md
"""

from __future__ import annotations

import argparse
import json
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    partes = []

    corpus_dir = os.path.join(args.data, "corpus")
    partes.append("# FONTE DE VERDADE — org `oncorretor`\n")
    partes.append("Tudo que o chatbot pode legitimamente afirmar está aqui. "
                  "Qualquer fato fora deste arquivo é alucinação.\n")

    partes.append("\n---\n\n## PARTE 1 — Documentos indexados (base do RAG)\n")
    for name in sorted(os.listdir(corpus_dir)):
        p = os.path.join(corpus_dir, name)
        if os.path.isfile(p):
            with open(p, encoding="utf-8", errors="replace") as f:
                partes.append(f"\n### {name}\n\n```\n{f.read()}\n```\n")

    faq_path = os.path.join(args.data, "faq_db.json")
    if os.path.exists(faq_path):
        faq = json.load(open(faq_path, encoding="utf-8"))
        partes.append(f"\n---\n\n## PARTE 2 — FAQ curado ({len(faq)} entradas)\n")
        partes.append("Respostas aprovadas pela org. O pipeline entrega estas "
                      "literalmente quando a similaridade passa do limiar.\n")
        for i, e in enumerate(faq, 1):
            partes.append(f"\n**{i}. P:** {e.get('frase', '')}\n\n"
                          f"**R:** {e.get('resposta', '')}\n")

    dtq_path = os.path.join(args.data, "DTQ.json")
    if os.path.exists(dtq_path):
        dtq = json.load(open(dtq_path, encoding="utf-8"))
        partes.append(f"\n---\n\n## PARTE 3 — Tópicos designados para ATENDENTE "
                      f"HUMANO ({len(dtq)} entradas)\n")
        partes.append("A própria org marcou estes assuntos como 'passar para "
                      "humano'. Escalar numa pergunta deste tipo é a decisão "
                      "CERTA, não uma falha.\n\n")
        for e in dtq:
            partes.append(f"- {e.get('frase', '')}\n")

    texto = "".join(partes)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(texto)
    print(f"{args.out}: {len(texto)} chars (~{len(texto) // 4} tokens)")


if __name__ == "__main__":
    main()
