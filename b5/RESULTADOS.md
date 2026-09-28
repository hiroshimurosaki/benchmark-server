# B5 — conversa dinâmica: resultados

- Rodada: início 2026-09-28T09:25:23 · prazo 2026-09-28T11:25:23 · fim 2026-09-28T09:58:50
- Org `oncorretor-perfeita` · modelo `qwen3.6:35b-a3b` · threshold 0.8
- Conversas concluídas: **22** de 120 objetivos · julgadas: 21 · fallbacks opencode: 45
- Painel: `C:\Users\fernando.murusaki\benchmark-server\b5\painel_r10.html`

## Números

| Métrica | Valor |
|---|---|
| Cliente satisfeito (juiz) sim / parcial / não | 8 / 9 / 4 (38% sim) |
| Objetivo cumprido | 12/21 (57%) |
| Nota geral média | 5.43 |
| Nota de qualidade média | 5.63 |
| Escalonamento | adequado: 2, desnecessario: 2, faltou: 2, nao_se_aplica: 15 |
| Conversas com alucinação | 8/21 (38%) |
| Latência do turno do bot p50 / p95 / máx | 7.0s / 13.3s / 18.3s |
| Turnos por conversa (média) | 3.7 |
| Fonte das respostas (turnos) | rag: 40, gate:opening_question: 22, saudacao: 12, escalou: 4, faq: 3, gate:closure: 1 |

## Por trilha

| Trilha | n | cumprido | sat. sim | nota geral | alucinação |
|---|---|---|---|---|---|
| confuso_digitacao | 3 | 0% | 0% | 2.8 | 100% |
| faq_direta | 6 | 50% | 50% | 5.5 | 50% |
| follow_up_contextual | 4 | 100% | 75% | 7.1 | 0% |
| fora_do_escopo | 1 | 100% | 0% | 5.5 | 0% |
| multi_pergunta | 2 | 50% | 0% | 4.0 | 0% |
| rag_documento | 4 | 75% | 50% | 6.8 | 25% |
| reclamacao_irritado | 1 | 0% | 0% | 3.5 | 100% |

## 10 piores

