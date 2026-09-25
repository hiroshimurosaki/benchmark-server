"""Sonda do Answer_generator: por que a geração RAG devolve 'RELEVANTE'/'IRRELEVANTE'?

Chama QaSystem.get_answer_from_rag com uma pergunta real (faq-12 T3) capturando as
mensagens exatas enviadas ao modelo e a saída, e testa variações (só no script)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diag_common as dc  # noqa: E402
from bot_env import Bot  # noqa: E402

bot = Bot(dc.ORG, os.path.join(dc.DIAG_DIR, "memory"))
from langchain_core.runnables import RunnableLambda  # noqa: E402

from Answer_service.src.services.API import llm_provider  # noqa: E402
from Answer_service.src.services.API.qa_system import QaSystem  # noqa: E402
from Answer_service.src.utils.prompt import DEFAULT_WHO_AM_I  # noqa: E402

CAPT = {}
orig_build = llm_provider.build_chat_model


def build(role="answer"):
    m = orig_build(role)
    CAPT["modelo"] = repr(m)[:400]

    def f(msgs):
        CAPT["msgs"] = [(type(x).__name__, x.content) for x in msgs]
        out = m.invoke(msgs)
        CAPT["raw"] = {"content": out.content, "meta": getattr(out, "response_metadata", {}),
                       "extra": getattr(out, "additional_kwargs", {})}
        return out
    return RunnableLambda(f)


llm_provider.build_chat_model = build
perguntas = sys.argv[1:] or [
    "Queria cancelar a adesão da SUSEP 3307715 que fiz hoje de manhã, vai ter multa ou alguma cobrança?",
    "queria cancelar a adesão que fiz hoje de manhã, vai ter multa ou alguma cobrança?",
]
for q in perguntas:
    out = QaSystem.get_answer_from_rag(bot.qa_system, q, q, DEFAULT_WHO_AM_I,
                                       answer_system_override="",
                                       help_portal_directive=(bot.org_cfg.prompts.help_portal_directive or ""))
    sysmsg = CAPT["msgs"][0][1]
    print("=" * 80)
    print("PERGUNTA:", q)
    print("MODELO:", CAPT["modelo"])
    print("SYSTEM chars:", len(sysmsg), "| USER:", CAPT["msgs"][1][1][:300])
    print("SYSTEM início:", sysmsg[:600].replace("\n", " | "))
    i = sysmsg.find("Contexto dos documentos base")
    print("SYSTEM contexto:", sysmsg[i:i + 1500].replace("\n", " | "))
    print("SAIDA:", repr(out))
    print("RAW meta:", json.dumps(CAPT["raw"]["meta"], ensure_ascii=False, default=str)[:600])
