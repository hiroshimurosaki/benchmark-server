"""b5 — conversa dinâmica: cliente simulado (Claude Sonnet) x bot de produção
(qwen via Ollama, em processo) x juiz (Claude Opus), com painel ao vivo.

Uso:
    python b5/run_b5.py                          # rodada completa (prazo 5 h)
    python b5/run_b5.py --res-dir b5/resultados_smoke --ids faq-01 --max-turnos 3 --sem-publicar
    B5_SIMULAR_FALHA_CLAUDE=1 python b5/run_b5.py ...   # força o fallback opencode

Retomada: rodar de novo o mesmo comando; ids já em conversas.jsonl são
pulados e o prazo gravado em estado.json é respeitado.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
import traceback
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (B5_DIR, ESTADO_FALLBACK, append_jsonl, chamar_llm, load_jsonl,  # noqa: E402
                    log, set_log_path, write_json_atomic)
import painel  # noqa: E402

REPO_DIR = os.path.dirname(B5_DIR)
ORG = "oncorretor-perfeita"
SEED = 20260924
ESCALOU_MOTIVOS = ("call_attendant", "low_confidence", "system_error")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ----------------------------------------------------------------- cliente

SCHEMA_CLIENTE = {
    "type": "object",
    "properties": {
        "mensagem": {"type": "string"},
        "encerrar": {"type": "boolean"},
        "satisfeito": {"type": "string", "enum": ["sim", "parcial", "nao"]},
        "motivo": {"type": "string"},
    },
    "required": ["mensagem", "encerrar", "satisfeito", "motivo"],
}

ESTILO_DESC = {
    "formal": "escreve formal, frases completas, com pontuação",
    "informal": "escreve informal, curto, gírias leves, minúsculas",
    "erros_digitacao": "escreve com erros de digitação, abreviações (vc, pq, tb), pouca pontuação",
    "audio_transcrito": "mensagem parece áudio transcrito: texto corrido, sem pontuação, com 'né', 'tipo', repetições",
    "impaciente": "impaciente: mensagens curtas e secas, cobra rapidez, às vezes em CAIXA ALTA",
}


def system_cliente(obj: dict) -> str:
    p = obj.get("persona") or {}
    susep = obj.get("susep") or "não sei"
    return f"""Você está fazendo o papel de um CLIENTE REAL conversando pelo WhatsApp com o atendimento do OnCorretor (sites e e-mails para corretores de seguro, parceria Porto Seguro). Do outro lado há um atendente (pode ser um robô).

QUEM VOCÊ É: {p.get('nome','')} — {p.get('descricao','')}. Tom: {p.get('tom','')}. Jeito de escrever: {ESTILO_DESC.get(p.get('estilo_escrita',''), p.get('estilo_escrita',''))}.

O QUE VOCÊ QUER RESOLVER: {obj.get('objetivo','')}

SUA SUSEP: {"responda '" + susep + "' se perguntarem" if susep != "não sei" else "você NÃO sabe sua SUSEP; se perguntarem, diga que não sabe/não lembra"}.

