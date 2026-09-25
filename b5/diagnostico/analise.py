"""Consolida o diagnóstico:

1. Tabela por turno não-gate (da rodada 'base' dos experimentos, que reexecuta cada turno
   com o estado ORIGINAL da sessão): top-3 FAQ/DTQ, score da FAQ do gabarito, posição do
   tópico do gabarito no FAISS e no contexto final, saída crua do gerador, veredito do
   answer_verifier e a causa-raiz (heurística — revisada à mão no relatório).
2. Taxa de "resposta correta sem escalar" e latência por config (experimentos + juiz).

Uso: python analise.py  → imprime e grava resultados/tabela_turnos.md e resultados/placar.md
"""
import json
import os
import statistics as st
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diag_common as dc  # noqa: E402

RES = os.path.join(dc.DIAG_DIR, "resultados")
LIMIAR = 0.8
MODO_C = "não tenho essa informação"


def eh_menu(txt):
    t = (txt or "")
    return "Pra te ajudar melhor" in t or "Você quer dizer" in t or "Preciso entender melhor" in t


def classificar(al, base):
    """Causa-raiz de um turno que falhou (primeira camada que tinha como acertar e errou)."""
    ev = base.get("eventos") or []
    looks = [e for e in ev if e["tipo"] == "semantic_lookup"]
    rags = [e for e in ev if e["tipo"] == "rag"]
    llm = [e for e in ev if e["tipo"] == "llm"]
    gab_ids = al["gabarito"].get("faq_ids", [])
    orig_txt = al["orig"]["texto_bot"] or ""
    motivos = []
    if al["prev_disamb"] and not any(e["etapa"] == "disambiguation" for e in llm) and not looks and not rags:
        pass
    # menu desnecessário
    if eh_menu(orig_txt) and not al["orig"]["escalou"]:
        motivos.append("DESAMBIGUACAO_DESNECESSARIA")
    # FAQ
    melhor_gab = None
    for lk in looks:
        for gid in gab_ids:
            g = lk["diag"]["gab_faq"].get(gid)
            if g and (melhor_gab is None or g["score"] > melhor_gab["score"]):
                melhor_gab = g
    if gab_ids and looks and (melhor_gab is None or melhor_gab["score"] < LIMIAR):
        motivos.append("FAQ_NAO_CASOU")
    # verificador reprovando FAQ boa
    for i, e in enumerate(llm):
        if e["etapa"] == "answer_verifier" and "IRRELEVANTE" in e["saida"].upper():
            resp = e["user"].split("RESPOSTA:", 1)[-1]
            if MODO_C not in resp.lower() and resp.strip(" '\n").upper() not in ("RELEVANTE", "IRRELEVANTE") \
                    and not eh_menu(resp) and len(resp) > 60:
                motivos.append("VERIFICADOR_REPROVOU_BOA?")
                break
    # RAG
    for r in rags:
        s = (r["saida"] or "").strip()
        if al["gabarito"].get("topicos") and not r["gab_no_contexto"]:
            motivos.append("RETRIEVER_ERROU")
        elif MODO_C in s.lower() or s.upper() in ("RELEVANTE", "IRRELEVANTE"):
            motivos.append("GERADOR_RECUSOU")
        break
    return motivos


