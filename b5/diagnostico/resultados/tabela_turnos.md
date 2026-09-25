| turno | caminho orig | caminho base | orig | nota | gab FAQ score (rank) | top1 FAQ | tópico gab FAISS/rerank/ctx | gerador (1ª saída) | ans_verifier | base agora | causa (heur.) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| conf-04:T3 | qv>dis | qv>dis | rag | 4 | - | - | - | - |  | errada | DESAMBIGUACAO_DESNECESSARIA |
| conf-04:T4 | ctx>qv>av | ctx>qv>av | faq | 8 | 0.85 (#1) | 0.85 Como recuperar ou redefinir sua sen | - | - | RELEVANTE | correta | ok |
| conf-04:T5 | ctx>qv>gen>av>gen>av>hist>av | ctx>qv>gen>av>gen>av>hist>av | escalonamento/ESC | 3 | 0.70 (#1) | 0.70 Como recuperar ou redefinir sua sen | [7]/[7]/não | Desculpe, não tenho essa informação nos meus docum | IRRELEVANTE,IRRELEVANTE,IRRELEVANTE | escalou | FAQ_NAO_CASOU + RETRIEVER_ERROU |
| faq-12:T3 | ctx>qv>gen>av>gen>av>hist>av | ctx>qv>gen>av>gen>av>hist>av | escalonamento/ESC | 1 | 0.64 (#1) | 0.64 Posso cancelar minha adesão no mesm | [1, 10]/[2, 3]/sim | RELEVANTE | IRRELEVANTE,IRRELEVANTE,IRRELEVANTE | escalou | FAQ_NAO_CASOU + GERADOR_RECUSOU |
| rag-10:T3 | ctx>qv>dis | ctx>qv>dis | rag | 1 | - | - | - | - |  | errada | DESAMBIGUACAO_DESNECESSARIA |
| rag-10:T4 | ctx>qv>gen>av>gen>av>hist>av | ctx>qv>gen>av>gen>av>hist>av | escalonamento/ESC | 2 | sem FAQ | 0.71 Meu painel de e-mail não abre, o qu | [9]/[7]/não | Desculpe, não tenho essa informação nos meus docum | IRRELEVANTE,IRRELEVANTE,IRRELEVANTE | escalou | RETRIEVER_ERROU |
| multi-06:T3 | qv>qv>gen>av>gen>av>hist>av>qv>av | qv>gen>av>gen>av>hist>av | faq | 4 | 0.58 (#34), 0.32 (#155) | 0.73 O formulário do meu site não está c | []/[]/não | Desculpe, não tenho essa informação nos meus docum | IRRELEVANTE,IRRELEVANTE,IRRELEVANTE | escalou | FAQ_NAO_CASOU + RETRIEVER_ERROU |
| multi-06:T4 | qv>dis>gen>av>gen>av>hist>av | qv>dis>gen>av>gen>av>hist>av | escalonamento/ESC | 1 | 0.51 (#39), 0.48 (#50) | 0.74 Preciso de mais contas de e-mail, o | [4, 12]/[1, 9]/sim | call_attendant | IRRELEVANTE,IRRELEVANTE,IRRELEVANTE | escalou | FAQ_NAO_CASOU |
| follow-04:T3 | ctx>qv>gen>av>gen>av>hist>av | ctx>qv>gen>av>gen>av>hist>av | escalonamento/ESC | 1 | 0.52 (#48), 0.59 (#6) | 0.65 Posso cancelar minha adesão no mesm | [1, 10]/[1, 3]/sim | Desculpe, não tenho essa informação nos meus docum | IRRELEVANTE,IRRELEVANTE,IRRELEVANTE | escalou | FAQ_NAO_CASOU + GERADOR_RECUSOU |
| follow-16:T3 | ctx>qv>dis | ctx>qv>dis>gen>av>gen>av>hist>av | rag | 2 | 0.55 (#48) | 0.69 O formulário do meu site não está c | [7]/[2]/sim | call_attendant | IRRELEVANTE,IRRELEVANTE,IRRELEVANTE | escalou | DESAMBIGUACAO_DESNECESSARIA + FAQ_NAO_CASOU |
| follow-16:T4 | qv>gen>av>gen>av>hist>av | qv>gen>av>gen>av>hist>av | rag | 3 | 0.41 (#105) | 0.59 Meu cliente disse que o formulario  | []/[]/não | AMBIGUO | IRRELEVANTE,IRRELEVANTE,IRRELEVANTE | escalou | DESAMBIGUACAO_DESNECESSARIA + FAQ_NAO_CASOU + RETRIEVER_ERROU |
| follow-16:T5 | ctx>qv>qv>gen>av>gen>av | ctx>qv>gen>av>gen>av>hist>av | escalonamento/ESC | 1 | 0.48 (#66) | 0.65 Como aumento a velocidade do meu si | [2]/[1]/sim | Desculpe, não tenho essa informação nos meus docum | IRRELEVANTE,IRRELEVANTE,IRRELEVANTE | escalou | FAQ_NAO_CASOU + VERIFICADOR_REPROVOU_BOA? + GERADOR_RECUSOU |
| conf-07:T3 | ctx>qv>dis | ctx>qv>dis | rag | 2 | - | - | - | - |  | errada | DESAMBIGUACAO_DESNECESSARIA |
| conf-07:T4 | ctx>qv>gen>av | ctx>qv>gen>av | rag | 3 | 0.45 (#73) | 0.72 É possível usar minha própria conta | [6]/[2]/sim | Para alterar o e-mail de contato que aparece ao cl | RELEVANTE | parcial | FAQ_NAO_CASOU |
| conf-07:T5 | ctx>qv>dis | ctx>qv>dis | rag | 1 | - | - | - | - |  | errada | DESAMBIGUACAO_DESNECESSARIA |
| follow-17:T3 | ctx>qv>dis | ctx>qv>gen>av>gen>av>hist>av | rag | 5 | 0.71 (#1) | 0.71 Salvei uma alteração no painel mas  | [1]/[1]/sim | Desculpe, não tenho essa informação nos meus docum | IRRELEVANTE,IRRELEVANTE,RELEVANTE | errada | ok |
| follow-17:T4 | ctx>qv>av | ctx>qv>av | faq | 9 | 0.90 (#1) | 0.90 Salvei uma alteração no painel mas  | - | - | RELEVANTE | correta | ok |
| follow-17:T5 | ctx>qv>dis | ctx>qv>dis | rag | 2 | - | - | - | - |  | errada | DESAMBIGUACAO_DESNECESSARIA |
| follow-17:T6 | ctx>qv>gen>av>gen>av | ctx>qv>gen>av>gen>av>hist>av | rag | 5 | 0.58 (#27) | 0.71 O formulário do meu site não está c | [18]/[11]/não | Desculpe, não tenho essa informação nos meus docum | IRRELEVANTE,IRRELEVANTE,IRRELEVANTE | escalou | ok |
| rag-08:T3 | ctx>qv>gen>av>gen>av>hist>av | ctx>qv>gen>av | escalonamento/ESC | 1 | sem FAQ | 0.68 Como configurar o webdomínio no OnC | [2]/[1]/sim | Para desbloquear o wizard do site que travou na co | RELEVANTE | parcial |  |
| recl-01:T3 | qv>dis | qv>dis | rag | 3 | - | - | - | - |  | errada | DESAMBIGUACAO_DESNECESSARIA |
| recl-01:T4 |  |  | faq | 1 | - | - | - | - |  | errada |  |
| recl-01:T5 |  |  | rag | 2 | - | - | - | - |  | errada |  |
| recl-01:T6 | ctx>qv>qv>gen>av>gen>av>hist>av>qv>dis | ctx>qv>qv>gen>av>gen>av>hist>av>qv>dis | rag | 1 | 0.33 (#123), 0.35 (#97) | 0.53 Posso cadastrar outra SUSEP secundá | [7, 11]/[5, 6]/sim | AMBIGUO | IRRELEVANTE,IRRELEVANTE,IRRELEVANTE | errada | DESAMBIGUACAO_DESNECESSARIA + FAQ_NAO_CASOU |
| recl-01:T7 | ctx>qv>dis | ctx>qv>qv>gen>av>gen>av>hist>av>qv>qv>av>qv>av | rag | 1 | 0.42 (#84), 0.44 (#52) | 0.65 Como funciona a cobrança do OnCorre | [1, 10]/[1, 5]/sim | Desculpe, não tenho essa informação nos meus docum | IRRELEVANTE,IRRELEVANTE,IRRELEVANTE,RELEVANTE,RELEVANTE | parcial | DESAMBIGUACAO_DESNECESSARIA + GERADOR_RECUSOU |
| fora-10:T3 | ctx>qv>gen>av>gen>av>hist>av | ctx>qv>gen>av>gen>av>hist>av | escalonamento/ESC | 2 | 0.51 (#50) | 0.65 Como faço para analisar meus dados  | []/[]/não | Desculpe, não tenho essa informação nos meus docum | IRRELEVANTE,IRRELEVANTE,IRRELEVANTE | escalou | FAQ_NAO_CASOU + RETRIEVER_ERROU |
| faq-03:T3 | ctx>qv>dis | ctx>qv>dis | rag | 3 | - | - | - | - |  | errada | DESAMBIGUACAO_DESNECESSARIA |
| faq-03:T4 | ctx>qv>gen>av>gen>av>hist>av | ctx>qv>qv>av>qv>gen>av>gen>av | escalonamento/ESC | 1 | 0.91 (#1) | 0.91 Recebi um aviso de inadimplência, o | [15]/[2]/sim | Desculpe, não tenho essa informação nos meus docum | RELEVANTE,IRRELEVANTE,RELEVANTE | correta | GERADOR_RECUSOU |
| conf-03:T3 | ctx>qv>dis | ctx>qv>dis | rag | 4 | - | - | - | - |  | errada | DESAMBIGUACAO_DESNECESSARIA |
| conf-03:T4 | ctx>qv>av | ctx>qv>av | faq | 9 | 0.84 (#1), 0.54 (#26) | 0.84 recebi um boleto diferente dizendo  | - | - | RELEVANTE | correta | ok |
| conf-03:T5 | qv>dis | qv>dis | rag | 2 | - | - | - | - |  | errada | DESAMBIGUACAO_DESNECESSARIA |
| faq-23:T3 | qv>gen>av>gen>av>hist>av | qv>gen>av>gen>av>hist>av | escalonamento/ESC | 1 | 0.64 (#16) | 0.70 O que é o oncorretor? | [4]/[2]/sim | Desculpe, não tenho essa informação nos meus docum | IRRELEVANTE,IRRELEVANTE,IRRELEVANTE | escalou | FAQ_NAO_CASOU + GERADOR_RECUSOU |
| rag-02:T3 | ctx>qv>qv>dis>qv>dis | ctx>qv>dis | rag | 1 | - | - | - | - |  | errada | DESAMBIGUACAO_DESNECESSARIA |
| rag-02:T4 |  |  | escalonamento/ESC | 6 | - | - | - | - |  | escalou |  |
| multi-09:T3 | qv>qv>dis>gen>av>gen>av>hist>av>qv>gen>av>gen>av>hist>av | qv>qv>dis>qv>gen>av>gen>av>hist>av | escalonamento/ESC | 1 | 0.50 (#64), 0.48 (#85) | 0.60 Meu acesso ao sistema está com prob | [1]/[1]/sim | AMBIGUO | IRRELEVANTE,IRRELEVANTE,IRRELEVANTE | errada | FAQ_NAO_CASOU |
| follow-01:T3 | ctx>qv>dis | ctx>qv>dis | rag | 4 | - | - | - | - |  | errada | DESAMBIGUACAO_DESNECESSARIA |
| follow-01:T4 | ctx>qv>av | ctx>qv>av | faq | 8 | 0.72 (#13) | 0.81 Como faço para aderir ao OnCorretor | - | - | RELEVANTE | parcial | ok |
| follow-01:T5 | qv>gen>av>gen>av>hist>av | qv>gen>av>gen>av>hist>av | escalonamento/ESC | 2 | 0.35 (#108) | 0.49 Com quem eu falo para tirar dúvidas | [3]/[1]/sim | AMBIGUO | IRRELEVANTE,IRRELEVANTE,IRRELEVANTE | escalou | FAQ_NAO_CASOU |
| rag-22:T3 | ctx>qv>dis | ctx>qv>gen>av | rag | 3 | sem FAQ | 0.74 Quero mudar o domínio, mas manter o | [6]/[12]/não | Para enviar documentos ou informações para nossa e | RELEVANTE | errada | DESAMBIGUACAO_DESNECESSARIA + RETRIEVER_ERROU |
| rag-22:T4 | ctx>qv>gen>av>gen>av>hist>av | ctx>qv>gen>av>gen>av>hist>av | escalonamento/ESC | 2 | sem FAQ | 0.68 O site não está aparecendo no Googl | [1]/[1]/sim | Desculpe, não tenho essa informação nos meus docum | IRRELEVANTE,IRRELEVANTE,IRRELEVANTE | escalou | GERADOR_RECUSOU |
| faq-22:T3 | ctx>qv>dis | ctx>qv>dis | rag | 3 | - | - | - | - |  | errada | DESAMBIGUACAO_DESNECESSARIA |
| faq-04:T3 | ctx>qv>qv>dis>qv>dis | ctx>qv>dis | rag | 0 | - | - | - | - |  | errada | DESAMBIGUACAO_DESNECESSARIA |
| faq-09:T2 | qv>gen>av | qv>gen>av>gen>av>hist>av | rag | 0 | 0.75 (#2), 0.75 (#1) | 0.75 O que é o ClubeVip? | [1]/[1]/sim | Desculpe, não tenho essa informação nos meus docum | IRRELEVANTE,IRRELEVANTE,IRRELEVANTE | escalou | FAQ_NAO_CASOU + GERADOR_RECUSOU |
| faq-09:T3 | ctx>qv>dis | ctx>qv>dis | rag | 3 | - | - | - | - |  | errada | DESAMBIGUACAO_DESNECESSARIA |
| faq-09:T4 | ctx>qv>av | ctx>qv>qv>dis>qv>dis | faq | 10 | - | - | - | - |  | errada | ok |
| faq-15:T3 | ctx>qv>gen>av>gen>av>hist>av | ctx>qv>dis | escalonamento/ESC | 1 | - | - | - | - |  | errada |  |