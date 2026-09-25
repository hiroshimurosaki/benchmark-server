"""Diagnóstico b5 — instrumentação do pipeline do bot SEM alterar o código dele.

Reaproveita ``b5/bot_env.py`` (env de produção qwen via túnel, Firestore só
leitura) e instala monkeypatches que só OBSERVAM:

* ``ClientAI.use_client``          → prompt (system/user) e saída crua de cada etapa aux
                                     (contextualizer, question_verifier, answer_verifier,
                                     historical_answer, disambiguation);
* ``processor.semantic_lookup``    → query, melhor entrada, top-3 FAQ e DTQ com score e
                                     score das entradas do gabarito;
* ``QaSystem.get_answer_from_rag`` → rag_query, trechos do FAISS (antes/depois do rerank
                                     do format_retriever) e saída crua do Answer_generator.

Parâmetros de experimento (C1–C4) também entram por aqui, via :class:`Config`.
"""

from __future__ import annotations

import copy
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field

DIAG_DIR = os.path.dirname(os.path.abspath(__file__))
B5_DIR = os.path.dirname(DIAG_DIR)
sys.path.insert(0, B5_DIR)

ORG = "oncorretor-perfeita"


def jl(p):
    return [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()]


def objetivos() -> dict:
    return {o["id"]: o for o in jl(os.path.join(B5_DIR, "objetivos_b5.jsonl"))}


# ------------------------------------------------------------------ config

@dataclass
class Config:
    nome: str = "base"
    limiar_faq: float | None = None          # C1: None = o da org (0.8)
    embedder: str | None = None              # C2: None = all-MiniLM-L6-v2 (produção)
    top_n: int | None = None                 # C3: None = 5 (RERANK_TOP_N)
    piso: float | None = None                # C3: None = 2 (RERANK_MIN_SCORE_FLOOR)
    verif_modo: str = "normal"               # C4: normal | sem_segundo_ciclo | aceita_nao_modo_c | relaxado
    ambiguo_so_curto: bool = False           # C7: AMBIGUO do question_verifier só vale p/ pergunta curta
    parse_opcao: bool = False                # C8: aceita "é a opção 3 mesmo, ..." como escolha do menu


VERIF_RELAXADO = """Você é um avaliador de respostas de um assistente de suporte.

Responda IRRELEVANTE somente se:
- a resposta for APENAS um pedido de desculpas / "não tenho essa informação", sem conteúdo útil; ou
- a resposta tratar de um assunto claramente diferente do perguntado.

Em qualquer outro caso (a resposta traz informação sobre o tema da pergunta, mesmo que parcial,
genérica ou com disclaimer) responda RELEVANTE.

RETORNE APENAS:
RELEVANTE
ou
IRRELEVANTE"""


# --------------------------------------------------------------- captura

class Captura:
    def __init__(self):
        self.eventos: list = []
        self.gabarito: dict = {}   # faq_ids / topicos do turno corrente

    def reset(self, gabarito: dict | None = None):
        self.eventos = []
        self.gabarito = gabarito or {}

    def add(self, tipo: str, **kw):
        kw["tipo"] = tipo
        kw["t"] = round(time.perf_counter(), 3)
        self.eventos.append(kw)


CAP = Captura()
CFG = Config()
_ESTADO: dict = {}


def _topico_de(header: str):
    m = re.match(r"\s*(\d+)", header or "")
    return int(m.group(1)) if m else None


def _rerank(docs, question: str):
    """Cópia da pontuação de Document_service/.../text_formatter.format_retriever,
    devolvendo a ordem completa (para ver posição antes/depois do corte)."""
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    q = question.lower()
    sw = set(stopwords.words("portuguese"))
    words = [t for t in word_tokenize(q) if t not in sw and t.isalnum()]
    out = []
    for i, d in enumerate(docs):
        header = d.metadata.get("cabecalho_numerado", "").lower()
        txt = d.page_content.lower()
        s = 0
        for w in words:
            if w in txt:
                s += 2
            if w in header:
                s += 6
        s += 8 * (0.6 ** i)
        out.append((s, i, d))
    out.sort(key=lambda x: x[0], reverse=True)
    return out


