# B5 — conversa dinâmica: resultados

- Rodada: início 2026-09-30T11:29:38 · prazo 2026-09-30T13:29:38 · fim 2026-09-30T12:09:41
- Org `oncorretor-perfeita` · modelo `qwen3.6:35b-a3b` · threshold 0.8
- Conversas concluídas: **22** de 120 objetivos · julgadas: 21 · fallbacks opencode: 22
- Painel: `C:\Users\fernando.murusaki\benchmark-server\b5\painel_r11.html`

## Números

| Métrica | Valor |
|---|---|
| Cliente satisfeito (juiz) sim / parcial / não | 3 / 17 / 1 (14% sim) |
| Objetivo cumprido | 17/21 (81%) |
| Nota geral média | 6.57 |
| Nota de qualidade média | 7.22 |
| Escalonamento | adequado: 2, desnecessario: 2, faltou: 1, nao_se_aplica: 16 |
| Conversas com alucinação | 0/21 (0%) |
| Latência do turno do bot p50 / p95 / máx | 6.9s / 15.8s / 21.9s |
| Turnos por conversa (média) | 3.7 |
| Fonte das respostas (turnos) | rag: 44, gate:opening_question: 22, saudacao: 6, faq: 5, escalou: 4, gate:closure: 1 |

## Por trilha

| Trilha | n | cumprido | sat. sim | nota geral | alucinação |
|---|---|---|---|---|---|
| confuso_digitacao | 3 | 100% | 33% | 7.3 | 0% |
| faq_direta | 6 | 67% | 0% | 5.9 | 0% |
| follow_up_contextual | 4 | 100% | 25% | 8.2 | 0% |
| fora_do_escopo | 1 | 0% | 0% | 4.0 | 0% |
| multi_pergunta | 2 | 50% | 0% | 4.5 | 0% |
| rag_documento | 4 | 100% | 25% | 7.5 | 0% |
| reclamacao_irritado | 1 | 100% | 0% | 4.5 | 0% |

## 10 piores

