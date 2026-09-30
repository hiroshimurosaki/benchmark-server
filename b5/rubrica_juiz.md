COMO DAR A NOTA (calibrado em 224 julgamentos do juiz anterior — siga estas faixas)

Decida primeiro os campos categóricos; a nota_geral decorre deles.

1. objetivo_cumprido
   - true: o cliente saiu com a informação ou o encaminhamento que precisava, OU o bot
     recusou/transferiu quando esse era o comportamento esperado.
   - false: o principal ficou sem resposta, veio errado, ou o bot transferiu sem precisar.

2. escalonamento
   - "desnecessario": o documento ou o FAQ respondiam e o bot transferiu. É a falha mais grave.
   - "faltou": o cliente pediu uma pessoa, ou era caso de humano (estorno, erro na conta), e o bot não transferiu.
   - "adequado": transferiu e era preciso. "nao_se_aplica": não transferiu e não era preciso.

3. alucinacao.houve = true só com trecho do bot que CONTRADIZ ou NÃO ESTÁ no documento/FAQ
   (menu, campo, passo, prazo, valor, e-mail, promessa "nossa equipe vai..."). Copie o trecho exato.
   Paráfrase fiel do documento NÃO é alucinação. Na dúvida, procure o fato no documento antes de marcar.
   Não contam: saudação, pedido de SUSEP, mensagem de transferência, o portal ajuda.oncorretor.com.br,
   o e-mail atendimento@oncorretor.com.br como canal de solicitação.

4. cliente_satisfeito: "sim" resolveu sem atrito; "parcial" resolveu com atrito (pediu para repetir,
   resposta longa ou fora do ponto, um turno ruim); "nao" saiu sem solução ou irritado.

5. nota_geral (0-10) — FAIXAS OBRIGATÓRIAS:
   - 9 a 10: objetivo cumprido, satisfeito "sim", sem alucinação, sem turno fraco.
   - 7 a 8:  objetivo cumprido, no máximo um atrito leve, sem alucinação.
   - 5 a 6.5: objetivo cumprido com atrito relevante, OU com alucinação menor que não engana o cliente.
   - 3 a 4.5: objetivo NÃO cumprido, ou alucinação que leva o cliente a fazer algo errado,
             ou "faltou" escalonamento.
   - 1 a 2.5: escalonamento "desnecessario" logo no início, ou resposta errada que o cliente
             seguiria, ou satisfeito "nao".
   Tetos: objetivo_cumprido=false → no máximo 5.5. escalonamento "desnecessario" → no máximo 5.5
   (e 2.5 se foi o desfecho da conversa). alucinacao.houve=true → no máximo 8.
   satisfeito "sim" → no mínimo 5.5. satisfeito "nao" → no máximo 4.
   Use meio ponto (ex.: 6.5). A nota_geral costuma ficar ~0.5 acima da nota_qualidade quando o
   desfecho é bom, e abaixo quando o desfecho é ruim.

6. Seja consistente: duas conversas com o mesmo desfecho recebem a mesma faixa.
