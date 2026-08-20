# Plano — Benchmark de modelos locais (b1 + b2)

Doc canônico. Objetivo: descobrir o melhor modelo local (GGUF) para duas aplicações,
medindo tempo, tempo/qualidade sob paralelismo, qualidade da resposta e resistência a burla.

---

## Decisões travadas

1. **Runner**: ~~llama-server~~ → **Ollama** (revisado após descoberta: servidor não tem
   llama-server; tem Ollama já rodando, com endpoint OpenAI `/v1/chat/completions` na :11434,
   e gerencia carga/descarga de modelo na RAM sozinho). Os 13 GGUF do cache HF são registrados
   com `ollama create bench-<x> -f Modelfile` (`FROM <caminho.gguf>`).
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

## Hardware e roster real (descoberta 2026-08-18, servidor ianode / 10.10.10.151)

- **CORREÇÃO 2026-08-19: NÃO é CPU-only.** É um GMKtec EVO-X2, APU **AMD Ryzen AI Max+ 395
  (Strix Halo)** com **iGPU Radeon 8060S (RDNA 3.5, 40 CU)** + NPU XDNA, 64GB RAM unificada
  (~62 usável). A descoberta original só checou `nvidia-smi` e concluiu "CPU-only" — errado.
  O Ollama usa a iGPU via ROCm (62 tok/s num 4B, 40 num 20B = aceleração de GPU). A "VRAM" é
  fatia da RAM unificada. Modelos ≤~22GB rodam na iGPU; o **70B (41GB) força CPU** (`num_gpu 0`
  no Modelfile) porque um buffer ROCm único de 41GB estoura a fatia de VRAM.
- 32 cores, 62 GiB RAM, disco 1.3T livre. Cache HF = 223 GB.
- Runner: **Ollama** (`/usr/local/bin/ollama`), python3 e curl presentes. Sem llama-server/hf-cli.
- Ollama já tinha: `qwen3.6:35b-a3b` (22GB), `gpt-oss:20b` (13GB).
- **Modelos GGUF utilizáveis** (arquivo principal, ignorando `mmproj-*`):
  - barato (≤9B): LFM2.5-2.6B · Qwen3-4B · Llama-2-7b-ft · LlamaForecaster-8B · Qwen3.8-9B ·
    DeepSeek-V4-Pro-9B · Qwen3.5-9B-Defiant
  - médio (20–35B): gpt-oss:20b · Qwen3.8-27B · Qwen3.6-27B-MTP · Qwen3.6-27B-Fable ·
    Qwen3.6-35B-A3B (MoE) · qwen3.6:35b-a3b
  - pesado: **KafkaLM-70B-Q4** (~40GB, cabe). **Qwen3.5-122B-A10B DESCARTADO** (~68GB > 62GB RAM).
- Sem gguf usável (ignorados): MiniMax-H3, Qwen--3.5-122B (full), seedboxai-KafkaLM-70B (full),
  unsloth-DeepSeek-V4-Flash (download incompleto).
- Decisão: calibrar tok/s antes das 24h (CPU = vazão incerta).

## Convenções de calendário resolvidas (b1)

Âncoras: hoje = 2026-08-18 (**terça**), dataLastDay = 2026-08-15 (sábado), SMALL_SAMPLE_LIMIT = 30.
Semana = **segunda a domingo**:
- "semana passada" = 2026-08-10 .. 2026-08-16 (passa de dataLastDay → clamp p/ 15/08).
- "esta semana" = 2026-08-17 .. 2026-08-18 (ambos > dataLastDay → sem dado).
- "ontem" = 08-17 · "anteontem" = 08-16 · "este mês" = 08-01..08-18 · "julho" = 07-01..07-31.
- "últimos N dias" = janela terminando **ontem** (08-17), pois hoje é dia incompleto:
  últimos 3 = 08-15..08-17, 7 = 08-11..08-17, 15 = 08-03..08-17.
- "de 01 a 15 de agosto" = 08-01..08-15 (sem clamp).

## Status

