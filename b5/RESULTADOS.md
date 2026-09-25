# B5 — conversa dinâmica: resultados

- Rodada: início 2026-09-25T15:38:19 · prazo 2026-09-25T17:38:19 · fim 2026-09-25T15:59:32
- Org `oncorretor-perfeita` · modelo `qwen3.6:35b-a3b` · threshold 0.8
- Conversas concluídas: **22** de 120 objetivos · julgadas: 22 · fallbacks opencode: 0
- Painel: `C:\Users\fernando.murusaki\benchmark-server\b5\painel_r4.html`

## Números

| Métrica | Valor |
|---|---|
| Cliente satisfeito (juiz) sim / parcial / não | 11 / 11 / 0 (50% sim) |
| Objetivo cumprido | 18/22 (82%) |
| Nota geral média | 6.49 |
| Nota de qualidade média | 6.03 |
| Escalonamento | adequado: 1, desnecessario: 2, faltou: 3, nao_se_aplica: 16 |
| Conversas com alucinação | 6/22 (27%) |
| Latência do turno do bot p50 / p95 / máx | 7.2s / 12.0s / 19.2s |
| Turnos por conversa (média) | 3.8 |
| Fonte das respostas (turnos) | rag: 42, gate:opening_question: 22, saudacao: 10, gate:closure: 4, escalou: 3, faq: 2 |

## Por trilha

| Trilha | n | cumprido | sat. sim | nota geral | alucinação |
|---|---|---|---|---|---|
| confuso_digitacao | 3 | 67% | 0% | 5.0 | 67% |
| faq_direta | 7 | 100% | 71% | 8.0 | 14% |
| follow_up_contextual | 4 | 100% | 75% | 7.6 | 25% |
| fora_do_escopo | 1 | 0% | 0% | 2.5 | 0% |
| multi_pergunta | 2 | 0% | 0% | 3.0 | 50% |
| rag_documento | 4 | 100% | 75% | 7.1 | 25% |
| reclamacao_irritado | 1 | 100% | 0% | 4.5 | 0% |

## 10 piores

