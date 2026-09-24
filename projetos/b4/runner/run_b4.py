"""b4 — conversas inteiras contra o pipeline RAG real.

Diferença essencial para o b3: ali cada pergunta era um turno isolado com
telefone próprio, justamente para NÃO haver contaminação entre perguntas. Aqui é
o contrário — os turnos de um roteiro compartilham o mesmo telefone porque o
histórico acumulando É o objeto da medição. O que precisa ser isolado passa a ser
o roteiro: telefone distinto por (modelo, roteiro) e arquivo de histórico apagado
antes de começar, senão a memória de um roteiro vaza para o seguinte e a trilha
`memoria` mede lixo.

Reaproveita run_b3.py inteiro (ambiente, warmup, StageRecorder, resume). O que
muda é só o laço: `run_roteiro` em vez de `run_one`.

Uso:
    (da raiz do repo; --root aponta o bundle do b3: dados da org + índice FAISS)
    python projetos/b4/runner/run_b4.py --root projetos/b3 --repo /caminho/rag-chatbot --only qwen3.6:35b-a3b
    python projetos/b4/runner/run_b4.py --root projetos/b3 --repo ... --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback

# Imports locais. No repo: esta pasta + comum/ + projetos/b3/runner. No bundle do servidor
# (~/benchmark/b3/runner) tudo fica achatado em runner/ e as outras pastas
# simplesmente não existem — por isso o `isdir`.
_AQUI = os.path.dirname(os.path.abspath(__file__))
_RAIZ = os.path.normpath(os.path.join(_AQUI, "..", "..", ".."))
for _p in (os.path.join(_RAIZ, "comum"), os.path.join(_RAIZ, "projetos", "b3", "runner"), _AQUI):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from run_b3 import (  # noqa: E402  — reuso deliberado, não duplicar
    StageRecorder,
    append_jsonl,
    load_jsonl,
    log,
    warm_model,
)


def limpar_historico(phone: str, org_id: str) -> None:
    """Zera o histórico da sessão antes do roteiro começar.

    Sem isto, rodar o mesmo roteiro duas vezes (ou retomar um run interrompido)
    parte de um histórico sujo e a comparação entre modelos deixa de valer.
    """
    try:
        from Answer_service.src.services.historical.conversation_history import (
            get_history_file_path,
            get_session_id,
        )
        caminho = get_history_file_path(get_session_id(phone, org_id))
        if os.path.exists(caminho):
            os.remove(caminho)
    except Exception as e:  # nunca derrubar o run por causa da limpeza
        log(f"  aviso: falha ao limpar histórico de {phone}: {type(e).__name__}: {e}")


def run_roteiro(pipeline, roteiro: dict, model: str, org_id: str, rec: StageRecorder,
                gates=None) -> dict:
    """Uma conversa inteira, turno a turno, na mesma sessão.

    `gates` é o eixo do b4.3. Quando presente, é a tupla
    `(rodar_gates, opening_question, auto_close)` e cada turno passa pelos dois
    gates ANTES do pipeline — a mesma ordem do `ai_subscriber`. Sem ele, o
    comportamento é o do b4.1/b4.2: pipeline direto.

    Um turno consumido por um gate NÃO é falha do pipeline: o gate respondeu, e
    é isso que produção faz. Fica marcado com `outcome="gate"` e `gate=<quem>`
    para o juiz saber distinguir.
    """
    from Answer_service.src.services.processor import reset_greeting_for_session

    phone = f"bench4-{model.replace(':', '_')}-{roteiro['id']}"
    limpar_historico(phone, org_id)
    reset_greeting_for_session(phone)

    transcricao = []
    erro_fatal = None
    t_roteiro = time.perf_counter()

    for turno in roteiro["turnos"]:
        rec.reset()
        t0 = time.perf_counter()
        answer, escalation, err = "", None, None

        if gates is not None:
            rodar_gates, oq, ac = gates
            g = rodar_gates(turno["input"], phone, org_id, oq, ac)
            if not g.continuar:
                transcricao.append({
                    "n": turno["n"],
                    "input": turno["input"],
                    "espera": turno["espera"],
                    "answer": "\n".join(g.mensagens),
                    "outcome": "gate",
                    "gate": g.quem,
                    "escalation": None,
                    "error": None,
                    "latency_s": round(time.perf_counter() - t0, 3),
                    "stages": [],
                })
                continue

        try:
            answer, _qa, _client, meta = pipeline(turno["input"], phone)
            escalation = getattr(meta, "reason", None) if meta else None
            if escalation is None and isinstance(meta, dict):
                escalation = meta.get("reason")
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            traceback.print_exc()
        latencia = round(time.perf_counter() - t0, 3)

        answer = answer if isinstance(answer, str) else ""
        escalou = bool(escalation) or answer.strip() == "call_attendant"
        transcricao.append({
            "n": turno["n"],
            "input": turno["input"],
            "espera": turno["espera"],
            "answer": answer,
            "outcome": "error" if err else ("call_attendant" if escalou else "answered"),
            "escalation": escalation,
            "error": err,
            "latency_s": latencia,
            "stages": rec.stages,
        })

        if err:
            # Um turno que estourou invalida os seguintes (o histórico ficou num
            # estado que o roteiro não previu). Registra o que houve e para.
            erro_fatal = f"turno {turno['n']}: {err}"
            break

    return {
        "id": roteiro["id"],
        "model": model,
        "trilha": roteiro.get("trilha", ""),
        "nome": roteiro.get("nome", ""),
        "turnos_executados": len(transcricao),
        "turnos_previstos": len(roteiro["turnos"]),
        "latency_total_s": round(time.perf_counter() - t_roteiro, 3),
        "erro_fatal": erro_fatal,
        "criterio_final": roteiro.get("criterio_final", ""),
        "proibicoes_globais": roteiro.get("proibicoes_globais", []),
        "transcricao": transcricao,
    }


def done_keys_b4(path: str) -> set:
    """(roteiro_id, model) já concluídos — o resume do b4 é por conversa."""
    feitos = set()
    if not os.path.exists(path):
        return feitos
    with open(path, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            try:
                r = json.loads(linha)
                feitos.add((r["id"], r["model"]))
            except Exception:
                continue
    return feitos


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--org", default="oncorretor")
    ap.add_argument("--models", default="projetos/b4/runner/models_b4.jsonl")
    ap.add_argument("--roteiros", default="projetos/b4/roteiros_b4.jsonl")
    ap.add_argument("--host", default="http://127.0.0.1:11434")
    ap.add_argument("--out", default="projetos/b4/results_b4.jsonl")
    ap.add_argument("--only", default="", help="rodar só estes modelos (vírgula)")
    ap.add_argument("--limit", type=int, default=0, help="roteiros por modelo (0 = todos)")
    ap.add_argument("--num-ctx", type=int, default=8192)
    ap.add_argument("--provider", default="ollama", choices=["ollama", "groq"])
    ap.add_argument("--repo", default="", help="caminho do repo rag-chatbot")
    ap.add_argument("--key-prefix", default="")
    ap.add_argument("--prompt-answer", default="",
                    help="arquivo com um ANSWER_PROMPT_SYSTEM alternativo. É o "
                         "eixo do b4.2: mesmos roteiros, mesmo modelo, prompt "
                         "diferente — isola o efeito do prompt de tudo o mais.")
    ap.add_argument("--gates", action="store_true",
                    help="b4.3: roda opening_question_gate e closure_gate antes do "
                         "pipeline, como o ai_subscriber faz em produção. Exige "
                         "comum/gates_harness.py.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = os.path.abspath(args.root)

    def resolver(caminho: str) -> str:
        """`--root` aponta para o bundle da org (dados + índice FAISS), que no b3
        é `projetos/b3/`. Já roteiros e lista de modelos vivem fora dele. Aceita os dois:
        usa o caminho como veio se existir, senão tenta dentro do root.
        """
        if os.path.exists(caminho):
            return os.path.abspath(caminho)
        candidato = os.path.join(root, caminho)
        if os.path.exists(candidato):
            return candidato
        raise SystemExit(f"não encontrei {caminho} (nem em {root})")

    roteiros = load_jsonl(resolver(args.roteiros))
    models = load_jsonl(resolver(args.models))
    if args.only:
        querido = {m.strip() for m in args.only.split(",") if m.strip()}
        models = [m for m in models if m["name"] in querido]

    res_path = os.path.abspath(args.out)
    feitos = done_keys_b4(res_path)

    if args.dry_run:
        total = 0
        for m in models:
            sel = [r for r in roteiros if (r["id"], m["name"]) not in feitos]
            if args.limit:
                sel = sel[:args.limit]
            turnos = sum(len(r["turnos"]) for r in sel)
            total += turnos
            log(f"--- {m['name']}: {len(sel)} roteiros, {turnos} turnos ---")
        log(f"TOTAL: {total} turnos a executar")
        return

    # Ambiente do pipeline: mesma montagem do b3, passo a passo (não há atalho —
    # o b3 monta isso no corpo do main, não numa função reaproveitável).
    import b3_env  # noqa: E402

    os.environ["OLLAMA_BASE_URL"] = args.host
    os.environ["OLLAMA_NUM_CTX"] = str(args.num_ctx)

    # `repo_dir` só existe nas versões novas do b3_env (o servidor tem uma antiga,
    # e ela é a que produziu os resultados publicados do b3 — não sobrescrever).
    # Passa o argumento apenas quando foi pedido E a assinatura aceita.
    kw = {"bundle_root": root, "org_id": args.org, "provider": args.provider}
    if args.repo:
        import inspect
        if "repo_dir" in inspect.signature(b3_env.bootstrap).parameters:
            kw["repo_dir"] = args.repo
        else:
            log("aviso: b3_env sem suporte a --repo; usando o repo do bundle")
    ctx = b3_env.bootstrap(**kw)
    log(f"=== START b4 org={ctx.org_id} ai={ctx.features.ai.enabled} "
        f"threshold={ctx.features.ai.confidence_threshold} corpus={ctx.n_corpus} "
        f"num_ctx={args.num_ctx} ===")

    from Answer_service.src.controllers.api_key_manager import ChangeApiKey  # noqa: E402
    from Answer_service.src.services.API import llm_provider  # noqa: E402
    from Answer_service.src.services.API.client_ai import ClientAI  # noqa: E402
    from Answer_service.src.services.API.qa_system import get_qa_system  # noqa: E402
    from Answer_service.src.services.processor import answer_user_question  # noqa: E402

    ChangeApiKey.load_api_keys()
    if args.key_prefix:
        nomes = [k for k in ChangeApiKey.API_KEY_NAMES_ORDER if k.startswith(args.key_prefix)]
        if not nomes:
            log(f"FATAL: nenhuma chave com prefixo {args.key_prefix}")
            return
        ChangeApiKey.API_KEY_NAMES_ORDER = nomes
        ChangeApiKey.API_KEYS_DICT = {k: ChangeApiKey.API_KEYS_DICT[k] for k in nomes}
        ChangeApiKey.CURRENT_API_KEY_INDEX = 0
        os.environ["API_KEY"] = ChangeApiKey.API_KEYS_DICT[nomes[0]]

    rec = StageRecorder()
    llm_provider.set_observer(rec)

    verifier = ClientAI()
    client = verifier.create_client()
    if client is None:
        log("FATAL: cliente LLM não inicializou")
        return

    # Override do prompt de resposta. `ctx.prompts.answer_system` é o mesmo
    # canal que uma org usa para sobrescrever o prompt pelo Firestore, então o
    # experimento passa exatamente pelo caminho de produção — não por um atalho.
    if args.prompt_answer:
        caminho = resolver(args.prompt_answer)
        texto = open(caminho, encoding="utf-8").read()
        # O template de SYSTEM recebe só estes três (`qa_system.py:203-207`);
        # a pergunta vai na mensagem de USER, então `{question}` aqui estoura
        # com KeyError no format.
        faltando = [p for p in ("{context}", "{who_am_I}", "{help_portal_directive}")
                    if p not in texto]
        if faltando:
            raise SystemExit(f"prompt sem os placeholders {faltando} — o pipeline quebraria")
        if "{question}" in texto:
            raise SystemExit("{question} não existe no template de system — ele vai no user")
        ctx.prompts.answer_system = texto
        log(f"prompt de resposta sobrescrito por {os.path.basename(caminho)} "
            f"({len(texto)} chars, {len(texto.splitlines())} linhas)")

    # b4.3 — os gates do ai_subscriber. Import tardio e explícito: se o módulo
    # não existir ou não cumprir o contrato, quebra AQUI, antes de gastar GPU,
    # em vez de rodar 90 turnos e só depois descobrir que os gates não entraram.
    gates = None
    if args.gates:
        import gates_harness
        # `OrgContext` não carrega o settings cru (só features/prompts já
        # destilados), e `b3_env` é compartilhado com o run_b3 — leio o arquivo
        # aqui em vez de mudar a estrutura de que a outra rodada depende.
        p_set = os.path.join(root, "data", args.org, "settings.json")
        with open(p_set, encoding="utf-8") as fh:
            settings_cru = json.load(fh)
        oq, ac = gates_harness.carregar_features_gates(settings_cru)
        if not getattr(oq, "enabled", False) and not getattr(ac, "enabled", False):
            raise SystemExit("--gates pedido, mas as duas features estão desligadas "
                             "no settings.json — o run seria idêntico ao b4.1")
        gates = (gates_harness.rodar_gates, oq, ac)
        log(f"gates ATIVOS | opening_question={getattr(oq,'enabled',False)} "
            f"auto_close={getattr(ac,'enabled',False)}")

    qa_system = get_qa_system(ctx.org_id, ctx.features)
    susep = os.getenv("SUSEP_CODE", "12345678")
    live = {"client": client}

    def pipeline(body: str, phone: str):
        out = answer_user_question(
            body, phone, ctx.org_id, susep, live["client"], qa_system, verifier,
            True, ctx.who_am_i, ctx.prompts, ctx.features.ai.confidence_threshold,
        )
        if out[2] is not None:
            live["client"] = out[2]
        return out

    for m in models:
        nome, tier = m["name"], m.get("tier", "barato")
        sel = [r for r in roteiros if (r["id"], nome) not in feitos]
        if args.limit:
            sel = sel[:args.limit]
        if not sel:
            log(f"--- {nome}: nada a fazer (resume) ---")
            continue

        if args.provider == "groq":
            os.environ["GROQ_MODEL"] = nome
            w = {"load_s": 0.0, "ok": True}
        else:
            os.environ["OLLAMA_MODEL"] = nome
            os.environ["OLLAMA_THINK"] = "true" if m.get("thinking") else "false"

        turnos = sum(len(r["turnos"]) for r in sel)
        log(f"--- MODELO {nome} (tier={tier}, {len(sel)} roteiros, {turnos} turnos) ---")

        if args.provider != "groq":
            w = warm_model(nome, args.host)
            log(f"  warmup: load={w['load_s']}s ok={w['ok']} {w.get('erro', '')}")
            if not w["ok"]:
                for r in sel:
                    append_jsonl(res_path, {
                        "id": r["id"], "model": nome, "trilha": r.get("trilha", ""),
                        "erro_fatal": f"warmup: {w.get('erro')}", "transcricao": [],
                        "turnos_executados": 0, "turnos_previstos": len(r["turnos"]),
                    })
                continue

        for r in sel:
            out = run_roteiro(pipeline, r, nome, ctx.org_id, rec, gates)
            append_jsonl(res_path, out)
            marca = "ERRO" if out["erro_fatal"] else "ok"
            log(f"  [{r['id']}] {r['trilha']:<24}{out['turnos_executados']}/"
                f"{out['turnos_previstos']} turnos  {out['latency_total_s']:.1f}s  {marca}")

    log("=== FIM b4 ===")


if __name__ == "__main__":
    main()
