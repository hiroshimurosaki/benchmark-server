"""b4.3 — harness dos dois gates de producao para o benchmark.

Reproduz, fora do ai_subscriber, o que producao faz antes do pipeline RAG
(ai_subscriber.py:861-896): roda opening_question_gate e depois closure_gate,
nessa ordem. O ``run_b4.py`` chama :func:`rodar_gates` (sincrona) por turno e
so aciona o pipeline quando ``continuar`` e True.

Pontos em que o benchmark difere de producao (decisoes documentadas):

1. Sem persistencia no Firestore. Os gates chamam ``_persist_bot_msg_firestore``
   sem try/except; no benchmark isso levanta FileNotFoundError
   (serviceAccountKey.json ausente) e o bool de decisao se perde — alem de
   pular o ``update_session_context`` do caminho A, o que repetiria a pergunta
   da SUSEP. O harness troca o persist por no-op durante a chamada: a decisao
   (bool) e preservada, o efeito colateral de painel/GLPI e descartado.
2. Sem Gateway/tickets. ``closure_gate`` resolve ticket in-process via
   ``ticket_manager`` (nao e HTTP). No benchmark ``get_active_ticket`` e
   fixado em None (sem ticket ativo): o gate segue pelo fallback "marcar chat
   como resolved", cujo proprio ``_chat_ref.update`` ja tem try/except no
   codigo original e so loga warning. A conversa fica registrada como
   encerrada (flags limpas, goodbye enviado), nao morre.
3. Identidades sinteticas. Producao recebe ``chat_id``/``session_id`` do
   payload WhatsApp; aqui ``chat_id = phone + "@c.us"`` e ``session_id`` vem
   de ``get_session_id(phone, org_id)`` — o mesmo mapeamento que o historico
   usa, entao apagar o arquivo de historico (como o ``run_b4`` faz) limpa o
   contexto dos gates junto (mesmo arquivo JSON).
4. ``send_message_fn`` do gateway e trocada por um coletor em memoria: o que
   o gate "enviaria ao cliente" vai para ``ResultadoGates.mensagens``.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import types
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Ambiente: repo no sys.path + stub de firebase_admin (molde: b3_env.py)


def _ensure_repo() -> str:
    """Garante ``Answer_service`` importavel; devolve a raiz do repo usada."""
    try:
        import Answer_service  # noqa: F401
        import Answer_service.src.utils.config as _c
        return os.path.dirname(os.path.dirname(os.path.abspath(_c.__file__)))
    except ImportError:
        pass
    candidatos = []
    for env in ("RAGCHATBOT_REPO", "BENCH_REPO"):
        if os.environ.get(env):
            candidatos.append(os.environ[env])
    aqui = os.path.dirname(os.path.abspath(__file__))
    candidatos += [
        os.path.join(os.path.dirname(aqui), "repo"),
        os.path.normpath(os.path.join(aqui, "..", "..", "rag-chatbot")),
        os.path.normpath(os.path.join(aqui, "..", "rag-chatbot")),
        os.path.abspath("repo"),
    ]
    for cand in candidatos:
        init = os.path.join(cand, "Answer_service", "__init__.py")
        if os.path.isfile(init) or os.path.isdir(os.path.join(cand, "Answer_service")):
            if cand not in sys.path:
                sys.path.insert(0, cand)
            import Answer_service  # noqa: F401
            return cand
    raise ImportError(
        "gates_harness: repo rag-chatbot nao encontrado. Defina RAGCHATBOT_REPO "
        "ou rode a partir do bundle/servidor com repo/ ou ../rag-chatbot."
    )


def _install_firebase_stub() -> None:
    """Igual ao ``b3_env._install_firebase_stub`` (idempotente)."""
    if "firebase_admin" in sys.modules:
        return
    fb = types.ModuleType("firebase_admin")
    fb._apps = {}

    def _unavailable(*_a: Any, **_k: Any) -> Any:
        raise RuntimeError("firebase stub: Firestore indisponivel no benchmark")

    fb.initialize_app = _unavailable
    fb.get_app = _unavailable
    firestore = types.ModuleType("firebase_admin.firestore")
    firestore.client = _unavailable
    firestore.SERVER_TIMESTAMP = None
    credentials = types.ModuleType("firebase_admin.credentials")
    credentials.Certificate = _unavailable
    storage = types.ModuleType("firebase_admin.storage")
    storage.bucket = _unavailable
    fb.firestore = firestore
    fb.credentials = credentials
    fb.storage = storage
    for name, mod in (
        ("firebase_admin", fb),
        ("firebase_admin.firestore", firestore),
        ("firebase_admin.credentials", credentials),
        ("firebase_admin.storage", storage),
    ):
        sys.modules[name] = mod


# ---------------------------------------------------------------------------
# Contrato — API exata consumida pelo run_b4.py


@dataclass
class OpeningQuestion:
    """Duck-type de ``OpeningQuestionFeature`` (ai_subscriber.py:163)."""

    enabled: bool = False
    text: str = ""
    field: str = ""
    confirm: str = ""
    skip_value: str = ""
    identifier_regex: str = ""
    fallback_message: str = ""


@dataclass
class AutoClose:
    """Duck-type de ``AutoCloseOnGratitudeFeature`` (ai_subscriber.py:178)."""

    enabled: bool = False
    ask_message: str = ""
    goodbye_message: str = ""
    timeout_message: str = ""


@dataclass
class ResultadoGates:
    continuar: bool = True
    mensagens: list = field(default_factory=list)
    quem: str = ""  # "" | "opening_question" | "closure"


def _str(v: Any) -> str:
    return str(v) if v is not None else ""


def carregar_features_gates(settings: dict) -> tuple:
    """Monta (opening_question, auto_close) a partir do settings.json.

    Campo ausente = feature desligada, nunca excecao (``settings`` vazio/None
    tambem vale: tudo desligado).
    """
    settings = settings or {}
    fdata = settings.get("features") or {}
    ai = fdata.get("ai") or {}
    oq_d = ai.get("opening_question") or {}
    ac_d = ai.get("auto_close_on_gratitude") or {}
    oq = OpeningQuestion(
        enabled=bool(oq_d.get("enabled", False)),
        text=_str(oq_d.get("text") or ""),
        field=_str(oq_d.get("field") or ""),
        confirm=_str(oq_d.get("confirm") or ""),
        skip_value=_str(oq_d.get("skip_value") or ""),
        identifier_regex=_str(oq_d.get("identifier_regex") or ""),
        fallback_message=_str(oq_d.get("fallback_message") or ""),
    )
    ac = AutoClose(
        enabled=bool(ac_d.get("enabled", False)),
        ask_message=_str(ac_d.get("ask_message") or ""),
        goodbye_message=_str(ac_d.get("goodbye_message") or ""),
        timeout_message=_str(ac_d.get("timeout_message") or ""),
    )
    return oq, ac


# ---------------------------------------------------------------------------
# Neutralizacao do Firestore durante a chamada dos gates


@contextmanager
def _gates_sem_firestore() -> Iterator[None]:
    """Troca os toques de Firestore por equivalentes inertes (restaurados no fim).

    - ``_persist_bot_msg_firestore`` dos dois gates -> no-op (so alimenta
      painel/GLPI; a decisao do gate nao depende dele).
    - ``ticket_manager.get_active_ticket`` -> None (sem ticket no benchmark;
      o fallback do proprio gate ja absorve a falha do ``_chat_ref``).
    """
    import Answer_service.src.services.closure_gate as cg
    import Answer_service.src.services.opening_question_gate as og

    async def _noop_persist(*_a: Any, **_k: Any) -> None:
        return None

    async def _sem_ticket_ativo(_chat_id: str, _org_id: str) -> None:
        return None

    try:
        import communicationChannels_service.core.ticket_manager as tm
    except Exception:
        tm = None
    if tm is None:
        from datetime import datetime, timezone

        tm = types.ModuleType("communicationChannels_service.core.ticket_manager")

        async def _add_msg(_chat_id: str = "", _org_id: str = "", msg_id: str = "", **_k: Any) -> str:
            return msg_id

        class _ChatStatus:
            BOT_ACTIVE = "bot_active"
            UNASSIGNED = "unassigned"
            ASSIGNED = "assigned"
            RESOLVED = "resolved"

        class _Ref:
            async def update(self, *_a: Any, **_k: Any) -> None:
                return None

        tm.add_message_to_chat = _add_msg  # type: ignore[attr-defined]
        tm.get_active_ticket = _sem_ticket_ativo  # type: ignore[attr-defined]
        tm.ChatStatus = _ChatStatus  # type: ignore[attr-defined]
        tm._chat_ref = lambda _o, _c: _Ref()  # type: ignore[attr-defined]
        tm.now_ts = lambda: datetime.now(timezone.utc)  # type: ignore[attr-defined]
        sys.modules["communicationChannels_service.core.ticket_manager"] = tm

    alvos = [
        (og, "_persist_bot_msg_firestore", _noop_persist),
        (cg, "_persist_bot_msg_firestore", _noop_persist),
        (tm, "get_active_ticket", _sem_ticket_ativo),
    ]
    originais = [(mod, nome, getattr(mod, nome, None)) for mod, nome, _ in alvos]
    for mod, nome, novo in alvos:
        setattr(mod, nome, novo)
    try:
        yield
    finally:
        for mod, nome, antigo in originais:
            if antigo is not None:
                setattr(mod, nome, antigo)


async def _rodar_async(
    body: str,
    phone: str,
    org_id: str,
    opening_question: Any,
    auto_close: Any,
) -> ResultadoGates:
    import Answer_service.src.services.closure_gate as cg
    import Answer_service.src.services.historical.conversation_history as hist
    import Answer_service.src.services.opening_question_gate as og

    if not isinstance(body, str):
        body = "" if body is None else str(body)
    session_id = hist.get_session_id(phone, org_id)
    chat_id = "%s@c.us" % phone

    mensagens: list = []

    async def _coletor(_session_id: str, _chat_id: str, texto: str, *_a: Any, **_k: Any) -> bool:
        mensagens.append(texto)
        return True

    with _gates_sem_firestore():
        try:
            cont = await og.run_opening_question_gate(
                body=body,
                chat_id=chat_id,
                org_id=org_id,
                session_id=session_id,
                from_number=phone,
                opening_question=opening_question,
                send_message_fn=_coletor,
            )
        except Exception as e:
            logger.warning("[gates] opening quebrou (%s: %s) — degradando p/ pipeline",
                           type(e).__name__, e)
            return ResultadoGates(continuar=True, mensagens=[], quem="")
        if not cont:
            return ResultadoGates(continuar=False, mensagens=list(mensagens),
                                  quem="opening_question")
        base = len(mensagens)
        try:
            cont = await cg.run_closure_gate(
                body=body,
                chat_id=chat_id,
                org_id=org_id,
                session_id=session_id,
                from_number=phone,
                auto_close=auto_close,
                send_message_fn=_coletor,
            )
        except Exception as e:
            logger.warning("[gates] closure quebrou (%s: %s) — degradando p/ pipeline",
                           type(e).__name__, e)
            return ResultadoGates(continuar=True, mensagens=[], quem="")
        if not cont:
            return ResultadoGates(continuar=False, mensagens=mensagens[base:],
                                  quem="closure")
    return ResultadoGates(continuar=True, mensagens=[], quem="")


def rodar_gates(
    body: str,
    phone: str,
    org_id: str,
    opening_question: Any,
    auto_close: Any,
) -> ResultadoGates:
    """Roda opening e depois closure, na ordem do ai_subscriber. Sincrona.

    Nunca levanta excecao: gate quebrado degrada para ``continuar=True``
    (comportamento de hoje, pipeline puro).
    """
    _ensure_repo()
    _install_firebase_stub()
    try:
        return asyncio.run(_rodar_async(body, phone, org_id, opening_question, auto_close))
    except Exception as e:
        logger.warning("[gates] falha geral (%s: %s) — degradando p/ pipeline",
                       type(e).__name__, e)
        return ResultadoGates(continuar=True, mensagens=[], quem="")
