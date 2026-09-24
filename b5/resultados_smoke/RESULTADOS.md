# B5 — conversa dinâmica: resultados

- Rodada: início 2026-09-24T16:04:57 · prazo 2026-09-24T21:04:57 · fim 2026-09-24T16:05:59
- Org `oncorretor-perfeita` · modelo `qwen3.6:35b-a3b` · threshold 0.8
- Conversas concluídas: **1** de 120 objetivos · julgadas: 1 · fallbacks opencode: 0
- Painel: `C:\Users\fernando.murusaki\benchmark-server\b5\resultados_smoke\painel.html`

## Números

| Métrica | Valor |
|---|---|
| Cliente satisfeito (juiz) sim / parcial / não | 0 / 0 / 1 (0% sim) |
| Objetivo cumprido | 0/1 (0%) |
| Nota geral média | 1.00 |
| Nota de qualidade média | 2.50 |
| Escalonamento | nao_se_aplica: 1 |
| Conversas com alucinação | 0/1 (0%) |
| Latência do turno do bot p50 / p95 / máx | 7.3s / 10.8s / 11.2s |
| Turnos por conversa (média) | 4.0 |
| Fonte das respostas (turnos) | gate:opening_question: 2, rag: 2 |

## Por trilha

| Trilha | n | cumprido | sat. sim | nota geral | alucinação |
|---|---|---|---|---|---|
| rag_documento | 1 | 0% | 0% | 1.0 | 0% |

## 10 piores

| id | trilha | nota | satisf. | parada | problemas |
|---|---|---|---|---|---|
| [`rag-02`](painel.html#rag-02) | rag_documento | 1 | nao | max_turnos | Não informou em nenhum momento o e-mail atendimento@oncorretor.com.br nem o procedimento de alteração cadastral; Mandou dois menus de desambiguação duplicados e irrelevantes na mesma mensagem; Ignorou a escolha explícita |

## 10 melhores

| id | trilha | nota | satisf. | parada | destaques/obs. |
|---|---|---|---|---|---|
| [`rag-02`](painel.html#rag-02) | rag_documento | 1 | nao | max_turnos | Não informou em nenhum momento o e-mail atendimento@oncorretor.com.br nem o procedimento de alteração cadastral; Mandou dois menus de desambiguação duplicados e irrelevantes na mesma mensagem; Ignorou a escolha explícita |

Transcrição completa de cada conversa: `painel.html` (abrir por file://) ou `resultados/conversas.jsonl`; veredito: `resultados/julgamentos.jsonl`.
