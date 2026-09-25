"""Dump compacto das 22 conversas da b5 (para leitura humana / classificação do cliente)."""
import json
import os

B5 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(B5, "resultados")


def jl(p):
    return [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()]


obj = {o["id"]: o for o in jl(os.path.join(B5, "objetivos_b5.jsonl"))}
jul = {j["id"]: j for j in jl(os.path.join(R, "julgamentos.jsonl"))}
for c in jl(os.path.join(R, "conversas.jsonl")):
    o = obj[c["id"]]
    v = jul[c["id"]]["veredito"]
    print(f"=== {c['id']} [{c['trilha']}] esperado={c['comportamento_esperado']} max={c['max_turnos']} "
          f"parada={c['parada']} nota={v.get('nota_geral')} obj={v.get('objetivo_cumprido')}")
    print("  PERSONA:", o["persona"]["descricao"], "|", o["persona"]["tom"], "|", o["persona"]["estilo_escrita"])
    print("  OBJ:", o["objetivo"][:300])
    print("  GAB:", json.dumps(o["gabarito"], ensure_ascii=False)[:500])
    for t in c["transcricao"]:
        print(f"  C{t['n']}: {t['texto_cliente'][:300]}")
        print(f"  B{t['n']} [{t['fonte']}|{t.get('motivo_escalonamento')}|conf={t.get('confianca')}|"
              f"{t.get('latencia_s')}s]: {(t['texto_bot'] or '')[:200]!r}")
    print("  REACAO:", c.get("reacao_final"))
