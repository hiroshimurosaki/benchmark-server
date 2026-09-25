# B5 — conversa dinâmica: resultados

- Rodada: início 2026-09-25T15:13:02 · prazo 2026-09-25T17:13:02 · fim 2026-09-25T15:35:14
- Org `oncorretor-perfeita` · modelo `qwen3.6:35b-a3b` · threshold 0.8
- Conversas concluídas: **22** de 120 objetivos · julgadas: 22 · fallbacks opencode: 0
- Painel: `C:\Users\fernando.murusaki\benchmark-server\b5\painel_r3.html`

## Números

| Métrica | Valor |
|---|---|
| Cliente satisfeito (juiz) sim / parcial / não | 11 / 10 / 1 (50% sim) |
| Objetivo cumprido | 17/22 (77%) |
| Nota geral média | 6.39 |
| Nota de qualidade média | 5.95 |
| Escalonamento | adequado: 1, desnecessario: 2, faltou: 1, nao_se_aplica: 18 |
| Conversas com alucinação | 8/22 (36%) |
| Latência do turno do bot p50 / p95 / máx | 6.8s / 15.8s / 19.9s |
| Turnos por conversa (média) | 3.6 |
| Fonte das respostas (turnos) | rag: 39, gate:opening_question: 22, saudacao: 10, faq: 5, escalou: 3, gate:closure: 1 |

## Por trilha

| Trilha | n | cumprido | sat. sim | nota geral | alucinação |
|---|---|---|---|---|---|
| confuso_digitacao | 3 | 67% | 0% | 5.0 | 100% |
| faq_direta | 7 | 86% | 57% | 7.2 | 29% |
| follow_up_contextual | 4 | 100% | 75% | 7.1 | 25% |
| fora_do_escopo | 1 | 0% | 0% | 2.5 | 0% |
| multi_pergunta | 2 | 50% | 50% | 5.2 | 0% |
| rag_documento | 4 | 75% | 75% | 6.6 | 50% |
| reclamacao_irritado | 1 | 100% | 0% | 7.0 | 0% |

## 10 piores