# ---------------------------------------------------------- instalação

def instalar(bot) -> None:
    """Instala as sondas. Chamar UMA vez depois de ``Bot(...)``."""
    import numpy as np
    import Answer_service.src.services.processor as proc
    import Answer_service.src.services.semantic.semantic_matcher as sm
    import Document_service.src.services.text_formatter as tf
    from Answer_service.src.services.API.client_ai import ClientAI
    from Answer_service.src.services.API.qa_system import QaSystem
    from Document_service.src.services.vectorstore import acess_vector_store
    from sentence_transformers.util import cos_sim

    _ESTADO["bot"] = bot
    _ESTADO["vs"] = acess_vector_store(ORG)
    _ESTADO["tf"] = tf
    _ESTADO["tf_orig"] = (tf.RERANK_TOP_N, tf.RERANK_MIN_SCORE_FLOOR)

    # ---- use_client
    orig_use = ClientAI.use_client

    def use_client(self, client, system_content, user_content, max_tokens, temperature, question,
                   from_who="verifier"):
        if from_who in ("answer_verifier",) and CFG.verif_modo == "relaxado":
            system_content = VERIF_RELAXADO
        t0 = time.perf_counter()
        out = orig_use(self, client, system_content, user_content, max_tokens, temperature,
                       question, from_who)
        if from_who == "answer_verifier" and CFG.verif_modo == "aceita_nao_modo_c":
            # aceita qualquer resposta que não seja MODO C / sentinela
            resp = user_content.split("RESPOSTA:", 1)[-1]
            if "não tenho essa informação" not in resp.lower() and "call_attendant" not in resp:
                out = "RELEVANTE"
        if from_who == "question_verifier" and CFG.ambiguo_so_curto and "AMBIGUO" in out.upper():
            import Answer_service.src.services.processor as _p
            frase = user_content.split("PERGUNTA:", 1)[-1].strip()
            if not _p._is_short_query(frase):
                out = "RELEVANTE"
        CAP.add("llm", etapa=from_who, system=system_content[-1500:], user=user_content[-2500:],
                saida=out, dur_s=round(time.perf_counter() - t0, 2))
        return out

    ClientAI.use_client = use_client

    # ---- C8: escolha do menu em frase longa
    orig_parse = proc._parse_disambiguation_choice
    _re_op = re.compile(r"\b(?:op[cç][aã]o|n[uú]mero|a)\s*([1-9])(?!\d)", re.I)

    def parse_choice(text, num_options):
        n = orig_parse(text, num_options)
        if n is None and CFG.parse_opcao and text:
            m = _re_op.search(text) or re.match(r"\s*([1-9])(?!\d)", text)
            if m and 1 <= int(m.group(1)) <= num_options:
                n = int(m.group(1))
        CAP.add("parse_escolha", texto=text[:120], escolha=n)
        return n

    proc._parse_disambiguation_choice = parse_choice

    # ---- semantic lookup (FAQ) com embedder trocável
    orig_lookup = sm.semantic_lookup
    _ESTADO["emb_cache"] = {}

    def _emb_model(nome):
        from sentence_transformers import SentenceTransformer
        if nome is None:
            return sm._get_model()
        if nome not in _ESTADO["emb_cache"]:
            _ESTADO["emb_cache"][nome] = SentenceTransformer(nome)
        return _ESTADO["emb_cache"][nome]

    _ESTADO["emb_idx"] = {}

    def _indice(nome, intention):
        chave = (nome, intention)
        if chave not in _ESTADO["emb_idx"]:
            cache = sm._get_org_cache(ORG)
            entries = cache.dtq_entries if intention == 2 else cache.faq_entries
            if nome is None:
                embs = cache.dtq_embeddings if intention == 2 else cache.faq_embeddings
            else:
                m = _emb_model(nome)
                pref = "query: " if "e5" in nome else ""
                embs = m.encode([pref + sm._preprocess(e.get("frase", e.get("question", "")))
                                 for e in entries], show_progress_bar=False)
            _ESTADO["emb_idx"][chave] = (entries, embs)
        return _ESTADO["emb_idx"][chave]

    def ranking(query, nome=None, intention=1):
        entries, embs = _indice(nome, intention)
        m = _emb_model(nome)
        pref = "query: " if nome and "e5" in nome else ""
        q = m.encode([pref + sm._preprocess(query)], show_progress_bar=False)
        sims = cos_sim(q, embs).flatten().numpy()
        order = np.argsort(-sims)
        return entries, sims, order

    _ESTADO["ranking"] = ranking

    def diag_lookup(query, nome=None):
        res = {}
        for intention, lab in ((1, "faq"), (2, "dtq")):
            entries, sims, order = ranking(query, nome, intention)
            res[f"top3_{lab}"] = [{"id": entries[i].get("_id"), "score": round(float(sims[i]), 4),
                                   "frase": entries[i].get("frase", "")[:120]} for i in order[:3]]
            gab = {}
            for gid in CAP.gabarito.get("faq_ids", []):
                for rank, i in enumerate(order):
                    if entries[i].get("_id") == gid:
                        gab[gid] = {"score": round(float(sims[i]), 4), "rank": rank + 1}
            res[f"gab_{lab}"] = gab
        return res

    _ESTADO["diag_lookup"] = diag_lookup

    def semantic_lookup(user_phrase, org_id, intention=1):
        if CFG.embedder is None:
            r = orig_lookup(user_phrase, org_id, intention)
        else:
            entries, sims, order = ranking(user_phrase, CFG.embedder, intention)
            e = entries[int(order[0])]
            s = float(sims[int(order[0])])
            r = (e.get("frase", ""), e.get("resposta", ""), e.get("intencao", "unknown"), s, s,
                 False, e.get("_id"))
        CAP.add("semantic_lookup", query=user_phrase, melhor_id=r[6], melhor_score=round(r[3], 4),
                melhor_frase=(r[0] or "")[:120], diag=diag_lookup(user_phrase, CFG.embedder))
        return r

    proc.semantic_lookup = semantic_lookup

    orig_topn = sm.semantic_lookup_top_n

    def semantic_lookup_top_n(user_phrase, org_id, n=3, intention=1):
        if CFG.embedder is None:
            return orig_topn(user_phrase, org_id, n, intention)
        entries, sims, order = ranking(user_phrase, CFG.embedder, intention)
        return [{"question": entries[i].get("frase", ""), "answer": entries[i].get("resposta", ""),
                 "intention": entries[i].get("intencao", "unknown"), "similarity": float(sims[i])}
                for i in order[:n]]

    sm.semantic_lookup_top_n = semantic_lookup_top_n
    if hasattr(proc, "semantic_lookup_top_n"):
        proc.semantic_lookup_top_n = semantic_lookup_top_n

    # ---- RAG
    orig_rag = QaSystem.get_answer_from_rag

    def get_answer_from_rag(prep_chain, question_with_historical, pure_question, who_am_i="",
                            answer_system_override="", help_portal_directive=""):
        tf.RERANK_TOP_N = CFG.top_n or _ESTADO["tf_orig"][0]
        tf.RERANK_MIN_SCORE_FLOOR = CFG.piso if CFG.piso is not None else _ESTADO["tf_orig"][1]
        # sonda: o mesmo retriever MMR do qa_system
        ret = _ESTADO["vs"].as_retriever(search_type="mmr",
                                         search_kwargs={"k": 20, "fetch_k": 30, "lambda_mult": 0.5})
        docs = ret.invoke(question_with_historical)
        rr = _rerank(docs, question_with_historical)
        top_n = tf.RERANK_TOP_N
        piso = tf.RERANK_MIN_SCORE_FLOOR
        mantidos = [x for x in rr[:top_n] if x[0] > piso]
        gab_top = set(CAP.gabarito.get("topicos", []))
        pos_antes = [i + 1 for i, d in enumerate(docs)
                     if _topico_de(d.metadata.get("cabecalho_numerado")) in gab_top]
        pos_depois = [k + 1 for k, x in enumerate(rr)
                      if _topico_de(x[2].metadata.get("cabecalho_numerado")) in gab_top]
        no_contexto = any(_topico_de(x[2].metadata.get("cabecalho_numerado")) in gab_top
                          for x in mantidos)
        t0 = time.perf_counter()
        out = orig_rag(prep_chain, question_with_historical, pure_question, who_am_i,
                       answer_system_override, help_portal_directive)
        CAP.add("rag", rag_query=question_with_historical[-1500:], pure_question=pure_question,
                headers_faiss=[d.metadata.get("cabecalho_numerado", "")[:60] for d in docs],
                headers_contexto=[x[2].metadata.get("cabecalho_numerado", "")[:60] for x in mantidos],
                pos_gab_faiss=pos_antes, pos_gab_rerank=pos_depois, gab_no_contexto=no_contexto,
                n_contexto=len(mantidos), saida=out, dur_s=round(time.perf_counter() - t0, 2))
        return out

    QaSystem.get_answer_from_rag = staticmethod(get_answer_from_rag)


