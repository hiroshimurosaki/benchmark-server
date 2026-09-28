# B5 — conversa dinâmica: resultados

- Rodada: início 2026-09-28T08:56:34 · prazo 2026-09-28T10:56:34 · fim 2026-09-28T09:21:05
- Org `oncorretor-perfeita` · modelo `qwen3.6:35b-a3b` · threshold 0.8
- Conversas concluídas: **22** de 120 objetivos · julgadas: 22 · fallbacks opencode: 0
- Painel: `C:\Users\fernando.murusaki\benchmark-server\b5\painel_r9.html`

## Números

| Métrica | Valor |
|---|---|
| Cliente satisfeito (juiz) sim / parcial / não | 9 / 9 / 4 (41% sim) |
| Objetivo cumprido | 17/22 (77%) |
| Nota geral média | 6.05 |
| Nota de qualidade média | 5.62 |
| Escalonamento | adequado: 1, desnecessario: 2, faltou: 1, nao_se_aplica: 18 |
| Conversas com alucinação | 5/22 (23%) |
| Latência do turno do bot p50 / p95 / máx | 8.9s / 16.5s / 20.5s |
| Turnos por conversa (média) | 3.7 |
| Fonte das respostas (turnos) | rag: 43, gate:opening_question: 22, saudacao: 10, escalou: 3, faq: 3, gate:closure: 1 |

## Por trilha

| Trilha | n | cumprido | sat. sim | nota geral | alucinação |
|---|---|---|---|---|---|
| confuso_digitacao | 3 | 67% | 33% | 5.0 | 33% |
| faq_direta | 7 | 86% | 57% | 7.0 | 14% |
| follow_up_contextual | 4 | 75% | 75% | 6.8 | 25% |
| fora_do_escopo | 1 | 100% | 0% | 5.5 | 0% |
| multi_pergunta | 2 | 0% | 0% | 3.8 | 50% |
| rag_documento | 4 | 100% | 25% | 5.5 | 25% |
| reclamacao_irritado | 1 | 100% | 0% | 7.0 | 0% |

## 10 piores