| id | trilha | nota | satisf. | parada | problemas |
|---|---|---|---|---|---|
| [`fora-10`](painel.html#fora-10) | fora_do_escopo | 2.5 | parcial | escalou | Não recusou com educação um assunto fora do escopo (imposto de renda); Transferiu para humano sem necessidade (motivo: baixa confiança); Não disse com o que pode ajudar (site, landing pages, e-mails, domínio, adesão, cob |
| [`multi-09`](painel.html#multi-09) | multi_pergunta | 3 | parcial | escalou | Na pergunta com vários itens, o bot respondeu só um item por vez.; Não respondeu sobre as redes sociais (Configurações Básicas > Informações Úteis), embora a informação esteja no documento e no FAQ.; Transferiu para huma |
| [`conf-07`](painel.html#conf-07) | confuso_digitacao | 4 | parcial | max_turnos | Resposta correta só no 5º turno, apesar de o pedido estar claro desde o início; Turno 3 confundiu troca de e-mail de contato com senha de e-mail; Turno 3 afirmou falsamente que não há opção de mudar o e-mail na configura |
| [`faq-12`](painel.html#faq-12) | faq_direta | 4 | parcial | max_turnos | Nunca informou que o custo do domínio registrado pelo OnCorretor pode ser cobrado; No turno 4, casou com a FAQ errada (mensalidade) e não respondeu sobre taxas extras; No turno 3, afirmou com certeza que haverá cobrança, |
| [`rag-08`](painel.html#rag-08) | rag_documento | 4 | nao | cliente_encerrou | Inventou o e-mail atendimento@oncorretor.com.br para envio do print; Inventou uma lista de dados a incluir no chamado; Não recebeu o print na conversa nem transferiu para um humano abrir o chamado N3; Saudação duplicada  |
| [`conf-03`](painel.html#conf-03) | confuso_digitacao | 5 | parcial | max_turnos | Nos turnos 2 e 3 ignorou a FAQ sobre boleto suspeito, que respondia o caso direto; Inventou consequências (domínio congelado, removido e liberado para terceiros) e um fluxo de chamado que não estão no material; Vazou uma |
| [`rag-10`](painel.html#rag-10) | rag_documento | 6 | sim | cliente_encerrou | Omitiu as recomendações de ativar 2FA, trocar senhas periodicamente/usar senhas fortes e manter o antivírus atualizado; Informou o e-mail atendimento@oncorretor.com.br, que não consta no documento; Não sugeriu trocar a s |
| [`faq-03`](painel.html#faq-03) | faq_direta | 6 | parcial | max_turnos | Não respondeu se dá para achar o cadastro pelo nome ou CPF (turno 2); Saudação repetida: 'Boa tarde! Olá!'; Turno 3 repete o turno 2 quase na íntegra; Turno 4 usou a FAQ de preço em vez de responder sobre boleto; Não inf |
| [`conf-04`](painel.html#conf-04) | confuso_digitacao | 6 | parcial | cliente_encerrou | Omitiu a opção de redefinir pelo painel (painel.seudominio.com.br) para quem tem acesso de administrador; Disse que o e-mail ao atendimento é a 'única opção', o que contradiz a FAQ; Inventou que não é possível acelerar o |
| [`follow-04`](painel.html#follow-04) | follow_up_contextual | 6.5 | parcial | cliente_encerrou | Turno 3 classificado como saudação: responde 'Como posso ajudá-lo?' a um agradecimento ou encerramento; Não confirma os próximos passos ao cliente que não tem certeza da data do pedido; 'Boa tarde' repetido no turno 2, d |

## 10 melhores

| id | trilha | nota | satisf. | parada | destaques/obs. |
|---|---|---|---|---|---|
| [`faq-09`](painel.html#faq-09) | faq_direta | 9 | sim | cliente_encerrou | O turno 3 repete a instrução de pedir pelo site sem necessidade; Algumas frases soam formais demais para WhatsApp ('Trata-se de uma consultoria voltada a modernizar') |
| [`faq-23`](painel.html#faq-23) | faq_direta | 9 | sim | cliente_encerrou | Respondeu 'Boa tarde' quando o cliente tinha dito 'Bom dia'; Não citou o chat no site nem que todo atendimento gera chamado; O pedido de SUSEP atrasou um pouco a resposta a um cliente com pressa |
| [`rag-22`](painel.html#rag-22) | rag_documento | 9 | sim | cliente_encerrou | O turno 3 repete toda a lista e o link, mesmo com a cliente já tendo confirmado e agradecido; Não houve uma despedida simples e natural no fechamento |
| [`faq-04`](painel.html#faq-04) | faq_direta | 8 | parcial | max_turnos | Saudação duplicada no turno 2 ('Boa tarde! 😊' seguido de 'Olá!'); Turno 3 repete quase literalmente as frases do turno 2 sobre a causa do bloqueio e a normalização do fluxo; Não respondeu de forma direta e personalizada  |
| [`multi-06`](painel.html#multi-06) | multi_pergunta | 7.5 | sim | cliente_encerrou | Omitiu a etapa de informar o token, clicar em 'Validar Token' e em 'Ativar'; Deu só a instrução do Google Authenticator; faltou o caminho do Microsoft Authenticator ('Outro (Google, Facebook, etc.)'); Passos 3 e 4 redund |
| [`follow-17`](painel.html#follow-17) | follow_up_contextual | 7.5 | sim | cliente_encerrou | No turno 3, o bot afirmou que o print deve ser do site, o que não está no documento nem na FAQ.; No turno 3, justificou a comparação entre painel e site sem base no material.; No turno 4, respondeu ao agradecimento com u |
| [`rag-02`](painel.html#rag-02) | rag_documento | 7.5 | sim | cliente_encerrou | Omitiu os dados a enviar na troca do e-mail de cadastro (SUSEP, domínio, CPF/CNPJ, novo e-mail); Omitiu a recomendação de usar e-mail externo (Gmail/Hotmail); Despedida classificada como saudação: resposta 'Como posso aj |
| [`follow-16`](painel.html#follow-16) | follow_up_contextual | 7.5 | sim | cliente_encerrou | Menu de desambiguação com opções sem relação com a pergunta (VIP, 2FA, e-mail) logo depois de uma resposta já completa; Mensagem de encerramento do cliente classificada como saudação: o bot respondeu 'Como posso ajudá-lo |
| [`faq-22`](painel.html#faq-22) | faq_direta | 7.5 | sim | cliente_encerrou | Saudação 'Boa tarde!' incoerente com o 'bom dia' da cliente e repetida no meio da conversa; Ao agradecimento o bot respondeu com uma saudação de abertura, sem encerrar a conversa; 'ajudá-lo' no masculino para uma cliente |
| [`recl-01`](painel.html#recl-01) | reclamacao_irritado | 7 | parcial | escalou | Saudações repetidas ('Boa tarde! 😊', 'Olá!') no meio da conversa com um cliente irritado; Respostas longas e repetitivas: o bloco do e-mail aparece duas vezes; Chamou a cobrança de 'indevida' antes de qualquer análise; N |

Transcrição completa de cada conversa: `painel.html` (abrir por file://) ou `resultados/conversas.jsonl`; veredito: `resultados/julgamentos.jsonl`.
