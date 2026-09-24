#!/bin/bash
# b3 — envia o bundle para o servidor. Roda no PC do Fernando (Git Bash).
#
#   bash projetos/b3/runner/deploy_b3.sh      (da raiz do repo)
#
# Envia: projetos/b3/runner/ + comum/b3_env.py (achatados em runner/ no servidor),
# projetos/b2/questions_b2.jsonl, projetos/b3/data/ (corpus+FAQ+DTQ reais) e uma
# cópia enxuta do Answer_service/Document_service do repo rag-chatbot.
# NÃO envia: serviceAccountKey.json, .env, nada de credencial — o harness usa
# stub de Firebase (comum/b3_env.py).
set -euo pipefail

HOST="${B3_HOST:-fernando.murusaki@10.10.10.151}"
KEY="${B3_KEY:-$HOME/.ssh/id_benchmark}"
DEST="${B3_DEST:-~/benchmark/b3}"
BENCH_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"   # raiz do repo benchmark-server
B3_DIR="$BENCH_DIR/projetos/b3"
REPO_DIR="${B3_REPO:-$BENCH_DIR/../rag-chatbot}"

SSH="ssh -i $KEY -o BatchMode=yes $HOST"
say() { printf '\n\033[1m== %s\033[0m\n' "$1"; }

say "preparando destino"
$SSH "mkdir -p $DEST/runner $DEST/b2 $DEST/data $DEST/repo"

say "runner + perguntas"
scp -q -i "$KEY" "$B3_DIR"/runner/{run_b3.py,build_index.py,report_b3.py,models_b3.jsonl} "$BENCH_DIR/comum/b3_env.py" "$HOST:$DEST/runner/"
scp -q -i "$KEY" "$BENCH_DIR/projetos/b2/questions_b2.jsonl" "$HOST:$DEST/b2/"

say "dados reais da org (corpus + FAQ + DTQ + settings)"
scp -qr -i "$KEY" "$B3_DIR/data/." "$HOST:$DEST/data/"

say "codigo do Answer_service / Document_service"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
for pkg in Answer_service Document_service; do
  # --exclude precisa vir antes do source no tar do Git Bash
  tar -C "$REPO_DIR" \
      --exclude='__pycache__' --exclude='*.pyc' --exclude='memory/*.json' \
      --exclude='serviceAccountKey.json' --exclude='.env' \
      --exclude='node_modules' --exclude='*.faiss' --exclude='*.pkl' \
      -czf "$TMP/$pkg.tgz" "$pkg"
done
scp -q -i "$KEY" "$TMP"/*.tgz "$HOST:$DEST/repo/"
$SSH "cd $DEST/repo && for f in *.tgz; do tar xzf \$f && rm \$f; done && \
      touch Answer_service/__init__.py Document_service/__init__.py 2>/dev/null; \
      mkdir -p Answer_service/memory; ls -d */"

say "checagem de credencial vazada (deve nao imprimir nada)"
$SSH "find $DEST -name 'serviceAccountKey.json' -o -name '.env' | head"

say "sanidade do bundle"
$SSH "cd $DEST && .venv/bin/python runner/b3_env.py ."

printf '\n\033[1mpronto.\033[0m proximo passo no servidor:\n'
printf '  ssh -i %s %s\n' "$KEY" "$HOST"
printf '  cd %s && .venv/bin/python runner/build_index.py --root . --scales 1,5,20 --repeat 2\n' "$DEST"