| id | trilha | nota | satisf. | parada | problemas |
|---|---|---|---|---|---|
| [`conf-07`](painel.html#conf-07) | confuso_digitacao | 2 | nao | escalou | Transferiu para humano sem necessidade, por baixa confiança; Não entendeu a mensagem com erros de digitação ('imeil', 'cm troca la'); Não pediu para o cliente esclarecer antes de transferir; Não informou o caminho Config |
| [`follow-04`](painel.html#follow-04) | follow_up_contextual | 2.5 | nao | cliente_encerrou | Aplicou errado a regra do dia 20: disse que o cancelamento até o dia 20 só evita cobranças futuras e mantém a cobrança atual; Desencorajou um pedido de estorno que, pelo documento, tinha fundamento; O cliente desistiu de |
| [`multi-09`](painel.html#multi-09) | multi_pergunta | 3 | nao | escalou | Não respondeu onde ficam os links de redes sociais (Configurações Básicas > Informações Úteis); Turno 3 respondeu sobre logotipo, um assunto que não foi perguntado; Transferiu para humano sem necessidade, por baixa confi |
| [`rag-08`](painel.html#rag-08) | rag_documento | 4 | nao | max_turnos | Repetiu os passos de aba anônima e outro navegador depois de a cliente dizer que já tinha testado; Não respondeu à pergunta direta sobre abrir o chamado pelo chat; Não transferiu para humano apesar da urgência e da persi |
| [`multi-06`](painel.html#multi-06) | multi_pergunta | 4.5 | parcial | cliente_encerrou | Afirmou não ter as regras de senha, que estão documentadas no tópico 42 e na FAQ; Não informou o mínimo de 6 caracteres nem a regra de 3 dos 4 requisitos; Omitiu a etapa de validar o token e ativar na autenticação em dua |
| [`faq-12`](painel.html#faq-12) | faq_direta | 5 | parcial | cliente_encerrou | Não avisou que o custo do domínio registrado pelo OnCorretor pode ser cobrado mesmo com o serviço ativo por pouco tempo; Quando o cliente perguntou 'não vai ter cobrança nenhuma?', a resposta deixou entender que o custo  |
| [`fora-10`](painel.html#fora-10) | fora_do_escopo | 5.5 | parcial | cliente_encerrou | A recusa não disse que o assunto não é do OnCorretor nem listou os serviços com que o bot pode ajudar, ao contrário do que a FAQ indica; Respondeu 'Bom dia' quando a cliente disse 'boa tarde'; Respondeu à despedida com u |
| [`conf-04`](painel.html#conf-04) | confuso_digitacao | 5.5 | parcial | cliente_encerrou | Não citou a redefinição pelo painel de e-mails (painel.seudominio.com.br) para quem tem acesso de administrador; Não explicou que no webmail o usuário é só o nome antes do '@', possível causa do erro de login; Turno 3 ig |
| [`rag-22`](painel.html#rag-22) | rag_documento | 6 | parcial | cliente_encerrou | Turno 2 sem o e-mail de destino e sem introdução, o que obrigou a cliente a perguntar de novo; Turno 3 com o conteúdo duplicado e um 'Olá!' no meio da mensagem; Saudação errada: 'Bom dia' quando a cliente disse 'boa tard |
| [`rag-10`](painel.html#rag-10) | rag_documento | 6 | parcial | cliente_encerrou | Deixou de fora 3 das 4 recomendações do tópico 28: autenticação em dois fatores, troca periódica de senhas fortes e antivírus atualizado; Não respondeu de forma direta se o e-mail pedindo senha vinha do OnCorretor; Disse |

## 10 melhores

| id | trilha | nota | satisf. | parada | destaques/obs. |
|---|---|---|---|---|---|
| [`follow-16`](painel.html#follow-16) | follow_up_contextual | 9 | sim | cliente_encerrou | Disse 'Bom dia!' quando o cliente tinha cumprimentado com 'boa tarde'.; Cumprimentou de novo no turno 2 sem necessidade.; Tom um pouco formal ('É importante saber...') para um cliente informal. |
| [`faq-09`](painel.html#faq-09) | faq_direta | 8.5 | sim | cliente_encerrou | Cumprimentou com 'Bom dia!' quando a cliente tinha dito 'boa tarde', e cumprimentou de novo depois do gate da SUSEP; A resposta do turno 3 repete informações já dadas, sem acrescentar nada; Não ofereceu mais ajuda nem en |
| [`faq-22`](painel.html#faq-22) | faq_direta | 8 | sim | cliente_encerrou | Cumprimento repetido ('Bom dia!' no turno 2 e 'Olá!' no turno 3); Não reconheceu que a cliente estava agradecendo e encerrando: repetiu a resposta inteira em vez de se despedir; Informações repetidas deixaram o fim da co |
| [`follow-17`](painel.html#follow-17) | follow_up_contextual | 8 | sim | cliente_encerrou | No último turno o bot respondeu à despedida com uma saudação genérica, 'Como posso ajudá-lo?'; Saudação no horário errado ('Bom dia' quando a cliente disse 'boa tarde'); Tratou a cliente no masculino ('ajudá-lo'); No tur |
| [`faq-04`](painel.html#faq-04) | faq_direta | 8 | sim | cliente_encerrou | No turno 3, o agradecimento foi tratado como saudação e o bot respondeu com uma mensagem genérica, fora de contexto; Não houve fechamento adequado depois do agradecimento; Usou 'ajudá-lo' (masculino) com uma cliente mulh |
| [`conf-03`](painel.html#conf-03) | confuso_digitacao | 7.5 | sim | cliente_encerrou | No turno 2 o bot não tratou a suspeita de boleto com valor alto, que era a dúvida central do cliente; No turno 2 o bot recomendou 'fazer o pagamento antes do vencimento', o que é arriscado diante de um boleto possivelmen |
| [`follow-01`](painel.html#follow-01) | follow_up_contextual | 7.5 | sim | cliente_encerrou | Não informou que não há taxa de adesão; Saudação 'Bom dia' respondendo a um 'boa tarde'; No turno 4, respondeu à despedida com uma saudação genérica e no masculino ('ajudá-lo'); Não mencionou como pedir o cancelamento (e |
| [`recl-01`](painel.html#recl-01) | reclamacao_irritado | 7 | parcial | escalou | Nenhuma empatia com um cliente visivelmente irritado; Saudação repetida ('Bom dia!') depois de já ter cumprimentado; Não reconheceu que cancelar até o dia 20 impede novas cobranças, o que favorece o estorno; Turno 3 repe |
| [`faq-15`](painel.html#faq-15) | faq_direta | 7 | sim | cliente_encerrou | Não alertou sobre guardar os códigos de recuperação, que não podem ser consultados depois; Não citou os botões 'Validar Token' e 'Ativar'; Deu 'Bom dia' quando o cliente disse 'Boa tarde'; No encerramento, respondeu com  |
| [`faq-23`](painel.html#faq-23) | faq_direta | 6.5 | parcial | max_turnos | No turno 2, o menu de desambiguação não tinha relação com o pedido explícito de telefone do suporte; Disse 'Bom dia' quando o cliente tinha dito 'Boa tarde'; Levou um turno a mais para responder uma pergunta direta de FA |

Transcrição completa de cada conversa: `painel.html` (abrir por file://) ou `resultados/conversas.jsonl`; veredito: `resultados/julgamentos.jsonl`.
