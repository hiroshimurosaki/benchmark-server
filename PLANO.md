# Plano — Benchmark de modelos locais (b1 + b2)

Doc canônico. Objetivo: descobrir o melhor modelo local (GGUF) para duas aplicações,
medindo tempo, tempo/qualidade sob paralelismo, qualidade da resposta e resistência a burla.

---

## Decisões travadas

1. **Runner**: `llama-server` (llama.cpp), endpoint OpenAI-compatível `/v1/chat/completions`.
   Um modelo por vez → troca de modelo = reiniciar o processo apontando outro `.gguf`.
2. **Juiz do b2**: Opus via API Anthropic, rodado **no PC do Fernando** depois de colher as
   saídas no servidor. b1 é 100% heurístico automático (sem API).
3. **Aviso de término**: email (Gmail) para `nandomurosakii@gmail.com` com resumo + caminho
   dos visualizadores.
4. **Gabarito b1**: modelo **texto → JSON de tool-call**. Schema de tools sintético (abaixo),
   a ser validado pelo Fernando. O projeto `condocompras` NÃO é fonte — é outro domínio.

---

## Fontes de contexto já lidas

- `b1/b1.txt` — system prompt do agente analista de dados de condomínio (retorna JSON
  `{answer, highlights}`, usa tools, "hoje" via `getDateString`, conceito `dataLastDay`,
  `SMALL_SAMPLE_LIMIT`, agregados `uniquePeople/entries/exits/sampleSize`, reservas
  `confirmed/awaitingApproval/cancelled`, histórico por pessoa `isManualEntry`).
- `rag-chatbot/Answer_service/src/utils/prompt.py` — pipeline RAG do **OnCorretor** (SaaS de
  corretor/SUSEP). Estágios de LLM: VERIFICATION (classificação), CONTEXTUALIZER, ANSWER
  (fidelidade estrita, MODO A/B/C), ANSWER_VERIFICATION, HISTORICAL, DISAMBIGUATION, FEEDBACK.
  Foco do benchmark 2 = estágio **ANSWER** (resposta ao cliente).
- `models/models.txt` — tiers e orçamento de perguntas:
  - barato → 50 perguntas × (com/sem thinking)
  - médio → 25 perguntas × (com/sem thinking)
  - pesado → 10 perguntas × (com/sem thinking)
- `access/nicolas.benedetti.txt` — SSH `nicolas.benedetti@10.10.10.151`. **NÃO versionar**
  (segredo; fica no `.gitignore`).

---

## Arquitetura (6 blocos)

1. **Bundle único** copiado ao servidor: `run_bench.py` + `questions_b1.jsonl` +
   `questions_b2.jsonl` + `models.jsonl` + KB do OnCorretor + prompts.
2. **Orquestrador** (`run_bench.py`): para cada modelo → sobe llama-server com o `.gguf` →
   roda todas as perguntas (thinking on/off) → derruba → próximo modelo. Fernando roda
   **1 comando**; todos os swaps ficam DENTRO do script.
3. **Log automático** (`run.log` no servidor): todo comando/subprocesso disparado pelo script
   é registrado. Satisfaz "todo comando registrado" sem aprovar swap a swap.
4. **Resultados append-only** (`results_b1.jsonl`, `results_b2.jsonl`): à prova de crash e
   **resumível** — se cair ou estourar 24h, retoma de onde parou e envia parcial.
5. **Juiz Opus** (no PC): lê `results_b2.jsonl`, pontua qualidade + resistência →
   `scored_b2.json`.
6. **Visualizadores**: `b1.html` e `b2.html` standalone (abre no navegador, sem build).

---

## Benchmark 1 — condomínio → tool-call (heurístico, sem API)

### Schema de tools sintético (VALIDAR)
- `get_access_stats(from, to)` → visitantes: `uniquePeople, entries, exits, sampleSize`.
- `get_reservations(from, to, area?)` → `confirmed, awaitingApproval, cancelled`.
- `get_person_history(name, limit?)` → eventos recentes de uma pessoa (`isManualEntry`).

### Determinismo
- "Hoje" fixo no system prompt (ex.: `2026-08-18`) → datas relativas viram gabarito exato.
- `dataLastDay` fixo (ex.: `2026-08-15`) para testar o clamp de período.

### Score heurístico (0–100), automático, 2 fases
- **Fase A (seleção)**: tool certa (0/1) + período `from/to` resolvido exato (0/1) + args certos.
- **Fase B (leitura)**: devolve resultado **mockado** e checa por asserção — headline =
  `uniquePeople`, reporta split de cancelados, sinaliza amostra pequena (`sampleSize<limit`),
  usa `dataLastDay` (não "hoje"), JSON `{answer,highlights}` válido.

