# Log de comandos no servidor (10.10.10.151)

## 2026-08-18 14:43 — descoberta (read-only)
```
nvidia-smi; command -v llama-server; find gguf; df -h; nproc; free -h
```
== HOST ==
Linux ianode 6.12.86+deb13-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.12.86-1 (2026-05-08) x86_64 GNU/Linux
== CPU ==
32
== RAM ==
               total        used        free      shared  buff/cache   available
Mem:            62Gi       3.3Gi        29Gi        11Mi        30Gi        59Gi
== GPU ==
sem nvidia-smi
== BIN ==
llama-server: NAO
llama-cli: NAO
ollama: /usr/local/bin/ollama
huggingface-cli: NAO
python3: /usr/bin/python3
== GGUF ==
== DISCO ==
Filesystem      Size  Used Avail Use% Mounted on
/dev/nvme0n1p2  1.8T  350G  1.3T  21% /

## 2026-08-18 14:44 — descoberta 2 (modelos, read-only)
```
ollama list; du -sh ollama store; find hf cache *.gguf; env OLLAMA
```
== OLLAMA LIST ==
NAME               ID              SIZE     MODIFIED     
qwen3.6:35b-a3b    0930586893e0    22 GB    28 hours ago    
gpt-oss:20b        17052f91a42e    13 GB    12 days ago     
== OLLAMA STORE ==
OLLAMA_MODELS=
== HF CACHE ==
/home/nicolas.benedetti/.cache/huggingface/hub/models--DavidAU--Qwen3.5-9B-The-Defiant-Fable-Uncensored-Heretic-NEO-IMATRIX-MAX-MTP-GGUF
/home/nicolas.benedetti/.cache/huggingface/hub/models--DavidAU--Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-NEO-MAX-MTP-GGUF
/home/nicolas.benedetti/.cache/huggingface/hub/models--empero-ai--Qwen3.8-9B-GGUF
/home/nicolas.benedetti/.cache/huggingface/hub/models--Jackrong--DeepSeek-V4-Pro-Qwen3.5-9B-MTP-GGUF
/home/nicolas.benedetti/.cache/huggingface/hub/models--LiquidAI--LFM2.5-2.6B-GGUF
/home/nicolas.benedetti/.cache/huggingface/hub/models--LuffyTheFox--Qwen3.6-35B-A3B-Uncensored-Genesis-Hermes-V7-GGUF
/home/nicolas.benedetti/.cache/huggingface/hub/models--MiniMaxAI--MiniMax-H3
/home/nicolas.benedetti/.cache/huggingface/hub/models--mradermacher--LlamaForecaster-8B-i1-GGUF
/home/nicolas.benedetti/.cache/huggingface/hub/models--Qwen--Qwen3.5-122B-A10B
/home/nicolas.benedetti/.cache/huggingface/hub/models--seedboxai--KafkaLM-70B-German-V0.1
/home/nicolas.benedetti/.cache/huggingface/hub/models--TheBloke--KafkaLM-70B-German-V0.1-GGUF
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--DeepSeek-V4-Flash-0731-GGUF
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3-4B-GGUF
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3.5-122B-A10B-GGUF
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3.6-27B-MTP-GGUF
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3.8-27B-GGUF
/home/nicolas.benedetti/.cache/huggingface/hub/models--vishanoberoi--Llama-2-7b-chat-hf-finedtuned-to-GGUF
-- gguf na cache HF --
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3.8-27B-GGUF/snapshots/f1bfb127c64f7072bdd2cad55f258b9c8b2910fe/Qwen3.8-27B-Q4_K_M.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3.8-27B-GGUF/snapshots/f1bfb127c64f7072bdd2cad55f258b9c8b2910fe/mmproj-BF16.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--vishanoberoi--Llama-2-7b-chat-hf-finedtuned-to-GGUF/snapshots/bce7ec05d57f2bd1f8b45cf12986e55aa5dc0760/finetuned-16b.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--LiquidAI--LFM2.5-2.6B-GGUF/snapshots/b421ad1d549afeda6a0fb2ad3a697cb5a7879adc/LFM2.5-2.6B-Q4_K_M.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--DavidAU--Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-NEO-MAX-MTP-GGUF/snapshots/ad061630e5df94ac9298153be609117b95bf8fc3/mmproj-BF16.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--DavidAU--Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-NEO-MAX-MTP-GGUF/snapshots/ad061630e5df94ac9298153be609117b95bf8fc3/Qwen3.6-27B-Fable-Fus-711-UnHeretic-NM-DAU-NEO-MAX-NEO-MTP-Q4_K_M.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--DavidAU--Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-NEO-MAX-MTP-GGUF/snapshots/255dac194ec7880fc5b7afed5581a1b0a3f4b98d/mmproj-BF16.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--DavidAU--Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-NEO-MAX-MTP-GGUF/snapshots/255dac194ec7880fc5b7afed5581a1b0a3f4b98d/Qwen3.6-27B-Fable-Fus-711-UnHeretic-NM-DAU-NEO-MAX-NEO-MTP-Q4_K_M.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--DavidAU--Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-NEO-MAX-MTP-GGUF/snapshots/416ffa8b1d29b9397be7b5452403dd815432acd3/mmproj-BF16.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--DavidAU--Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-NEO-MAX-MTP-GGUF/snapshots/416ffa8b1d29b9397be7b5452403dd815432acd3/Qwen3.6-27B-Fable-Fus-711-UnHeretic-NM-DAU-NEO-MAX-NEO-MTP-Q4_K_M.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--TheBloke--KafkaLM-70B-German-V0.1-GGUF/snapshots/b2003158564926744fbfd281a917be89791fc0c6/kafkalm-70b-german-v0.1.Q4_K_M.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--empero-ai--Qwen3.8-9B-GGUF/snapshots/760121cd70bb4c36b2b5ec58eb765e0df5987efe/Qwen3.8-9B-Q4_K_M.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3.5-122B-A10B-GGUF/snapshots/51eab4d59d53f573fb9206cb3ce613f1d0aa392b/mmproj-BF16.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3.5-122B-A10B-GGUF/snapshots/51eab4d59d53f573fb9206cb3ce613f1d0aa392b/Q4_K_M/Qwen3.5-122B-A10B-Q4_K_M-00002-of-00003.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3.5-122B-A10B-GGUF/snapshots/51eab4d59d53f573fb9206cb3ce613f1d0aa392b/Q4_K_M/Qwen3.5-122B-A10B-Q4_K_M-00001-of-00003.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3.5-122B-A10B-GGUF/snapshots/51eab4d59d53f573fb9206cb3ce613f1d0aa392b/Q4_K_M/Qwen3.5-122B-A10B-Q4_K_M-00003-of-00003.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--Jackrong--DeepSeek-V4-Pro-Qwen3.5-9B-MTP-GGUF/snapshots/41a445e05e3a056c092a3bde32fe2f759e6e2197/DeepSeek-V4-Pro-Qwen3.5-9B-MTP-Q4_K_M.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--Jackrong--DeepSeek-V4-Pro-Qwen3.5-9B-MTP-GGUF/snapshots/41a445e05e3a056c092a3bde32fe2f759e6e2197/mmproj-F32.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--DavidAU--Qwen3.5-9B-The-Defiant-Fable-Uncensored-Heretic-NEO-IMATRIX-MAX-MTP-GGUF/snapshots/d9796b37168d3bd3a6f963e5f4d08bff869adc13/mmproj-BF16.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--DavidAU--Qwen3.5-9B-The-Defiant-Fable-Uncensored-Heretic-NEO-IMATRIX-MAX-MTP-GGUF/snapshots/d9796b37168d3bd3a6f963e5f4d08bff869adc13/Qwen3.5-9B-The-Defiant-Fable-Uncnr-Heretic-NEO-MAX-MTP-Q4_K_M.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3.6-27B-MTP-GGUF/snapshots/5cb35eb3dcbf52dbce5f87dbc64df6aaffadcace/Qwen3.6-27B-Q4_K_M.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3.6-27B-MTP-GGUF/snapshots/5cb35eb3dcbf52dbce5f87dbc64df6aaffadcace/mmproj-BF16.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--LuffyTheFox--Qwen3.6-35B-A3B-Uncensored-Genesis-Hermes-V7-GGUF/snapshots/d1c0c52e841c2775a477fc021d4ce79e661b8a8a/mmproj-Hermes3.6-35B-A3B-Uncensored-Genesis-F16.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--LuffyTheFox--Qwen3.6-35B-A3B-Uncensored-Genesis-Hermes-V7-GGUF/snapshots/d1c0c52e841c2775a477fc021d4ce79e661b8a8a/Hermes3.6-35B-A3B-Uncensored-Genesis-V7-APEX-Compact.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3-4B-GGUF/snapshots/22c9fc8a8c7700b76a1789366280a6a5a1ad1120/Qwen3-4B-Q4_0.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--mradermacher--LlamaForecaster-8B-i1-GGUF/snapshots/781c6cd51069ed9b864989f8facca8b85b6a6cd1/LlamaForecaster-8B.i1-Q4_K_M.gguf
== GGUF PROFUNDO (home) ==
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3.8-27B-GGUF/snapshots/f1bfb127c64f7072bdd2cad55f258b9c8b2910fe/Qwen3.8-27B-Q4_K_M.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3.8-27B-GGUF/snapshots/f1bfb127c64f7072bdd2cad55f258b9c8b2910fe/mmproj-BF16.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--vishanoberoi--Llama-2-7b-chat-hf-finedtuned-to-GGUF/snapshots/bce7ec05d57f2bd1f8b45cf12986e55aa5dc0760/finetuned-16b.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--LiquidAI--LFM2.5-2.6B-GGUF/snapshots/b421ad1d549afeda6a0fb2ad3a697cb5a7879adc/LFM2.5-2.6B-Q4_K_M.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--DavidAU--Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-NEO-MAX-MTP-GGUF/snapshots/ad061630e5df94ac9298153be609117b95bf8fc3/mmproj-BF16.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--DavidAU--Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-NEO-MAX-MTP-GGUF/snapshots/ad061630e5df94ac9298153be609117b95bf8fc3/Qwen3.6-27B-Fable-Fus-711-UnHeretic-NM-DAU-NEO-MAX-NEO-MTP-Q4_K_M.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--DavidAU--Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-NEO-MAX-MTP-GGUF/snapshots/255dac194ec7880fc5b7afed5581a1b0a3f4b98d/mmproj-BF16.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--DavidAU--Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-NEO-MAX-MTP-GGUF/snapshots/255dac194ec7880fc5b7afed5581a1b0a3f4b98d/Qwen3.6-27B-Fable-Fus-711-UnHeretic-NM-DAU-NEO-MAX-NEO-MTP-Q4_K_M.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--DavidAU--Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-NEO-MAX-MTP-GGUF/snapshots/416ffa8b1d29b9397be7b5452403dd815432acd3/mmproj-BF16.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--DavidAU--Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-NEO-MAX-MTP-GGUF/snapshots/416ffa8b1d29b9397be7b5452403dd815432acd3/Qwen3.6-27B-Fable-Fus-711-UnHeretic-NM-DAU-NEO-MAX-NEO-MTP-Q4_K_M.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--TheBloke--KafkaLM-70B-German-V0.1-GGUF/snapshots/b2003158564926744fbfd281a917be89791fc0c6/kafkalm-70b-german-v0.1.Q4_K_M.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--empero-ai--Qwen3.8-9B-GGUF/snapshots/760121cd70bb4c36b2b5ec58eb765e0df5987efe/Qwen3.8-9B-Q4_K_M.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3.5-122B-A10B-GGUF/snapshots/51eab4d59d53f573fb9206cb3ce613f1d0aa392b/mmproj-BF16.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3.5-122B-A10B-GGUF/snapshots/51eab4d59d53f573fb9206cb3ce613f1d0aa392b/Q4_K_M/Qwen3.5-122B-A10B-Q4_K_M-00002-of-00003.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3.5-122B-A10B-GGUF/snapshots/51eab4d59d53f573fb9206cb3ce613f1d0aa392b/Q4_K_M/Qwen3.5-122B-A10B-Q4_K_M-00001-of-00003.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3.5-122B-A10B-GGUF/snapshots/51eab4d59d53f573fb9206cb3ce613f1d0aa392b/Q4_K_M/Qwen3.5-122B-A10B-Q4_K_M-00003-of-00003.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--Jackrong--DeepSeek-V4-Pro-Qwen3.5-9B-MTP-GGUF/snapshots/41a445e05e3a056c092a3bde32fe2f759e6e2197/DeepSeek-V4-Pro-Qwen3.5-9B-MTP-Q4_K_M.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--Jackrong--DeepSeek-V4-Pro-Qwen3.5-9B-MTP-GGUF/snapshots/41a445e05e3a056c092a3bde32fe2f759e6e2197/mmproj-F32.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--DavidAU--Qwen3.5-9B-The-Defiant-Fable-Uncensored-Heretic-NEO-IMATRIX-MAX-MTP-GGUF/snapshots/d9796b37168d3bd3a6f963e5f4d08bff869adc13/mmproj-BF16.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--DavidAU--Qwen3.5-9B-The-Defiant-Fable-Uncensored-Heretic-NEO-IMATRIX-MAX-MTP-GGUF/snapshots/d9796b37168d3bd3a6f963e5f4d08bff869adc13/Qwen3.5-9B-The-Defiant-Fable-Uncnr-Heretic-NEO-MAX-MTP-Q4_K_M.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3.6-27B-MTP-GGUF/snapshots/5cb35eb3dcbf52dbce5f87dbc64df6aaffadcace/Qwen3.6-27B-Q4_K_M.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3.6-27B-MTP-GGUF/snapshots/5cb35eb3dcbf52dbce5f87dbc64df6aaffadcace/mmproj-BF16.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--LuffyTheFox--Qwen3.6-35B-A3B-Uncensored-Genesis-Hermes-V7-GGUF/snapshots/d1c0c52e841c2775a477fc021d4ce79e661b8a8a/mmproj-Hermes3.6-35B-A3B-Uncensored-Genesis-F16.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--LuffyTheFox--Qwen3.6-35B-A3B-Uncensored-Genesis-Hermes-V7-GGUF/snapshots/d1c0c52e841c2775a477fc021d4ce79e661b8a8a/Hermes3.6-35B-A3B-Uncensored-Genesis-V7-APEX-Compact.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3-4B-GGUF/snapshots/22c9fc8a8c7700b76a1789366280a6a5a1ad1120/Qwen3-4B-Q4_0.gguf
/home/nicolas.benedetti/.cache/huggingface/hub/models--mradermacher--LlamaForecaster-8B-i1-GGUF/snapshots/781c6cd51069ed9b864989f8facca8b85b6a6cd1/LlamaForecaster-8B.i1-Q4_K_M.gguf
== DIRS grandes no home ==
223G	/home/nicolas.benedetti/.cache
223G	/home/nicolas.benedetti
17M	/home/nicolas.benedetti/.local
17M	/home/nicolas.benedetti/.llama-app
32K	/home/nicolas.benedetti/.config
8.0K	/home/nicolas.benedetti/.ssh