| id | trilha | nota | satisf. | parada | problemas |
|---|---|---|---|---|---|
| [`fora-10`](painel.html#fora-10) | fora_do_escopo | 2.5 | parcial | escalou | Não recusou o pedido fora do escopo (imposto de renda); Não informou com o que o OnCorretor pode ajudar (site, landing pages, e-mails, domínio, adesão, cobrança); Transferiu para humano sem necessidade, por baixa confian |
| [`conf-07`](painel.html#conf-07) | confuso_digitacao | 2.5 | parcial | escalou | Não citou Configurações Básicas > Informações Úteis, que está no documento e no FAQ; Não passou a orientação de cache (Ctrl+F5, aba anônima, outro navegador); Afirmou não ter a informação que estava no material; Turno 4  |
| [`multi-09`](painel.html#multi-09) | multi_pergunta | 3 | parcial | escalou | Ignorou a pergunta sobre Instagram/Facebook, que a FAQ responde (Informações Úteis); Turno 2 repetitivo, com o link do portal duplicado; Não deixou explícito que favicon e botão ficam na mesma tela; Turno 3 com desambigu |
| [`multi-06`](painel.html#multi-06) | multi_pergunta | 3 | parcial | cliente_encerrou | Negou que exista regra de senha, contradizendo o documento e o FAQ (6 caracteres, 3 de 4 requisitos); Não informou que a autenticação em duas etapas é obrigatória (desde 20/02/2024); Passo a passo sem a etapa de informar |
| [`recl-01`](painel.html#recl-01) | reclamacao_irritado | 4.5 | parcial | cliente_encerrou | Não escalou para humano, como era esperado, mesmo com cliente irritado pedindo verificação no sistema; Turno 3 repetiu o procedimento de cancelamento para quem já tinha cancelado; Omitiu a parte da regra que diz que canc |
| [`rag-08`](painel.html#rag-08) | rag_documento | 5 | parcial | cliente_encerrou | Inventou o e-mail atendimento@oncorretor.com.br, que não está no documento; Não ofereceu atendente humano quando a cliente pediu, mesmo sendo caso urgente de chamado para o Nível 3; Não pediu o print pelo próprio chat, c |
| [`conf-03`](painel.html#conf-03) | confuso_digitacao | 5.5 | parcial | cliente_encerrou | Turno 2 negou ter informação que o documento contém; Turno 2 sugeriu pagar antes do vencimento diante de um boleto possivelmente falso; Afirmações fora do material: descontos, área de cliente, perda do domínio; Pedido ex |
| [`follow-01`](painel.html#follow-01) | follow_up_contextual | 6.5 | sim | cliente_encerrou | Omitiu a mensalidade de R$ 52,50 e a ausência de taxa de adesão; Omitiu o requisito de produção mínima de R$ 100 na Porto Seguro; Saudação duplicada no turno 2; Disse não ter informação sobre fidelidade, quando podia ded |
| [`faq-12`](painel.html#faq-12) | faq_direta | 6.5 | parcial | max_turnos | No turno 2 o bot disse que não tinha a informação, embora exista uma FAQ específica.; Citou 'regras de estorno para períodos já cobrados', que não aparecem no documento.; Nunca afirmou de forma explícita que dá para canc |
| [`follow-04`](painel.html#follow-04) | follow_up_contextual | 6.5 | parcial | cliente_encerrou | Não perguntou a data do pedido para aplicar a regra do dia 20 ao caso do cliente; Afirmou algo que não está no documento: pedido até o dia 20 (inclusive) não gera novas cobranças; Esticou a FAQ de renovação de domínio al |

## 10 melhores

| id | trilha | nota | satisf. | parada | destaques/obs. |
|---|---|---|---|---|---|
| [`rag-22`](painel.html#rag-22) | rag_documento | 9.5 | sim | cliente_encerrou | No turno 3, o bot não confirmou explicitamente o resumo da cliente antes de propor o encerramento; Repetiu 'Boa tarde' no turno 2, depois de já ter saudado a cliente |
| [`follow-16`](painel.html#follow-16) | follow_up_contextual | 9.3 | sim | cliente_encerrou | Cumprimento repetido ('Boa tarde!') depois da saudação inicial; Despedida muito seca, sem oferecer mais ajuda |
| [`faq-04`](painel.html#faq-04) | faq_direta | 9 | sim | max_turnos | Saudação duplicada no turno 2 ('Boa tarde! 😊' seguido de 'Olá!'); Turno 2 um pouco extenso para o tom de WhatsApp; Pouca empatia explícita diante da ansiedade da cliente no turno 1 |
| [`faq-23`](painel.html#faq-23) | faq_direta | 9 | sim | cliente_encerrou | Saudação duplicada no turno 2 ('Boa tarde!' + 'Olá!'); Não mencionou o chat no site como canal |
| [`faq-22`](painel.html#faq-22) | faq_direta | 9 | sim | cliente_encerrou | Saudação 'Boa tarde!' incoerente com o 'bom dia' da cliente; Não mencionou que a cobrança e os links do COL continuam vinculados à Porto Seguro; Não confirmou se a SUSEP poderia ficar para depois |
| [`follow-17`](painel.html#follow-17) | follow_up_contextual | 8 | sim | cliente_encerrou | Respondeu à despedida com uma saudação genérica, como se a conversa estivesse começando; Usou 'ajudá-lo' no masculino com uma cliente mulher; Repetiu 'Boa tarde' fora de contexto nos turnos 2 e 4 |
| [`faq-15`](painel.html#faq-15) | faq_direta | 8 | sim | cliente_encerrou | O passo 4 ficou vago: não cita 'Validar Token' nem 'Ativar'.; A instrução de leitura do QR vale só para o Google Authenticator; o caminho do Microsoft Authenticator ('Outro') ficou de fora.; A despedida do cliente foi cl |
| [`faq-09`](painel.html#faq-09) | faq_direta | 7.5 | sim | cliente_encerrou | Turno 4: responde ao agradecimento com uma saudação genérica em vez de se despedir; Usa 'ajudá-lo' no masculino com uma cliente mulher; Saudações repetidas ('Boa tarde! Olá!', 'Olá!' no meio da conversa) |
| [`rag-02`](painel.html#rag-02) | rag_documento | 7 | sim | cliente_encerrou | O e-mail de destino não apareceu na primeira resposta e a cliente precisou perguntar de novo; Faltou citar os dados exigidos para trocar o e-mail de cadastro: SUSEP, domínio, CPF/CNPJ e novo e-mail; Faltou a recomendação |
| [`conf-04`](painel.html#conf-04) | confuso_digitacao | 7 | parcial | cliente_encerrou | Não citou a redefinição pelo painel de e-mails para quem tem acesso de administrador; Turno 3 deu passos de login com a senha atual para uma cliente que a esqueceu; Leu 'aa td bem' como pergunta ('Tudo bem por aqui també |

Transcrição completa de cada conversa: `painel.html` (abrir por file://) ou `resultados/conversas.jsonl`; veredito: `resultados/julgamentos.jsonl`.