- [x] Contexto lido (b1, b2/prompts, models, acesso).
- [x] Decisões travadas (runner, juiz, aviso, gabarito b1).
- [x] Plano canônico escrito.
- [x] Banco b1 (50) + `b1/schema_b1.json` — validado, correção de semana aplicada.
- [x] Banco b2 (50) + `b2/kb_oncorretor.md` — validado.
- [x] Descoberta no servidor (ver `server/command_log.md`: CPU-only, Ollama, calibração).
- [x] `run_bench.py` (orquestrador Ollama) — feito; +`--models` +`--limit` (smoke).
- [x] Corretor heurístico b1 (`score_b1.py`) — feito (selftest embutido).
- [ ] Juiz Opus b2 — **ADIADO** (decisão 2026-08-19: entregar b1 primeiro).
- [x] Smoke (2 rodadas) — pegou e corrigiu o bug de `num_predict` curto com thinking.
- [~] **Run completo b1 RODANDO** (lançado 2026-08-19 16:24 em tmux `bench`, 860 itens,
  ETA ~5-8h). Loop `dashboard_b1.py` regenera `dashboard_b1.json` a cada 120s.
- [x] Visualizadores: `b1.html` (resultado final) + **`dashboard_b1.html` (ao vivo)** +
  `dashboard_b1.py` (gerador) + `docs/*.png` (fluxogramas). `b2.html` adiado com o b2.

### RESULTADO b1 (2026-08-19, run completo 1470/1470)
- **Concluído**: 1470 respostas, 10 erros — todos de `llama3.3:70b` (HTTP 500 / OOM na VRAM,
  puxado do registry sem `num_gpu 0`). Os outros 29 modelos: 0 erros. Pendência: re-rodar o
  llama3.3:70b em CPU (decisão do Fernando) ou deixar marcado como falho.
- **Top por nota:** qwen36-27b-fable 88.2 · defiant-9b 87.4 · qwen38-27b 86.5 · gemma2:9b 85.3.
- **Pick prático (velocidade+custo+consistência):** **q4b (Qwen3-4B)** — nota 82.6, **60 tok/s,
  2.4GB, eficiência 34.4** (2× o próximo). Os 27B no topo custam 6-7× por ~5 pontos.
- **Achado que muda arquitetura:** a checagem "Datas/args exatos" fica em **46% no roster
  inteiro** (fraqueza sistêmica, não só do q4b). "Não inventa números" em 47% (segurança).
  → Resolver **datas em código** (parser determinístico) vale mais que trocar de modelo.
- **Cuidado:** os campeões de nota (fable-27b, defiant-9b) são merges uncensored/heretic —
  bons no b1, perigosos pro b2 (guardrails). Não usar em produção com regras.
- Dashboard passou a expor `models[].checks` + `checks_resumo` (acerto por tipo de checagem).

### Dashboard v3 — decisões de design (2026-08-19)
- **Um dashboard só** (`dashboard_b1.html`) serve run parcial E resultado final —
  `dashboard_b1.json` é superconjunto do `scored_b1.json`. **`b1.html` aposentado.**
- **Metadados por modelo** puxados via `ollama show` (sem inferência, não atrapalha o run):
  params, quant, context length, arch → cache em `model_meta.json`. Habilita eixo de custo
  contínuo (não só tier) e eficiência = nota/GB.
- **Telemetria** via `sysmon.py` (loop tmux `sysmon`, amostra a cada 20s → `sysmon.jsonl`):
  RAM/VRAM/CPU + modelo carregado + GPU/CPU. Alimenta painel servidor + footprint por modelo.
- **3 visualizações** do trade-off qualidade×custo (dispersão / ranking / quadrantes) +
  progresso enriquecido (ficha técnica + pontuação parcial) + refino anti-slop (ícones SVG,
  1 acento, fonte display). Conceitos no canvas /design: artifact e9736813.
- Loops no servidor: tmux `bench` (run), `sysmon` (telemetria 20s), `dash` (dashboard 60s).
- Auto-refresh no PC: `sync_dashboard.bat` (scp 15s) + File System Access API no HTML.

### 2ª leva de modelos (2026-08-19) — comparação estendida
- +16 modelos oficiais adicionados ao `models.jsonl` (mantidos os originais p/ comparar):
  Qwen2.5 (3b/7b/14b/32b + coder-7b), Llama (3.2-3b/3.1-8b/3.3-70b), Gemma2 (9b/27b),
  Mistral 7b + Nemo-12b, Granite3.1-8b, Hermes3-8b, Phi-4-14b, Command-R-35b (RAG→b2).
  Todos `thinking:false` (não têm toggle de thinking). Total previsto: **1470 itens**.
