# b4 — esquema dos roteiros

Um roteiro é uma conversa inteira: 5-8 turnos do cliente, **fixos**, na mesma
sessão (mesmo telefone → o histórico acumula de verdade).

## Por que turnos fixos e não cliente simulado por LLM

Cliente simulado é mais realista, mas cada modelo receberia uma conversa
diferente, e aí metade da variação medida vem do simulador, não do modelo sob
teste. Com roteiro fixo os N modelos enfrentam a sequência idêntica e a
diferença é deles. O preço é alguma artificialidade quando o bot erra cedo e o
turno seguinte não encaixa — e isso é justamente o que a avaliação sobre a
transcrição inteira precisa capturar.

## Formato (uma linha JSON por roteiro)

```json
{
  "id": "r4-01",
  "nome": "frase curta que descreve a conversa",
  "trilha": "memoria | fidelidade | resistencia_progressiva | repeticao",
  "turnos": [
    {"n": 1, "input": "texto do cliente", "espera": "o que o bot deveria fazer NESTE turno"}
  ],
  "criterio_final": "o que define sucesso, avaliado sobre a transcrição INTEIRA",
  "proibicoes_globais": ["coisa que o bot não pode fazer em NENHUM turno"]
}
```

## As quatro trilhas

| trilha | o que mede | o b3 media? |
|---|---|---|
| `memoria` | lembra no turno 5 do que foi dito no turno 2 | não |
| `fidelidade` | responde certo ao longo da conversa, sem inventar | parcialmente |
| `resistencia_progressiva` | ataque no turno 6 depois de 5 turnos amigáveis | **não** — e é o prêmio |
| `repeticao` | repete menu já dado? re-pergunta o já respondido? | não |

## Regras de escrita dos turnos

1. **O turno N+1 não pode depender de acerto no turno N.** Ele assume o fluxo
   natural, mas tem que fazer sentido mesmo se o bot errou antes — senão a
   medição vira "o bot acertou o turno 1?" repetida.
2. **Follow-up com pronome é obrigatório** em pelo menos um turno de cada
   roteiro ("e quanto custa isso?", "e se eu cancelar?") — é o que testa o
   contextualizador.
3. **Fundamento na fonte.** Toda expectativa de conteúdo sai de
   `projetos/b3/judge/fonte_verdade.md`. Se a fonte não cobre, a expectativa é escalar.
4. `espera` descreve COMPORTAMENTO, não texto literal — o juiz avalia sentido.
5. Um roteiro tem 5 a 8 turnos. Menos que 5 não acumula estado suficiente;
   mais que 8 estoura a janela de histórico do pipeline e mede outra coisa.
6. **Na trilha `memoria`, o fato a ser lembrado deve vir do CLIENTE, não do bot.**
   Se o turno 6 pergunta "lembra o valor que VOCÊ me falou?", ele só funciona
   caso o bot tenha acertado o turno 3 — e aí a regra 1 é violada: mede-se
   recuperação de novo, não memória. Se o turno 6 pergunta "lembra quanto de
   produção EU te falei?", o fato entrou pela conversa e a memória fica isolada
   das outras etapas do pipeline.

   `r4-01` é a exceção conhecida: ele pergunta pelo valor que o BOT disse, então
   mede consistência-consigo-mesmo, não memória pura. Foi mantido de propósito —
   contradizer-se entre turnos é falha real e vale medir — mas não sirva dele de
   modelo ao escrever roteiros novos de `memoria`.
