# B5 — conversa dinâmica: resultados

- Rodada: início 2026-09-25T17:12:44 · prazo 2026-09-25T19:12:44 · fim 2026-09-25T17:32:13
- Org `oncorretor-perfeita` · modelo `qwen3.6:35b-a3b` · threshold 0.8
- Conversas concluídas: **22** de 120 objetivos · julgadas: 22 · fallbacks opencode: 0
- Painel: `C:\Users\fernando.murusaki\benchmark-server\b5\painel_r5.html`

## Números

| Métrica | Valor |
|---|---|
| Cliente satisfeito (juiz) sim / parcial / não | 13 / 8 / 1 (59% sim) |
| Objetivo cumprido | 18/22 (82%) |
| Nota geral média | 6.50 |
| Nota de qualidade média | 5.85 |
| Escalonamento | adequado: 3, desnecessario: 3, faltou: 1, nao_se_aplica: 15 |
| Conversas com alucinação | 6/22 (27%) |
| Latência do turno do bot p50 / p95 / máx | 7.0s / 14.9s / 22.6s |
| Turnos por conversa (média) | 3.5 |
| Fonte das respostas (turnos) | rag: 29, gate:opening_question: 22, saudacao: 12, escalou: 6, faq: 5, gate:closure: 2 |

## Por trilha

| Trilha | n | cumprido | sat. sim | nota geral | alucinação |
|---|---|---|---|---|---|
| confuso_digitacao | 3 | 67% | 33% | 5.7 | 67% |
| faq_direta | 7 | 100% | 71% | 7.5 | 14% |
| follow_up_contextual | 4 | 100% | 75% | 8.0 | 25% |
| fora_do_escopo | 1 | 0% | 0% | 2.5 | 0% |
| multi_pergunta | 2 | 100% | 100% | 6.8 | 0% |
| rag_documento | 4 | 50% | 50% | 4.6 | 50% |
| reclamacao_irritado | 1 | 100% | 0% | 7.0 | 0% |

## 10 piores

