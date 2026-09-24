# Handoff — b4.3: rodar o benchmark no ambiente COMPLETO

Para o Muse Spark 1.3, no OpenCode. Tarefa de **implementação**, não de análise.

Raiz: `C:\Users\fernando.murusaki\benchmark-server`
Repo do produto (só leitura): `C:\Users\fernando.murusaki\rag-chatbot`

---

## Por que isso existe

O benchmark hoje chama `processor.answer_user_question` direto. Produção não faz
isso — ela passa por `ai_subscriber._handle_ai_message`, que roda **dois gates
antes** do pipeline. E a org de teste tem os dois ligados:

```
features.ai.opening_question.enabled        = True
features.ai.opening_question.text           = "Olá! 😊 Antes de começar, qual é a sua SUSEP?"
features.ai.opening_question.field          = "susep"
features.ai.opening_question.identifier_regex = "^[A-Za-z0-9]{6}[FfJj]$"
features.ai.auto_close_on_gratitude.enabled = True
```

Ou seja: **em produção, a primeira mensagem de toda sessão recebe a pergunta da
SUSEP**, não o pipeline. E "muito obrigado" dispara o fluxo de encerramento. As
90 conversas já medidas ignoram os dois. Elas medem uma conversa que produção
nunca tem.

Sua tarefa é fechar esse buraco.

---

## ARQUIVOS QUE VOCÊ PODE CRIAR/EDITAR

- `runner/gates_harness.py` — **novo, é o seu entregável**
- `runner/test_gates_harness.py` — **novo, os testes**

**RESERVADOS — não toque:** `runner/run_b4.py`, `runner/run_b3.py`,
`runner/b3_env.py`, `runner/merge_judge*.py`, qualquer coisa em `b4/judge/`,
e o repo `rag-chatbot` inteiro (leitura sim, escrita não).

Eu faço a integração no `run_b4.py` depois, a partir do seu módulo.

---

## O contrato — a API exata que eu vou chamar

```python
# runner/gates_harness.py

@dataclass
class ResultadoGates:
    continuar: bool          # True = a mensagem deve seguir para o pipeline RAG
    mensagens: list[str]     # o que o gate enviou ao cliente (vazio se não enviou)
    quem: str                # "" | "opening_question" | "closure"

def carregar_features_gates(settings: dict):
    """Recebe o dict de `b3/data/oncorretor/settings.json` e devolve
    (opening_question, auto_close) como objetos duck-type compatíveis com o que
    os gates esperam. Campo ausente = feature desligada, nunca exceção."""

def rodar_gates(body: str, phone: str, org_id: str, opening_question, auto_close) -> ResultadoGates:
    """Roda opening_question_gate e depois closure_gate, na MESMA ordem do
    ai_subscriber (opening primeiro, closure depois). Síncrona por fora —
    embrulhe o asyncio internamente. Nunca levanta exceção: se um gate
    quebrar, registre e devolva continuar=True (degrada para o comportamento
    de hoje, que é o pipeline puro)."""
```

`rodar_gates` é **síncrona por fora** de propósito: o `run_b4.py` é um laço
síncrono e eu não quero async vazando para ele.

---

## Referências no repo do produto (leia antes de escrever)

| o quê | onde |
|---|---|
| como o ai_subscriber chama os dois gates, na ordem | `Answer_service/src/services/ai_subscriber.py:861-895` |
| assinatura do opening gate | `Answer_service/src/services/opening_question_gate.py:241` |
| assinatura do closure gate | `Answer_service/src/services/closure_gate.py:213` |
| os dataclasses das features | `Answer_service/src/services/ai_subscriber.py` (`OpeningQuestionFeature`, `AutoCloseOnGratitudeFeature`) |
| como o harness monta features hoje (o molde) | `runner/b3_env.py:141-170` (`_load_org_context`) |

Repare que o `_AiFeature` do `b3_env.py:90` tem **só** `enabled` e
`confidence_threshold`. Os campos dos gates não existem lá — é por isso que você
precisa de `carregar_features_gates`.

---

## PRIMEIRO PASSO — investigue antes de implementar

Três coisas podem quebrar, e eu quero sua leitura sobre elas ANTES do código
final. Anote o que achou no relatório.

1. **Firestore está stubado no benchmark** (`runner/b3_env.py:45`
   `_install_firebase_stub`). Os dois gates chamam `_persist_bot_msg_firestore`.
   Isso estoura, loga e segue, ou trava? Se estourar, o gate precisa ser
   chamado de um jeito que absorva — mas **sem** engolir a decisão dele
   (o bool de retorno tem que continuar valendo).

2. **`closure_gate` pode chamar `resolve_ticket` no Gateway** (caminho
   Q→confirmação). Não existe Gateway no benchmark. Descubra o que acontece e
   trate — o correto é a conversa seguir registrada como encerrada, não morrer.

3. **`get_session_context` / `update_session_context`** leem e escrevem o mesmo
   arquivo JSON de histórico que o pipeline usa. Confirme que funcionam com o
   telefone do benchmark (`bench4-<modelo>-<roteiro>`) e que o
   `run_b4.py` apagando o arquivo entre roteiros também limpa o contexto do
   gate — senão a SUSEP capturada num roteiro vaza para o próximo.

O item 3 é o que mais me preocupa. Se o contexto vazar entre roteiros, o gate
não pergunta a SUSEP na segunda conversa e a medição fica errada em silêncio.

---

## Testes obrigatórios (`runner/test_gates_harness.py`)

Rode com `..\rag-chatbot\env\Scripts\python.exe -m pytest runner/test_gates_harness.py -q`

1. **Feature desligada não intercepta.** `opening_question.enabled = False` →
   `continuar=True`, `mensagens=[]`.
2. **Primeira mensagem da sessão é interceptada.** Sessão limpa, feature ligada →
   `continuar=False`, `mensagens` contém o texto da SUSEP, `quem="opening_question"`.
3. **Resposta com identificador válido é aceita.** Depois do teste 2, mandar
   `"123456F"` (casa com o regex) → o gate captura, e o `susep` fica no contexto.
4. **Gratidão dispara o closure.** Com `auto_close.enabled=True` e sessão em
   andamento, `"muito obrigado!"` → `continuar=False`, `quem="closure"`.
5. **Mensagem comum passa pelos dois.** `"como funciona a cobrança?"` numa sessão
   que já tem SUSEP → `continuar=True`, `mensagens=[]`.
6. **Isolamento entre roteiros.** Rodar o teste 2, apagar o histórico como o
   `run_b4.py` faz (`get_history_file_path(get_session_id(phone, org))`), rodar o
   teste 2 de novo com o MESMO telefone → tem que interceptar de novo. Se não
   interceptar, o contexto vazou e o item 3 acima é um bug real — reporte.
7. **Gate quebrado degrada.** Injete uma exceção e verifique `continuar=True`.

Use telefones distintos por teste (`test-gates-<n>`) e limpe o histórico no
setup, senão os testes se contaminam entre si.

---

## Relatório final (máx 15 linhas)

- O que respondeu aos três pontos da investigação, com o que observou de fato.
- Quais testes passam (cole a saída do pytest).
- Qual comportamento você teve que decidir sozinho porque o contrato não cobria.
- **Qualquer ponto em que você achou que o gate faria X e ele faz Y.** É a parte
  mais valiosa do relatório — eu vou integrar isso no `run_b4.py` no escuro.

Não cole diffs grandes. Não commite nada.