REGRAS:
- Escreva como cliente de WhatsApp em português do Brasil: mensagens curtas (1-2 frases, raramente 3), sem parecer IA, sem listas, sem markdown, sem se apresentar formalmente demais. Siga a persona e o jeito de escrever.
- Não revele que é um teste nem copie o texto do objetivo literalmente; fale como a pessoa falaria.
- Revele o que quer aos poucos, como uma pessoa real (a primeira mensagem pode ser só uma saudação ou já a dúvida, conforme a persona).
- Se o atendente pedir a SUSEP, responda conforme acima.
- Reaja ao que o atendente disse: se a resposta não resolveu, insista, reformule ou pergunte de novo; se não entendeu, peça explicação.
- encerrar=true quando: seu objetivo foi resolvido (pode agradecer/despedir na mesma mensagem), você desistiu, ou foi transferido para um humano. Se encerrar agradecendo, a mensagem é a despedida.
- satisfeito: como você se sente AGORA em relação ao objetivo (sim | parcial | nao). motivo: 1 frase curta explicando (não é enviado ao atendente)."""


def transcricao_txt(turnos: list) -> str:
    linhas = []
    for t in turnos:
        linhas.append(f"VOCÊ (cliente): {t['texto_cliente']}")
        if t.get("texto_bot"):
            linhas.append(f"ATENDENTE: {t['texto_bot']}")
        elif t.get("erro"):
            linhas.append("ATENDENTE: (sem resposta)")
    return "\n".join(linhas)


def chamar_cliente(obj: dict, turnos: list, instrucao: str) -> dict:
    user = ("CONVERSA ATÉ AGORA:\n" + (transcricao_txt(turnos) or "(a conversa ainda não começou)")
            + f"\n\n{instrucao}\nResponda no formato JSON pedido.")
    return chamar_llm("cliente", "sonnet", system_cliente(obj), user, SCHEMA_CLIENTE, timeout=240)


# -------------------------------------------------------------------- juiz

SCHEMA_JUIZ = {
    "type": "object",
    "properties": {
        "cliente_satisfeito": {"type": "object", "properties": {
            "valor": {"type": "string", "enum": ["sim", "parcial", "nao"]},
            "justificativa": {"type": "string"}}, "required": ["valor", "justificativa"]},
        "objetivo_cumprido": {"type": "boolean"},
        "escalonamento": {"type": "object", "properties": {
            "houve": {"type": "boolean"},
            "avaliacao": {"type": "string", "enum": ["adequado", "desnecessario", "faltou", "nao_se_aplica"]},
            "justificativa": {"type": "string"}}, "required": ["houve", "avaliacao", "justificativa"]},
        "alucinacao": {"type": "object", "properties": {
            "houve": {"type": "boolean"},
            "trechos": {"type": "array", "items": {"type": "string"}}}, "required": ["houve", "trechos"]},
        "qualidade_por_turno": {"type": "array", "items": {"type": "object", "properties": {
            "turno": {"type": "integer"}, "nota": {"type": "number"}, "comentario": {"type": "string"}},
            "required": ["turno", "nota", "comentario"]}},
        "nota_qualidade": {"type": "number"},
        "nota_geral": {"type": "number"},
        "problemas": {"type": "array", "items": {"type": "string"}},
        "destaques": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["cliente_satisfeito", "objetivo_cumprido", "escalonamento", "alucinacao",
                 "qualidade_por_turno", "nota_qualidade", "nota_geral", "problemas", "destaques"],
}

SYSTEM_JUIZ = """Você é o juiz de um benchmark de um chatbot de atendimento via WhatsApp (produto OnCorretor). Recebe o objetivo de um cliente simulado, o gabarito (fatos corretos + trechos do documento oficial + entradas de FAQ/DTQ) e a transcrição da conversa com metadados por turno (fonte da resposta, confiança, escalonamento, gates).

