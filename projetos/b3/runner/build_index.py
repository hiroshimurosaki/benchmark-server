#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
b3 / pergunta 3 — "em quanto tempo é montado o banco vetorial?"

Cronometra a indexação REAL (mesmo parser, mesmo chunking, mesmo modelo de
embedding, mesmo tipo de índice do Document_service), quebrada por etapa, em
vários tamanhos de corpus.

Por que medir escalado: o corpus real da oncorretor é UM arquivo de 61 KB. No
tamanho de hoje o tempo é dominado pelo load do `all-MiniLM-L6-v2`, não pelo
embedding — a resposta crua ("uns segundos") não serve para planejar. Os
múltiplos mostram a curva.

Fidelidade ao código de produção (Document_service/src/services/vectorstore.py:44-70):
    generate_chunks(docs_path)                                  intelligent_parser.py:305
    Document(page_content=chunk.pop("texto"), metadata=chunk)   vectorstore.py:51
    RecursiveCharacterTextSplitter(chunk_size=800, overlap=200) vectorstore.py:59
    HuggingFaceEmbeddings("all-MiniLM-L6-v2", device="cpu")     vectorstore.py:38
    FAISS.from_documents(...)  -> IndexFlatL2                   vectorstore.py:67
    save_local(index_path)                                      vectorstore.py:70

Uso:
    .venv/bin/python runner/build_index.py --root . --org oncorretor \
        --scales 1,5,20 --repeat 2 --out index_bench.json
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime

# Imports locais. No repo: esta pasta + comum/. No bundle do servidor
# (~/benchmark/b3/runner) tudo fica achatado em runner/ e as outras pastas
# simplesmente não existem — por isso o `isdir`.
_AQUI = os.path.dirname(os.path.abspath(__file__))
_RAIZ = os.path.normpath(os.path.join(_AQUI, "..", "..", ".."))
for _p in (os.path.join(_RAIZ, "comum"), _AQUI):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)
import b3_env  # noqa: E402


def _t():
    return time.perf_counter()


def scale_corpus(src_dir: str, dst_dir: str, factor: int) -> dict:
    """Materializa um corpus `factor`× maior duplicando os arquivos-fonte."""
    if os.path.isdir(dst_dir):
        shutil.rmtree(dst_dir)
    os.makedirs(dst_dir, exist_ok=True)
    total = 0
    n = 0
    for name in sorted(os.listdir(src_dir)):
        s = os.path.join(src_dir, name)
        if not os.path.isfile(s):
            continue
        with open(s, "rb") as f:
            data = f.read()
        stem, ext = os.path.splitext(name)
        for i in range(factor):
            out = os.path.join(dst_dir, name if i == 0 else f"{stem}__c{i:03d}{ext}")
            with open(out, "wb") as f:
                f.write(data)
            total += len(data)
            n += 1
    return {"files": n, "bytes": total}


def measure_once(org_id: str, docs_path: str) -> dict:
    """Uma montagem completa do índice, cronometrada por etapa."""
    # Mesmos imports do Document_service/src/services/vectorstore.py:5-8 — se
    # divergir aqui, o benchmark mede outra coisa.
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    from Answer_service.src.utils.config import get_org_faiss_index_path
    from Document_service.src.services.intelligent_parser import generate_chunks

    index_path = get_org_faiss_index_path(org_id)
    if os.path.isdir(index_path):
        shutil.rmtree(index_path, ignore_errors=True)
    os.makedirs(index_path, exist_ok=True)

    m = {}

    t0 = _t()
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2", model_kwargs={"device": "cpu"}
    )
    m["model_load_s"] = round(_t() - t0, 3)

    t0 = _t()
    chunks = generate_chunks(docs_path)
    m["parse_s"] = round(_t() - t0, 3)
    m["chunks_parser"] = len(chunks)

    t0 = _t()
    documents = []
    for chunk in chunks:
        c = dict(chunk)
        documents.append(Document(page_content=c.pop("texto"), metadata=c))
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
    splitted = splitter.split_documents(documents)
    m["split_s"] = round(_t() - t0, 3)
    m["chunks_final"] = len(splitted)
    m["chars_total"] = sum(len(d.page_content) for d in splitted)

    t0 = _t()
    store = FAISS.from_documents(splitted, embeddings)
    m["embed_index_s"] = round(_t() - t0, 3)

    t0 = _t()
    store.save_local(index_path)
    m["save_s"] = round(_t() - t0, 3)

    t0 = _t()
    FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    m["reload_s"] = round(_t() - t0, 3)

    m["build_total_s"] = round(
        m["model_load_s"] + m["parse_s"] + m["split_s"] + m["embed_index_s"] + m["save_s"], 3
    )
    m["build_sem_model_load_s"] = round(m["build_total_s"] - m["model_load_s"], 3)
    if m["chunks_final"]:
        m["ms_por_chunk"] = round(m["embed_index_s"] * 1000 / m["chunks_final"], 2)
    m["index_bytes"] = sum(
        os.path.getsize(os.path.join(index_path, f)) for f in os.listdir(index_path)
    )
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--org", default="oncorretor")
    ap.add_argument("--scales", default="1,5,20", help="múltiplos do corpus real")
    ap.add_argument("--repeat", type=int, default=2)
    ap.add_argument("--out", default="index_bench.json")
    args = ap.parse_args()

    ctx = b3_env.bootstrap(bundle_root=args.root, org_id=args.org, fresh_index=True)
    src_corpus = os.path.join(os.path.abspath(args.root), "data", args.org, "corpus")

    import platform

    report = {
        "quando": datetime.now().isoformat(timespec="seconds"),
        "host": platform.node(),
        "cpu_count": os.cpu_count(),
        "python": platform.python_version(),
        "org": args.org,
        "embedding_model": "all-MiniLM-L6-v2 (384d, device=cpu)",
        "chunk": {"size": 800, "overlap": 200, "splitter": "RecursiveCharacterTextSplitter"},
        "index": "FAISS IndexFlatL2 (LangChain default)",
        "runs": [],
    }

    for scale in [int(s) for s in args.scales.split(",") if s.strip()]:
        info = scale_corpus(src_corpus, ctx.docs_path, scale)
        print(f"\n=== corpus {scale}x — {info['files']} arquivo(s), "
              f"{info['bytes']/1024:.1f} KB ===", flush=True)
        for r in range(args.repeat):
            m = measure_once(args.org, ctx.docs_path)
            m.update({"scale": scale, "rep": r, **info})
            report["runs"].append(m)
            print(
                f"  rep{r}: total={m['build_total_s']}s "
                f"(model_load={m['model_load_s']} parse={m['parse_s']} "
                f"split={m['split_s']} embed+index={m['embed_index_s']} save={m['save_s']}) "
                f"chunks={m['chunks_final']} {m.get('ms_por_chunk')}ms/chunk",
                flush=True,
            )

    # Restaura o corpus real para o run_b3 não usar o corpus inflado.
    scale_corpus(src_corpus, ctx.docs_path, 1)
    from Answer_service.src.utils.config import get_org_signature_path
    sig = get_org_signature_path(args.org)
    if os.path.exists(sig):
        os.remove(sig)

    out = os.path.join(os.path.abspath(args.root), args.out)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(f"\nOK -> {out}")


if __name__ == "__main__":
    main()
