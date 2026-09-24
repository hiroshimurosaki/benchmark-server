#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera dashboard_b1.json (v2) a partir do results_b1.jsonl PARCIAL + sysmon.jsonl,
enquanto o benchmark roda. Reusa a pontuacao do score_b1.py.

Rodar em loop no servidor:
  while true; do python3 dashboard_b1.py --root . --out ../dashboard_b1.json; sleep 60; done

Saida (resumo do schema):
  progress{total_expected,n_done,n_error,pct,eta_seconds,compute_elapsed_s,current_model,by_model[]}
  models[]{model,label,tier,thinking,n,nota_media,perfeitas,boas,pct_perfeitas,
           lat_min_s,lat_max_s,lat_mean_s,ttft_mean_s,time_total_s,time_share_pct,
           por_categoria{},footprint{size_gib,pct_ram,processor}}
  best{overall,by_tier,best_value}
  server{ram_used_gib,ram_total_gib,ram_pct,vram_used_gib,vram_total_gib,vram_pct,
         cpu_pct,current_model,current_processor,sampled_at}
  por_pergunta[]{id,category,user,nota_media,n}   # ordenado dificil->facil
"""
import argparse, json, os, re, subprocess
from datetime import datetime
from collections import defaultdict

import score_b1  # mesmo diretorio

TIER_ORDER = ["barato", "medio", "pesado"]
PASS_BOA = 70.0  # nota >= => "boa"

# rotulos amigaveis por checagem (pra "onde cada modelo perde ponto")
CODE_LABEL = {
    "tool": "Escolha da tool",
    "args": "Datas/args exatos",
    "read:headline_uniquePeople": "Headline (nº pessoas)",
    "read:clamp_datalastday": "Avisa corte (dataLastDay)",
    "read:report_cancelled_split": "Split de cancelados",
    "read:flag_small_sample": "Sinaliza amostra pequena",
    "read:state_no_data": "Diz quando não há dado",
    "read:multiple_people_flag": "Sinaliza múltiplas pessoas",
    "read:older_events_not_checked": "Ressalva eventos antigos",
    "read:valid_json": "JSON válido",
    "read:no_retry": "Não repete a tool",
    "adv:break_json": "Resiste a quebrar JSON",
    "adv:leak_system_prompt": "Não vaza o prompt",
    "adv:invent_numbers": "Não inventa números",
    "adv:obey_injection": "Resiste a injection",
}


def flat_checks(bd):
    """Achata o breakdown do score_b1 em {codigo: bool}."""
    out = {}
    if "tool_correct" in bd:
        out["tool"] = bool(bd["tool_correct"])
    if "args_correct" in bd:
        out["args"] = bool(bd["args_correct"])
    for k, v in (bd.get("reading") or {}).items():
        out["read:" + k] = bool(v)
    for k, v in (bd.get("forbidden_avoided") or {}).items():
        out["adv:" + k] = bool(v)
    return out


def tier_ok(q, tier):
    return tier in q.get("tiers", []) or (q.get("tier") == tier)


def load_jsonl(path):
    out = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        pass
    return out


def label_of(name):
    return re.sub(r":latest$", "", re.sub(r"^bench-", "", name))


def ollama_sizes():
    """tag(sem :latest) -> tamanho em GiB, via 'ollama list' (best-effort)."""
    sizes = {}
    try:
        out = subprocess.run(["ollama", "list"], capture_output=True, text=True,
                             timeout=10).stdout.splitlines()
        for row in out[1:]:
            m = re.match(r"(\S+)\s+\S+\s+([\d.]+)\s*(GB|MB)", row)
            if m:
                name, num, unit = m.group(1), float(m.group(2)), m.group(3)
                gib = num if unit == "GB" else num / 1024
                sizes[re.sub(r":latest$", "", name)] = round(gib, 1)
    except Exception:
        pass
    return sizes


def ollama_meta(models, cache_path):
    """{name -> {params,params_b,quant,ctx,arch}} via 'ollama show', cacheado em disco.
    Metadados nao mudam durante o run; roda 'ollama show' so 1x por modelo."""
    cache = {}
    if os.path.exists(cache_path):
        try:
            cache = json.load(open(cache_path, encoding="utf-8"))
        except Exception:
            cache = {}
    changed = False
    for m in models:
        name = m["name"]
        if name in cache:
            continue
        try:
            out = subprocess.run(["ollama", "show", name], capture_output=True,
                                 text=True, timeout=20).stdout
        except Exception:
            continue
        d = {}
        for key, field in [("architecture", "arch"), ("parameters", "params"),
                           ("context length", "ctx"), ("quantization", "quant")]:
            mm = re.search(rf"{key}\s+(\S+)", out)
            if mm:
                d[field] = mm.group(1)
        if d.get("params"):
            try:
                d["params_b"] = float(re.sub(r"[^0-9.]", "", d["params"]))
            except Exception:
                d["params_b"] = None
        cache[name] = d
        changed = True
    if changed:
        try:
            json.dump(cache, open(cache_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        except Exception:
            pass
    return cache


def build(args):
    root = os.path.abspath(args.root)
    models = load_jsonl(os.path.join(root, args.models))
    questions = load_jsonl(args.questions)
    qmap = {q["id"]: q for q in questions}
    results = load_jsonl(args.results)
    sysmon = load_jsonl(os.path.join(root, "..", "sysmon.jsonl"))
    sizes = ollama_sizes()
    meta = ollama_meta(models, os.path.join(root, "..", "model_meta.json"))

    tier_of = {m["name"]: m["tier"] for m in models}
    think_of = {m["name"]: bool(m.get("thinking")) for m in models}

    # ---- total esperado por (modelo x thinking-variante) e por modelo
    def n_q(tier):
        return sum(1 for q in questions if tier_ok(q, tier))
    model_total = {}   # por modelo (todas as variantes)
    per_tier_total = defaultdict(int)
    total_expected = 0
    for m in models:
        nv = 2 if m.get("thinking") else 1
        t = nv * n_q(m["tier"])
        model_total[m["name"]] = t
        per_tier_total[m["tier"]] += t
        total_expected += t

    # ---- agrega resultados por modelo (juntando variantes de thinking p/ visao de modelo)
    #      e tambem por (modelo, thinking) p/ leaderboard/best.
    per_model = defaultdict(lambda: {"n": 0, "sum": 0.0, "perfeitas": 0, "boas": 0,
                                     "lats": [], "ttfts": [], "time": 0.0, "tokens": 0.0, "done": 0,
                                     "by_cat": defaultdict(lambda: {"n": 0, "sum": 0.0}),
                                     "checks": defaultdict(lambda: {"pass": 0, "total": 0}),
                                     "tier": None})
    check_global = defaultdict(lambda: {"pass": 0, "total": 0})  # resumo geral por checagem
    per_variant = defaultdict(lambda: {"n": 0, "sum": 0.0, "time": 0.0, "ttft": 0.0,
                                       "tier": None})
    per_q = defaultdict(lambda: {"n": 0, "sum": 0.0})
    n_error = 0
    total_time = 0.0

    for res in results:
        model = res["model"]
        tier = res.get("tier") or tier_of.get(model, "?")
        q = qmap.get(res["id"])
        if res.get("error"):
            n_error += 1
        nota = 0.0
        checks = {}
        if q and not res.get("error"):
            nota, bd = score_b1.score_one(res, q["gabarito"])
            checks = flat_checks(bd)
        la = (res.get("phaseA", {}) or {}).get("latency_s") or 0
        lb = (res.get("phaseB", {}) or {}).get("latency_s") or 0
        item_lat = la + lb
        ttft = (res.get("phaseA", {}) or {}).get("ttft_s")
        total_time += item_lat

        toks = ((res.get("phaseA", {}) or {}).get("tokens_out") or 0) + \
               ((res.get("phaseB", {}) or {}).get("tokens_out") or 0)
        pm = per_model[model]
        pm["tier"] = tier
        pm["done"] += 1
        pm["time"] += item_lat
        pm["tokens"] += toks
        for code, ok in checks.items():
            pm["checks"][code]["total"] += 1
            check_global[code]["total"] += 1
            if ok:
                pm["checks"][code]["pass"] += 1
                check_global[code]["pass"] += 1
        if item_lat:
            pm["lats"].append(item_lat)
        if ttft:
            pm["ttfts"].append(ttft)
        if nota is not None:
            pm["n"] += 1
            pm["sum"] += nota
            if nota >= 100:
                pm["perfeitas"] += 1
            if nota >= PASS_BOA:
                pm["boas"] += 1
            if q:
                c = pm["by_cat"][q["category"]]
                c["n"] += 1
                c["sum"] += nota
                pq = per_q[res["id"]]
                pq["n"] += 1
                pq["sum"] += nota

        pv = per_variant[(model, bool(res.get("thinking")))]
        pv["tier"] = tier
        if nota is not None:
            pv["n"] += 1
            pv["sum"] += nota
        pv["time"] += item_lat
        pv["ttft"] += ttft or 0

    # ---- footprint / processor por modelo (via sysmon)
    fp_proc = {}     # tag(sem :latest) -> processor mais recente observado
    fp_vram = defaultdict(float)
    for s in sysmon:
        lm = s.get("loaded_model")
        if not lm:
            continue
        key = re.sub(r":latest$", "", lm)
        if s.get("processor"):
            fp_proc[key] = s["processor"]

    ram_total = None
    if sysmon:
        ram_total = sysmon[-1].get("ram_total_gib")

    # ---- monta models[]
    models_out = []
    for model, pm in per_model.items():
        lats = pm["lats"]
        key = re.sub(r":latest$", "", model)
        size = sizes.get(key)
        md = meta.get(model, {})
        nota = round(pm["sum"] / pm["n"], 1) if pm["n"] else None
        models_out.append({
            "model": model, "label": label_of(model), "tier": pm["tier"],
            "thinking": think_of.get(model),
            "n": pm["n"],
            "nota_media": nota,
            "perfeitas": pm["perfeitas"], "boas": pm["boas"],
            "pct_perfeitas": round(100.0 * pm["perfeitas"] / pm["n"], 1) if pm["n"] else None,
            "lat_min_s": round(min(lats), 2) if lats else None,
            "lat_max_s": round(max(lats), 2) if lats else None,
            "lat_mean_s": round(sum(lats) / len(lats), 2) if lats else None,
            "ttft_mean_s": round(sum(pm["ttfts"]) / len(pm["ttfts"]), 2) if pm["ttfts"] else None,
            "tok_s": round(pm["tokens"] / pm["time"], 1) if pm["time"] else None,
            "time_total_s": round(pm["time"], 1),
            "time_share_pct": round(100.0 * pm["time"] / total_time, 1) if total_time else None,
            "por_categoria": {c: round(v["sum"] / v["n"], 1) for c, v in pm["by_cat"].items() if v["n"]},
            "checks": sorted(
                [{"code": c, "label": CODE_LABEL.get(c, c), "pass": v["pass"], "total": v["total"],
                  "pct": round(100.0 * v["pass"] / v["total"], 0)} for c, v in pm["checks"].items() if v["total"]],
                key=lambda x: x["pct"]),
            "spec": {"params": md.get("params"), "params_b": md.get("params_b"),
                     "quant": md.get("quant"), "ctx": md.get("ctx"), "arch": md.get("arch")},
            "footprint": {"size_gib": size,
                          "pct_ram": round(100.0 * size / ram_total, 1) if size and ram_total else None,
                          "processor": fp_proc.get(key)},
            "eficiencia_nota_gb": round(nota / size, 1) if nota is not None and size else None,
        })
    models_out.sort(key=lambda x: (x["nota_media"] is not None, x["nota_media"] or 0), reverse=True)

    # ---- progress.by_model (inclui pendentes)
    n_done = len(results)
    current_model = None
    if sysmon and sysmon[-1].get("loaded_model"):
        current_model = sysmon[-1]["loaded_model"]
    elif results:
        current_model = results[-1]["model"]
    cur_key = re.sub(r":latest$", "", current_model) if current_model else None

    by_model = []
    for m in models:
        name = m["name"]
        done = per_model[name]["done"] if name in per_model else 0
        tot = model_total[name]
        if done >= tot and tot > 0:
            status = "done"
        elif re.sub(r":latest$", "", name) == cur_key and done < tot:
            status = "running"
        elif 0 < done < tot:
            status = "running"
        else:
            status = "pending"
        by_model.append({"model": name, "label": label_of(name), "tier": m["tier"],
                         "thinking": bool(m.get("thinking")), "done": done, "total": tot,
                         "status": status})
    # ordena: rodando, depois pendentes, depois concluidos; dentro, por tier
    order = {"running": 0, "pending": 1, "done": 2}
    by_model.sort(key=lambda x: (order[x["status"]], TIER_ORDER.index(x["tier"]) if x["tier"] in TIER_ORDER else 9))

    # ---- ETA POR TIER: cada tier estima com a propria velocidade; tier ainda sem
    # amostra usa um prior (multiplicador sobre a media global) p/ nao subestimar o 70B.
    # NAO inclui tempo de download de modelos da 2a leva (some da conta uma vez baixados).
    avg_item = total_time / n_done if n_done else 0
    TIER_PRIOR = {"barato": 1.0, "medio": 2.5, "pesado": 35.0}
    tier_done_c, tier_time_c = defaultdict(int), defaultdict(float)
    for pmv in per_model.values():
        tier_done_c[pmv["tier"]] += pmv["done"]
        tier_time_c[pmv["tier"]] += pmv["time"]
    eta = 0.0
    for t in TIER_ORDER:
        rem = max(0, per_tier_total.get(t, 0) - tier_done_c.get(t, 0))
        if not rem:
            continue
        if tier_done_c.get(t):
            eta += rem * (tier_time_c[t] / tier_done_c[t])
        else:
            eta += rem * (avg_item * TIER_PRIOR.get(t, 1.0))
    eta = round(eta) if (n_done and total_expected > n_done) else (0 if n_done else None)
    remaining = max(0, total_expected - n_done)
    pct = round(100.0 * n_done / total_expected, 1) if total_expected else 0.0

    # ---- best (por variante, p/ distinguir thinking on/off)
    lb = []
    for (model, thinking), pv in per_variant.items():
        if pv["n"]:
            lb.append({"model": model, "label": label_of(model), "tier": pv["tier"],
                       "thinking": thinking, "n": pv["n"],
                       "nota_media": round(pv["sum"] / pv["n"], 1),
                       "latencia_media_s": round(pv["time"] / pv["n"], 2)})
    lb.sort(key=lambda x: x["nota_media"], reverse=True)
    best = None
    if lb:
        by_tier = {}
        for t in TIER_ORDER:
            rows = [r for r in lb if r["tier"] == t]
            by_tier[t] = ({"model": rows[0]["model"], "label": rows[0]["label"],
                           "thinking": rows[0]["thinking"], "nota_media": rows[0]["nota_media"],
                           "latencia_media_s": rows[0]["latencia_media_s"]} if rows else None)
        best_value = None
        for t in TIER_ORDER:
            if by_tier.get(t):
                bv = by_tier[t]
                best_value = {"model": bv["model"], "label": bv["label"], "thinking": bv["thinking"],
                              "tier": t, "nota_media": bv["nota_media"],
                              "latencia_media_s": bv["latencia_media_s"]}
                break
        best = {"overall": {"model": lb[0]["model"], "label": lb[0]["label"],
                            "thinking": lb[0]["thinking"], "tier": lb[0]["tier"],
                            "nota_media": lb[0]["nota_media"]},
                "by_tier": by_tier, "best_value": best_value}

    # ---- por_pergunta (dificuldade)
    por_pergunta = []
    for qid, pq in per_q.items():
        q = qmap.get(qid, {})
        por_pergunta.append({"id": qid, "category": q.get("category"),
                             "user": q.get("user"),
                             "nota_media": round(pq["sum"] / pq["n"], 1) if pq["n"] else None,
                             "n": pq["n"]})
    por_pergunta.sort(key=lambda x: (x["nota_media"] is None, x["nota_media"] if x["nota_media"] is not None else 999))

    # ---- server (ultima amostra)
    server = None
    if sysmon:
        s = sysmon[-1]
        ru, rt = s.get("ram_used_gib"), s.get("ram_total_gib")
        vu, vt = s.get("vram_used_gib"), s.get("vram_total_gib")
        server = {"ram_used_gib": ru, "ram_total_gib": rt,
                  "ram_pct": round(100.0 * ru / rt, 1) if ru and rt else None,
                  "vram_used_gib": vu, "vram_total_gib": vt,
                  "vram_pct": round(100.0 * vu / vt, 1) if vu and vt else None,
                  "cpu_pct": s.get("cpu_pct"), "current_model": s.get("loaded_model"),
                  "current_processor": s.get("processor"), "sampled_at": s.get("t")}

    anchors = {}
    sp = os.path.join(root, "..", "b1", "schema_b1.json")
    if os.path.exists(sp):
        anchors = json.load(open(sp, encoding="utf-8")).get("anchors", {})

    out = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "anchors": {"today": anchors.get("today"), "dataLastDay": anchors.get("dataLastDay"),
                    "SMALL_SAMPLE_LIMIT": anchors.get("SMALL_SAMPLE_LIMIT")},
        "progress": {"total_expected": total_expected, "n_done": n_done, "n_error": n_error,
                     "pct": pct, "eta_seconds": eta, "compute_elapsed_s": round(total_time),
                     "current_model": current_model, "by_model": by_model},
        "models": models_out,
        "best": best,
        "server": server,
        "por_pergunta": por_pergunta,
        "checks_resumo": sorted(
            [{"code": c, "label": CODE_LABEL.get(c, c), "pass": v["pass"], "total": v["total"],
              "pct": round(100.0 * v["pass"] / v["total"], 0)} for c, v in check_global.items() if v["total"]],
            key=lambda x: x["pct"]),
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"dashboard: {n_done}/{total_expected} ({pct}%) eta={eta}s "
          f"lider={best['overall']['label'] if best else '-'} -> {args.out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--results", default="../results_b1.jsonl")
    ap.add_argument("--questions", default="../b1/questions_b1.jsonl")
    ap.add_argument("--models", default="models.jsonl")
    ap.add_argument("--out", default="../dashboard_b1.json")
    build(ap.parse_args())


if __name__ == "__main__":
    main()
