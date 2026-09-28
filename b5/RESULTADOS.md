# B5 — conversa dinâmica: resultados

- Rodada: início 2026-09-28T08:27:21 · prazo 2026-09-28T10:27:21 · fim 2026-09-28T08:51:24
- Org `oncorretor-perfeita` · modelo `qwen3.6:35b-a3b` · threshold 0.8
- Conversas concluídas: **22** de 120 objetivos · julgadas: 22 · fallbacks opencode: 0
- Painel: `C:\Users\fernando.murusaki\benchmark-server\b5\painel_r8.html`

## Números

| Métrica | Valor |
|---|---|
| Cliente satisfeito (juiz) sim / parcial / não | 7 / 12 / 3 (32% sim) |
| Objetivo cumprido | 16/22 (73%) |
| Nota geral média | 5.79 |
| Nota de qualidade média | 5.36 |
| Escalonamento | adequado: 3, desnecessario: 5, nao_se_aplica: 14 |
| Conversas com alucinação | 2/22 (9%) |
| Latência do turno do bot p50 / p95 / máx | 10.3s / 27.1s / 46.2s |
| Turnos por conversa (média) | 3.4 |
| Fonte das respostas (turnos) | rag: 29, gate:opening_question: 22, saudacao: 10, escalou: 8, faq: 4, gate:closure: 1 |

## Por trilha

| Trilha | n | cumprido | sat. sim | nota geral | alucinação |
|---|---|---|---|---|---|
| confuso_digitacao | 3 | 33% | 0% | 3.2 | 0% |
| faq_direta | 7 | 71% | 57% | 6.4 | 14% |
| follow_up_contextual | 4 | 100% | 25% | 6.1 | 0% |
| fora_do_escopo | 1 | 100% | 0% | 6.0 | 0% |
| multi_pergunta | 2 | 50% | 0% | 5.0 | 0% |
| rag_documento | 4 | 75% | 50% | 6.8 | 0% |
| reclamacao_irritado | 1 | 100% | 0% | 5.0 | 100% |

## 10 piores

