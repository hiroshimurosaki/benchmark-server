#!/usr/bin/env bash
# Registra os GGUF do cache HF como tags Ollama bench-<x> (idempotente: ollama create sobrescreve).
# Roda NO SERVIDOR (ianode / 10.10.10.151), usuario nicolas.benedetti.
# NAO registra gpt-oss:20b nem qwen3.6:35b-a3b (ja existem no ollama).
# Uso:  bash register_models.sh [--smoke]
#   --smoke: registra so os 3 modelos do smoke (bench-lfm25, bench-q4b; gpt-oss ja existe).
set -u
HF="$HOME/.cache/huggingface/hub"

# tag -> caminho do gguf principal (ignora mmproj-*)
declare -A M=(
  [bench-lfm25]="$HF/models--LiquidAI--LFM2.5-2.6B-GGUF/snapshots/b421ad1d549afeda6a0fb2ad3a697cb5a7879adc/LFM2.5-2.6B-Q4_K_M.gguf"
  [bench-q4b]="$HF/models--unsloth--Qwen3-4B-GGUF/snapshots/22c9fc8a8c7700b76a1789366280a6a5a1ad1120/Qwen3-4B-Q4_0.gguf"
  [bench-llama2-7b]="$HF/models--vishanoberoi--Llama-2-7b-chat-hf-finedtuned-to-GGUF/snapshots/bce7ec05d57f2bd1f8b45cf12986e55aa5dc0760/finetuned-16b.gguf"
  [bench-forecaster8b]="$HF/models--mradermacher--LlamaForecaster-8B-i1-GGUF/snapshots/781c6cd51069ed9b864989f8facca8b85b6a6cd1/LlamaForecaster-8B.i1-Q4_K_M.gguf"
  [bench-qwen38-9b]="$HF/models--empero-ai--Qwen3.8-9B-GGUF/snapshots/760121cd70bb4c36b2b5ec58eb765e0df5987efe/Qwen3.8-9B-Q4_K_M.gguf"
  [bench-deepseek-9b]="$HF/models--Jackrong--DeepSeek-V4-Pro-Qwen3.5-9B-MTP-GGUF/snapshots/41a445e05e3a056c092a3bde32fe2f759e6e2197/DeepSeek-V4-Pro-Qwen3.5-9B-MTP-Q4_K_M.gguf"
  [bench-defiant-9b]="$HF/models--DavidAU--Qwen3.5-9B-The-Defiant-Fable-Uncensored-Heretic-NEO-IMATRIX-MAX-MTP-GGUF/snapshots/d9796b37168d3bd3a6f963e5f4d08bff869adc13/Qwen3.5-9B-The-Defiant-Fable-Uncnr-Heretic-NEO-MAX-MTP-Q4_K_M.gguf"
  [bench-qwen38-27b]="$HF/models--unsloth--Qwen3.8-27B-GGUF/snapshots/f1bfb127c64f7072bdd2cad55f258b9c8b2910fe/Qwen3.8-27B-Q4_K_M.gguf"
  [bench-qwen36-27b-mtp]="$HF/models--unsloth--Qwen3.6-27B-MTP-GGUF/snapshots/5cb35eb3dcbf52dbce5f87dbc64df6aaffadcace/Qwen3.6-27B-Q4_K_M.gguf"
  [bench-qwen36-27b-fable]="$HF/models--DavidAU--Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-NEO-MAX-MTP-GGUF/snapshots/ad061630e5df94ac9298153be609117b95bf8fc3/Qwen3.6-27B-Fable-Fus-711-UnHeretic-NM-DAU-NEO-MAX-NEO-MTP-Q4_K_M.gguf"
  [bench-qwen36-35b-a3b]="$HF/models--LuffyTheFox--Qwen3.6-35B-A3B-Uncensored-Genesis-Hermes-V7-GGUF/snapshots/d1c0c52e841c2775a477fc021d4ce79e661b8a8a/Hermes3.6-35B-A3B-Uncensored-Genesis-V7-APEX-Compact.gguf"
  [bench-kafka70b]="$HF/models--TheBloke--KafkaLM-70B-German-V0.1-GGUF/snapshots/b2003158564926744fbfd281a917be89791fc0c6/kafkalm-70b-german-v0.1.Q4_K_M.gguf"
)

SMOKE=(bench-lfm25 bench-q4b)
if [ "${1:-}" = "--smoke" ]; then
  TAGS=("${SMOKE[@]}")
else
  TAGS=("${!M[@]}")
fi

# Modelos grandes demais para a fatia de VRAM da GPU (APU Strix Halo, mem unificada):
# forcar CPU (num_gpu 0) para nao estourar o buffer ROCm. O 70B (~41GB) cabe na RAM (62GB).
declare -A NUM_GPU=(
  [bench-kafka70b]=0
)

TMP="$(mktemp -d)"
for tag in "${TAGS[@]}"; do
  gguf="${M[$tag]}"
  if [ ! -f "$gguf" ]; then
    echo "SKIP $tag  (gguf ausente: $gguf)"
    continue
  fi
  printf 'FROM %s\n' "$gguf" > "$TMP/Modelfile"
  if [ -n "${NUM_GPU[$tag]:-}" ]; then
    printf 'PARAMETER num_gpu %s\n' "${NUM_GPU[$tag]}" >> "$TMP/Modelfile"
    echo "   (num_gpu=${NUM_GPU[$tag]} -> CPU)"
  fi
  echo "== ollama create $tag =="
  ollama create "$tag" -f "$TMP/Modelfile" && echo "OK $tag" || echo "FALHOU $tag"
done
rm -rf "$TMP"
echo "== ollama list =="
ollama list