- Baixam via `ollama pull` (registro Ollama) em tmux `pull` (`pull_extra_models.sh`, ~30MB/s).
- **Orquestração autônoma:** tmux `wave2` espera o run atual E o pull terminarem
  (`tmux has-session bench`/`pull`), aí dispara `run_bench` de novo — resume pula os já feitos
  e roda só os 16 novos. Sem corrida (um `run_bench` por vez). Roda de madrugada sozinho.
- **Velocidade** virou métrica de 1ª classe: `tok_s` por modelo no gerador; a dispersão do
  dashboard virou **2D configurável** (eixos X/Y à escolha + tamanho=velocidade + presets).

### Operação do run (para retomar de outra conversa)
- Acesso via chave: `ssh -i ~/.ssh/id_benchmark nicolas.benedetti@10.10.10.151` (senha
  Mudar@123 continua válida; a chave privada está no PC do Fernando).
- Acompanhar: `tmux attach -t bench` ou `tail -f ~/benchmark/run_console.log`.
- Resultados: `~/benchmark/results_b1.jsonl` (append-only, resumível: matar e relançar
  `python3 run_bench.py --root . --bench b1` retoma de onde parou).
- Dashboard ao vivo: `scp` do `~/benchmark/dashboard_b1.json` pro PC e recarregar no
  `dashboard_b1.html` (file:// não faz auto-poll).
- Fim: `scp results_b1.jsonl` → `python3 score_b1.py` → `scored_b1.json` → abrir `b1.html`.

## As-built / handoff (2026-08-19) — foco b1

Decisões desta sessão (não estavam no plano):
- **Escopo reduzido a b1** por ora (Fernando). b2 (prompt ANSWER, juiz Opus, `b2.html`)
  fica para rodada futura. Motivo prático: o `ANSWER_PROMPT` real (`prompt.py`) não está no
  repo — só a referência. b1 é autossuficiente.
- **Smoke antes das 24h**: `models_smoke.jsonl` (3 modelos) + `--limit N` no `run_bench.py`
  validam pipeline e medem tok/s real antes de comprometer 24h.
- **Aviso de término por email caiu**; Claude reporta o leaderboard quando os resultados
  voltarem por scp.

Arquivos novos/alterados (b1):
- `runner/prompts/b1_system.txt` — system do b1 (traduzido de `b1/b1.txt`; placeholders
  `{today}`/`{dataLastDay}`/`{small_sample_limit}` interpolados pelo runner).
- `runner/models.jsonl` — roster completo b1 (14 tags Ollama; `thinking` on nos Qwen3.x/gpt-oss).
- `runner/models_smoke.jsonl` — subconjunto de 3 p/ smoke.
- `runner/register_models.sh` — `ollama create bench-<x>` a partir dos GGUF do cache HF
  (idempotente; `--smoke` registra só os do smoke). Roda NO servidor.
- `runner/run_bench.py` — +flags `--models`, `--limit`; carga de dados guardada por bench
  (com `--bench b1` não exige arquivos de b2).

Verificação: edits conferidos por leitura. **Selftest/dry-run NÃO rodados localmente**
(este PC não tem Python real, só o stub da Store) — rodam no servidor como 1º passo (dry-run
antes do smoke). `score_b1.py --selftest` deve passar lá.

Achados que contrariam expectativa:
- **KafkaLM-70B (pesado): calibração deu 0 tok/s / load 0s** — provável falha de load.
  Marcado em `models.jsonl`; verificar `ollama run bench-kafka70b` antes das 24h. Tier pesado
  em risco (pode ficar sem modelo).
- GGUFs experimentais (DeepSeek-V4-Pro-9B, Defiant-9B) podem falhar no load do Ollama; o
  runner captura exceção por item e segue (não derruba o run).

### Pendências
**Decisão do Fernando:**
- Chave da API Anthropic + teto de custo — só quando reabrir o **b2** (juiz Opus).
- b2: âncora "boleto" escopada a domínio (mensalidade só desconto SUSEP). Conferir ao reabrir b2.
- b1: convenção "últimos N dias termina ontem" — já aplicada no schema; confirmar.

**Dívida técnica:**
- Rodar `score_b1.py --selftest` e `run_bench --dry-run` no servidor (falta ambiente Python local).
- Confirmar suporte real a `think` por modelo (flags em `models.jsonl` são estimativa).
