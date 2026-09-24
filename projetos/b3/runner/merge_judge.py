#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
b3 — junta os veredictos dos subagentes num `scored_b3.json` com o MESMO
formato que o `judge_b3.py` (juiz por API) produziria, para o `report_b3.py` e
o `dashboard_b3.html` não saberem a diferença.

Desanonimiza pelo `_mapa.json` e valida: rótulo inexistente, veredicto faltando,
nota fora de 0-100 e pergunta sem cobertura viram aviso explícito — julgamento
silenciosamente incompleto é pior que julgamento ausente.

    python3 projetos/b3/runner/merge_judge.py --dir projetos/b3/judge --out projetos/b3/scored_b3.json
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from collections import defaultdict


def load_jsonl(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def recomputar_nota(v: dict, n_objetivos: int, desfecho: str) -> int:
    """A nota é ARITMÉTICA, não julgamento — então é minha, não do juiz.

    Dois motivos para recalcular em vez de confiar no número que veio:

    1. **Consistência.** São 10 juízes independentes. Cada um somando 40/25/20/
       10/5 na cabeça produz desvios que não se cancelam; o ranking entre
       modelos julgados por lotes diferentes fica contaminado.
    2. **Bug da v2 da rubrica**, apontado pelo lote 01: o teto de 30 para
       `pediu_esclarecimento` também caía sobre respostas HÍBRIDAS — que
       entregaram o conteúdo certo e só depois emendaram um menu. Elas ficavam
       empatadas com quem não entregou nada. O teto agora só vale quando o
       modelo não cumpriu objetivo nenhum.

    O que fica com o juiz é o julgamento de verdade: cumpriu o objetivo?
    alucinou? o desfecho era apropriado? violou proibição? o modo estava certo?
    """
    cumpridos = min(int(v.get("objetivos_cumpridos") or 0), max(n_objetivos, 0))
    nota = 40 * (cumpridos / n_objetivos) if n_objetivos else 40.0
    if not v.get("alucinacao"):
        nota += 25
    if v.get("desfecho_apropriado", True):
        nota += 20
    if not int(v.get("proibicoes_violadas") or 0):
        nota += 10
    if v.get("modo_ok"):
        nota += 5
    # Teto do menu: só para quem não entregou NADA. Híbrido não é penalizado.
    if desfecho == "pediu_esclarecimento" and cumpridos == 0:
        nota = min(nota, 30)
    return int(round(max(0.0, min(100.0, nota))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--questions", default="projetos/b2/questions_b2.jsonl",
                    help="para saber quantos objetivos cada pergunta tem")
    ap.add_argument("--juiz", default="claude-opus-5 (subagente)")
    args = ap.parse_args()

    n_obj = {q["id"]: len(q.get("objetivos") or []) for q in load_jsonl(args.questions)}
    # desfecho por (id, rotulo), lido dos próprios lotes que o juiz recebeu
    desf = {}
    for p in sorted(glob.glob(os.path.join(args.dir, "lote_*.json"))):
        for pac in json.load(open(p, encoding="utf-8")):
            for r in pac["respostas"]:
                desf[(pac["id"], r["rotulo"])] = r["desfecho"]

    mapa = json.load(open(os.path.join(args.dir, "_mapa.json"), encoding="utf-8"))
    esperado = {(qid, rot) for qid, m in mapa.items() for rot in m}

    veredictos = []
    vistos = set()
    avisos = []

    for path in sorted(glob.glob(os.path.join(args.dir, "veredicto_*.json"))):
        try:
            blob = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            avisos.append(f"{os.path.basename(path)}: JSON inválido ({e})")
            continue
        itens = blob.get("veredictos", blob) if isinstance(blob, dict) else blob
        for v in itens:
            qid, rot = v.get("id"), v.get("rotulo")
            if qid not in mapa or rot not in mapa.get(qid, {}):
                avisos.append(f"{os.path.basename(path)}: rótulo desconhecido {qid}/{rot}")
                continue
            if (qid, rot) in vistos:
                avisos.append(f"{os.path.basename(path)}: veredicto duplicado {qid}/{rot}")
                continue
            nota = v.get("nota")
            if not isinstance(nota, (int, float)) or not 0 <= nota <= 100:
                avisos.append(f"{os.path.basename(path)}: nota inválida em {qid}/{rot}: {nota!r}")
                continue
            vistos.add((qid, rot))
            d = desf.get((qid, rot), "?")
            veredictos.append({
                "id": qid,
                "model": mapa[qid][rot],
                "desfecho": d,
                "objetivos_total": n_obj.get(qid, 0),
                "objetivos_cumpridos": int(v.get("objetivos_cumpridos") or 0),
                "proibicoes_violadas": int(v.get("proibicoes_violadas") or 0),
                "modo_detectado": v.get("modo_detectado", "outro"),
                "modo_ok": bool(v.get("modo_ok")),
                "alucinacao": bool(v.get("alucinacao")),
                "desfecho_apropriado": bool(v.get("desfecho_apropriado", True)),
                "nota": recomputar_nota(v, n_obj.get(qid, 0), d),
                "nota_juiz": int(round(nota)),   # o número que o juiz somou
                "porque": (v.get("porque") or "")[:300],
            })

    faltando = esperado - vistos
    if faltando:
        por_q = defaultdict(int)
        for qid, _ in faltando:
            por_q[qid] += 1
        avisos.append(f"{len(faltando)} veredicto(s) faltando em "
                      f"{len(por_q)} pergunta(s): "
                      + ", ".join(f"{k}({v})" for k, v in sorted(por_q.items())[:12])
                      + (" ..." if len(por_q) > 12 else ""))

    # Divergência entre a nota recalculada e a que cada juiz somou: se for
    # grande, os 10 lotes não estão na mesma escala e o ranking não fecha.
    difs = [abs(v["nota"] - v["nota_juiz"]) for v in veredictos]
    div = {
        "media": round(sum(difs) / len(difs), 1) if difs else 0,
        "maxima": max(difs) if difs else 0,
        "acima_de_10_pts": sum(1 for d in difs if d > 10),
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"modelo_juiz": args.juiz, "effort": "n/a (subagente)",
                   "custo_tokens": {}, "avisos": avisos,
                   "divergencia_nota_recalculada_x_juiz": div,
                   "veredictos": veredictos}, f, ensure_ascii=False, indent=1)

    print(f"{len(veredictos)}/{len(esperado)} veredictos -> {args.out}")
    print(f"divergência nota recalculada × juiz: média {div['media']} pts, "
          f"máx {div['maxima']}, {div['acima_de_10_pts']} acima de 10 pts")
    for a in avisos:
        print("  AVISO:", a)


if __name__ == "__main__":
    main()
