# benchmark-server

Benchmarks de modelos locais (Ollama no servidor `ianode`) para o Doc Assist. O plano
canônico, com decisões e histórico de cada rodada, é o [PLANO.md](PLANO.md).

## Estrutura

| Pasta | O que tem |
|---|---|
| `projetos/b1/` | b1 — tool-call/JSON do analista de condomínio: perguntas, schema, prompt, runner, score, dashboard |
| `projetos/b2/` | b2 — RAG com a KB do OnCorretor colada no prompt: perguntas (também usadas pelo b3), KB, conversas reais |
| `projetos/b3/` | b3 — pipeline RAG real (Answer_service) por etapa: bundle da org (`data/`), runner, juiz, dashboard, resultados |
| `projetos/b4/` | b4 — conversas inteiras (roteiros multi-turno) contra o pipeline do b3; b4.2 prompt enxuto, b4.3 gates |
| `projetos/b5/` | reservado — b5 (conversa dinâmica) vem da branch `b5-conversa-dinamica` |
| `comum/` | código usado por mais de um projeto: `b3_env.py` (b3+b4), `gates_harness.py` (+ teste), `modelos/` (catálogo e rosters Groq/Cohere) |
| `infra/` | servidor: `server/` (notas/comandos), `monitor/` (monitor ao vivo + bandeja), `modelos/` (registrar/baixar modelos no Ollama), `sysmon.py` |
| `docs/` | diagramas gerais do ciclo do benchmark |

Dentro de cada projeto: `runner/` é o código específico; dados, rubrica, handoffs, dashboard
e resultados ficam na raiz da pasta do projeto.

### Dependências entre projetos (deliberadas)

- **b1 → b2:** `projetos/b1/runner/run_bench.py` roda b1 **e** b2 (`--bench b1,b2`); o b2 nunca teve runner próprio.
- **b3 → b2:** o b3 usa as 50 perguntas de `projetos/b2/questions_b2.jsonl`.
- **b4 → b3:** o b4 roda contra o bundle do b3 (`--root projetos/b3`: `data/` + índice FAISS),
  importa `run_b3.py` (StageRecorder, warmup, resume) e o juiz usa `projetos/b3/judge/fonte_verdade.md`.

## Como rodar

Python do PC: `../rag-chatbot/env/Scripts/python.exe` (os runners do b3/b4 importam o
`Answer_service` do repo `rag-chatbot`, achado via `--repo` ou ao lado deste repo).

**b1 / b2** (roda no servidor; pasta de trabalho = `projetos/b1/runner`)
```bash
cd projetos/b1/runner
python3 run_bench.py --root . --bench b1,b2 [--models models_smoke.jsonl --limit 5] [--dry-run]
python3 score_b1.py                     # -> projetos/b1/scored_b1.json
python3 dashboard_b1.py --root .        # -> projetos/b1/dashboard_b1.json (abrir dashboard_b1.html)
```
`projetos/b1/sync_dashboard.bat` puxa o `dashboard_b1.json` do servidor a cada 15 s.

**b3** (bundle = `projetos/b3`; no servidor vira `~/benchmark/b3`)
```bash
bash projetos/b3/runner/deploy_b3.sh     # envia o bundle (runner/ achatado + data/ + código do rag-chatbot)
# no servidor, em ~/benchmark/b3:
.venv/bin/python runner/build_index.py --root . --scales 1,5,20 --repeat 2
.venv/bin/python runner/run_b3.py --root . --all-questions --out results_b3.jsonl
# no PC, via Groq, a partir de projetos/b3:
python runner/run_b3.py --root . --provider groq --repo ../../../rag-chatbot \
  --models ../../comum/modelos/models_groq.jsonl --questions ../b2/questions_b2.jsonl --out results_groq.jsonl
# juiz (da raiz do repo):
python projetos/b3/runner/make_judge_packets.py --results ... --questions projetos/b2/questions_b2.jsonl --out projetos/b3/judge
python projetos/b3/runner/merge_judge.py --dir projetos/b3/judge --out projetos/b3/scored_b3.json
```
Ao vivo: `projetos/b3/sync_dashboard_b3.bat` → `projetos/b3/live/`; no `dashboard_b3.html`,
"Acompanhar ao vivo" e escolher essa pasta.

**b4** (da raiz do repo)
```bash
python projetos/b4/runner/run_b4.py --root projetos/b3 --dry-run
python projetos/b4/runner/run_b4.py --root projetos/b3 --repo ../rag-chatbot            # -> projetos/b4/results_b4.jsonl
python projetos/b4/runner/run_b4.py --root projetos/b3 --repo ../rag-chatbot --gates --out projetos/b4/results_b4_3.jsonl
python projetos/b4/runner/make_judge_packets_b4.py      # -> projetos/b4/judge/
python projetos/b4/runner/merge_judge_b4.py             # -> projetos/b4/veredictos_b4.json
```
Dashboard: `projetos/b4/dashboard_b4.html` (arraste os pares `results_*` + `veredictos_*`).

**Testes do harness de gates:** `python -m pytest comum/test_gates_harness.py -q`

**Monitor do servidor:** `infra/monitor/monitor_servidor.bat` (janela) ou
`infra/monitor/instalar_monitor.ps1` (ícone na bandeja + perfil do Windows Terminal).

## Onde ficam os resultados

- Cada projeto grava na própria pasta: `projetos/b1/results_b1.jsonl`, `projetos/b2/results_b2.jsonl`,
  `projetos/b3/results_*.jsonl`, `projetos/b4/results_b4*.jsonl`.
- `results_*.jsonl`, `scored_*.json` e `run.log` são **gitignored** (vivem no servidor/PC);
  o que está versionado são os consolidados: `projetos/b3/live/*.json`, `projetos/b3/judge/`,
  `projetos/b4/veredictos_*.json`, `projetos/b4/judge*/`, `projetos/b1/dashboard_b1.json`.
- Segredos ficam em `access/` (gitignored) — nunca versionar.
