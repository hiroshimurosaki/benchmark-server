"""Monta os pacotes de julgamento do b4 (conversas inteiras).

Diferença para o b3: lá a unidade era a resposta e os rótulos eram por pergunta.
Aqui a unidade é a CONVERSA, e o rótulo é sorteado POR ROTEIRO — assim o juiz não
consegue seguir um mesmo modelo de roteiro em roteiro e criar efeito halo
("R03 foi bem antes, deve ir bem de novo").
"""
from __future__ import annotations
import argparse, json, os, random


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="b4/results_b4.jsonl")
    ap.add_argument("--out", default="b4/judge")
    ap.add_argument("--lotes", type=int, default=3)
    ap.add_argument("--seed", type=int, default=20260917)
    args = ap.parse_args()

    rs = [json.loads(l) for l in open(args.results, encoding="utf-8") if l.strip()]
    os.makedirs(args.out, exist_ok=True)
    rnd = random.Random(args.seed)

    por_roteiro: dict[str, list] = {}
    for r in rs:
        por_roteiro.setdefault(r["id"], []).append(r)

    mapa: dict[str, dict[str, str]] = {}
    pacotes = []
    for rid in sorted(por_roteiro):
        convs = sorted(por_roteiro[rid], key=lambda x: x["model"])
        rotulos = [f"R{i:02d}" for i in range(1, len(convs) + 1)]
        rnd.shuffle(rotulos)
        mapa[rid] = {rot: c["model"] for rot, c in zip(rotulos, convs)}
        for rot, c in zip(rotulos, convs):
            pacotes.append({
                "id": rid,
                "rotulo": rot,
                "trilha": c["trilha"],
                "nome": c["nome"],
                "criterio_final": c["criterio_final"],
                "proibicoes_globais": c["proibicoes_globais"],
                "erro_fatal": c.get("erro_fatal"),
                "turnos": [
                    {"n": t["n"], "cliente": t["input"], "espera": t["espera"],
                     "bot": t["answer"], "desfecho": t["outcome"]}
                    for t in c["transcricao"]
                ],
            })

    rnd.shuffle(pacotes)
    tam = (len(pacotes) + args.lotes - 1) // args.lotes
    for i in range(args.lotes):
        parte = pacotes[i * tam:(i + 1) * tam]
        if not parte:
            continue
        p = os.path.join(args.out, f"lote_{i+1:02d}.json")
        json.dump(parte, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        kb = os.path.getsize(p) / 1024
        print(f"{p}: {len(parte)} conversas, {kb:.0f} KB (~{kb*1024/3.5/1000:.0f}k tokens)")

    json.dump(mapa, open(os.path.join(args.out, "_mapa.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\nmapa rótulo→modelo em {args.out}/_mapa.json (o juiz NÃO recebe este arquivo)")
    print(f"total: {len(pacotes)} conversas")


if __name__ == "__main__":
    main()