| id | trilha | nota | satisf. | parada | problemas |
|---|---|---|---|---|---|
| [`rag-10`](painel.html#rag-10) | rag_documento | 1.5 | nao | max_turnos | Chamou de 'procedimento comum' um e-mail pedindo senha, o que reforça o risco de golpe; Turno 3 respondeu sobre logotipo, fora do contexto; Turno 4 tratou phishing como redefinição de senha; Não citou 2FA, troca periódic |
| [`rag-08`](painel.html#rag-08) | rag_documento | 2.5 | parcial | escalou | Transferiu para humano apesar de o documento (tópico 18) ter a resposta completa; Não indicou a aba anônima nem a troca de navegador; Não explicou as causas prováveis (cache, cookies, extensões); Não pediu o print do err |
| [`fora-10`](painel.html#fora-10) | fora_do_escopo | 2.5 | parcial | escalou | Não recusou com educação um pedido fora do escopo (imposto de renda); Não informou com o que pode ajudar (site, landing pages, e-mails, domínio, adesão, cobrança); Escalou por baixa confiança sem necessidade, ocupando um |
| [`conf-07`](painel.html#conf-07) | confuso_digitacao | 3.5 | parcial | escalou | Não citou o submenu Informações Úteis, que é o caminho correto; Inventou módulos 'Contato'/'Rodapé' como alternativa; Menu de desambiguação sem relação com a pergunta, misturado à resposta no turno 3; Ignorou duas vezes  |
| [`faq-03`](painel.html#faq-03) | faq_direta | 6 | parcial | max_turnos | No turno 3, falou de cancelamento voluntário quando o cliente queria continuar.; Não respondeu como falar com o gerente comercial.; Não perguntou se o cliente tinha outra SUSEP com produção ativa, o que ajudaria a regula |
| [`conf-04`](painel.html#conf-04) | confuso_digitacao | 6 | parcial | escalou | Saudação 'Boa tarde' incoerente com o 'bom dia' da cliente.; Não explicou claramente que 'seudominio' é um modelo a ser substituído até o turno 4.; Inventou passos de navegação no painel que não estão no material.; Turno |
| [`multi-09`](painel.html#multi-09) | multi_pergunta | 6.5 | sim | cliente_encerrou | Na primeira resposta, deixou sem resposta a pergunta sobre Instagram e Facebook, e a cliente teve de perguntar de novo; Link de ajuda repetido duas vezes na mesma mensagem; Passos genéricos e desnecessários para o favico |
| [`rag-02`](painel.html#rag-02) | rag_documento | 7 | sim | cliente_encerrou | Omitiu a recomendação de enviar do mesmo e-mail cadastrado na adesão; Não mencionou a validação de titularidade (contrato social/CPF) para envio a partir de outro e-mail; Não recomendou usar um e-mail externo (Gmail/Hotm |
| [`multi-06`](painel.html#multi-06) | multi_pergunta | 7 | sim | cliente_encerrou | Turno 3: o bot trouxe um menu de desambiguação sem relação com a pergunta sobre autenticação em duas etapas.; Turno 3: o bot não deu o passo a passo, que foi pedido explicitamente, e o cliente precisou perguntar de novo. |
| [`follow-01`](painel.html#follow-01) | follow_up_contextual | 7 | sim | cliente_encerrou | Afirmou que não há cláusula de fidelidade nem prazo mínimo, informação ausente do documento; Respondeu a despedida da cliente com uma saudação genérica no masculino; Saudações fora de contexto: 'Boa tarde!' no turno 2, ' |

## 10 melhores

| id | trilha | nota | satisf. | parada | destaques/obs. |
|---|---|---|---|---|---|
| [`follow-16`](painel.html#follow-16) | follow_up_contextual | 9.5 | sim | cliente_encerrou | Saudação 'Boa tarde!' repetida depois da saudação inicial; Não houve follow-up real: o bot antecipou toda a informação, e a trilha contextual não foi exercitada |
| [`follow-17`](painel.html#follow-17) | follow_up_contextual | 8 | sim | cliente_encerrou | Turno 3: agradecimento/encerramento tratado como saudação, com resposta genérica 'Como posso ajudá-lo?'; Turno 3: tratamento no masculino ('ajudá-lo') com uma cliente mulher; Turno 3: não confirmou o resumo correto da cl |
| [`faq-09`](painel.html#faq-09) | faq_direta | 8 | sim | cliente_encerrou | Despedida da cliente classificada como saudação; o bot respondeu 'Como posso ajudá-lo?' fora de contexto; Tratamento no masculino ('ajudá-lo') para uma cliente mulher; Saudação duplicada no turno 2 ('Boa tarde! 😊' e 'Olá |
| [`faq-23`](painel.html#faq-23) | faq_direta | 8 | sim | cliente_encerrou | Saudação duplicada no turno 2 ('Boa tarde!' + 'Olá!'); Turno 3: resposta de saudação genérica ao agradecimento e encerramento do cliente; Não houve despedida adequada |
| [`faq-22`](painel.html#faq-22) | faq_direta | 8 | sim | cliente_encerrou | Turno 3: o agradecimento foi tratado como saudação ('Como posso ajudá-lo?'), sem fechar a conversa; 'ajudá-lo' no masculino para uma cliente mulher; 'Boa tarde!' repetido no meio da conversa, no turno 2; O 'Sim' do iníci |
| [`faq-04`](painel.html#faq-04) | faq_direta | 7.5 | parcial | escalou | Transferência abrupta no turno 3, sem nenhuma orientação parcial; Não esclareceu que o gerente comercial é o da companhia/seguradora, algo que o texto ('junto à companhia') permitia sugerir; Turno 2 é uma cópia longa do  |
| [`follow-04`](painel.html#follow-04) | follow_up_contextual | 7.5 | parcial | cliente_encerrou | Turno 2 não diz como pedir o estorno (e-mail com extrato e comprovante) nem quando o estorno é possível; Saudação duplicada no turno 2 ('Boa tarde! 😊 Olá!'); Turno 2 fecha com orientação vaga ('painel', 'chamado interno' |
| [`faq-15`](painel.html#faq-15) | faq_direta | 7.5 | sim | cliente_encerrou | Turno 3 inclui detalhes fora do documento (código de 6 dígitos que muda a cada 30s, 'única forma de entrar'); Instruiu 'Ler código QR' para os dois apps; no Microsoft Authenticator a opção é 'Outro (Google, Facebook, etc |
| [`conf-03`](painel.html#conf-03) | confuso_digitacao | 7.5 | sim | cliente_encerrou | No turno 4, o bot respondeu ao agradecimento com uma saudação genérica em vez de se despedir; Não explicou por que precisava da SUSEP quando o cliente perguntou; Repetiu 'Boa tarde' no meio da conversa; O turno 3 repete  |
| [`rag-22`](painel.html#rag-22) | rag_documento | 7.5 | sim | cliente_encerrou | Dica de cache (Ctrl+F5/aba anônima) fora do documento e sem relação com o erro de edição; Turno 3 respondeu com uma saudação genérica em vez de agradecer e encerrar; Tratou a cliente no masculino ('ajudá-lo'); Repetiu o  |

Transcrição completa de cada conversa: `painel.html` (abrir por file://) ou `resultados/conversas.jsonl`; veredito: `resultados/julgamentos.jsonl`.