| id | trilha | nota | satisf. | parada | problemas |
|---|---|---|---|---|---|
| [`faq-03`](painel.html#faq-03) | faq_direta | 1.5 | nao | escalou | O FAQ direto (oLM2w5c1u7t9qQ7ITWa6) não foi usado; a resposta veio do RAG com conteúdo inventado.; Disse que era preciso pagar faturas ou boleto, o que contradiz a cobrança feita só por desconto na comissão.; Inventou um |
| [`conf-07`](painel.html#conf-07) | confuso_digitacao | 1.5 | nao | max_turnos | Nunca informou o caminho correto: Configurações Básicas > Informações Úteis; Leu a pergunta como troca do e-mail de login; Inventou que o e-mail de contato do site se configura no painel de e-mails; Mandou o cliente para |
| [`conf-03`](painel.html#conf-03) | confuso_digitacao | 2 | nao | max_turnos | Recuou após alerta correto e não reafirmou não pagar antes de conferir; Turno 4 trocou boleto por troca de senha; Não adaptou explicação para idoso sem habilidade com e-mail; Resposta final se eximiu em vez de resolver |
| [`multi-09`](painel.html#multi-09) | multi_pergunta | 2 | nao | escalou | Não entregou nenhum dos 3 caminhos: favicon, botão 'Simule e Contrate', redes sociais; Escalonamento desnecessário com resposta disponível no FAQ/documento; Errou o período do dia na saudação do turno 2 |
| [`faq-12`](painel.html#faq-12) | faq_direta | 3 | parcial | cliente_encerrou | Garantiu que não haveria cobrança num pedido feito depois do dia 20, contrariando o documento; Criou uma exceção de 'não houve uso efetivo' que não existe no documento; Não avisou que o domínio registrado pelo OnCorretor |
| [`rag-10`](painel.html#rag-10) | rag_documento | 3.5 | parcial | cliente_encerrou | A busca no documento falhou: o bot negou ter informação que está no tópico 28; Não passou as recomendações de segurança (remetente, 2FA, senhas fortes e periódicas, antivírus); Não confirmou claramente que o e-mail era g |
| [`recl-01`](painel.html#recl-01) | reclamacao_irritado | 3.5 | parcial | cliente_encerrou | Não escalou, embora o esperado fosse transferir para um atendente; O turno 4 contradiz o documento: diz que não há regra para pedidos até o dia 20 (o documento diz que não há novas cobranças); O turno 4 diz que o extrato |
| [`faq-04`](painel.html#faq-04) | faq_direta | 4 | parcial | max_turnos | Confundiu bloqueio de SUSEP com política de bloqueio de envio de e-mail do Skymail; Associou bloqueio indevidamente a envio em massa/webmail vs Outlook; Não reforçou procurar gerente comercial após cliente dizer que não  |
| [`conf-04`](painel.html#conf-04) | confuso_digitacao | 5 | parcial | escalou | Ignorou que a cliente não consegue enviar e-mail e repetiu a mesma orientação; Não sugeriu enviar o pedido de outro e-mail (Gmail ou Hotmail) nem citou telefone e WhatsApp oficiais; Não informou que no webmail o usuário  |
| [`fora-10`](painel.html#fora-10) | fora_do_escopo | 5.5 | parcial | cliente_encerrou | Recusa genérica, sem listar o que o OnCorretor oferece (site, landing pages, e-mails, domínio, adesão, cobrança); Não usou a resposta da FAQ de fora do escopo nem o tópico 68 do documento; Disse "Bom dia" quando a client |

## 10 melhores

| id | trilha | nota | satisf. | parada | destaques/obs. |
|---|---|---|---|---|---|
| [`faq-23`](painel.html#faq-23) | faq_direta | 9.5 | sim | cliente_encerrou | Entregou os 4 itens do objetivo em uma única resposta correta; SUSEP e encerramento conduzidos sem atrito |
| [`rag-22`](painel.html#rag-22) | rag_documento | 9 | sim | cliente_encerrou | Saudação 'Bom dia' após cliente dizer 'boa tarde'; Turno 3 adiciona checklist genérico após resolução já confirmada |
| [`faq-15`](painel.html#faq-15) | faq_direta | 8 | sim | cliente_encerrou | Omite etapas Validar Token e Ativar do gabarito; Encerramento com saudação genérica em vez de despedida |
| [`follow-17`](painel.html#follow-17) | follow_up_contextual | 8 | sim | cliente_encerrou | Disse 'Bom dia' quando a cliente tinha cumprimentado com 'boa tarde'; No último turno, respondeu ao agradecimento com uma saudação genérica, como se a conversa estivesse começando; Usou 'ajudá-lo' (masculino) com uma cli |
| [`follow-16`](painel.html#follow-16) | follow_up_contextual | 7.5 | sim | cliente_encerrou | No turno 3, a despedida do cliente foi tratada como saudação e o bot respondeu 'Como posso ajudá-lo?' em vez de encerrar; Respondeu 'Bom dia' quando o cliente disse 'boa tarde'; Repetiu a saudação no turno 2, depois do g |
| [`rag-02`](painel.html#rag-02) | rag_documento | 7.5 | sim | cliente_encerrou | Turno 3 reinicia conversa em vez de encerrar; Omitiu validação de titularidade se e-mail remetente for diferente; Omitiu recomendação de e-mail externo Gmail/Hotmail; Saudação com período errado: responde Bom dia a Boa t |
| [`rag-08`](painel.html#rag-08) | rag_documento | 7 | parcial | escalou | Disse 'Bom dia' quando a cliente tinha dito 'boa tarde'; Erro de digitação 'travessa' no lugar de 'trava'; Link do portal de ajuda repetido em turnos seguidos; Mensagem de transferência genérica, sem reconhecer a urgênci |
| [`faq-09`](painel.html#faq-09) | faq_direta | 7 | sim | cliente_encerrou | Turno 3 não encerra a conversa, reinicia com saudação genérica; Saudação com período errado em turnos 2 e 3 (Bom dia vs Boa tarde) |
| [`follow-01`](painel.html#follow-01) | follow_up_contextual | 7 | sim | cliente_encerrou | Turno 2 impõe menu desnecessário em vez de responder adesão; Turno 3 omite preço, taxa, produção mínima e forma de cobrança da adesão; Turno 5 ignora encerramento e repete saudação genérica |
| [`multi-06`](painel.html#multi-06) | multi_pergunta | 6 | parcial | cliente_encerrou | No turno 3, mandou os passos da cotação Segfy em vez da ativação da autenticação em duas etapas; Não avisou para guardar os códigos de recuperação, que não podem ser consultados depois; Não informou o endereço painel.seu |

Transcrição completa de cada conversa: `painel.html` (abrir por file://) ou `resultados/conversas.jsonl`; veredito: `resultados/julgamentos.jsonl`.
