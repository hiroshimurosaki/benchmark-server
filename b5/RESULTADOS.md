# B5 — conversa dinâmica: resultados

- Rodada: início 2026-09-25T14:45:47 · prazo 2026-09-25T16:45:47 · fim 2026-09-25T15:07:30
- Org `oncorretor-perfeita` · modelo `qwen3.6:35b-a3b` · threshold 0.8
- Conversas concluídas: **22** de 120 objetivos · julgadas: 22 · fallbacks opencode: 0
- Painel: `C:\Users\fernando.murusaki\benchmark-server\b5\painel_r2.html`

## Números

| Métrica | Valor |
|---|---|
| Cliente satisfeito (juiz) sim / parcial / não | 10 / 12 / 0 (45% sim) |
| Objetivo cumprido | 18/22 (82%) |
| Nota geral média | 6.02 |
| Nota de qualidade média | 5.40 |
| Escalonamento | adequado: 3, desnecessario: 2, nao_se_aplica: 17 |
| Conversas com alucinação | 17/22 (77%) |
| Latência do turno do bot p50 / p95 / máx | 7.0s / 14.5s / 29.4s |
| Turnos por conversa (média) | 3.6 |
| Fonte das respostas (turnos) | rag: 37, gate:opening_question: 22, saudacao: 12, escalou: 5, faq: 3, gate:closure: 1 |

## Por trilha

| Trilha | n | cumprido | sat. sim | nota geral | alucinação |
|---|---|---|---|---|---|
| confuso_digitacao | 3 | 67% | 0% | 5.0 | 100% |
| faq_direta | 7 | 100% | 71% | 6.9 | 43% |
| follow_up_contextual | 4 | 100% | 75% | 7.1 | 75% |
| fora_do_escopo | 1 | 0% | 0% | 2.0 | 100% |
| multi_pergunta | 2 | 50% | 0% | 4.5 | 100% |
| rag_documento | 4 | 75% | 50% | 6.0 | 100% |
| reclamacao_irritado | 1 | 100% | 0% | 6.0 | 100% |

## 10 piores

