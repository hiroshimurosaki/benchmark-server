"""Rejulga as conversas já gravadas de uma rodada com o juiz ATUAL, sem rodar o bot.

Serve para separar mudança de MEDIDA de mudança do bot: as mesmas transcrições,
outro juiz. Grava em outra pasta; a rodada original fica intacta.

    python b5/rejulgar.py --de b5/resultados_r6 --para b5/resultados_r6_juizdoc \
        --bot-repo C:\\...\\worktrees\\qualidade-atendimento
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import B5_DIR, append_jsonl, load_jsonl  # noqa: E402
from run_b5 import Material, chamar_juiz  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--de", required=True)
    ap.add_argument("--para", required=True)
    ap.add_argument("--bot-repo", required=True, help="repo com scripts/org_perfeita (doc + FAQ/DTQ)")
    ap.add_argument("--objetivos", default=os.path.join(B5_DIR, "objetivos_b5.jsonl"))
    a = ap.parse_args()

    os.makedirs(a.para, exist_ok=True)
    for arq in ("conversas.jsonl", "turnos.jsonl"):
        src = os.path.join(a.de, arq)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(a.para, arq))

    objs = {o["id"]: o for o in load_jsonl(a.objetivos)}
    mat = Material(a.bot_repo, {})
    p_juiz = os.path.join(a.para, "julgamentos.jsonl")
    feitos = {j["id"] for j in load_jsonl(p_juiz)}
    for conv in load_jsonl(os.path.join(a.de, "conversas.jsonl")):
        if conv["id"] in feitos:
            continue
        j = chamar_juiz(objs[conv["id"]], conv, mat)
        v = j["obj"] if j["ok"] else None
        append_jsonl(p_juiz, {"id": conv["id"], "tentativa": conv.get("tentativa"),
                              "juiz_modelo": j["modelo"], "juiz_dur_s": j.get("dur_s"),
                              "juiz_custo_usd": j.get("custo_usd"), "veredito": v,
                              "erro": None if j["ok"] else j["erro"]})
        print(conv["id"], "nota", (v or {}).get("nota_geral"),
              "aluc", ((v or {}).get("alucinacao") or {}).get("houve"), flush=True)


if __name__ == "__main__":
    main()
