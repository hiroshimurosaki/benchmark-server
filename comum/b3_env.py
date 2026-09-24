#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
b3 — bootstrap do ambiente que faz o pipeline REAL do Answer Service rodar
isolado no servidor, sem Firebase e sem rede.

Por que existe: o b2 mandava UMA chamada com a KB inteira colada no prompt.
O fluxo de verdade faz 3-4 chamadas por pergunta (contextualizador → verificador
→ RAG → verificador de resposta) e pode escalar para atendente em 6 pontos
diferentes. Medir latência de uma chamada não responde nada sobre o produto.
Este módulo faz o `processor.answer_user_question` real rodar.

O que ele monta, em ordem:
  1. sys.path  → o bundle tem `repo/Answer_service` e `repo/Document_service`
  2. stub de `firebase_admin` → NENHUMA credencial de produção vai ao servidor.
     Com `firebase_admin._apps` vazio, `semantic_matcher._get_org_cache` devolve
     None e o código cai sozinho no fallback JSON (semantic_matcher.py:114-127).
     `qa_system._download_org_documents` também degrada para os arquivos locais
     (qa_system.py:62 `_has_local_files`).
  3. semeia os dados exportados nas DUAS árvores que o código usa:
       {app}/data/{org}/raw_docs   ← corpus  (config.py:31)
       {app}/orgs/{org}/*.json     ← FAQ/DTQ (config.py:109)
     São árvores diferentes para a mesma org — inconsistência conhecida do
     config.py, reproduzida aqui de propósito.
  4. env do provedor local (LLM_PROVIDER=ollama)

Uso:
    import b3_env
    ctx = b3_env.bootstrap(bundle_root=".", org_id="oncorretor")
    from Answer_service.src.services.processor import answer_user_question
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import types
from dataclasses import dataclass, field


# --------------------------------------------------------------------- stubs

def _install_firebase_stub() -> None:
    """Injeta um `firebase_admin` falso em sys.modules.

    Precisa acontecer ANTES de qualquer import do Answer_service. O contrato
    que o código real espera é mínimo: `_apps` vazio e um `firestore.client()`
    que levanta. Todo consumidor já trata isso como 'Firestore indisponível'.
    """
    if "firebase_admin" in sys.modules:
        return

    fb = types.ModuleType("firebase_admin")
    fb._apps = {}                                   # noqa: SLF001 — é o contrato real

    def _unavailable(*_a, **_k):
        raise RuntimeError("firebase stub: Firestore indisponível no benchmark b3")

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


# ------------------------------------------------------- shims de configuração

@dataclass
class _AiFeature:
    enabled: bool = True
    confidence_threshold: float = 0.74


@dataclass
class _Flag:
    enabled: bool = False


@dataclass
class _Features:
    """Duck-type do `OrgFeatures` de ai_subscriber.py:239.

    Reimplementado em vez de importado porque importar `ai_subscriber` arrasta
    FastAPI, websockets e mTLS — nada disso participa do pipeline de resposta.
    `get_qa_system` só lê `features.ai.enabled` (qa_system.py:277).
    """
    ai: _AiFeature = field(default_factory=_AiFeature)
    messaging: _Flag = field(default_factory=lambda: _Flag(True))
    tickets: _Flag = field(default_factory=_Flag)
    glpi: _Flag = field(default_factory=_Flag)


@dataclass
class _OrgPrompts:
    """Duck-type do `OrgPrompts`. Campo vazio = usa o prompt default do
    `prompt.py`, que é como as orgs sem override rodam hoje."""
    verification_system: str = ""
    answer_system: str = ""
    answer_verification_no_history_system: str = ""
    answer_verification_with_history_system: str = ""
    historical_system: str = ""
    contextualizer_system: str = ""
    disambiguation_system: str = ""
    help_portal_directive: str = ""


@dataclass
class OrgContext:
    org_id: str
    who_am_i: str
    features: _Features
    prompts: _OrgPrompts
    docs_path: str
    org_path: str
    n_faq: int
    n_dtq: int
    n_corpus: int


def _load_org_context(data_dir: str, org_id: str) -> tuple[dict, _Features, _OrgPrompts, str]:
    """Reconstrói OrgConfig a partir do settings.json exportado.

    Espelha ai_subscriber.get_org_config (linhas 272-335) — inclusive o default
    0.70 do threshold quando o campo não existe, que é o valor do código, não o
    0.74 do processor.
    """
    path = os.path.join(data_dir, org_id, "settings.json")
    settings = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            settings = json.load(f)

    fdata = settings.get("features", {}) or {}
    ai_data = fdata.get("ai", {}) or {}
    features = _Features(
        ai=_AiFeature(
            enabled=bool(ai_data.get("enabled", False)),
            confidence_threshold=float(ai_data.get("confidence_threshold", 0.70)),
        ),
        messaging=_Flag(bool((fdata.get("messaging") or {}).get("enabled", False))),
        tickets=_Flag(bool((fdata.get("tickets") or {}).get("enabled", False))),
        glpi=_Flag(bool((fdata.get("glpi") or {}).get("enabled", False))),
    )

    p = settings.get("prompts", {}) or {}
    prompts = _OrgPrompts(**{
        k: str(p.get(k, "") or "") for k in _OrgPrompts.__dataclass_fields__
    })
    return settings, features, prompts, str(settings.get("system_prompt", "") or "")


# --------------------------------------------------------------------- seeding

def _seed_org_data(data_dir: str, org_id: str, fresh_index: bool) -> tuple[str, str, int]:
    """Copia o corpus e os JSONs exportados para os paths que o código lê."""
    from Answer_service.src.utils.config import (
        get_org_docs_path,
        get_org_paths,
        get_org_signature_path,
    )

    src = os.path.join(data_dir, org_id)
    docs_path = get_org_docs_path(org_id)
    paths = get_org_paths(org_id)
    os.makedirs(paths["raw_docs"], exist_ok=True)

    n_corpus = 0
    corpus_src = os.path.join(src, "corpus")
    if os.path.isdir(corpus_src):
        for name in sorted(os.listdir(corpus_src)):
            s = os.path.join(corpus_src, name)
            if os.path.isfile(s):
                shutil.copy2(s, os.path.join(docs_path, name))
                n_corpus += 1

    for fname in ("faq_db.json", "DTQ.json", "victim_faq.json"):
        s = os.path.join(src, fname)
        if os.path.exists(s):
            shutil.copy2(s, paths[{
                "faq_db.json": "faq_db",
                "DTQ.json": "dtq_db",
                "victim_faq.json": "victim_faq",
            }[fname]])

    if fresh_index:
        # docs.sig é cache-invalidation por mtime (docs_signature_manage.py:11).
        # Apagar força `acess_vector_store` a reconstruir o índice do zero — é o
        # que o build_index.py cronometra.
        sig = get_org_signature_path(org_id)
        if os.path.exists(sig):
            os.remove(sig)

    return docs_path, os.path.dirname(paths["faq_db"]), n_corpus


# ------------------------------------------------------------------- bootstrap

def bootstrap(
    bundle_root: str = ".",
    org_id: str = "oncorretor",
    provider: str = "ollama",
    fresh_index: bool = False,
    repo_dir: str | None = None,
) -> OrgContext:
    """Prepara o processo e devolve o contexto da org. Chame ANTES de importar
    qualquer coisa do Answer_service.

    `repo_dir` permite apontar para o repo rag-chatbot direto (usado na linha de
    base do Groq, que roda no PC e não tem a cópia `repo/` do bundle).
    """
    root = os.path.abspath(bundle_root)
    repo = os.path.abspath(repo_dir) if repo_dir else os.path.join(root, "repo")
    if repo not in sys.path:
        sys.path.insert(0, repo)

    if provider == "groq":
        # Linha de base: provedor atual de produção, sem stub — precisa das
        # GROQ_KEY_* do .env. O stub de Firebase continua ativo para o
        # benchmark não depender do Firestore (o pipeline cai no JSON local).
        from dotenv import load_dotenv
        load_dotenv(os.path.join(repo, ".env"))
        load_dotenv()

    _install_firebase_stub()

    os.environ["LLM_PROVIDER"] = provider
    if provider == "ollama":
        # O pipeline inteiro lê os.environ["API_KEY"]; sem uma chave qualquer o
        # ChangeApiKey.load_api_keys quebra no boot (api_key_manager.py:60).
        os.environ.setdefault("OLLAMA_KEY_1", "ollama")
        os.environ.setdefault("API_KEY", "ollama")
        os.environ.setdefault("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        os.environ.setdefault("OLLAMA_NUM_CTX", "8192")
        os.environ.setdefault("OLLAMA_THINK", "false")
    # Modelo de embedding já em cache local — não medir download de rede.
    os.environ.setdefault("HF_HUB_OFFLINE", "1")

    data_dir = os.path.join(root, "data")
    settings, features, prompts, who_am_i = _load_org_context(data_dir, org_id)
    docs_path, org_path, n_corpus = _seed_org_data(data_dir, org_id, fresh_index)

    def _count(fname: str) -> int:
        p = os.path.join(data_dir, org_id, fname)
        if not os.path.exists(p):
            return 0
        with open(p, encoding="utf-8") as f:
            return len(json.load(f))

    return OrgContext(
        org_id=org_id,
        who_am_i=who_am_i,
        features=features,
        prompts=prompts,
        docs_path=docs_path,
        org_path=org_path,
        n_faq=_count("faq_db.json"),
        n_dtq=_count("DTQ.json"),
        n_corpus=n_corpus,
    )


if __name__ == "__main__":
    ctx = bootstrap(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(json.dumps({
        "org": ctx.org_id,
        "ai_enabled": ctx.features.ai.enabled,
        "threshold": ctx.features.ai.confidence_threshold,
        "corpus_files": ctx.n_corpus,
        "faq": ctx.n_faq,
        "dtq": ctx.n_dtq,
        "docs_path": ctx.docs_path,
        "org_path": ctx.org_path,
        "who_am_i_len": len(ctx.who_am_i),
    }, indent=1, ensure_ascii=False))