def aplicar_config(cfg: Config) -> None:
    global CFG
    for k, v in vars(cfg).items():
        setattr(CFG, k, v)


def limiar_efetivo(bot) -> float:
    return CFG.limiar_faq if CFG.limiar_faq is not None else bot.org_cfg.features.ai.confidence_threshold


# ------------------------------------------------------ estado da sessão

def snapshot(bot, chat_id: str) -> dict:
    import Answer_service.src.services.processor as proc
    from Answer_service.src.services.historical.conversation_history import (
        get_history_file_path, get_session_id)
    p = get_history_file_path(get_session_id(chat_id, ORG))
    hist = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None
    return {"hist": hist,
            "awaiting": copy.deepcopy(proc._awaiting_disambiguation.get(chat_id)),
            "greeted": chat_id in proc._greeted_sessions,
            "negfb": proc._negative_feedback_count.get(chat_id)}


def restaurar(bot, chat_id: str, snap: dict) -> None:
    import Answer_service.src.services.processor as proc
    from Answer_service.src.services.historical.conversation_history import (
        get_history_file_path, get_session_id)
    p = get_history_file_path(get_session_id(chat_id, ORG))
    if snap["hist"] is None:
        if os.path.exists(p):
            os.remove(p)
    else:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(snap["hist"], f, ensure_ascii=False)
    proc._awaiting_disambiguation.pop(chat_id, None)
    if snap["awaiting"]:
        proc._awaiting_disambiguation[chat_id] = copy.deepcopy(snap["awaiting"])
    proc._greeted_sessions.discard(chat_id)
    if snap["greeted"]:
        proc._greeted_sessions.add(chat_id)
    proc._negative_feedback_count.pop(chat_id, None)
    if snap["negfb"]:
        proc._negative_feedback_count[chat_id] = snap["negfb"]


