# B5 — conversa dinâmica: resultados

- Rodada: início 2026-09-25T18:34:03 · prazo 2026-09-28T09:57:39 · fim 2026-09-28T08:11:11
- Org `oncorretor-perfeita` · modelo `qwen3.6:35b-a3b` · threshold 0.8
- Conversas concluídas: **22** de 120 objetivos · julgadas: 22 · fallbacks opencode: 0
- Painel: `C:\Users\fernando.murusaki\benchmark-server\b5\painel_r7.html`

## Números

| Métrica | Valor |
|---|---|
| Cliente satisfeito (juiz) sim / parcial / não | 8 / 13 / 1 (36% sim) |
| Objetivo cumprido | 19/22 (86%) |
| Nota geral média | 6.20 |
| Nota de qualidade média | 5.61 |
| Escalonamento | adequado: 1, desnecessario: 2, faltou: 1, nao_se_aplica: 18 |
| Conversas com alucinação | 7/22 (32%) |
| Latência do turno do bot p50 / p95 / máx | 6.9s / 20.2s / 21.9s |
| Turnos por conversa (média) | 3.7 |
| Fonte das respostas (turnos) | rag: 41, gate:opening_question: 22, saudacao: 11, faq: 3, escalou: 3, gate:closure: 2 |

## Por trilha

| Trilha | n | cumprido | sat. sim | nota geral | alucinação |
|---|---|---|---|---|---|
| confuso_digitacao | 3 | 100% | 0% | 6.2 | 33% |
| faq_direta | 7 | 86% | 43% | 6.8 | 29% |
| follow_up_contextual | 4 | 75% | 50% | 5.6 | 25% |
| fora_do_escopo | 1 | 100% | 0% | 5.5 | 0% |
| multi_pergunta | 2 | 50% | 0% | 4.2 | 50% |
| rag_documento | 4 | 100% | 75% | 7.1 | 25% |
| reclamacao_irritado | 1 | 100% | 0% | 5.5 | 100% |

## 10 piores

