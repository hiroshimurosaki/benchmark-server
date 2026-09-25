"""Calibração offline (só CPU) do limiar do matcher de FAQ para cada embedder.

Para cada pergunta real dos turnos não-gate (texto cru do cliente) e para as perguntas
de T1 (C5), mede: score da FAQ do gabarito, rank, e o melhor score de uma FAQ que NÃO é
do gabarito. Para um limiar L: acerto = top1 é do gabarito e score>=L; erro = top1 não é do
gabarito e score>=L (responderia a FAQ errada); o resto cai no RAG.

Não chama LLM. Uso: python calibrar_embedder.py
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diag_common as dc  # noqa: E402
from bot_env import SA_PATH  # noqa: E402

import firebase_admin  # noqa: E402
from firebase_admin import credentials, firestore  # noqa: E402
from sentence_transformers import SentenceTransformer  # noqa: E402
from sentence_transformers.util import cos_sim  # noqa: E402
import string  # noqa: E402

if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(SA_PATH))
db = firestore.client()
faq = [{**(d.to_dict() or {}), "_id": d.id} for d in db.collection("orgs").document(dc.ORG).collection("faq").stream()]
RES = os.path.join(dc.DIAG_DIR, "resultados")
alvos = json.load(open(os.path.join(RES, "alvos.json"), encoding="utf-8"))
c5 = json.load(open(os.path.join(RES, "alvos_c5.json"), encoding="utf-8"))
qs = []
for a in alvos + c5:
    if len(a["pergunta"].split()) < 4:   # "1", "é a opção 2" — não é pergunta
        continue
    qs.append((a["pergunta"], set(a["gabarito"].get("faq_ids", []))))


def prep(t):
    return t.lower().translate(str.maketrans("", "", string.punctuation))


MODELOS = {"MiniLM (prod)": ("all-MiniLM-L6-v2", ""),
           "multi-MiniLM-L12": ("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", ""),
           "e5-small": ("intfloat/multilingual-e5-small", "query: ")}
saida = {}
for nome, (mid, pref) in MODELOS.items():
    m = SentenceTransformer(mid)
    E = m.encode([pref + prep(f.get("frase", "")) for f in faq], show_progress_bar=False)
    Q = m.encode([pref + prep(q) for q, _ in qs], show_progress_bar=False)
    S = cos_sim(Q, E).numpy()
    rows = []
    for i, (q, gab) in enumerate(qs):
        order = np.argsort(-S[i])
        top = faq[order[0]]["_id"]
        gs = [S[i][j] for j in range(len(faq)) if faq[j]["_id"] in gab]
        ng = max(S[i][j] for j in range(len(faq)) if faq[j]["_id"] not in gab)
        rank = min([list(order).index(j) + 1 for j in range(len(faq)) if faq[j]["_id"] in gab] or [None]) \
            if gab else None
        rows.append({"q": q[:60], "tem_gab": bool(gab), "gab": float(max(gs)) if gs else None,
                     "rank": rank, "top_eh_gab": top in gab, "top": float(S[i][order[0]]), "melhor_nao_gab": float(ng)})
    com = [r for r in rows if r["tem_gab"]]
    print(f"\n=== {nome}: {len(rows)} perguntas ({len(com)} com FAQ no gabarito)")
    print(f"  top1 é a FAQ do gabarito: {sum(r['top_eh_gab'] for r in com)}/{len(com)}; "
          f"na top3: {sum(1 for r in com if r['rank'] and r['rank'] <= 3)}/{len(com)}")
    print(f"  score médio da FAQ correta: {np.mean([r['gab'] for r in com]):.3f} | "
          f"melhor não-gabarito: {np.mean([r['melhor_nao_gab'] for r in rows]):.3f}")
    for L in (0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5):
        ac = sum(1 for r in rows if r["top_eh_gab"] and r["top"] >= L)
        er = sum(1 for r in rows if not r["top_eh_gab"] and r["top"] >= L)
        print(f"  L={L:.2f}: FAQ certa={ac:2d}  FAQ errada={er:2d}  vai p/ RAG={len(rows) - ac - er:2d}")
    saida[nome] = rows
json.dump(saida, open(os.path.join(RES, "calibracao_embedder.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