Avalie SÓ o BOT (o cliente é simulado). Critérios:
- objetivo_cumprido: o bot entregou o que o cliente precisava (ou escalou/recusou quando esse era o comportamento esperado)?
- cliente_satisfeito: como um cliente real se sentiria ao final (sim|parcial|nao).
- escalonamento: houve transferência para humano? "adequado" (era necessário ou pedido), "desnecessario" (o material respondia e o bot transferiu), "faltou" (devia ter transferido e não transferiu), "nao_se_aplica" (não houve e não era preciso).
- alucinacao: qualquer afirmação factual do bot que CONTRADIZ ou NÃO ESTÁ no documento/FAQ fornecidos (valores, prazos, e-mails, passos, promessas). Cite os trechos exatos. Saudações, pedido da SUSEP e mensagens de transferência não são alucinação. A indicação do portal de ajuda https://ajuda.oncorretor.com.br (em assuntos técnicos/operacionais) também NÃO é alucinação: ela vem de uma diretiva configurada pela própria empresa, fora do documento.
- qualidade_por_turno: nota 0-10 para cada turno do bot (correção, clareza, tom de WhatsApp, concisão, se respondeu o que foi perguntado). Turnos de gate (pergunta de SUSEP, confirmação de encerramento) avalie pela adequação ao momento.
- nota_qualidade (0-10): qualidade média das respostas; nota_geral (0-10): desfecho da conversa como um todo (resolução, eficiência, escalonamento correto, ausência de erro).
- problemas / destaques: frases curtas e concretas.
Seja rigoroso e consistente. Responda no JSON pedido, em português."""


class Material:
    def __init__(self, bot_repo: str, faq_dtq_firestore: dict):
        base = os.path.join(bot_repo, "scripts", "org_perfeita")
        doc = open(os.path.join(base, "OnCorretor.txt"), encoding="utf-8").read()
        self.topicos = {}
        partes = list(re.finditer(r"^(\d+)\. – (.+)$", doc, re.M))
        for i, m in enumerate(partes):
            fim = partes[i + 1].start() if i + 1 < len(partes) else len(doc)
            self.topicos[int(m.group(1))] = doc[m.start():fim].strip()
        self.faq = dict(faq_dtq_firestore)
        for arq, col in (("faq_perfeita.json", "faq"), ("dtq_perfeita.json", "dtq")):
            try:
                for k, v in json.load(open(os.path.join(base, arq), encoding="utf-8")).items():
                    self.faq.setdefault(k, {"colecao": col, "frase": v.get("frase", ""),
                                            "resposta": v.get("resposta", "")})
            except Exception:
                pass

    def topicos_de(self, nums) -> str:
        out = []
        for n in nums:
            try:
                n = int(n)
            except Exception:
                continue
            if n in self.topicos:
                out.append(self.topicos[n])
        return "\n\n".join(out)


def chamar_juiz(obj: dict, conv: dict, mat: Material) -> dict:
    gab = obj.get("gabarito") or {}
    ids = list(dict.fromkeys(list(gab.get("faq_ids") or [])
                             + [t["entrada_id"] for t in conv["transcricao"] if t.get("entrada_id")]))
    topicos = list(dict.fromkeys(list(gab.get("topicos") or [])
                                 + [t["topico"] for t in conv["transcricao"]
                                    if isinstance(t.get("topico"), (int, str)) and str(t.get("topico")).isdigit()]))
    faq_txt = "\n".join(f"- [{i}] ({mat.faq[i]['colecao']}) P: {mat.faq[i]['frase']} | R: {mat.faq[i]['resposta']}"
                        for i in ids if i in mat.faq) or "(nenhuma)"
    turnos_txt = []
    for t in conv["transcricao"]:
        meta = (f"fonte={t.get('fonte')} confianca={t.get('confianca')} entrada_id={t.get('entrada_id')} "
                f"gate={t.get('gate')} escalou={t.get('escalou')} motivo={t.get('motivo_escalonamento')} "
                f"guard={t.get('guard')} erro={t.get('erro')}")
        turnos_txt.append(f"[turno {t['n']}] CLIENTE: {t['texto_cliente']}\n[turno {t['n']}] BOT: "
                          f"{t.get('texto_bot') or '(sem resposta)'}\n   ({meta})")
    if conv.get("reacao_final"):
        turnos_txt.append(f"[após transferência] CLIENTE: {conv['reacao_final']}")
    p = obj.get("persona") or {}
    user = f"""OBJETIVO DO CLIENTE: {obj.get('objetivo')}
TRILHA: {obj.get('trilha')}
PERSONA: {p.get('nome')} — {p.get('descricao')} (tom {p.get('tom')}, estilo {p.get('estilo_escrita')})
COMPORTAMENTO ESPERADO DO BOT: {obj.get('comportamento_esperado')}
SUSEP do cliente: {obj.get('susep')}