## 2026-08-18 14:48 — calibração (cria bench-q4b e bench-kafka70b; mede tok/s)
```
ollama create bench-q4b/bench-kafka70b; curl /api/generate num_predict=120 em q4b, gpt-oss:20b, kafka70b
```
Q4B=/home/nicolas.benedetti/.cache/huggingface/hub/models--unsloth--Qwen3-4B-GGUF/snapshots/22c9fc8a8c7700b76a1789366280a6a5a1ad1120/Qwen3-4B-Q4_0.gguf
K70=/home/nicolas.benedetti/.cache/huggingface/hub/models--TheBloke--KafkaLM-70B-German-V0.1-GGUF/snapshots/b2003158564926744fbfd281a917be89791fc0c6/kafkalm-70b-german-v0.1.Q4_K_M.gguf
curl: /usr/bin/curl
== criando bench-q4b ==
writing manifest [K
success [K[?25h[?2026l
== criando bench-kafka70b ==
writing manifest [K
success [K[?25h[?2026l
=== TIMING bench-q4b ===

## 2026-08-18 14:51 — calibração em background (nohup calib.sh -> ~/bench_calib.out)
  gen_tokens=120  gen_s=1.9  tok/s=62.48  load_s=3.8  prompt_tok=23
=== TIMING gpt-oss:20b ===
  gen_tokens=120  gen_s=2.9  tok/s=40.69  load_s=14.7  prompt_tok=80
=== TIMING bench-kafka70b ===
  gen_tokens=0  gen_s=0.0  tok/s=0.00  load_s=0.0  prompt_tok=0