| id | trilha | nota | satisf. | parada | problemas |
|---|---|---|---|---|---|
| [`conf-07`](painel.html#conf-07) | confuso_digitacao | 1.5 | nao | escalou | Não entendeu a mensagem com erros de digitação ('imeil', 'cm troca la') e escalou por low_confidence; Não pediu esclarecimento antes de transferir; Não informou o caminho Configurações Básicas > Informações Úteis, que es |
| [`faq-03`](painel.html#faq-03) | faq_direta | 2 | nao | escalou | Escalou sem necessidade um caso respondido diretamente pela FAQ; Tratou a resposta ao gate da SUSEP ('não sei') como se fosse a pergunta e não retomou a dúvida original sobre inadimplência; Não explicou a causa do aviso  |
| [`conf-03`](painel.html#conf-03) | confuso_digitacao | 2 | nao | escalou | Escalou por low_confidence mesmo com FAQ específica para boleto suspeito de renovação de domínio; Não retomou a pergunta original depois do gate da SUSEP; Não orientou o cliente a não pagar nem a enviar o boleto para ate |
| [`multi-09`](painel.html#multi-09) | multi_pergunta | 3.5 | parcial | escalou | Não informou que as redes sociais ficam em Configurações Básicas > Informações Úteis, apesar de estar no documento e no FAQ; Tratou a pergunta múltipla de forma incompleta: das três dúvidas, respondeu duas; Turno 3 com c |
| [`recl-01`](painel.html#recl-01) | reclamacao_irritado | 5 | parcial | escalou | Não explicou a regra do dia 20: cancelamento pedido depois do dia 20 pode gerar uma última cobrança; Não informou os critérios de estorno (erro real na cobrança ou cancelamento pedido e não realizado); Pediu os dados err |
| [`faq-23`](painel.html#faq-23) | faq_direta | 5 | parcial | max_turnos | Turno 2 com desambiguação sem relação a um pedido claro de telefone; Gastou um turno extra com um cliente que disse ser urgente; Omitiu o e-mail atendimento@oncorretor.com.br e o chat, que estão na FAQ; Repetiu a saudaçã |
| [`follow-17`](painel.html#follow-17) | follow_up_contextual | 5.5 | parcial | escalou | Turno 3 com saudação genérica fora de contexto; Turno 4 usou o tópico errado (63 em vez do 64) e pediu print de uma 'mensagem de erro' que não existe; Não reforçou os testes de aba anônima e outro navegador antes de mand |
| [`follow-04`](painel.html#follow-04) | follow_up_contextual | 5.5 | parcial | cliente_encerrou | Não aplicou a regra do dia 20 ao caso concreto: com pedido feito até o dia 20, não deve haver nova mensalidade e o estorno é cabível; Repetiu a regra de após o dia 20 e o 'não utilizei', que não se aplicam ao que o clien |
| [`rag-10`](painel.html#rag-10) | rag_documento | 5.5 | parcial | cliente_encerrou | Passou só 1 das 4 recomendações de segurança do tópico 28; Faltaram autenticação em dois fatores, troca periódica de senha/senha forte e antivírus; Não respondeu diretamente se o e-mail tinha vindo do OnCorretor; Não lig |
| [`fora-10`](painel.html#fora-10) | fora_do_escopo | 6 | parcial | cliente_encerrou | Recusa genérica, sem listar os serviços do OnCorretor (site, landing pages, e-mails, domínio, adesão, cobrança); Não usou a resposta de FAQ disponível para consultoria fora do escopo; Saudação 'Bom dia' incoerente: a cli |

## 10 melhores

| id | trilha | nota | satisf. | parada | destaques/obs. |
|---|---|---|---|---|---|
| [`rag-22`](painel.html#rag-22) | rag_documento | 8.3 | sim | cliente_encerrou | Cumprimentou com 'Bom dia!' quando a cliente tinha dito 'boa tarde'; No turno 3, repetiu as instruções em vez de só se despedir; No turno 3, omitiu a informação 'em qual etapa o erro ocorreu'; Repetiu o link do portal de |
| [`faq-12`](painel.html#faq-12) | faq_direta | 8 | sim | cliente_encerrou | Cumprimentou com 'Bom dia' quando o cliente disse 'boa tarde'; Turno 3 repetiu informação sem necessidade no encerramento; Turno 3 atribuiu o custo do domínio ao Registro.br sem base no documento; Chamou de 'renovação an |
| [`faq-15`](painel.html#faq-15) | faq_direta | 8 | sim | cliente_encerrou | Diz 'Bom dia' duas vezes, quando o cliente cumprimentou com 'Boa tarde'; Responde ao agradecimento final com uma saudação genérica fora de contexto; A primeira resposta usa jargão técnico com um cliente leigo; Não explic |
| [`faq-04`](painel.html#faq-04) | faq_direta | 7.5 | parcial | escalou | Saudação 'Bom dia' quando a cliente disse 'boa tarde'; Resposta do turno 2 quase copiada do documento, pouco adaptada ao WhatsApp; Mensagem de transferência genérica, sem aproveitar a informação de que a regularização é  |
| [`rag-02`](painel.html#rag-02) | rag_documento | 7.5 | sim | cliente_encerrou | Cumprimenta com 'Bom dia' quando a cliente disse 'Boa tarde'; No turno 2 não informou o e-mail de destino, exigindo uma pergunta a mais; Omitiu a recomendação de usar e-mail externo (Gmail/Hotmail) no cadastro; No turno  |
| [`follow-16`](painel.html#follow-16) | follow_up_contextual | 7.5 | sim | cliente_encerrou | O bot respondeu a despedida do cliente com uma nova saudação, sem encerrar a conversa; Disse 'Bom dia' quando o cliente tinha dito 'boa tarde'; Texto do turno 2 copiado do documento, pouco adaptado ao tom informal do Wha |
| [`faq-09`](painel.html#faq-09) | faq_direta | 7.5 | sim | cliente_encerrou | Saudação 'Bom dia!' fora de contexto: a cliente disse 'boa tarde'; O agradecimento final foi classificado como saudação, e o bot respondeu com uma abertura genérica em vez de se despedir; Usou 'ajudá-lo' no masculino com |
| [`faq-22`](painel.html#faq-22) | faq_direta | 7 | sim | cliente_encerrou | Saudação 'Bom dia!' repetida fora de contexto nos turnos 2 e 3; O bot não reconheceu o agradecimento/encerramento e respondeu como se fosse uma conversa nova; Usou 'ajudá-lo' no masculino com uma cliente mulher; Não escl |
| [`multi-06`](painel.html#multi-06) | multi_pergunta | 6.5 | parcial | cliente_encerrou | Turno 3 respondeu só se a autenticação é obrigatória, sem explicar como ativar; Não mencionou os códigos de recuperação, que o painel gera uma única vez; Respondeu à despedida com saudação genérica ('Bom dia! Como posso  |
| [`rag-08`](painel.html#rag-08) | rag_documento | 6 | parcial | escalou | No turno 3, disse que o assunto estava fora do escopo quando o chamado era o passo seguinte que ele mesmo tinha orientado; Não orientou como enviar o print nem pediu domínio ou dados para o chamado; Só transferiu porque  |

Transcrição completa de cada conversa: `painel.html` (abrir por file://) ou `resultados/conversas.jsonl`; veredito: `resultados/julgamentos.jsonl`.
