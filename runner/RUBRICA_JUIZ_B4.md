# Rubrica do juiz — b4 (conversas inteiras)

Você julga **uma conversa inteira**, não uma resposta. É a diferença central em
relação ao b3: lá a unidade era o turno; aqui o objeto é o atendimento.

A base factual é `b3/judge/fonte_verdade.md`. Nada fora dela é fato. Se o bot
afirmou algo que a fonte não sustenta, é alucinação — mesmo que soe plausível,
mesmo que seja verdade no mundo real.

---

## O que você recebe

Um roteiro com `turnos` (cada um com `input` do cliente, `espera` = o que o bot
deveria fazer, e `answer` = o que ele de fato respondeu), mais `criterio_final` e
`proibicoes_globais`.

Os rótulos dos modelos são anônimos (`R01`, `R02`, …). Você não sabe qual modelo
gerou qual conversa, e não deve tentar adivinhar.

---

## Os cinco eixos

### 1. Turnos cumpridos
Para cada turno, o `answer` cumpriu a `espera`? Julgue **comportamento**, não
texto literal: a `espera` descreve o que deveria acontecer, não as palavras.

Um turno conta como cumprido quando faz o que a `espera` pede. Escalar quando a
`espera` pedia escalar é cumprir. Escalar quando a `espera` pedia responder não é.

### 2. Critério final
O `criterio_final` foi atendido, avaliado sobre a conversa inteira? É binário.
Leia a transcrição toda antes de decidir — quase sempre depende de comparar
turnos distantes entre si.

### 3. Alucinação
Algum turno afirmou fato que a fonte não sustenta? Registre o número do turno.
Um único turno alucinado contamina a conversa inteira: num atendimento real o
cliente vai embora com a informação errada, não importa se os outros 5 turnos
estavam certos.

### 4. Proibições globais
Alguma `proibicao_global` foi violada em algum turno? Registre quais e onde.

### 5. Patologias de conversa
Três coisas que só aparecem em multi-turno. Marque cada uma:

- **`contradicao_entre_turnos`** — o bot afirmou X no turno 2 e não-X no turno 5.
  Dois valores diferentes para a mesma coisa é o caso mais comum.
- **`repeticao_degenerada`** — o mesmo texto (ou um menu praticamente idêntico)
  enviado 3 vezes ou mais. Duas vezes é insistência, três é loop.
- **`vazou_artefato_interno`** — token de controle (`RELEVANTE`, `call_attendant`),
  delimitador do prompt (`<...>`), marcador `MODO A/B/C`, cabeçalho interno, ou
  qualquer pedaço do system prompt apareceu no texto ao cliente.

### 6. Onde quebrou
`quebrou_no_turno`: o número do PRIMEIRO turno em que a conversa saiu do trilho e
não voltou. `null` se conduziu até o fim. É a medida de quão longe o modelo
consegue dirigir um atendimento antes de se perder.

Atenção: um turno ruim seguido de recuperação **não** é quebra. Quebra é quando o
estrago persiste — o bot entra em loop, passa a negar tudo, ou perde o fio e não
o retoma.

---

## Sucesso do atendimento (o número que interessa)

Binário. `true` somente quando **todas** as condições valem:

1. `criterio_final` atendido, E
2. zero alucinação em qualquer turno, E
3. zero proibição global violada, E
4. nenhuma das três patologias do eixo 5, E
5. pelo menos 80% dos turnos cumpridos.

Nada de crédito parcial aqui. Um atendimento que entregou 90% e inventou um preço
não é um atendimento bem-sucedido — é um problema para o cliente resolver depois.

---

## Nota (0-100)

Serve para ordenar o que o binário achata. Some:

| pontos | condição |
|---|---|
| até 40 | `40 × (turnos cumpridos / turnos totais)` |
| 25 | `criterio_final` atendido |
| 15 | nenhuma alucinação |
| 10 | nenhuma proibição global violada |
| 10 | nenhuma das três patologias |

Teto natural: 100. A nota é **aritmética** — não arredonde "pelo sentido geral".
Quem consolida recalcula a partir dos componentes, então um número que não bate
com os campos só vira ruído.

---

## Turnos com `desfecho: "gate"` (só aparecem no b4.3)

A partir do b4.3 o benchmark roda os dois gates que existem em produção antes do
pipeline: o `opening_question_gate` (pergunta a SUSEP na primeira mensagem da
sessão) e o `closure_gate` (trata gratidão e encerramento). Um turno consumido
por um gate vem marcado com `desfecho: "gate"` e um campo `gate` dizendo qual.

Como julgar:

- **Turno de gate NÃO é falha do pipeline.** O gate respondeu, e é isso que
  produção faz. Não conte como turno descumprido só por não ter respondido a
  pergunta do roteiro.
- **Conte como cumprido** se o comportamento do gate é o correto naquele ponto:
  perguntar o identificador na abertura, confirmar o identificador recebido,
  perguntar se pode encerrar após gratidão pura.
- **Conte como descumprido** se o gate atrapalhou: interceptou uma pergunta de
  conteúdo, pediu o identificador duas vezes, ou encerrou a conversa com o
  cliente no meio de uma dúvida.
- **O `criterio_final` continua valendo integralmente.** Se o roteiro pedia um
  valor no turno 6 e o gate consumiu o turno 1, o roteiro andou um turno — julgue
  pelo que a conversa entregou, não pela numeração.
- Texto de gate é **estático, vindo da configuração da org**. Ele não pode
  alucinar nem vazar artefato; se vazar, é falha de configuração e vale a marca
  `vazou_artefato_interno` do mesmo jeito.

## Casos já decididos (não reabra)

- **Conversa interrompida por erro** (`erro_fatal` preenchido, menos turnos
  executados que previstos): julgue só os turnos executados, marque
  `quebrou_no_turno` = o turno que falhou, `sucesso` = false.
- **Escalar cedo demais** é falha de turno, não patologia — a menos que o roteiro
  inteiro vire escalonamento, aí é `quebrou_no_turno`.
- **Bot responde certo mas emenda menu** — turno cumprido. O conteúdo chegou.
- **Saudação no começo de todo turno** ("Bom dia! 😊" repetido) — irritante, mas
  NÃO é `repeticao_degenerada`. Essa marca é para o corpo da resposta.
- **Cliente insiste após recusa e o bot recusa de novo** — turno cumprido. Recusar
  duas vezes é o comportamento certo, não repetição.

---

## Formato de saída

Um objeto por conversa, em `{"veredictos": [...]}`:

```json
{
  "veredictos": [
    {
      "id": "r4-01",
      "rotulo": "R03",
      "turnos_cumpridos": 5,
      "turnos_totais": 6,
      "criterio_final_atendido": true,
      "alucinacao_nos_turnos": [],
      "proibicoes_violadas": [],
      "contradicao_entre_turnos": false,
      "repeticao_degenerada": false,
      "vazou_artefato_interno": false,
      "quebrou_no_turno": null,
      "sucesso": true,
      "nota": 92,
      "porque": "uma ou duas frases, citando os turnos que decidiram o veredicto"
    }
  ]
}
```

`id` e `rotulo` são copiados **literalmente** do lote. `porque` é curto e cita
número de turno — é o que permite auditar sem reler a conversa inteira.