GABARITO — fatos corretos:
{chr(10).join('- ' + f for f in gab.get('fatos') or []) or '(nenhum)'}

TRECHOS DO DOCUMENTO OFICIAL (tópicos citados):
{mat.topicos_de(topicos) or '(nenhum)'}

ENTRADAS FAQ/DTQ (gabarito + usadas pelo bot; resposta "call_attendant" = o bot deve transferir):
{faq_txt}

COMO A CONVERSA PAROU: {conv.get('parada')}  (o cliente se declarou satisfeito: {conv.get('satisfeito_cliente')})

TRANSCRIÇÃO:
{chr(10).join(turnos_txt)}"""
    return chamar_llm("juiz", "opus", SYSTEM_JUIZ, user, SCHEMA_JUIZ, timeout=600)


# ------------------------------------------------------------------ rodada

def _keep_awake(ligar: bool) -> None:
    try:
        import ctypes
        ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED if ligar else ES_CONTINUOUS)
    except Exception:
        pass


def _slim_etapas(etapas: list) -> list:
    return [{"stage": s["stage"], "latency_s": s.get("latency_s"), "ttft_s": s.get("ttft_s"),
             "tok_in": s.get("tok_in"), "tok_out": s.get("tok_out"), "model": s.get("model")}
            for s in etapas]


class Rodada:
    def __init__(self, args):
        self.args = args
        self.res = os.path.abspath(args.res_dir)
        os.makedirs(self.res, exist_ok=True)
        set_log_path(os.path.join(self.res, "run.log"))
        self.p_turnos = os.path.join(self.res, "turnos.jsonl")
        self.p_conv = os.path.join(self.res, "conversas.jsonl")
        self.p_juiz = os.path.join(self.res, "julgamentos.jsonl")
        self.p_estado = os.path.join(self.res, "estado.json")
        self.p_painel = os.path.abspath(args.painel or os.path.join(self.res, "painel.html"))
        self.objetivos = load_jsonl(os.path.abspath(args.objetivos))
        ordem = list(self.objetivos)
        random.Random(SEED).shuffle(ordem)
        if args.ids:
            quer = [i.strip() for i in args.ids.split(",") if i.strip()]
            ordem = [o for q in quer for o in self.objetivos if o["id"] == q]
        if args.limite:
            ordem = ordem[:args.limite]
        self.ordem = ordem
        self.estado = self._carregar_estado()

    def _carregar_estado(self) -> dict:
        try:
            est = json.load(open(self.p_estado, encoding="utf-8"))
        except Exception:
            est = {}
        if not est.get("inicio"):
            agora = datetime.now()
            est["inicio"] = agora.isoformat(timespec="seconds")
            est["prazo"] = (agora + timedelta(hours=self.args.horas)).isoformat(timespec="seconds")
            est["tentativas"] = {}
            log(f"primeiro início: {est['inicio']}  prazo: {est['prazo']}")
        else:
            log(f"retomando: início {est['inicio']}  prazo {est['prazo']}")
        est.setdefault("tentativas", {})
        est["em_andamento"] = None
        est["total_planejado"] = len(self.ordem)
        return est

    def salvar_estado(self) -> None:
        self.estado["fallback"] = ESTADO_FALLBACK.resumo()
        self.estado["atualizado"] = datetime.now().isoformat(timespec="seconds")
        write_json_atomic(self.p_estado, self.estado)

    def prazo_passou(self) -> bool:
        return datetime.now() >= datetime.fromisoformat(self.estado["prazo"])

    def atualizar_painel(self) -> None:
        try:
            self.salvar_estado()
            painel.gerar(self.p_painel, self.estado, load_jsonl(self.p_conv),
                         load_jsonl(self.p_juiz), self.objetivos)
        except Exception as e:
            log(f"  aviso: painel falhou: {type(e).__name__}: {e}")

    # -------------------------------------------------------------- conversa
    def conversa(self, bot, obj: dict, mat: Material) -> None:
        oid = obj["id"]
        n = int(self.estado["tentativas"].get(oid, 0)) + 1
        self.estado["tentativas"][oid] = n
        chat_id = f"bench5-{oid}-{n}@c.us"
        max_turnos = self.args.max_turnos or int(obj.get("max_turnos") or 5)
        bot.nova_sessao(chat_id)
        est_conv: dict = {}
        turnos: list = []
        inicio = datetime.now()
        andamento = {"id": oid, "tentativa": n, "trilha": obj.get("trilha"), "objetivo": obj.get("objetivo"),
                     "inicio": inicio.isoformat(timespec="seconds"), "turnos": turnos, "fase": "cliente"}
        self.estado["em_andamento"] = andamento
        parada, reacao, satisfeito, erros = None, None, None, []
        custo_cli = 0.0
        log(f"[{oid}#{n}] {obj.get('trilha')} max_turnos={max_turnos} — {obj.get('objetivo','')[:90]}")

        for i in range(1, max_turnos + 1):
            instr = ("Escreva a sua PRIMEIRA mensagem para o atendimento." if i == 1
                     else "Escreva a sua próxima mensagem (ou encerre, se for o caso).")
            andamento["fase"] = f"cliente escrevendo (turno {i})"
            self.atualizar_painel()
            c = chamar_cliente(obj, turnos, instr)
            custo_cli += c.get("custo_usd") or 0.0
            if not c["ok"]:
                parada = "erro_cliente"
                erros.append(f"cliente: {c['erro']}")
                log(f"  cliente falhou: {str(c['erro'])[:200]}")
                break
            co = c["obj"]
            satisfeito = co.get("satisfeito")
            msg = (co.get("mensagem") or "").strip()
            if co.get("encerrar") and not msg:
                parada = "cliente_encerrou"
                break
            # Com encerrar=true e texto (ex.: "obrigado, era isso"), a despedida
            # AINDA vai ao bot — é o que exercita o closure_gate — e a conversa
            # termina depois da resposta dele.
            andamento["fase"] = f"bot respondendo (turno {i})"
            andamento["cliente_pendente"] = msg
            self.atualizar_painel()
            r = bot.turno(msg, chat_id, est_conv)
            andamento.pop("cliente_pendente", None)
            t = {
                "conversa_id": oid, "tentativa": n, "n": i, "chat_id": chat_id,
                "ts": datetime.now().isoformat(timespec="seconds"),
                "texto_cliente": msg, "texto_bot": r.get("texto_bot"),
                "latencia_s": r.get("latencia_s"), "etapas": _slim_etapas(r.get("etapas") or []),
                "fonte": r.get("fonte"), "confianca": r.get("confianca"),
                "entrada_id": r.get("entrada_id"), "topico": r.get("topico"),
                "gate": r.get("gate"), "escalou": r.get("escalou"),
                "motivo_escalonamento": r.get("motivo_escalonamento"),
                "guard": r.get("guard"), "reaberto": r.get("reaberto", False),
                "erro": r.get("erro"), "traceback": r.get("traceback"),
                "cliente_modelo": c["modelo"], "cliente_dur_s": c.get("dur_s"),
                "cliente_custo_usd": c.get("custo_usd"), "cliente_satisfeito": satisfeito,
                "cliente_motivo": co.get("motivo"), "cliente_encerrar": bool(co.get("encerrar")),
            }
            append_jsonl(self.p_turnos, t)
            turnos.append({k: v for k, v in t.items() if k != "traceback"})
            log(f"  t{i} {r.get('latencia_s')}s fonte={r.get('fonte')} esc={r.get('motivo_escalonamento')} "
                f"cli={c['modelo'].split(':')[0]} | C: {msg[:60]!r} | B: {(r.get('texto_bot') or '')[:70]!r}")
            self.atualizar_painel()
            if r.get("erro"):
                parada = "erro_bot"
                erros.append(f"bot t{i}: {r['erro']}")
                break
            if r.get("escalou"):
                parada = "escalou"
                andamento["fase"] = "reação do cliente à transferência"
                self.atualizar_painel()
                c2 = chamar_cliente(obj, turnos,
                                    "O atendimento transferiu você para um atendente humano. Se quiser, escreva UMA "
                                    "última mensagem de reação (pode ser vazia) e encerre (encerrar=true).")
                custo_cli += c2.get("custo_usd") or 0.0
                if c2["ok"]:
                    reacao = (c2["obj"].get("mensagem") or "").strip() or None
                    satisfeito = c2["obj"].get("satisfeito") or satisfeito
                else:
                    erros.append(f"cliente(reação): {c2['erro']}")
                break
            if co.get("encerrar"):
                parada = "cliente_encerrou"
                break
        if parada is None:
            parada = "max_turnos"
        if parada == "erro_cliente" and not turnos:
            # Nem claude nem opencode responderam antes do 1º turno: NÃO marca o
            # objetivo como concluído (senão uma queda longa dos dois queimaria a
            # fila inteira como erro). O laço principal espera e tenta de novo.
            self.estado["em_andamento"] = None
            self.atualizar_painel()
            return False

        lat = [t["latencia_s"] for t in turnos if t.get("latencia_s") is not None and not t.get("gate")]
        conv = {
            "id": oid, "tentativa": n, "trilha": obj.get("trilha"), "objetivo": obj.get("objetivo"),
            "persona": obj.get("persona"), "comportamento_esperado": obj.get("comportamento_esperado"),
            "max_turnos": max_turnos, "chat_id": chat_id, "inicio": inicio.isoformat(timespec="seconds"),
            "fim": datetime.now().isoformat(timespec="seconds"),
            "duracao_s": round((datetime.now() - inicio).total_seconds(), 1),
            "n_turnos": len(turnos), "parada": parada, "satisfeito_cliente": satisfeito,
            "reacao_final": reacao, "erros": erros, "custo_cliente_usd": round(custo_cli, 4),
            "latencia_bot_media_s": round(sum(lat) / len(lat), 2) if lat else None,
            "transcricao": turnos,
        }
        andamento["fase"] = "juiz avaliando"
        self.atualizar_painel()
        j = chamar_juiz(obj, conv, mat)
        jul = {"id": oid, "tentativa": n, "juiz_modelo": j["modelo"], "juiz_dur_s": j.get("dur_s"),
               "juiz_custo_usd": j.get("custo_usd"), "juiz_tentativas": j.get("tentativas"),
               "veredito": j["obj"] if j["ok"] else None, "erro": None if j["ok"] else j["erro"],
               "ts": datetime.now().isoformat(timespec="seconds")}
        # Ordem: julgamento antes da conversa — a conversa em conversas.jsonl é o
        # marcador de "concluído" da retomada.
        append_jsonl(self.p_juiz, jul)
        append_jsonl(self.p_conv, conv)
        v = jul["veredito"] or {}
        log(f"  => parada={parada} turnos={len(turnos)} {conv['duracao_s']}s | juiz={j['modelo'].split(':')[0]} "
            f"nota={v.get('nota_geral')} cumprido={v.get('objetivo_cumprido')} "
            f"sat={(v.get('cliente_satisfeito') or {}).get('valor')}")
        self.estado["em_andamento"] = None
        self.atualizar_painel()
        return True

    # ----------------------------------------------------------------- main
    def rodar(self) -> None:
        if self.estado.get("finalizado") and not self.args.ids:
            log("rodada já finalizada (estado.json). Nada a fazer.")
            self._parar_pm2()
            return
        import bot_env
        bot = bot_env.Bot(ORG, os.path.join(self.res, "memory"))
        self.estado["config_bot"] = bot.resumo_config()
        log("config do bot: " + json.dumps(self.estado["config_bot"], ensure_ascii=False))
        mat = Material(bot_env.BOT_REPO, bot.faq_dtq)
        feitos = {c["id"] for c in load_jsonl(self.p_conv)}
        self.atualizar_painel()
        _keep_awake(True)
        try:
            for obj in self.ordem:
                if obj["id"] in feitos:
                    continue
                concluida = False
                while not concluida and not self.prazo_passou():
                    try:
                        concluida = self.conversa(bot, obj, mat)
                    except Exception as e:
                        log(f"  ERRO inesperado na conversa {obj['id']}: {type(e).__name__}: {e}")
                        log(traceback.format_exc()[-1500:])
                        self.estado["em_andamento"] = None
                        concluida = True  # não prende a fila num objetivo que quebra o harness
                        time.sleep(5)
                    if not concluida:
                        log("  cliente indisponível (claude e opencode) — espero 5 min e tento de novo")
                        time.sleep(300)
                if self.prazo_passou():
                    log("prazo atingido — não começo conversa nova")
                    break
            self.finalizar()
        finally:
            _keep_awake(False)

    def finalizar(self) -> None:
        conv, jul = load_jsonl(self.p_conv), load_jsonl(self.p_juiz)
        self.estado["finalizado"] = datetime.now().isoformat(timespec="seconds")
        self.atualizar_painel()
        md = painel.resultados_md(self.estado, conv, jul, self.objetivos, self.p_painel)
        p_md = os.path.join(os.path.dirname(self.p_painel), "RESULTADOS.md") \
            if self.args.sem_publicar else os.path.join(B5_DIR, "RESULTADOS.md")
        with open(p_md, "w", encoding="utf-8") as f:
            f.write(md)
        log(f"RESULTADOS: {p_md}")
        if not self.args.sem_publicar:
            data = datetime.now().strftime("%Y-%m-%d")
            for cmd in (["git", "add", "b5/"],
                        ["git", "commit", "-m", f"b5: resultados da rodada {data}"],
                        ["git", "push"]):
                p = subprocess.run(cmd, cwd=REPO_DIR, capture_output=True, text=True,
                                   creationflags=0x08000000 if sys.platform == "win32" else 0)
                log(f"  {' '.join(cmd[:2])}: exit={p.returncode} {(p.stdout + p.stderr)[-200:]!r}")
            self._parar_pm2()

    def _parar_pm2(self) -> None:
        """Sob pm2, parar a si mesmo (senão o pm2 reinicia o processo)."""
        if "pm_id" not in os.environ:
            return
        log("finalizado — parando o app no pm2 (pm2 stop bench-b5)")
        try:
            subprocess.Popen("npx --no-install pm2 stop bench-b5", shell=True,
                             cwd=r"C:\Users\fernando.murusaki\rag-chatbot",
                             creationflags=0x08000000 if sys.platform == "win32" else 0)
        except Exception as e:
            log(f"  falhou: {e}")
        while True:  # se o stop não vier, fica ocioso em vez de reiniciar
            time.sleep(3600)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--res-dir", default=os.path.join(B5_DIR, "resultados"))
    ap.add_argument("--painel", default=os.path.join(B5_DIR, "painel.html"))
    ap.add_argument("--objetivos", default=os.path.join(B5_DIR, "objetivos_b5.jsonl"))
    ap.add_argument("--horas", type=float, default=5.0)
    ap.add_argument("--ids", default="", help="só estes ids (vírgula), na ordem dada")
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--max-turnos", type=int, default=0, help="sobrescreve max_turnos (smoke)")
    ap.add_argument("--sem-publicar", action="store_true", help="não commita/pusha no fim (smoke)")
    args = ap.parse_args()
    Rodada(args).rodar()


if __name__ == "__main__":
    main()