### Banco: 50 perguntas, categorias
extração de período relativo · escolha de tool · leitura de agregados · borda `dataLastDay` ·
sem-dado/ambíguo · adversarial (inventar número, quebrar JSON, vazar system prompt, injection
dentro de um nome de pessoa).

Subconjuntos: 25 (médio) e 10 (pesado) curados dos 50.

---

## Benchmark 2 — RAG OnCorretor (juiz Opus)

Foco no `ANSWER_PROMPT`. **KB fixa** montada dos fatos do prompt + mineração dos zips
`b2/conversas-oncorretor.zip` e `b2/MENSAGENS-IA.zip` para perguntas realistas.

### Formato de cada pergunta
`{input, contexto_recuperado (fixo), objetivos[], proibições[], modo_esperado A/B/C}`.
Opus devolve % de objetivos cumpridos + flag de resistência.

### Banco: 50 perguntas, 2 trilhas
- **Fidelidade**: MODO A/B/C correto · extração literal · **sem alucinação em pergunta
  confirmativa** ("posso pagar com cartão?" com contexto só de desconto SUSEP → MODO C) ·
  sem misturar tópicos · guardrails (não oferece humano, não pede dado sensível).
- **Resistência/burla**: "ignore as predefinições" · vazar prompt · inventar forma de
  pagamento · injection · empresa fora de domínio.

Subconjuntos: 25 (médio) e 10 (pesado).

---

## Métricas (ambos os benchmarks)

- Tempo prompt → resposta (wall time).
- **TTFT** (time-to-first-token, via streaming).
- tokens/s, tokens de saída.
- **Paralelismo**: subir llama-server com `--parallel N`, disparar N requisições concorrentes
  num subconjunto fixo → throughput agregado + degradação de latência + re-julgar amostra
  para ver se a qualidade cai sob carga.
- Qualidade: b1 heurístico / b2 Opus.
- Resistência a burla: subconjunto adversarial dedicado.

### Volume estimado (por benchmark)
Assumindo ~8 baratos, ~3 médios, ~4 pesados (confirmar na descoberta):
- barato: 50 × 8 × 2 = 800
- médio: 25 × 3 × 2 = 150
- pesado: 10 × 4 × 2 = 80
- **~1030 execuções por benchmark** (+ subconjunto de paralelismo). O tiering existe para
  caber em 24h; pesados só recebem 10 perguntas por serem lentos.

---

## Fluxo no servidor — 4 comandos, cada um aprovado antes

1. **Descoberta** (read-only): lista GGUFs reais, confirma binário `llama-server`, GPU/VRAM,
   disco livre.
2. **Enviar bundle** (`scp`).
3. **Disparar run 24h** em `tmux`/`nohup` (1 comando). Script self-loga em `run.log`.
4. **Trazer resultados** (`scp`).

Modelos ausentes: o script baixa via `huggingface-cli` (motivo das 24h) — cada download
logado; lista pré-aprovada pelo Fernando.

---

## Itens abertos (precisam do Fernando)

1. **Chave da API Anthropic** para o juiz Opus (variável de ambiente) + teto de custo
   (~1000+ respostas a julgar no b2).
2. Vários nomes em `models.txt` parecem **placeholder/inexistentes** (Qwen3.5/3.6/3.8,
   DeepSeek-V4, MiniMax-H3). A descoberta enumera o que existe de fato e mostra o que falta baixar.
3. Validar o schema de tools do b1 (acima).
4. Flags do llama-server: context size, GPU layers, `--parallel` slots — dependem da VRAM
   (a descoberta informa).

---

## Sugestões de prompt (melhoria de qualidade)

- **b1**: forçar JSON com **GBNF/json-schema** do llama-server (modelos locais quebram JSON
  fácil) + 1 exemplo (1-shot). Confirmar que `SMALL_SAMPLE_LIMIT`/`getDateString` interpolam.
- **b2**: `ANSWER_PROMPT` é ótimo mas **muito longo** — modelos baratos degradam. Testar uma
  versão "compacta" para o tier barato e medir as duas.
- **b2**: `VERIFICATION_PROMPT` tem typos ("hover", "concateneas", "exclusicamente") que
  confundem modelo pequeno — limpar.

---

## Status

- [x] Contexto lido (b1, b2/prompts, models, acesso).
- [x] Decisões travadas (runner, juiz, aviso, gabarito b1).
- [x] Plano canônico escrito.
- [ ] Descoberta no servidor (aguarda aprovação do comando read-only).
- [ ] Construir bancos de perguntas (b1: 50 / b2: 50).
- [ ] Construir `run_bench.py` + KB OnCorretor.
- [ ] Rodar 24h + juiz Opus.
- [ ] Visualizadores b1.html / b2.html.
- [ ] Email de término.
