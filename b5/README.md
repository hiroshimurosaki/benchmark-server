# B5 — conversa dinâmica

Cliente simulado (Claude Sonnet) conversa com o **bot de produção** (qwen3.6:35b-a3b via Ollama,
rodando em processo) sobre objetivos reais de cliente; ao fim de cada conversa, um juiz (Claude
Opus) avalia. Tudo o que é gerado fica em `b5/`. A pasta não importa nada de `runner/`.

## Arquivos

| Arquivo | O que é |
|---|---|
| `objetivos_b5.jsonl` | 120 objetivos (gerados uma vez por `gerar_objetivos.py`: 3 lotes pelo Opus, 3 pelo fallback opencode, porque a cota acabou no meio) |
| `run_b5.py` | runner: laço conversa → juiz → painel, prazo, retomada |
| `bot_env.py` | ambiente do bot + um turno com a mesma ordem de `ai_subscriber._handle_ai_message` |
| `common.py` | chamadas `claude -p` com fallback para `opencode`, JSONL, log |
| `painel.py` | `painel.html` autocontido (abre por file://, recarrega a cada 15 s) e `RESULTADOS.md` |
| `resultados/` | `turnos.jsonl`, `conversas.jsonl`, `julgamentos.jsonl`, `estado.json`, `run.log` |
| `resultados_smoke*/` | smokes: normal e com falha do claude forçada |

## Como rodar

```bash
# rodada (5 h a partir do primeiro início), via pm2, a partir de C:\Users\fernando.murusaki\rag-chatbot
npx --no-install pm2 start C:/Users/fernando.murusaki/benchmark-server/b5/run_b5.py --name bench-b5 \
  --interpreter C:/Users/fernando.murusaki/rag-chatbot/env/Scripts/python.exe \
  --cwd C:/Users/fernando.murusaki/benchmark-server --max-restarts 5 --restart-delay 30000
npx --no-install pm2 logs bench-b5      # acompanhar
npx --no-install pm2 stop bench-b5      # parar (a conversa em andamento se perde e é refeita na retomada)

# smoke (1 objetivo curto, sem commit)
python b5/run_b5.py --res-dir b5/resultados_smoke --painel b5/resultados_smoke/painel.html --ids rag-02 --max-turnos 4 --sem-publicar
# smoke do fallback (imita o 429 "You've hit your monthly spend limit" do claude)
B5_SIMULAR_FALHA_CLAUDE=1 python b5/run_b5.py --res-dir b5/resultados_smoke_fallback ... --sem-publicar
```

**Retomar:** rodar de novo (ou `pm2 restart bench-b5`). Os ids já em `conversas.jsonl` são pulados; o
prazo gravado em `resultados/estado.json` vale (apagar esse arquivo = prazo novo). Uma conversa
interrompida é refeita com um `chat_id` novo (`bench5-<id>-<tentativa>@c.us`).

**No prazo** não começa conversa nova, termina a em andamento (+ juiz), escreve `b5/RESULTADOS.md`
e o painel final, faz `git add b5/ && git commit && git push` e dá `pm2 stop bench-b5` em si mesmo.
Se a fila acabar antes do prazo, finaliza do mesmo jeito. A máquina fica acordada durante a rodada
(`SetThreadExecutionState`).

## Por turno / por conversa

- **Bot, por turno:** `opening_question_gate → closure_gate → answer_user_question(body, chat_id, org,
  SUSEP_DEFAULT, client, qa_system, verifier, True, system_prompt, prompts, threshold) →
  _aplicar_guard_saida → markdown_to_whatsapp`, com a mesma regra de escalonamento
  (`tickets.enabled` e resposta vazia/`call_attendant` → o cliente recebe o aviso do motivo).
  Settings da org lidos do Firestore (threshold 0.8, os dois gates ligados). Histórico limpo e
  `reset_greeting_for_session` a cada atendimento.
- **Cliente:** `claude -p --model sonnet --json-schema` → `{mensagem, encerrar, satisfeito, motivo}`.
  Para quando: o cliente encerra (se a despedida tem texto, ela vai ao bot antes, para exercitar o
  closure_gate); o bot escala (o cliente ganha UMA mensagem de reação, que não vai ao bot); estoura
  `max_turnos`; ou o bot dá erro.
- **Juiz:** `claude -p --model opus --json-schema`, recebe objetivo, persona, gabarito, o texto dos
  tópicos do documento citados, as FAQ/DTQ do gabarito e as usadas pelo bot (`entrada_id`), e a
  transcrição com fonte/confiança/escalonamento/gate por turno.
- **Fallback (cliente, juiz, gerador):** claude falhou (exit≠0, `is_error`, 429, ou "hit your … limit")
  → espera 30 s e tenta 1× → `opencode run --model opencode/muse-spark-1.3-contributor-free --pure`
  pedindo só o JSON. 3 falhas seguidas do claude → 20 min direto no opencode. Quem respondeu fica em
  `cliente_modelo` (turno) e `juiz_modelo` (julgamento). Se nem o opencode responder antes do 1º
  turno, o objetivo NÃO é marcado como feito: espera 5 min e tenta de novo.
- **Registrado:** textos, latência do turno, tempo e tokens por etapa de LLM (observer do
  `llm_provider`), fonte, confiança, entrada_id, tópico, motivo do escalonamento, gate que
  interceptou, se o guard de saída alterou, erro + traceback, modelo/tempo/custo do cliente e do juiz.

## Segurança: Firestore de produção, só leitura

`bot_env.py` troca **todo** método de escrita do SDK (Document set/update/create/delete,
Collection.add, batch/transaction commit, Blob upload/delete) por exceção; as escritas conhecidas
dos gates (persistir a mensagem do bot, `_chat_ref.update` do fechamento, ticket ativo) viram no-op
antes disso. Histórico de conversa e audit de tokens vão para `resultados/memory/` (fora do repo do
bot, que é só leitura).

## O que NÃO é reproduzido

- **Dedup por msgId** (TTL 60 s de reconexão do WhatsApp): cada mensagem é única aqui.
- **Gravação no Firestore** (mensagens do cliente/bot, painel, metadados de rastreio).
- **Transição real de ticket:** não há `escalate_ticket`/`resolve_ticket`/`reopen_chat`. Escalou →
  a conversa termina (em produção o bot se cala porque o chat vira `unassigned`). O fechamento pelo
  closure_gate marca "encerrado" em memória; se o cliente escrever de novo, o harness faz o que o
  passo 4 do ai_subscriber faz (reabre com `reset_greeting_for_session`).
- **Envio pelo Node / WhatsApp:** o texto é capturado em memória; nada sai para cliente real.
- **Mídia, timeout do closure_sweeper (5 min), cache de config de 5 min, concorrência** entre chats.
- A SUSEP que o cliente informa só alimenta o gate (como em produção); `answer_user_question`
  recebe `SUSEP_DEFAULT`, como no `_handle_ai_message`.
