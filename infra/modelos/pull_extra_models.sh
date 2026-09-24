#!/usr/bin/env bash
# Baixa a 2a leva de modelos oficiais do registro Ollama (ollama pull).
# Roda NO servidor, em tmux. Continua mesmo se um pull falhar (tag errada / rede).
# Uso: bash pull_extra_models.sh
set -u
MODELS=(
  qwen2.5:3b
  qwen2.5:7b
  qwen2.5-coder:7b
  llama3.2:3b
  llama3.1:8b
  gemma2:9b
  mistral:7b
  granite3.1-dense:8b
  hermes3:8b
  qwen2.5:14b
  qwen2.5:32b
  mistral-nemo:12b
  gemma2:27b
  phi4:14b
  command-r:35b
  llama3.3:70b
)
echo "== disco antes =="; df -h / | tail -1
for m in "${MODELS[@]}"; do
  echo "== pull $m ($(date +%T)) =="
  if ollama pull "$m"; then echo "OK $m"; else echo "FALHOU $m"; fi
done
echo "== disco depois =="; df -h / | tail -1
echo "== ollama list =="; ollama list
echo "== PULL 2a LEVA CONCLUIDO =="
