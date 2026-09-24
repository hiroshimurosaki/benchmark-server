"""Testes do harness b4.3 (handoff B43_GATES, 7 obrigatorios + 1 extra).

Rode da raiz do benchmark-server:
    ..\\rag-chatbot\\env\\Scripts\\python.exe -m pytest runner/test_gates_harness.py -q
"""

import copy
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gates_harness as gh

ORG = "oncorretor"
FONES = ["test-gates-%d" % n for n in range(1, 9)]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS = os.path.join(ROOT, "b3", "data", "oncorretor", "settings.json")


def _settings_base() -> dict:
    with open(SETTINGS, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session", autouse=True)
def _restaura_session_map():
    """Nao poluir o repo: snapshot de session_map.json, restore no fim."""
    gh._ensure_repo()
    from Answer_service.src.services.historical.conversation_history import SESSION_MAP_FILE
    antes = None
    if os.path.exists(SESSION_MAP_FILE):
        with open(SESSION_MAP_FILE, encoding="utf-8") as f:
            antes = f.read()
    yield
    for fone in FONES + ["test-gates-extra"]:
        try:
            from Answer_service.src.services.historical.conversation_history import (
                get_history_file_path,
                get_session_id,
            )
            p = get_history_file_path(get_session_id(fone, ORG))
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
    if antes is not None:
        with open(SESSION_MAP_FILE, "w", encoding="utf-8") as f:
            f.write(antes)


def _limpar(fone: str) -> None:
    from Answer_service.src.services.historical.conversation_history import (
        get_history_file_path,
        get_session_id,
    )
    p = get_history_file_path(get_session_id(fone, ORG))
    if os.path.exists(p):
        os.remove(p)


def _ligados():
    return gh.carregar_features_gates(_settings_base())


# 1. Feature desligada nao intercepta.
def test_1_feature_desligada_nao_intercepta():
    s = _settings_base()
    s["features"]["ai"]["opening_question"]["enabled"] = False
    s["features"]["ai"]["auto_close_on_gratitude"]["enabled"] = False
    oq, ac = gh.carregar_features_gates(s)
    _limpar(FONES[0])
    r = gh.rodar_gates("ola, quero ajuda", FONES[0], ORG, oq, ac)
    assert (r.continuar, r.mensagens, r.quem) == (True, [], "")


# 2. Primeira mensagem da sessao e interceptada.
def test_2_primeira_mensagem_interceptada():
    oq, ac = _ligados()
    _limpar(FONES[1])
    r = gh.rodar_gates("ola", FONES[1], ORG, oq, ac)
    assert r.continuar is False
    assert r.quem == "opening_question"
    assert any("SUSEP" in m for m in r.mensagens)


# 3. Resposta com identificador valido e aceita.
def test_3_identificador_valido_capturado():
    oq, ac = _ligados()
    _limpar(FONES[2])
    gh.rodar_gates("oi", FONES[2], ORG, oq, ac)
    r = gh.rodar_gates("123456F", FONES[2], ORG, oq, ac)
    assert r.continuar is False and r.quem == "opening_question"
    from Answer_service.src.services.historical.conversation_history import get_session_context
    assert get_session_context(FONES[2], ORG).get("susep") == "123456F"


# 4. Gratidao dispara o closure.
def test_4_gratidao_dispara_closure():
    oq, ac = _ligados()
    _limpar(FONES[3])
    from Answer_service.src.services.historical.conversation_history import update_session_context
    update_session_context(FONES[3], ORG, "susep", "123456F")
    r = gh.rodar_gates("muito obrigado!", FONES[3], ORG, oq, ac)
    assert r.continuar is False
    assert r.quem == "closure"
    assert len(r.mensagens) == 1


# 5. Mensagem comum passa pelos dois.
def test_5_mensagem_comum_passa():
    oq, ac = _ligados()
    _limpar(FONES[4])
    from Answer_service.src.services.historical.conversation_history import update_session_context
    update_session_context(FONES[4], ORG, "susep", "123456F")
    r = gh.rodar_gates("como funciona a cobranca?", FONES[4], ORG, oq, ac)
    assert (r.continuar, r.mensagens, r.quem) == (True, [], "")


# 6. Isolamento entre roteiros (limpeza igual a do run_b4.py).
def test_6_isolamento_entre_roteiros():
    oq, ac = _ligados()
    fone = FONES[5]
    _limpar(fone)
    r1 = gh.rodar_gates("oi", fone, ORG, oq, ac)
    assert r1.continuar is False
    from Answer_service.src.services.historical.conversation_history import (
        get_history_file_path,
        get_session_id,
    )
    caminho = get_history_file_path(get_session_id(fone, ORG))
    os.remove(caminho)
    r2 = gh.rodar_gates("oi", fone, ORG, oq, ac)
    assert r2.continuar is False and r2.quem == "opening_question"
    assert any("SUSEP" in m for m in r2.mensagens)


# 7. Gate quebrado degrada para pipeline puro.
def test_7_gate_quebrado_degrada():
    oq, ac = _ligados()
    _limpar(FONES[6])
    import Answer_service.src.services.opening_question_gate as og

    async def _quebrado(*_a, **_k):
        raise RuntimeError("pane simulada")

    monkey = pytest.MonkeyPatch()
    monkey.setattr(og, "run_opening_question_gate", _quebrado)
    try:
        r = gh.rodar_gates("ola", FONES[6], ORG, oq, ac)
    finally:
        monkey.undo()
    assert (r.continuar, r.mensagens, r.quem) == (True, [], "")


# Extra. settings sem os campos = tudo desligado, nunca excecao.
def test_extra_settings_vazio_desliga_tudo():
    oq, ac = gh.carregar_features_gates({})
    assert oq.enabled is False and ac.enabled is False
    _limpar(FONES[7])
    r = gh.rodar_gates("ola", FONES[7], ORG, oq, ac)
    assert (r.continuar, r.mensagens, r.quem) == (True, [], "")
    oq2, ac2 = gh.carregar_features_gates(copy.deepcopy(_settings_base()))
    assert oq2.enabled is True and ac2.enabled is True
    assert oq2.field == "susep"
    assert "SUSEP" in oq2.text
