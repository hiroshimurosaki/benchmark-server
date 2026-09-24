#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
b3 — exporta os dados REAIS de uma org do Firebase para o bundle do benchmark.

Roda NO PC do Fernando (precisa de firebase-admin + config/serviceAccountKey.json
do repo rag-chatbot). Escreve tudo em benchmark-server/projetos/b3/data/{org_id}/.

Saidas:
  corpus/<arquivos do Storage documents/{org}/>   -> vira raw_docs no servidor
  faq_db.json     lista [{frase, resposta, intencao}]  (colecao orgs/{org}/faq)
  DTQ.json        idem                                  (colecao orgs/{org}/dtq)
  victim_faq.json []                                    (nao existe no Firestore)
  settings.json   doc orgs/{org}/config/settings (features, prompts, threshold)
  manifest.json   contagens + hash, pra conferir no servidor

Uso (do diretorio do repo rag-chatbot, que tem o serviceAccountKey):
  ./env/Scripts/python.exe ../benchmark-server/projetos/b3/runner/export_org_data.py \
      --org oncorretor --out ../benchmark-server/projetos/b3/data
"""
import argparse, hashlib, json, os, sys

import firebase_admin
from firebase_admin import credentials, firestore, storage


def norm_entry(d: dict) -> dict:
    """Normaliza para o formato que semantic_matcher._build_cache espera."""
    return {
        "frase": d.get("frase") or d.get("question") or "",
        "resposta": d.get("resposta") or d.get("answer") or "",
        "intencao": d.get("intencao") or d.get("intention") or "",
    }


def dump_collection(db, path: str) -> list:
    out = []
    for doc in db.collection(path).stream():
        e = norm_entry(doc.to_dict() or {})
        if e["frase"]:
            out.append(e)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--org", default="oncorretor")
    ap.add_argument("--cred", default="config/serviceAccountKey.json")
    ap.add_argument("--out", required=True, help="diretorio de saida (projetos/b3/data)")
    args = ap.parse_args()

    sa = json.load(open(args.cred, encoding="utf-8"))
    pid = sa["project_id"]
    firebase_admin.initialize_app(
        credentials.Certificate(args.cred),
        {"storageBucket": f"{pid}.firebasestorage.app"},
    )
    db = firestore.client()
    org = args.org
    base = os.path.join(args.out, org)
    corpus = os.path.join(base, "corpus")
    os.makedirs(corpus, exist_ok=True)

    manifest = {"project": pid, "org": org, "corpus": []}

    # ---- 1. corpus (Firebase Storage) --------------------------------------
    bucket = storage.bucket()
    for blob in bucket.list_blobs(prefix=f"documents/{org}/"):
        name = blob.name.split("/", 2)[-1]
        if not name:
            continue
        dest = os.path.join(corpus, name)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        data = blob.download_as_bytes()          # BINARIO (o controller de prod
        with open(dest, "wb") as f:              # baixa em modo texto -> bug
            f.write(data)                        # conhecido, ver relatorio)
        manifest["corpus"].append({
            "name": name, "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()[:16],
        })
        print(f"corpus  {name}  {len(data)} bytes")

    # ---- 2. FAQ / DTQ ------------------------------------------------------
    faq = dump_collection(db, f"orgs/{org}/faq")
    dtq = dump_collection(db, f"orgs/{org}/dtq")
    for fname, payload in (("faq_db.json", faq), ("DTQ.json", dtq),
                           ("victim_faq.json", [])):
        with open(os.path.join(base, fname), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)
    manifest["faq"] = len(faq)
    manifest["dtq"] = len(dtq)
    print(f"faq     {len(faq)} entradas")
    print(f"dtq     {len(dtq)} entradas")

    # ---- 3. settings da org ------------------------------------------------
    settings = db.document(f"orgs/{org}/config/settings").get().to_dict() or {}
    with open(os.path.join(base, "settings.json"), "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=1, default=str)
    ai = (settings.get("features") or {}).get("ai") or {}
    manifest["confidence_threshold"] = ai.get("confidence_threshold")
    manifest["ai_enabled"] = ai.get("enabled")
    print(f"settings ai={ai.get('enabled')} threshold={ai.get('confidence_threshold')}")

    with open(os.path.join(base, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    print(f"\nOK -> {base}")


if __name__ == "__main__":
    sys.exit(main())