| id | trilha | nota | satisf. | parada | problemas |
|---|---|---|---|---|---|
| [`fora-10`](painel.html#fora-10) | fora_do_escopo | 2 | parcial | escalou | Não recusou o assunto fora do escopo (imposto de renda); Ofereceu explicar a declaração de IR, prometendo algo que a plataforma não faz; Menu de desambiguação confuso, misturando SUSEP e IR; Transferência desnecessária p |
| [`multi-09`](painel.html#multi-09) | multi_pergunta | 3 | parcial | escalou | Não respondeu a terceira pergunta (redes sociais) no turno 2, que tinha várias perguntas; Resposta do turno 2 repetida em blocos, com o mesmo caminho e o mesmo link duas vezes; Turno 3 mostrou menus de desambiguação sem  |
| [`rag-10`](painel.html#rag-10) | rag_documento | 3.5 | parcial | max_turnos | Turno 2: a busca na FAQ trouxe uma entrada institucional sem relação com a pergunta (confiança de 0,81).; Turno 3: o bot se recusou a responder mesmo havendo o tópico 28 no documento.; Citou o e-mail atendimento@oncorret |
| [`conf-07`](painel.html#conf-07) | confuso_digitacao | 3.5 | parcial | cliente_encerrou | Não indicou o caminho exato: Configurações Básicas > Informações Úteis; Inventou as seções 'Contato/Perfil' e 'Dados da Empresa'; Mandou o cliente ao 'Clube VIP' e ao 'construtor', que não estão no material; Deixou de fo |
| [`conf-04`](painel.html#conf-04) | confuso_digitacao | 5 | parcial | cliente_encerrou | Turno 2 respondeu sobre troca de SUSEP de cobrança em vez da senha do e-mail; Saudação 'Boa tarde' inconsistente com o 'bom dia' da cliente; Não mencionou a redefinição pelo administrador no painel de e-mails; Turno 4 co |
| [`faq-03`](painel.html#faq-03) | faq_direta | 5.5 | parcial | cliente_encerrou | Alucinação no turno 3: o bot citou uma seção "Meu Gerente"/"Contato" no portal que não consta no material; Não informou o e-mail atendimento@oncorretor.com.br, nem para pedir a troca de SUSEP, nem para buscar o contato d |
| [`rag-02`](painel.html#rag-02) | rag_documento | 5.5 | sim | cliente_encerrou | Turno 2 inventou autoatendimento via área administrativa, contrariando o documento; Turno 2 trouxe orientação sobre senha sem relação com a pergunta; Faltou recomendar e-mail externo (Gmail/Hotmail) como e-mail de cadast |
| [`multi-06`](painel.html#multi-06) | multi_pergunta | 6 | parcial | cliente_encerrou | No turno 3 ignorou a pergunta sobre autenticação em duas etapas e repetiu as regras de senha; Afirmação sem base no documento: o sistema 'pode recusar a alteração e exibir um aviso'; Passo a passo sem a etapa de informar |
| [`recl-01`](painel.html#recl-01) | reclamacao_irritado | 6 | parcial | escalou | Omitiu o procedimento de estorno (e-mail + extrato + comprovante), que está no FAQ; Disse que não tinha a informação nos documentos, o que é falso; Explicou a regra do dia 20 só pelo lado desfavorável, sem dizer que até  |
| [`faq-12`](painel.html#faq-12) | faq_direta | 6.5 | sim | cliente_encerrou | Turno 2 não informou que não há multa, embora isso fosse parte central da dúvida; Não explicou com clareza que o custo do domínio registrado pelo OnCorretor pode ser cobrado mesmo que o serviço fique ativo por pouco temp |

## 10 melhores

| id | trilha | nota | satisf. | parada | destaques/obs. |
|---|---|---|---|---|---|
| [`follow-17`](painel.html#follow-17) | follow_up_contextual | 8 | sim | cliente_encerrou | No turno 3, o bot tomou o agradecimento e a despedida por saudação e reiniciou o atendimento com 'Como posso ajudá-lo?'; Usou o masculino ('ajudá-lo') com uma cliente mulher; Repetiu 'Boa tarde!' no turno 2 depois de já  |
| [`rag-08`](painel.html#rag-08) | rag_documento | 7.5 | parcial | escalou | Saudação duplicada no turno 2 ('Boa tarde! 😊 Olá!'); Não respondeu à pergunta da cliente sobre outra forma de localizar a SUSEP; Link ajuda.oncorretor.com.br não consta no material fornecido; Na transferência, não pediu  |
| [`faq-15`](painel.html#faq-15) | faq_direta | 7.5 | sim | cliente_encerrou | Saudação duplicada no turno 2 ('Boa tarde! 😊 Olá!'); Nenhuma das respostas mencionou o clique final em 'Ativar'; O turno 2 não informou o endereço painel.seudominio.com.br; No turno 3, o bot repetiu todo o conteúdo quand |
| [`faq-09`](painel.html#faq-09) | faq_direta | 7.5 | sim | cliente_encerrou | Saudação duplicada no turno 2 ('Boa tarde! 😊' seguido de 'Olá!'); No turno 3, o agradecimento foi classificado como saudação e o bot respondeu com uma frase genérica, sem se despedir; O bot usou 'ajudá-lo' no masculino c |
| [`faq-22`](painel.html#faq-22) | faq_direta | 7.5 | sim | cliente_encerrou | Repetiu a saudação 'Boa tarde!' no meio da conversa; Respondeu ao agradecimento final com uma saudação genérica em vez de se despedir; Usou 'ajudá-lo' no masculino com uma cliente mulher; Não comentou que a cliente não s |
| [`rag-22`](painel.html#rag-22) | rag_documento | 7.5 | sim | cliente_encerrou | Saudação duplicada no turno 2 ('Boa tarde!' seguido de 'Olá!'); Link ajuda.oncorretor.com.br não consta no documento nem no FAQ; No turno 3 o bot não percebeu o encerramento e reiniciou a conversa com uma saudação genéri |
| [`follow-01`](painel.html#follow-01) | follow_up_contextual | 7 | sim | cliente_encerrou | Não informou a mensalidade de R$ 52,50 nem que não há taxa de adesão; Falou de adesão manual com formulário e termo, o que não está no material; Incluiu o link ajuda.oncorretor.com.br, que não está no material; Disse que |
| [`follow-16`](painel.html#follow-16) | follow_up_contextual | 7 | sim | cliente_encerrou | Escreveu 'SUSEP' no lugar de 'Porto Seguro' no turno 2; Saudação 'Boa tarde!' duplicada no turno 2; Turno 3 repete quase igual o conteúdo do turno 2; Despedida do cliente tratada como nova saudação ('Como posso ajudá-lo? |
| [`faq-04`](painel.html#faq-04) | faq_direta | 7 | sim | cliente_encerrou | Afirmou que o bloqueio impede emissões de apólice, o que não consta no documento; Tratou a despedida da cliente como saudação ('Como posso ajudá-lo?'); Usou o masculino ('ajudá-lo') com uma cliente mulher; Repetiu 'Boa t |
| [`conf-03`](painel.html#conf-03) | confuso_digitacao | 6.5 | parcial | escalou | Não informou que o OnCorretor não envia boleto e que a renovação é descontada da conta comissão; Não alertou sobre boletos falsos de empresas com nome parecido (BR.Registro); Sugeriu 'outros serviços inclusos', o que não |

Transcrição completa de cada conversa: `painel.html` (abrir por file://) ou `resultados/conversas.jsonl`; veredito: `resultados/julgamentos.jsonl`.