def main():
    alvos = {f"falha:{a['conversa_id']}:T{a['n']}": a
             for a in json.load(open(os.path.join(RES, "alvos.json"), encoding="utf-8"))}
    exps = dc.jl(os.path.join(RES, "experimentos.jsonl"))
    juiz = {}
    p = os.path.join(RES, "julgamentos_exp.jsonl")
    if os.path.exists(p):
        for r in dc.jl(p):
            juiz[r["hash"]] = r
    import hashlib

    def veredito(r):
        if r["escalou"]:
            return "escalou"
        h = hashlib.sha1((r["alvo"] + "\n" + (r["texto"] or "")).encode("utf-8")).hexdigest()
        return (juiz.get(h) or {}).get("veredito", "?")

    base = {r["alvo"]: r for r in exps if r["config"] == "base"}
    orig_et = {}
    for c in dc.jl(os.path.join(dc.B5_DIR, "resultados", "conversas.jsonl")):
        for t in c["transcricao"]:
            orig_et[f"falha:{c['id']}:T{t['n']}"] = [e["stage"] for e in t.get("etapas") or []]
    AB = {"contextualizer": "ctx", "question_verifier": "qv", "disambiguation": "dis", "Answer_generator": "gen",
          "answer_verifier": "av", "historical_answer": "hist"}
    linhas = ["| turno | caminho orig | caminho base | orig | nota | gab FAQ score (rank) | top1 FAQ | tópico gab FAISS/rerank/ctx | gerador (1ª saída) | ans_verifier | base agora | causa (heur.) |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    cont = Counter()
    for k, al in alvos.items():
        b = base.get(k)
        if not b:
            continue
        ev = b.get("eventos") or []
        looks = [e for e in ev if e["tipo"] == "semantic_lookup"]
        rags = [e for e in ev if e["tipo"] == "rag"]
        av = [e["saida"].strip()[:12] for e in ev if e["tipo"] == "llm" and e["etapa"] == "answer_verifier"]
        gab = "-"
        top1 = "-"
        if looks:
            d = looks[0]["diag"]
            top1 = f"{d['top3_faq'][0]['score']:.2f} {d['top3_faq'][0]['frase'][:35]}"
            gab = ", ".join(f"{v['score']:.2f} (#{v['rank']})" for v in d["gab_faq"].values()) or "sem FAQ"
        rg = "-"
        ger = "-"
        if rags:
            r0 = rags[0]
            rg = f"{r0['pos_gab_faiss'][:2]}/{r0['pos_gab_rerank'][:2]}/{'sim' if r0['gab_no_contexto'] else 'não'}"
            ger = (r0["saida"] or "").replace("\n", " ")[:50]
        mot = classificar(al, b) if al["falhou"] else []
        for m in mot:
            cont[m] += 1
        cam_o = ">".join(AB.get(x, x) for x in orig_et.get(k, []))
        cam_b = ">".join(AB.get(x[0], x[0]) for x in b["etapas"]).replace("Answer_generator", "gen")
        rg_gen = [AB.get("Answer_generator")] if rags else []
        cam_b = ">".join(AB.get(e["etapa"], e["etapa"]) if e["tipo"] == "llm" else "gen" for e in ev if e["tipo"] in ("llm", "rag"))
        linhas.append(f"| {k[6:]} | {cam_o} | {cam_b} | {al['orig']['fonte']}{'/ESC' if al['orig']['escalou'] else ''} | "
                      f"{al['orig']['nota_juiz']} | {gab} | {top1} | {rg} | {ger} | {','.join(av)} | "
                      f"{veredito(b)} | {' + '.join(mot) if al['falhou'] else 'ok'} |")
    open(os.path.join(RES, "tabela_turnos.md"), "w", encoding="utf-8").write("\n".join(linhas))
    print("\n".join(linhas))
    print("\ncontagem heurística:", dict(cont))

    # placar
    por_cfg = defaultdict(list)
    for r in exps:
        al = alvos.get(r["alvo"])
        if r["tipo"] == "falha" and (al is None or not al["falhou"]):
            continue
        por_cfg[(r["tipo"], r["config"])].append(r)
    out = ["| tipo | config | n | correta | parcial | errada | escalou | ? | acerto (correta) | acerto (+parcial) | latência média (s) | p90 |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for (tipo, cfg), rs in sorted(por_cfg.items()):
        c = Counter(veredito(r) for r in rs)
        lat = [r["latencia_s"] for r in rs if r.get("latencia_s") is not None]
        n = len(rs)
        p90 = sorted(lat)[int(0.9 * (len(lat) - 1))] if lat else 0
        out.append(f"| {tipo} | {cfg} | {n} | {c['correta']} | {c['parcial']} | {c['errada']} | {c['escalou']} | "
                   f"{c['?']} | {c['correta'] / n:.0%} | {(c['correta'] + c['parcial']) / n:.0%} | "
                   f"{st.mean(lat) if lat else 0:.1f} | {p90:.1f} |")
    open(os.path.join(RES, "placar.md"), "w", encoding="utf-8").write("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
