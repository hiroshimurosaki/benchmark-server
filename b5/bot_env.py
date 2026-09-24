"""b5 — o bot de produção rodando em processo, um turno por chamada.

Monta o ambiente (env de produção com Ollama/qwen, Firestore REAL em modo
somente leitura, histórico redirecionado para fora do repo do bot) e expõe
:class:`Bot` com :meth:`Bot.turno`, que replica a ordem de
``ai_subscriber._handle_ai_message`` (main):

    opening_question_gate → closure_gate → answer_user_question(...)
    → _aplicar_guard_saida → markdown_to_whatsapp

O que NÃO é reproduzido (ver README): dedup por msgId, gravação de mensagens
no Firestore, transição real de ticket (escalate/resolve), envio pelo Node.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
import traceback
import types
from contextlib import contextmanager
from typing import Any

BOT_REPO = os.environ.get(
    "B5_BOT_REPO",
    r"C:\Users\fernando.murusaki\rag-chatbot\.claude\worktrees\e1-env-audit")
SA_PATH = os.environ.get(
    "B5_SA_PATH", r"C:\Users\fernando.murusaki\rag-chatbot\config\serviceAccountKey.json")
BUCKET = "doc-assist-ms.firebasestorage.app"

ENV_PRODUCAO = {
    "LLM_PROVIDER": "ollama",
    "OLLAMA_BASE_URL": "http://127.0.0.1:11434",
    "OLLAMA_MODEL": "qwen3.6:35b-a3b",
    "OLLAMA_MODEL_ANSWER": "qwen3.6:35b-a3b",
    "OLLAMA_MODEL_AUX": "qwen3.6:35b-a3b",
    "OLLAMA_NUM_CTX": "8192",
    "OLLAMA_THINK": "false",
    "OLLAMA_TIMEOUT": "600",
    # Modo servidor local: o pipeline lê os.environ["API_KEY"] mesmo no Ollama;
    # produção usa OLLAMA_KEY_1=ollama (ver api_key_manager.load_api_keys).
    "OLLAMA_KEY_1": "ollama",
    "FIREBASE_SERVICE_ACCOUNT": SA_PATH,
    "GOOGLE_APPLICATION_CREDENTIALS": SA_PATH,
    "FIREBASE_STORAGE_BUCKET": f"gs://{BUCKET}",
}


# ------------------------------------------------------------ somente leitura

class EscritaBloqueada(PermissionError):
    pass


def _instalar_guarda_somente_leitura() -> None:
    """Toda escrita no Firestore/Storage vira exceção. Rede de segurança:
    o caminho do bot não deveria escrever (os pontos conhecidos são trocados
    por no-op no harness dos gates), mas Firestore aqui é PRODUÇÃO."""
    def _sync(nome):
        def f(*_a, **_k):
            raise EscritaBloqueada(f"b5: escrita bloqueada no Firestore ({nome})")
        return f

    def _async(nome):
        async def f(*_a, **_k):
            raise EscritaBloqueada(f"b5: escrita bloqueada no Firestore ({nome})")
        return f

    from google.cloud.firestore_v1 import (async_batch, async_collection, async_document,
                                           async_transaction, batch, collection, document,
                                           transaction)
    for cls in (document.DocumentReference,):
        for m in ("set", "update", "delete", "create"):
            setattr(cls, m, _sync(f"DocumentReference.{m}"))
    for m in ("set", "update", "delete", "create"):
        setattr(async_document.AsyncDocumentReference, m, _async(f"AsyncDocumentReference.{m}"))
    collection.CollectionReference.add = _sync("CollectionReference.add")
    async_collection.AsyncCollectionReference.add = _async("AsyncCollectionReference.add")
    batch.WriteBatch.commit = _sync("WriteBatch.commit")
    async_batch.AsyncWriteBatch.commit = _async("AsyncWriteBatch.commit")
    transaction.Transaction._commit = _sync("Transaction.commit")
    async_transaction.AsyncTransaction._commit = _async("AsyncTransaction.commit")
    try:
        from google.cloud.storage import blob as _blob
        for m in ("upload_from_string", "upload_from_filename", "upload_from_file", "delete"):
            setattr(_blob.Blob, m, _sync(f"Blob.{m}"))
    except Exception:
        pass


# ------------------------------------------------------------------ observer

class StageRecorder:
    """Uma linha por chamada de LLM, via ``llm_provider.set_observer`` (cópia
    do runner/run_b3.py:89, para a b5 ficar autocontida)."""

    def __init__(self):
        self.stages: list = []

    def __call__(self, stage: str, info: dict) -> None:
        self.stages.append({
            "stage": stage,
            "model": info.get("model", ""),
            "ttft_s": info.get("ttft_s"),
            "latency_s": info.get("total_s"),
            "tok_in": info.get("prompt_tokens", 0) or 0,
            "tok_out": info.get("completion_tokens", 0) or 0,
            "truncated": bool(info.get("truncated")),
        })

    def reset(self) -> None:
        self.stages = []


# ------------------------------------------------------------------- bootstrap

def bootstrap(dir_memoria: str):
    """Prepara env + sys.path + firebase e importa o bot. Chamar UMA vez."""
    for k, v in ENV_PRODUCAO.items():
        os.environ[k] = v
    os.environ.setdefault("PYTHONUTF8", "1")
    if BOT_REPO not in sys.path:
        sys.path.insert(0, BOT_REPO)

    # Histórico e audit de tokens fora do repo do bot (que é só leitura).
    os.makedirs(dir_memoria, exist_ok=True)
    import Answer_service.src.utils.config as cfg
    cfg.HISTORY_DIR = dir_memoria
    cfg.SESSION_MAP_FILE = os.path.join(dir_memoria, "session_map.json")
    cfg.tokens_history = os.path.join(dir_memoria, "tokens_history.json")

    import firebase_admin
    from firebase_admin import credentials
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(SA_PATH), {"storageBucket": BUCKET})
    _instalar_guarda_somente_leitura()

    import Answer_service.src.services.historical.conversation_history as hist
    assert hist.HISTORY_DIR == dir_memoria, "histórico não foi redirecionado"
    import Answer_service.src.services.ai_subscriber as sub  # noqa: F401
    return sub


# ------------------------------------------------------------- gates harness

@contextmanager
def _gates_sem_efeitos(flag: dict):
    """Cópia adaptada do runner/gates_harness.py: persistência do bot vira no-op,
    sem ticket ativo, e o ``_chat_ref(...).update`` do fechamento vira um
    registro em memória (``flag['encerrado']``) em vez de tocar o Firestore."""
    import Answer_service.src.services.closure_gate as cg
    import Answer_service.src.services.opening_question_gate as og
    import communicationChannels_service.core.ticket_manager as tm

    async def _noop(*_a, **_k):
        return None

    class _Ref:
        async def update(self, dados, *_a, **_k):
            flag["encerrado"] = True
            flag["encerrado_dados"] = {k: str(v) for k, v in (dados or {}).items()}

    alvos = [(og, "_persist_bot_msg_firestore", _noop),
             (cg, "_persist_bot_msg_firestore", _noop),
             (tm, "get_active_ticket", _noop),
             (tm, "_chat_ref", lambda _o, _c: _Ref())]
    originais = [(m, n, getattr(m, n)) for m, n, _ in alvos]
    for m, n, novo in alvos:
        setattr(m, n, novo)
    try:
        yield
    finally:
        for m, n, antigo in originais:
            setattr(m, n, antigo)


class Bot:
    def __init__(self, org_id: str, dir_memoria: str):
        self.org_id = org_id
        self.sub = bootstrap(dir_memoria)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        from Answer_service.src.services.API import llm_provider
        from Answer_service.src.services.API.client_ai import ClientAI
        from Answer_service.src.services.API.qa_system import get_qa_system

        self.rec = StageRecorder()
        llm_provider.set_observer(self.rec)
        self.org_cfg = self.loop.run_until_complete(self.sub.get_org_config(org_id))
        f = self.org_cfg.features
        if not f.ai.enabled:
            raise SystemExit(f"org {org_id} com features.ai desligada")
        # Mesmo que o startup do ai_subscriber (load_api_keys) + AppState.initialize_ai.
        from Answer_service.src.controllers.api_key_manager import ChangeApiKey
        ChangeApiKey.load_api_keys()
        self.chaves_llm = list(ChangeApiKey.API_KEY_NAMES_ORDER)
        self.verifier = ClientAI()
        self.client = self.verifier.create_client()
        if self.client is None:
            raise SystemExit("cliente LLM não inicializou")
        self.qa_system = get_qa_system(org_id, f)
        self.faq_dtq = self._ler_faq_dtq()

    def _ler_faq_dtq(self) -> dict:
        """FAQ/DTQ da org lidas do Firestore (leitura) para o juiz."""
        from firebase_admin import firestore
        db = firestore.client()
        out = {}
        for col in ("faq", "dtq"):
            for d in db.collection("orgs").document(self.org_id).collection(col).stream():
                x = d.to_dict() or {}
                out[d.id] = {"colecao": col, "frase": x.get("frase") or x.get("question") or "",
                             "resposta": x.get("resposta") or x.get("answer") or ""}
        return out

    def resumo_config(self) -> dict:
        f = self.org_cfg.features
        return {
            "org": self.org_id,
            "threshold": f.ai.confidence_threshold,
            "tickets": f.tickets.enabled,
            "opening_question": f.ai.opening_question.enabled,
            "auto_close_on_gratitude": f.ai.auto_close_on_gratitude.enabled,
            "system_prompt_chars": len(self.org_cfg.system_prompt or ""),
            "prompts_override": [k for k, v in vars(self.org_cfg.prompts).items() if v],
            "qa_system": self.qa_system is not None,
            "n_faq_dtq": len(self.faq_dtq),
            "modelo": os.environ["OLLAMA_MODEL"],
            "chaves_llm": self.chaves_llm,
        }

    def nova_sessao(self, chat_id: str) -> None:
        """Histórico limpo + saudação zerada para um atendimento novo."""
        from Answer_service.src.services.historical.conversation_history import (
            get_history_file_path, get_session_id)
        from Answer_service.src.services.processor import reset_greeting_for_session
        caminho = get_history_file_path(get_session_id(chat_id, self.org_id))
        if os.path.exists(caminho):
            os.remove(caminho)
        reset_greeting_for_session(chat_id)

    def turno(self, body: str, chat_id: str, estado: dict) -> dict:
        """Um turno do bot. ``estado`` é por conversa (flag de encerramento)."""
        from Answer_service.src.services.processor import (ESCALATION_MESSAGES,
                                                           reset_greeting_for_session)
        sub = self.sub
        f = self.org_cfg.features
        session_id = "bench5-session"
        from_number = chat_id  # em produção from == chatId (whatsapp-web.js)
        self.rec.reset()
        t0 = time.perf_counter()
        r: dict = {"gate": None, "texto_bot": None, "escalou": False, "motivo_escalonamento": None,
                   "fonte": None, "confianca": None, "entrada_id": None, "topico": None,
                   "guard": None, "erro": None, "resposta_crua": None}

        # Passo 4 do ai_subscriber: chat resolvido que recebe msg nova é reaberto
        # (bot_active) e a saudação é zerada.
        if estado.get("encerrado"):
            estado["encerrado"] = False
            reset_greeting_for_session(from_number)
            r["reaberto"] = True

        try:
            enviados: list = []

            async def coletor(_s, _c, texto, *_a, **_k):
                enviados.append(texto)
                return True

            async def gates():
                with _gates_sem_efeitos(estado):
                    from Answer_service.src.services.closure_gate import run_closure_gate
                    from Answer_service.src.services.opening_question_gate import \
                        run_opening_question_gate
                    ok = await run_opening_question_gate(
                        body=body, chat_id=chat_id, org_id=self.org_id, session_id=session_id,
                        from_number=from_number, opening_question=f.ai.opening_question,
                        send_message_fn=coletor)
                    if not ok:
                        return "opening_question"
                    ok = await run_closure_gate(
                        body=body, chat_id=chat_id, org_id=self.org_id, session_id=session_id,
                        from_number=from_number, auto_close=f.ai.auto_close_on_gratitude,
                        send_message_fn=coletor)
                    if not ok:
                        return "closure"
                    return None

            quem = self.loop.run_until_complete(gates())
            if quem:
                r["gate"] = quem
                r["texto_bot"] = "\n".join(enviados)
                r["fonte"] = f"gate:{quem}"
                r["encerrou_conversa"] = bool(estado.get("encerrado"))
            else:
                resposta, _, client_updated, escalation_meta, rastreio = sub.answer_user_question(
                    body, chat_id, self.org_id, sub.SUSEP_DEFAULT, self.client, self.qa_system,
                    self.verifier, True, self.org_cfg.system_prompt, self.org_cfg.prompts,
                    f.ai.confidence_threshold,
                )
                if client_updated is not None:
                    self.client = client_updated
                r["resposta_crua"] = resposta
                r["fonte"] = getattr(rastreio, "fonte", None)
                r["confianca"] = getattr(rastreio, "confianca", None)
                r["entrada_id"] = getattr(rastreio, "entrada_id", None)
                r["topico"] = getattr(rastreio, "topico", None)

                saida = sub._aplicar_guard_saida(resposta, escalation_meta, contexto=f"chat={chat_id}")
                if saida.bloqueado_motivo is not None:
                    resposta = "call_attendant"
                    r["guard"] = f"BLOQUEADO: {saida.bloqueado_motivo}"
                elif saida.resposta is not None:
                    if saida.higienizado:
                        r["guard"] = "HIGIENIZADO"
                    resposta = saida.resposta
                escalation_meta = saida.escalation_meta

                should_escalate = f.tickets.enabled and (
                    not resposta or resposta.strip() == "call_attendant"
                    or "call_attendant" in resposta.lower())
                if should_escalate:
                    r["escalou"] = True
                    r["motivo_escalonamento"] = (
                        escalation_meta.reason if escalation_meta
                        else ("call_attendant" if resposta and "call_attendant" in resposta.lower()
                              else "low_confidence"))
                    r["texto_bot"] = (sub.markdown_to_whatsapp(escalation_meta.user_message)
                                      if escalation_meta else "")
                    if not r["fonte"]:
                        r["fonte"] = "escalonamento"
                else:
                    final = (resposta or "").strip() or "Desculpe, não consegui gerar uma resposta."
                    if final.strip().lower() == "call_attendant":
                        final = ESCALATION_MESSAGES["low_confidence"]
                    r["texto_bot"] = sub.markdown_to_whatsapp(final)
        except Exception as e:
            r["erro"] = f"{type(e).__name__}: {e}"
            r["traceback"] = traceback.format_exc()[-2000:]

        r["latencia_s"] = round(time.perf_counter() - t0, 3)
        r["etapas"] = list(self.rec.stages)
        return r