| id | trilha | nota | satisf. | parada | problemas |
|---|---|---|---|---|---|
| [`faq-22`](painel.html#faq-22) | faq_direta | 2.5 | nao | max_turnos | Não respondeu se pode colocar logos de outras seguradoras; Não informou sem custo adicional; Não informou Configurações Avançadas > Gerenciador de Página para logos; Menu de desambiguacao irrelevante no turno 2 |
| [`multi-09`](painel.html#multi-09) | multi_pergunta | 2.5 | parcial | escalou | Transferência desnecessária para Instagram/Facebook com resposta no documento; Objetivo parcial: faltou caminho das redes sociais em Informações Úteis; Turno 2 repetitivo e verboso para WhatsApp |
| [`faq-09`](painel.html#faq-09) | faq_direta | 2.5 | parcial | escalou | Turno 3 recusou ajudar e trocou dúvida do Clube VIP por tutorial de pop-ups; Não reconfirmou gratuidade já explicada quando cliente pediu confirmação; Escalou por low_confidence quando o FAQ continha a resposta |
| [`fora-10`](painel.html#fora-10) | fora_do_escopo | 4 | parcial | max_turnos | Não listou com o que pode ajudar: site, landing pages, e-mails, domínio, adesão e cobrança; Repetiu resposta genérica no turno 3 sem responder pergunta direta; Saudação errada: Bom dia após cliente dizer boa tarde |
| [`recl-01`](painel.html#recl-01) | reclamacao_irritado | 4.5 | parcial | cliente_encerrou | Não escalou reclamação irritada de estorno quando o esperado era escalar; Repetiu 3x mesma instrução sem avançar nem acolher 'cancelei antes do dia 20'; Não corrigiu 'cobrança no cartão' — cobrança é desconto em comissão |
| [`conf-04`](painel.html#conf-04) | confuso_digitacao | 5.5 | parcial | max_turnos | Turno 3 trocou senha de e-mail por telefone/endereço do site; Turno 4 pediu para repetir dúvida já explicitada duas vezes |
| [`rag-10`](painel.html#rag-10) | rag_documento | 6.5 | parcial | max_turnos | Turno 3 oferece opções irrelevantes e ignora a pergunta; Turno 2 incompleto frente ao tópico 28; Cliente precisou repetir a dúvida sobre link clicado; Recomendação de manter antivírus atualizado não foi entregue |
| [`multi-06`](painel.html#multi-06) | multi_pergunta | 6.5 | parcial | cliente_encerrou | Resposta sobre 2FA inicial superficial exigiu repetição; Passo a passo omitiu Validar Token/Ativar e data 20/02/2024; Turno 4 longo, duplicado e com triplo link de portal; Encerramento com saudação genérica em vez de des |
| [`rag-02`](painel.html#rag-02) | rag_documento | 7 | parcial | cliente_encerrou | Turno 2 diz não ter info sobre telefone após orientar sobre telefone; Turno 4 reinicia com 'Como posso ajudá-lo?' após cliente encerrar |
| [`rag-08`](painel.html#rag-08) | rag_documento | 7 | parcial | escalou | Não respondeu se chamado estava aberto nem sobre prazo; Repetiu saudação e link do portal em turnos seguidos; Mensagem de transferência genérica sem confirmar próximo passo do print |

## 10 melhores

| id | trilha | nota | satisf. | parada | destaques/obs. |
|---|---|---|---|---|---|
| [`follow-16`](painel.html#follow-16) | follow_up_contextual | 10 | sim | cliente_encerrou | Informou onde consultar: área de Contatos do painel administrativo; Esclareceu que não há envio automático para Porto Seguro; Antecipou a segunda dúvida já no turno 2, resolvendo com eficiência |
| [`rag-22`](painel.html#rag-22) | rag_documento | 9.5 | sim | cliente_encerrou | Informou destino e lista completa de uma vez; Confirmação final manteve fidelidade ao documento |
| [`conf-07`](painel.html#conf-07) | confuso_digitacao | 9 | sim | cliente_encerrou | Turno 2 diz só 'Configurações Básicas' sem 'Informações Úteis'; Turno 2 responde 'Bom dia' após cliente dizer 'boa tarde' |
| [`faq-04`](painel.html#faq-04) | faq_direta | 8.0 | parcial | max_turnos | Turno 2 colou FAQ sem contextualizar 'outra SUSEP com produção ativa'; Conversa terminou por max_turnos sem fechamento de entendimento |
| [`follow-04`](painel.html#follow-04) | follow_up_contextual | 8 | parcial | cliente_encerrou | Turno final reinicia atendimento em vez de encerrar |
| [`conf-03`](painel.html#conf-03) | confuso_digitacao | 7.5 | parcial | cliente_encerrou | Turno 3 repete resposta anterior sem confirmação ou encerramento |
| [`faq-03`](painel.html#faq-03) | faq_direta | 7.5 | parcial | escalou | Transferiu na pergunta final sobre contato do gerente sem tentativa de orientação |
| [`follow-17`](painel.html#follow-17) | follow_up_contextual | 7.5 | parcial | cliente_encerrou | Turno 3 repete a mesma orientacao em dois paragrafos seguidos; Nao confirma de forma concisa o entendimento da cliente; Troca de saudacao: Bom dia apos cliente dizer boa tarde |
| [`follow-01`](painel.html#follow-01) | follow_up_contextual | 7.5 | parcial | cliente_encerrou | Turno 4 com saudação genérica fora de contexto após cliente agradecer |
| [`faq-23`](painel.html#faq-23) | faq_direta | 7.5 | parcial | cliente_encerrou | Turno 3 repete saudação em vez de confirmar encerramento; Troca de período: cliente disse boa tarde, bot respondeu bom dia |

Transcrição completa de cada conversa: `painel.html` (abrir por file://) ou `resultados/conversas.jsonl`; veredito: `resultados/julgamentos.jsonl`.