| id | trilha | nota | satisf. | parada | problemas |
|---|---|---|---|---|---|
| [`follow-16`](painel.html#follow-16) | follow_up_contextual | 1 | nao | escalou | A recuperação (RAG) não encontrou o tópico 60 nem a FAQ sobre leads, embora a pergunta fosse explícita.; No turno 2, alegou falta de contexto para uma pergunta clara e pediu que o cliente especificasse.; Cumprimentou com |
| [`multi-09`](painel.html#multi-09) | multi_pergunta | 2.5 | parcial | escalou | Confundiu o botão 'Simule e Contrate' com a integração Segfy (orientação errada); Não informou que o 'Simule e Contrate' fica em Configurações do Site, junto com o favicon; Nunca respondeu onde ficam as redes sociais (In |
| [`conf-07`](painel.html#conf-07) | confuso_digitacao | 5 | parcial | cliente_encerrou | O turno 2 não citou Informações Úteis e deu só uma orientação vaga.; O turno 3 disse que não há opção para trocar o e-mail exibido, contradizendo o tópico 52.; O bot inventou que o destinatário do formulário se configura |
| [`faq-23`](painel.html#faq-23) | faq_direta | 5 | parcial | max_turnos | Turno 2 apresentou um menu de desambiguação irrelevante apesar de o pedido ser claro; Saudação errada: 'Bom dia' em resposta a 'Boa tarde'; Omitiu o WhatsApp (11) 99714-9631, exigido pelo cliente; Omitiu o chat no site;  |
| [`fora-10`](painel.html#fora-10) | fora_do_escopo | 5.5 | parcial | cliente_encerrou | Não disse com o que pode ajudar (site, landing pages, e-mails, domínio, adesão, cobrança).; Recusa genérica ("produtos e serviços da empresa") em vez da resposta da FAQ.; "Bom dia" quando a cliente disse "boa tarde".; Re |
| [`faq-09`](painel.html#faq-09) | faq_direta | 5.5 | parcial | max_turnos | No turno 3, o bot negou que o Clube VIP fosse gratuito, contradizendo a FAQ e o próprio turno 2; No turno 3, trouxe um tema sem relação (logos de outras seguradoras); Disse 'Bom dia' quando a cliente tinha dito 'boa tard |
| [`recl-01`](painel.html#recl-01) | reclamacao_irritado | 5.5 | parcial | cliente_encerrou | Não escalou para humano, mesmo sendo esse o comportamento esperado e com o cliente irritado e pedindo solução imediata; Afirmou uma política que não está no documento: 'não realizamos devoluções por chat'; No turno 4 rep |
| [`multi-06`](painel.html#multi-06) | multi_pergunta | 6 | parcial | cliente_encerrou | No turno 2, ignorou a segunda pergunta (autenticação em duas etapas).; No turno 3, disse que os documentos não informam se a autenticação é obrigatória, mas o tópico 43 e o FAQ dizem que é.; Contradisse a si mesmo entre  |
| [`faq-12`](painel.html#faq-12) | faq_direta | 6 | parcial | max_turnos | Não respondeu de forma direta à pergunta sobre cancelar no dia 25; Diz não ter informação sobre taxas, embora o documento preveja a cobrança do domínio; Manda o cliente verificar no K1000, sistema interno a que o correto |
| [`follow-04`](painel.html#follow-04) | follow_up_contextual | 6 | parcial | cliente_encerrou | No turno 4, trata o estorno como atualização de dados cadastrais; Promete comunicação por e-mail sobre o andamento, o que não está no tópico de estorno; Não diz claramente que um cancelamento até o dia 20 seguido de cobr |

## 10 melhores

| id | trilha | nota | satisf. | parada | destaques/obs. |
|---|---|---|---|---|---|
| [`faq-03`](painel.html#faq-03) | faq_direta | 9 | sim | cliente_encerrou | Diz 'Bom dia!' quando o cliente cumprimentou com 'boa tarde'; Repete a saudação no turno 2, depois da pergunta da SUSEP; Não informa o e-mail atendimento@oncorretor.com.br para confirmar a regularização |
| [`faq-15`](painel.html#faq-15) | faq_direta | 8 | sim | cliente_encerrou | Não mencionou o passo de informar o token e clicar em 'Validar Token' e depois em 'Ativar'; A instrução 'toque em + e selecione Ler código QR' vale só para o Google Authenticator; no Microsoft Authenticator a opção é 'Ou |
| [`rag-22`](painel.html#rag-22) | rag_documento | 8 | sim | cliente_encerrou | Saudação 'Bom dia' errada: a cliente disse 'boa tarde'; No turno 3, respondeu ao agradecimento com uma saudação genérica, fora de contexto; Usou 'ajudá-lo' com uma cliente mulher; Não reconheceu o detalhe do erro ao clic |
| [`follow-17`](painel.html#follow-17) | follow_up_contextual | 8 | sim | cliente_encerrou | Disse 'Boa noite' quando a cliente tinha dito 'boa tarde'; No turno 3 respondeu ao agradecimento com uma saudação genérica, sem despedida nem confirmação; Usou 'ajudá-lo' (masculino) com uma cliente mulher; Não reconhece |
| [`faq-22`](painel.html#faq-22) | faq_direta | 7.5 | sim | cliente_encerrou | Disse 'Bom dia' duas vezes para uma cliente que cumprimentou com 'boa tarde'; No turno 3, respondeu ao agradecimento com uma saudação genérica ('Como posso ajudá-lo?'), sem encerrar a conversa e no masculino; Não citou a |
| [`follow-01`](painel.html#follow-01) | follow_up_contextual | 7.5 | sim | cliente_encerrou | Não informou que não há taxa de adesão; Ressalva 'não tenho essa informação' sobre fidelidade repetida, o que gera insegurança; Saudação 'Bom dia' incoerente com o 'boa tarde' da cliente; Último turno com saudação genéri |
| [`conf-04`](painel.html#conf-04) | confuso_digitacao | 7 | parcial | cliente_encerrou | Turno 2 perdeu o contexto e pediu para a cliente repetir a dúvida já informada; Saudação 'Boa noite' incoerente com o 'bom dia' da cliente; Um turno extra desnecessário antes da resposta útil |
| [`rag-02`](painel.html#rag-02) | rag_documento | 7 | sim | cliente_encerrou | Omitiu os dados exigidos para trocar o e-mail de cadastro: SUSEP, domínio, CPF/CNPJ e novo e-mail; Não recomendou usar um e-mail externo (Gmail/Hotmail) como e-mail de cadastro; Não disse que o ideal é enviar a partir do |
| [`rag-10`](painel.html#rag-10) | rag_documento | 7 | sim | cliente_encerrou | Disse 'Boa noite' quando o cliente disse 'boa tarde' e 'bom fim de tarde'; Não respondeu diretamente se o pedido para confirmar a senha é golpe nem orientou explicitamente a não responder ao e-mail; No turno 3, tratou a  |
| [`rag-08`](painel.html#rag-08) | rag_documento | 6.5 | parcial | escalou | Saudação 'Boa noite!' incoerente com o 'boa tarde' da cliente; Turno 4 repetiu aba anônima e outro navegador, que a cliente já tinha testado; Promessa de 'resolver rapidamente' sem base no documento; Não ofereceu transfe |

Transcrição completa de cada conversa: `painel.html` (abrir por file://) ou `resultados/conversas.jsonl`; veredito: `resultados/julgamentos.jsonl`.
