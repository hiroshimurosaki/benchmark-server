# B5 — conversa dinâmica: resultados

- Rodada: início 2026-09-25T17:38:02 · prazo 2026-09-25T19:38:02 · fim 2026-09-25T17:56:08
- Org `oncorretor-perfeita` · modelo `qwen3.6:35b-a3b` · threshold 0.8
- Conversas concluídas: **22** de 120 objetivos · julgadas: 22 · fallbacks opencode: 0
- Painel: `C:\Users\fernando.murusaki\benchmark-server\b5\painel_r6.html`

## Números

| Métrica | Valor |
|---|---|
| Cliente satisfeito (juiz) sim / parcial / não | 13 / 9 / 0 (59% sim) |
| Objetivo cumprido | 20/22 (91%) |
| Nota geral média | 7.05 |
| Nota de qualidade média | 6.16 |
| Escalonamento | adequado: 3, desnecessario: 1, faltou: 1, nao_se_aplica: 17 |
| Conversas com alucinação | 6/22 (27%) |
| Latência do turno do bot p50 / p95 / máx | 5.8s / 16.4s / 23.2s |
| Turnos por conversa (média) | 3.6 |
| Fonte das respostas (turnos) | rag: 35, gate:opening_question: 22, saudacao: 15, escalou: 4, faq: 2, gate:closure: 1 |

## Por trilha

| Trilha | n | cumprido | sat. sim | nota geral | alucinação |
|---|---|---|---|---|---|
| confuso_digitacao | 3 | 67% | 33% | 6.8 | 67% |
| faq_direta | 7 | 100% | 71% | 7.9 | 14% |
| follow_up_contextual | 4 | 100% | 75% | 7.6 | 25% |
| fora_do_escopo | 1 | 100% | 100% | 6.0 | 0% |
| multi_pergunta | 2 | 50% | 50% | 5.2 | 0% |
| rag_documento | 4 | 100% | 25% | 6.4 | 50% |
| reclamacao_irritado | 1 | 100% | 100% | 6.5 | 0% |

## 10 piores