def pipeline(bot, body: str, chat_id: str) -> dict:
    """Só o answer_user_question + guard + regra de escalonamento (sem gates),
    com o limiar do experimento."""
    sub = bot.sub
    f = bot.org_cfg.features
    t0 = time.perf_counter()
    resp, _, cu, meta, rast = sub.answer_user_question(
        body, chat_id, ORG, sub.SUSEP_DEFAULT, bot.client, bot.qa_system, bot.verifier, True,
        bot.org_cfg.system_prompt, bot.org_cfg.prompts, limiar_efetivo(bot))
    if cu is not None:
        bot.client = cu
    saida = sub._aplicar_guard_saida(resp, meta, contexto="diag")
    if saida.bloqueado_motivo is not None:
        resp = "call_attendant"
    elif saida.resposta is not None:
        resp = saida.resposta
    meta = saida.escalation_meta
    escalou = (not resp or resp.strip() == "call_attendant" or "call_attendant" in resp.lower())
    return {"texto": resp, "escalou": escalou,
            "motivo": (meta.reason if meta else ("low_confidence" if escalou else None)),
            "fonte": getattr(rast, "fonte", None), "entrada_id": getattr(rast, "entrada_id", None),
            "confianca": getattr(rast, "confianca", None),
            "latencia_s": round(time.perf_counter() - t0, 2)}