| id | trilha | nota | satisf. | parada | problemas |
|---|---|---|---|---|---|
| [`multi-09`](painel.html#multi-09) | multi_pergunta | 4 | parcial | escalou | Menu de desambiguação sem relação com a pergunta, colado antes da resposta no turno 2; Ignorou a terceira parte da pergunta (redes sociais) na mensagem com várias perguntas; Transferiu para humano sem necessidade uma per |
| [`conf-07`](painel.html#conf-07) | confuso_digitacao | 5.5 | parcial | cliente_encerrou | Não informou o caminho completo Configurações Básicas > Informações Úteis; Inventou campos e locais ('Dados da Empresa', 'construtor do site') que não estão no material; Resposta do turno 2 prolixa e hesitante ('caso não |
| [`fora-10`](painel.html#fora-10) | fora_do_escopo | 6 | sim | cliente_encerrou | A recusa é genérica e não lista os serviços do OnCorretor (site, landing pages, e-mails, domínio, adesão, cobrança).; A mesma mensagem de recusa foi repetida depois que a cliente se despediu.; Faltou uma despedida cordia |
| [`rag-02`](painel.html#rag-02) | rag_documento | 6 | parcial | cliente_encerrou | Disse não ter informação sobre atualização de telefone, mas o documento a cobre explicitamente; Omitiu a orientação de enviar preferencialmente do e-mail cadastrado na adesão; Omitiu a validação de titularidade (contrato |
| [`follow-04`](painel.html#follow-04) | follow_up_contextual | 6 | parcial | cliente_encerrou | Turno 2 com afirmações fora do material (multa, regra do dia 20 invertida como garantia); Turno 4 categórico: omitiu a condição de que o valor precisa estar correto; Turno 4 restringiu 'cancelamento não realizado' a pedi |
| [`rag-10`](painel.html#rag-10) | rag_documento | 6 | parcial | max_turnos | Não falou em autenticação em dois fatores; Não falou em trocar a senha periodicamente (a cada seis meses); Não mandou verificar o remetente e o domínio; Afirmou sem base no documento que o suporte não solicita senhas por |
| [`rag-08`](painel.html#rag-08) | rag_documento | 6 | parcial | escalou | No turno 3 o bot disse que o assunto estava fora do escopo, embora o documento cubra o caso; Não pediu o print do erro depois que as recomendações falharam; A escalada só aconteceu porque a cliente pediu, e não por inici |
| [`multi-06`](painel.html#multi-06) | multi_pergunta | 6.5 | sim | cliente_encerrou | Turno 3: a pergunta sobre autenticação em duas etapas foi tratada como saudação e ficou sem resposta; Omitiu o passo de informar o token e clicar em 'Validar Token' e 'Ativar'; Instrução de leitura do QR Code imprecisa p |
| [`recl-01`](painel.html#recl-01) | reclamacao_irritado | 6.5 | sim | cliente_encerrou | Não escalou para humano, embora o comportamento esperado fosse escalar; Último turno é uma saudação genérica sem ligação com a conversa; Não explicou que pedidos até o dia 20 não geram nova cobrança; Não citou a possível |
| [`conf-04`](painel.html#conf-04) | confuso_digitacao | 6.5 | parcial | escalou | Cumprimentou com 'Boa tarde' depois de a cliente dizer 'bom dia'; Turno 4 trouxe a área /adm do site, fora do assunto e sem base no material; Respostas repetitivas e longas para WhatsApp; Não respondeu quanto tempo leva  |

## 10 melhores

| id | trilha | nota | satisf. | parada | destaques/obs. |
|---|---|---|---|---|---|
| [`faq-22`](painel.html#faq-22) | faq_direta | 8.5 | sim | cliente_encerrou | Saudação 'Boa tarde!' repetida no meio da conversa; Não comentou a resposta da cliente de que não sabia a SUSEP; Omitiu que os links de venda online do COL são exclusivos de produtos Porto Seguro |
| [`faq-09`](painel.html#faq-09) | faq_direta | 8.5 | sim | cliente_encerrou | A despedida da cliente foi classificada como saudação, e o bot respondeu 'Como posso ajudá-lo?' em vez de encerrar.; Tratou a cliente no masculino ('ajudá-lo').; No turno 2, repetiu 'Boa tarde!' depois de já ter cumprime |
| [`conf-03`](painel.html#conf-03) | confuso_digitacao | 8.5 | sim | cliente_encerrou | No turno final, o agradecimento foi classificado como saudação e recebeu uma resposta genérica fora de contexto; 'Boa tarde!' repetido no turno 2, depois de já ter cumprimentado; Crases (formato markdown) no e-mail do tu |
| [`faq-23`](painel.html#faq-23) | faq_direta | 8.5 | sim | cliente_encerrou | O agradecimento final foi classificado como saudação, e o bot perguntou 'Como posso ajudá-lo?' em vez de se despedir; O bot omitiu que todo atendimento gera um chamado para registro e acompanhamento; O bot repetiu a saud |
| [`follow-17`](painel.html#follow-17) | follow_up_contextual | 8.5 | sim | cliente_encerrou | No turno 3, o bot respondeu ao agradecimento com uma saudação genérica, como se reiniciasse a conversa; Usou 'ajudá-lo' no masculino com uma cliente mulher; Repetiu o 'Boa tarde' no turno 2 |
| [`follow-16`](painel.html#follow-16) | follow_up_contextual | 8.5 | sim | cliente_encerrou | No turno 3, respondeu ao agradecimento com uma saudação genérica, como se a conversa estivesse começando; Repetiu 'Boa tarde!' no turno 2, depois de já ter cumprimentado o cliente |
| [`faq-04`](painel.html#faq-04) | faq_direta | 8 | sim | cliente_encerrou | No turno 3, o bot respondeu ao agradecimento com uma saudação genérica, ignorando que a cliente estava encerrando; Tratou a cliente no masculino ('ajudá-lo'); Repetiu 'Boa tarde' no meio da conversa; Não acolheu a ansied |
| [`faq-03`](painel.html#faq-03) | faq_direta | 7.5 | parcial | escalou | Não informou o e-mail atendimento@oncorretor.com.br para confirmar a situação da inadimplência (item 6 do documento); A mensagem de transferência é genérica e não diz o que o atendente vai resolver; Chamou de 'SUSEP em i |
| [`rag-22`](painel.html#rag-22) | rag_documento | 7.5 | sim | cliente_encerrou | Incluiu dica de cache/Ctrl+F5 que não está no documento; A dica de cache não combina com o relato de erro ao salvar; Turno 3 respondeu ao agradecimento com saudação genérica, fora de contexto; Usou 'ajudá-lo' com cliente |
| [`follow-01`](painel.html#follow-01) | follow_up_contextual | 7.5 | sim | cliente_encerrou | O agradecimento final foi tratado como saudação ('Como posso ajudá-lo?'), sem encerrar a conversa.; O bot usou o masculino ('ajudá-lo') com uma cliente mulher.; O bot repetiu 'Boa tarde!' no meio da conversa, no turno 2. |

Transcrição completa de cada conversa: `painel.html` (abrir por file://) ou `resultados/conversas.jsonl`; veredito: `resultados/julgamentos.jsonl`.
