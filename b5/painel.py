"""b5 — painel ao vivo (HTML autocontido) e RESULTADOS.md."""

from __future__ import annotations

import json
import os
import statistics
from datetime import datetime


def _juntar(conversas: list, julgamentos: list) -> list:
    jul = {(j["id"], j.get("tentativa")): j for j in julgamentos}
    ultimo = {}
    for c in conversas:
        ultimo[c["id"]] = c  # a última tentativa concluída vale
    out = []
    for c in ultimo.values():
        j = jul.get((c["id"], c.get("tentativa"))) or {}
        out.append({**c, "juiz": {"modelo": j.get("juiz_modelo"), "dur_s": j.get("juiz_dur_s"),
                                  "custo_usd": j.get("juiz_custo_usd"), "erro": j.get("erro"),
                                  "v": j.get("veredito")}})
    return out


def gerar(path: str, estado: dict, conversas: list, julgamentos: list, objetivos: list) -> None:
    dados = {
        "gerado": datetime.now().isoformat(timespec="seconds"),
        "estado": estado,
        "conversas": _juntar(conversas, julgamentos),
        "n_objetivos": len(objetivos),
    }
    js = json.dumps(dados, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.replace("__DADOS__", js)
    tmp = path + ".tmp"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html)
    os.replace(tmp, path)


# ------------------------------------------------------------------ markdown

def _pct(n, d):
    return f"{100 * n / d:.0f}%" if d else "—"


def _q(vals, q):
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return None
    k = (len(vals) - 1) * q
    lo = int(k)
    hi = min(lo + 1, len(vals) - 1)
    return vals[lo] + (vals[hi] - vals[lo]) * (k - lo)


def resultados_md(estado: dict, conversas: list, julgamentos: list, objetivos: list, p_painel: str) -> str:
    cs = _juntar(conversas, julgamentos)
    jv = [c for c in cs if c["juiz"]["v"]]
    n, nj = len(cs), len(jv)
    sat = {k: sum(1 for c in jv if c["juiz"]["v"]["cliente_satisfeito"]["valor"] == k) for k in ("sim", "parcial", "nao")}
    cumpr = sum(1 for c in jv if c["juiz"]["v"]["objetivo_cumprido"])
    alu = sum(1 for c in jv if c["juiz"]["v"]["alucinacao"]["houve"])
    esc = {}
    for c in jv:
        a = c["juiz"]["v"]["escalonamento"]["avaliacao"]
        esc[a] = esc.get(a, 0) + 1
    ng = [c["juiz"]["v"]["nota_geral"] for c in jv]
    nq = [c["juiz"]["v"]["nota_qualidade"] for c in jv]
    turnos = [t for c in cs for t in c["transcricao"]]
    lat = [t["latencia_s"] for t in turnos if not t.get("gate") and t.get("latencia_s") is not None]
    fontes = {}
    for t in turnos:
        k = "escalou" if t.get("escalou") else (t.get("fonte") or "?")
        fontes[k] = fontes.get(k, 0) + 1
    L = [f"# B5 — conversa dinâmica: resultados",
         "",
         f"- Rodada: início {estado.get('inicio')} · prazo {estado.get('prazo')} · fim {estado.get('finalizado')}",
         f"- Org `{(estado.get('config_bot') or {}).get('org')}` · modelo `{(estado.get('config_bot') or {}).get('modelo')}` · threshold {(estado.get('config_bot') or {}).get('threshold')}",
         f"- Conversas concluídas: **{n}** de {len(objetivos)} objetivos · julgadas: {nj} · fallbacks opencode: {(estado.get('fallback') or {}).get('n_fallbacks')}",
         f"- Painel: `{p_painel}`",
         "",
         "## Números",
         "",
         "| Métrica | Valor |", "|---|---|",
         f"| Cliente satisfeito (juiz) sim / parcial / não | {sat['sim']} / {sat['parcial']} / {sat['nao']} ({_pct(sat['sim'], nj)} sim) |",
         f"| Objetivo cumprido | {cumpr}/{nj} ({_pct(cumpr, nj)}) |",
         f"| Nota geral média | {statistics.mean(ng):.2f} |" if ng else "| Nota geral média | — |",
         f"| Nota de qualidade média | {statistics.mean(nq):.2f} |" if nq else "| Nota de qualidade média | — |",
         f"| Escalonamento | {', '.join(f'{k}: {v}' for k, v in sorted(esc.items()))} |",
         f"| Conversas com alucinação | {alu}/{nj} ({_pct(alu, nj)}) |",
         f"| Latência do turno do bot p50 / p95 / máx | {_q(lat, .5) or 0:.1f}s / {_q(lat, .95) or 0:.1f}s / {max(lat) if lat else 0:.1f}s |",
         f"| Turnos por conversa (média) | {statistics.mean([c['n_turnos'] for c in cs]):.1f} |" if cs else "| Turnos por conversa | — |",
         f"| Fonte das respostas (turnos) | {', '.join(f'{k}: {v}' for k, v in sorted(fontes.items(), key=lambda x: -x[1]))} |",
         "", "## Por trilha", "", "| Trilha | n | cumprido | sat. sim | nota geral | alucinação |", "|---|---|---|---|---|---|"]
    trilhas = sorted({c["trilha"] for c in cs})
    for tr in trilhas:
        g = [c for c in jv if c["trilha"] == tr]
        if not g:
            continue
        L.append(f"| {tr} | {len(g)} | {_pct(sum(1 for c in g if c['juiz']['v']['objetivo_cumprido']), len(g))} | "
                 f"{_pct(sum(1 for c in g if c['juiz']['v']['cliente_satisfeito']['valor'] == 'sim'), len(g))} | "
                 f"{statistics.mean(c['juiz']['v']['nota_geral'] for c in g):.1f} | "
                 f"{_pct(sum(1 for c in g if c['juiz']['v']['alucinacao']['houve']), len(g))} |")
    ordenadas = sorted(jv, key=lambda c: (c["juiz"]["v"]["nota_geral"], c["juiz"]["v"]["nota_qualidade"]))

    def linha(c):
        v = c["juiz"]["v"]
        prob = "; ".join(v.get("problemas") or [])[:220]
        dest = "; ".join(v.get("destaques") or [])[:220]
        return (f"| [`{c['id']}`](painel.html#{c['id']}) | {c['trilha']} | {v['nota_geral']} | "
                f"{v['cliente_satisfeito']['valor']} | {c['parada']} | {prob or dest} |")

    L += ["", "## 10 piores", "", "| id | trilha | nota | satisf. | parada | problemas |", "|---|---|---|---|---|---|"]
    L += [linha(c) for c in ordenadas[:10]]
    L += ["", "## 10 melhores", "", "| id | trilha | nota | satisf. | parada | destaques/obs. |", "|---|---|---|---|---|---|"]
    L += [linha(c) for c in list(reversed(ordenadas))[:10]]
    L += ["", "Transcrição completa de cada conversa: `painel.html` (abrir por file://) ou `resultados/conversas.jsonl`; veredito: `resultados/julgamentos.jsonl`.", ""]
    return "\n".join(L)


TEMPLATE = r"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="15">
<title>B5 conversa dinâmica</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{--bg:#f6f7f9;--card:#fff;--tx:#1b1f24;--mut:#5f6b7a;--bd:#e3e6ea;--ac:#3b5bdb;
--ok:#1a7f37;--okb:#e6f4ea;--warn:#9a6700;--warnb:#fff4d6;--bad:#c62828;--badb:#fdecea;--chip:#eef1f5}
@media (prefers-color-scheme:dark){:root{--bg:#0f1216;--card:#171b21;--tx:#e6e9ee;--mut:#9aa5b4;--bd:#2a313a;--ac:#8ea6ff;
--ok:#4cc472;--okb:#12301d;--warn:#e3b341;--warnb:#33290f;--bad:#ff6b6b;--badb:#3a1616;--chip:#222831}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);font:14px/1.5 Poppins,system-ui,-apple-system,Segoe UI,sans-serif}
.num,td.n,.kv{font-variant-numeric:tabular-nums}
header{padding:16px;border-bottom:1px solid var(--bd);background:var(--card);position:sticky;top:0;z-index:2}
header h1{margin:0;font-size:18px;font-weight:600}
header .sub{color:var(--mut);font-size:12px}
nav{display:flex;gap:4px;margin-top:10px;flex-wrap:wrap}
nav button{font:inherit;border:1px solid var(--bd);background:var(--chip);color:var(--tx);padding:5px 12px;border-radius:999px;cursor:pointer}
nav button.on{background:var(--ac);color:#fff;border-color:var(--ac)}
main{padding:16px;max-width:1280px;margin:0 auto}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:10px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:12px}
.card h3{margin:0 0 4px;font-size:12px;font-weight:500;color:var(--mut)}
.big{font-size:24px;font-weight:600}
.small{font-size:12px;color:var(--mut)}
h2{font-size:15px;font-weight:600;margin:22px 0 8px}
.bar{height:8px;border-radius:4px;background:var(--chip);overflow:hidden;display:flex;margin-top:6px}
.bar i{display:block;height:100%}
.ok{color:var(--ok)}.warn{color:var(--warn)}.bad{color:var(--bad)}
.bok{background:var(--ok)}.bwarn{background:var(--warn)}.bbad{background:var(--bad)}.bmut{background:var(--mut)}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--bd);border-radius:10px;overflow:hidden}
th,td{padding:7px 9px;border-bottom:1px solid var(--bd);text-align:left;vertical-align:top}
th{font-size:12px;font-weight:500;color:var(--mut);background:var(--chip)}
td.n,th.n{text-align:right}
.wrap{overflow-x:auto}
.pill{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;background:var(--chip)}
.pill.ok{background:var(--okb)}.pill.warn{background:var(--warnb)}.pill.bad{background:var(--badb)}
.filtros{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}
select,input{font:inherit;padding:5px 8px;border:1px solid var(--bd);border-radius:8px;background:var(--card);color:var(--tx)}
details.conv{background:var(--card);border:1px solid var(--bd);border-radius:10px;margin-bottom:8px}
details.conv>summary{cursor:pointer;padding:10px 12px;display:flex;gap:8px;flex-wrap:wrap;align-items:center;list-style:none}
details.conv>summary::-webkit-details-marker{display:none}
.corpo{padding:0 12px 12px}
.msg{margin:6px 0;padding:8px 10px;border-radius:10px;max-width:760px;white-space:pre-wrap;word-wrap:break-word}
.cli{background:var(--chip)}
.bot{background:var(--okb);margin-left:auto}
.meta{font-size:11px;color:var(--mut);margin:-2px 0 8px;text-align:right}
.veredito{border-top:1px solid var(--bd);margin-top:10px;padding-top:8px;font-size:13px}
.veredito ul{margin:4px 0;padding-left:18px}
.vazio{color:var(--mut);padding:20px;text-align:center}
@media (max-width:600px){main{padding:12px 16px}.big{font-size:20px}.msg{max-width:100%}}
</style>
</head>
<body>
<header>
  <h1>B5 — conversa dinâmica <span class="small" id="org"></span></h1>
  <div class="sub" id="sub"></div>
  <nav id="nav"></nav>
</header>
<main id="main"></main>
<script type="application/json" id="dados">__DADOS__</script>
<script>
const D = JSON.parse(document.getElementById('dados').textContent);
const E = D.estado || {};
const CS = D.conversas || [];
const ls = {get(k,d){try{const v=localStorage.getItem('b5.'+k);return v===null?d:JSON.parse(v)}catch(e){return d}},
            set(k,v){try{localStorage.setItem('b5.'+k,JSON.stringify(v))}catch(e){}}};
const esc = s => String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const q = (a,p) => {a=a.filter(x=>x!=null).sort((x,y)=>x-y); if(!a.length) return null; const k=(a.length-1)*p, lo=Math.floor(k), hi=Math.min(lo+1,a.length-1); return a[lo]+(a[hi]-a[lo])*(k-lo)};
const f1 = x => x==null?'—':(+x).toFixed(1);
const pct = (n,d) => d? Math.round(100*n/d)+'%':'—';
const mean = a => a.length? a.reduce((s,x)=>s+x,0)/a.length : null;
const hms = s => {if(s==null||s<0) s=0; s=Math.round(s); const h=Math.floor(s/3600), m=Math.floor(s%3600/60); return h? h+'h'+String(m).padStart(2,'0') : m+'min'+String(s%60).padStart(2,'0')+'s'};
const cor = (v,bom,ruim,maiorMelhor=true) => v==null?'':(maiorMelhor?(v>=bom?'ok':v<=ruim?'bad':'warn'):(v<=bom?'ok':v>=ruim?'bad':'warn'));
const V = c => (c.juiz||{}).v;
const JV = CS.filter(V);
const TURNOS = CS.flatMap(c=>c.transcricao||[]);
function categoriaFonte(t){ if(t.erro) return 'erro'; if(t.escalou) return 'escalou'; if(t.gate) return 'gate'; const f=(t.fonte||'?'); if(/sauda/i.test(f)) return 'saudação'; return f; }

const agora = new Date(), ini = new Date(E.inicio), prazo = new Date(E.prazo);
const decorrido = (agora-ini)/1000, restante = (prazo-agora)/1000;
const durMed = mean(CS.map(c=>c.duracao_s).filter(x=>x));
const estim = CS.length + (durMed && restante>0 ? Math.floor(restante/durMed) : 0);
document.getElementById('org').textContent = E.config_bot ? `· ${E.config_bot.org} · ${E.config_bot.modelo}` : '';
document.getElementById('sub').textContent = `atualizado ${D.gerado.replace('T',' ')} · recarrega a cada 15 s` + (E.finalizado?' · RODADA FINALIZADA':'');

const ABAS = [['geral','Visão geral'],['vivo','Ao vivo'],['trilhas','Por trilha'],['conversas','Conversas']];
let aba = ls.get('aba','geral');
const nav = document.getElementById('nav');
ABAS.forEach(([k,t])=>{const b=document.createElement('button'); b.textContent=t; b.onclick=()=>{aba=k; ls.set('aba',k); render(); window.scrollTo(0,0)}; b.dataset.k=k; nav.appendChild(b)});

function card(t, big, sub, cls){return `<div class="card"><h3>${t}</h3><div class="big num ${cls||''}">${big}</div>${sub?`<div class="small">${sub}</div>`:''}</div>`}
function barra(partes){const tot=partes.reduce((s,p)=>s+p[0],0)||1; return `<div class="bar">${partes.map(p=>`<i class="${p[1]}" style="width:${100*p[0]/tot}%" title="${p[2]}: ${p[0]}"></i>`).join('')}</div>`}

function geral(){
  const fb = E.fallback||{}, um = fb.ultimo_modelo||{};
  const sat = {sim:0,parcial:0,nao:0}; JV.forEach(c=>sat[V(c).cliente_satisfeito.valor]++);
  const cumpr = JV.filter(c=>V(c).objetivo_cumprido).length;
  const ng = mean(JV.map(c=>V(c).nota_geral)), nq = mean(JV.map(c=>V(c).nota_qualidade));
  const escA = {adequado:0,desnecessario:0,faltou:0,nao_se_aplica:0}; JV.forEach(c=>escA[V(c).escalonamento.avaliacao]++);
  const alu = JV.filter(c=>V(c).alucinacao.houve).length;
  const lat = TURNOS.filter(t=>!t.gate && t.latencia_s!=null).map(t=>t.latencia_s);
  const fontes = {}; TURNOS.forEach(t=>{const k=categoriaFonte(t); fontes[k]=(fontes[k]||0)+1});
  const etapas = {}; TURNOS.forEach(t=>(t.etapas||[]).forEach(s=>{(etapas[s.stage]=etapas[s.stage]||{l:[],ti:0,to:0}); etapas[s.stage].l.push(s.latency_s); etapas[s.stage].ti+=s.tok_in||0; etapas[s.stage].to+=s.tok_out||0}));
  const tpc = CS.map(c=>c.n_turnos);
  const paradas = {}; CS.forEach(c=>paradas[c.parada]=(paradas[c.parada]||0)+1);
  let h = `<h2>Progresso</h2><div class="grid">
   ${card('Conversas concluídas', `${CS.length} <span class="small">/ ${E.total_planejado||D.n_objetivos}</span>`, `estimativa até o prazo: ~${estim}`)}
   ${card('Tempo decorrido', hms(decorrido), `início ${esc((E.inicio||'').replace('T',' '))}`)}
   ${card('Tempo restante', E.finalizado?'—':hms(restante), `prazo ${esc((E.prazo||'').replace('T',' '))}`, restante<1800&&!E.finalizado?'warn':'')}
   ${card('Em andamento', E.em_andamento? esc(E.em_andamento.id) : '—', E.em_andamento? esc(E.em_andamento.fase||''):'')}
   ${card('Modelo do cliente / juiz', `<span style="font-size:14px">${esc((um.cliente||'—').split('/').pop())}<br>${esc((um.juiz||'—').split('/').pop())}</span>`, `fallbacks opencode: ${fb.n_fallbacks||0}${fb.em_janela_fallback?' · EM JANELA DE FALLBACK':''}`, fb.n_fallbacks?'warn':'')}
   ${card('Duração média / conversa', durMed? hms(durMed):'—', `paradas: ${Object.entries(paradas).map(([k,v])=>k+' '+v).join(', ')||'—'}`)}
  </div>
  <h2>Qualidade (juiz)</h2><div class="grid">
   ${card('Cliente satisfeito', pct(sat.sim,JV.length), `sim ${sat.sim} · parcial ${sat.parcial} · não ${sat.nao}`+barra([[sat.sim,'bok','sim'],[sat.parcial,'bwarn','parcial'],[sat.nao,'bbad','não']]), cor(JV.length?sat.sim/JV.length:null,.7,.4))}
   ${card('Objetivo cumprido', pct(cumpr,JV.length), `${cumpr} de ${JV.length} julgadas`, cor(JV.length?cumpr/JV.length:null,.75,.5))}
   ${card('Nota geral média', f1(ng), '0–10', cor(ng,7.5,5))}
   ${card('Nota de qualidade média', f1(nq), '0–10', cor(nq,7.5,5))}
   ${card('Escalonamento', `${escA.adequado} <span class="small">adequado</span>`, `desnecessário ${escA.desnecessario} · faltou ${escA.faltou} · n/a ${escA.nao_se_aplica}`+barra([[escA.adequado,'bok','adequado'],[escA.nao_se_aplica,'bmut','n/a'],[escA.desnecessario,'bwarn','desnecessário'],[escA.faltou,'bbad','faltou']]))}
   ${card('Alucinação', pct(alu,JV.length), `${alu} conversas com trecho inventado`, cor(JV.length?alu/JV.length:null,.05,.15,false))}
  </div>
  <h2>Bot</h2><div class="grid">
   ${card('Latência do turno p50', f1(q(lat,.5))+'s', `${lat.length} turnos (sem gates)`, cor(q(lat,.5),15,40,false))}
   ${card('Latência do turno p95', f1(q(lat,.95))+'s', `máx ${f1(lat.length?Math.max(...lat):null)}s`, cor(q(lat,.95),30,60,false))}
   ${card('Turnos por conversa', f1(mean(tpc)), `máx ${tpc.length?Math.max(...tpc):'—'}`)}
   ${card('Fonte das respostas', TURNOS.length, Object.entries(fontes).sort((a,b)=>b[1]-a[1]).map(([k,v])=>`${esc(k)} ${pct(v,TURNOS.length)}`).join(' · '))}
  </div>
  <h2>Latência por etapa (LLM)</h2><div class="wrap"><table><tr><th>Etapa</th><th class="n">chamadas</th><th class="n">p50 (s)</th><th class="n">p95 (s)</th><th class="n">tokens in (méd.)</th><th class="n">tokens out (méd.)</th></tr>
  ${Object.entries(etapas).sort((a,b)=>b[1].l.length-a[1].l.length).map(([k,e])=>`<tr><td>${esc(k)}</td><td class="n">${e.l.length}</td><td class="n">${f1(q(e.l,.5))}</td><td class="n">${f1(q(e.l,.95))}</td><td class="n">${Math.round(e.ti/e.l.length)}</td><td class="n">${Math.round(e.to/e.l.length)}</td></tr>`).join('') || '<tr><td colspan="6" class="vazio">sem dados ainda</td></tr>'}
  </table></div>`;
  return h;
}

function turnoHtml(t){
  const meta = [t.latencia_s!=null?`${f1(t.latencia_s)}s`:null, t.gate?`gate: ${t.gate}`:null, t.fonte?`fonte: ${t.fonte}`:null,
    t.confianca!=null?`conf ${(+t.confianca).toFixed(2)}`:null, t.entrada_id?`entrada ${t.entrada_id}`:null,
    t.escalou?`ESCALOU (${t.motivo_escalonamento})`:null, t.guard?`guard: ${t.guard}`:null, t.erro?`ERRO: ${t.erro}`:null,
    (t.etapas||[]).length? (t.etapas.map(s=>`${s.stage} ${f1(s.latency_s)}`).join(' · ')):null,
    t.cliente_modelo?`cliente: ${t.cliente_modelo.split('/').pop()}`:null].filter(Boolean).join(' · ');
  return `<div class="msg cli">${esc(t.texto_cliente)}</div><div class="msg bot">${esc(t.texto_bot||'(sem resposta)')}</div><div class="meta">turno ${t.n} · ${esc(meta)}</div>`;
}

function vivo(){
  const a = E.em_andamento;
  if(!a) return `<div class="vazio">${E.finalizado?'Rodada finalizada.':'Nenhuma conversa em andamento neste instante.'}</div>` + (CS.length? '<h2>Última concluída</h2>'+convHtml(CS[CS.length-1], true):'');
  return `<div class="card"><b>${esc(a.id)}</b> <span class="pill">${esc(a.trilha)}</span> <span class="small">tentativa ${a.tentativa} · desde ${esc((a.inicio||'').replace('T',' '))}</span>
   <div class="small" style="margin-top:4px">${esc(a.objetivo)}</div><div style="margin-top:6px"><span class="pill warn">${esc(a.fase||'')}</span></div></div>
   <div style="margin-top:10px">${(a.turnos||[]).map(turnoHtml).join('')}${a.cliente_pendente?`<div class="msg cli">${esc(a.cliente_pendente)}</div><div class="meta">aguardando o bot…</div>`:''}</div>`;
}

function trilhas(){
  const g = {}; CS.forEach(c=>(g[c.trilha]=g[c.trilha]||[]).push(c));
  const rows = Object.entries(g).sort().map(([k,cs])=>{const j=cs.filter(V); const ng=mean(j.map(c=>V(c).nota_geral)); const cu=j.filter(c=>V(c).objetivo_cumprido).length; const sa=j.filter(c=>V(c).cliente_satisfeito.valor==='sim').length; const al=j.filter(c=>V(c).alucinacao.houve).length; const es=cs.filter(c=>c.parada==='escalou').length; const lat=cs.flatMap(c=>c.transcricao).filter(t=>!t.gate&&t.latencia_s!=null).map(t=>t.latencia_s);
    return `<tr><td>${esc(k)}</td><td class="n">${cs.length}</td><td class="n ${cor(j.length?cu/j.length:null,.75,.5)}">${pct(cu,j.length)}</td><td class="n ${cor(j.length?sa/j.length:null,.7,.4)}">${pct(sa,j.length)}</td><td class="n ${cor(ng,7.5,5)}">${f1(ng)}</td><td class="n ${cor(j.length?al/j.length:null,.05,.15,false)}">${pct(al,j.length)}</td><td class="n">${pct(es,cs.length)}</td><td class="n">${f1(mean(cs.map(c=>c.n_turnos)))}</td><td class="n">${f1(q(lat,.5))}</td></tr>`}).join('');
  return `<div class="wrap"><table><tr><th>Trilha</th><th class="n">n</th><th class="n">cumprido</th><th class="n">satisf. sim</th><th class="n">nota geral</th><th class="n">alucinação</th><th class="n">escalou</th><th class="n">turnos</th><th class="n">lat. p50 (s)</th></tr>${rows||'<tr><td colspan="9" class="vazio">sem dados ainda</td></tr>'}</table></div>`;
}

function convHtml(c, aberto){
  const v = V(c);
  const nota = v? v.nota_geral : null;
  const sat = v? v.cliente_satisfeito.valor : null;
  const scls = sat==='sim'?'ok':sat==='parcial'?'warn':sat==='nao'?'bad':'';
  const ver = v? `<div class="veredito"><b>Juiz</b> <span class="small">(${esc((c.juiz.modelo||'').split('/').pop())}, ${f1(c.juiz.dur_s)}s)</span> — cumprido: <b>${v.objetivo_cumprido?'sim':'não'}</b> · satisfeito: <b>${esc(sat)}</b> (${esc(v.cliente_satisfeito.justificativa)}) · escalonamento: <b>${esc(v.escalonamento.avaliacao)}</b> (${esc(v.escalonamento.justificativa)}) · qualidade ${f1(v.nota_qualidade)} · geral ${f1(v.nota_geral)}
     ${v.alucinacao.houve?`<div class="bad">Alucinação: ${v.alucinacao.trechos.map(esc).join(' | ')}</div>`:''}
     ${(v.problemas||[]).length?`<div>Problemas:<ul>${v.problemas.map(p=>`<li>${esc(p)}</li>`).join('')}</ul></div>`:''}
     ${(v.destaques||[]).length?`<div>Destaques:<ul>${v.destaques.map(p=>`<li>${esc(p)}</li>`).join('')}</ul></div>`:''}
     <div class="small">Por turno: ${(v.qualidade_por_turno||[]).map(x=>`t${x.turno} ${x.nota} — ${esc(x.comentario)}`).join(' · ')}</div></div>`
     : `<div class="veredito small">${c.juiz&&c.juiz.erro?'Juiz falhou: '+esc(c.juiz.erro):'sem veredito'}</div>`;
  return `<details class="conv" id="${esc(c.id)}" data-id="${esc(c.id)}" ${aberto?'open':''}><summary><b>${esc(c.id)}</b><span class="pill">${esc(c.trilha)}</span>
     <span class="pill ${cor(nota,7.5,5)}">nota ${f1(nota)}</span><span class="pill ${scls}">${esc(sat||'—')}</span><span class="pill">${esc(c.parada)}</span>
     <span class="small">${c.n_turnos} turnos · ${hms(c.duracao_s)} · esperado: ${esc(c.comportamento_esperado)}</span></summary>
     <div class="corpo"><div class="small">${esc(c.objetivo)}<br>Persona: ${esc((c.persona||{}).nome)} — ${esc((c.persona||{}).estilo_escrita)}, ${esc((c.persona||{}).tom)}</div>
     ${(c.transcricao||[]).map(turnoHtml).join('')}${c.reacao_final?`<div class="msg cli">${esc(c.reacao_final)}</div><div class="meta">reação final do cliente</div>`:''}${ver}</div></details>`;
}

function conversas(){
  const fl = ls.get('filtros',{trilha:'',sat:'',nota:'',busca:''});
  const trs = [...new Set(CS.map(c=>c.trilha))].sort();
  const lista = CS.filter(c=>{const v=V(c); if(fl.trilha&&c.trilha!==fl.trilha) return false; if(fl.sat&&(!v||v.cliente_satisfeito.valor!==fl.sat)) return false;
     if(fl.nota==='ruim'&&!(v&&v.nota_geral<5)) return false; if(fl.nota==='media'&&!(v&&v.nota_geral>=5&&v.nota_geral<7.5)) return false; if(fl.nota==='boa'&&!(v&&v.nota_geral>=7.5)) return false;
     if(fl.busca&&!JSON.stringify(c).toLowerCase().includes(fl.busca.toLowerCase())) return false; return true}).reverse();
  const abertos = ls.get('abertos',[]);
  return `<div class="filtros">
    <select id="f-trilha"><option value="">todas as trilhas</option>${trs.map(t=>`<option ${fl.trilha===t?'selected':''}>${esc(t)}</option>`).join('')}</select>
    <select id="f-sat"><option value="">toda satisfação</option>${['sim','parcial','nao'].map(s=>`<option ${fl.sat===s?'selected':''}>${s}</option>`).join('')}</select>
    <select id="f-nota"><option value="">toda nota</option><option value="ruim" ${fl.nota==='ruim'?'selected':''}>&lt; 5</option><option value="media" ${fl.nota==='media'?'selected':''}>5–7,5</option><option value="boa" ${fl.nota==='boa'?'selected':''}>≥ 7,5</option></select>
    <input id="f-busca" placeholder="buscar texto" value="${esc(fl.busca)}">
    <span class="small" style="align-self:center">${lista.length} conversas</span></div>
    ${lista.map(c=>convHtml(c, abertos.includes(c.id) || location.hash==='#'+c.id)).join('') || '<div class="vazio">nenhuma conversa</div>'}`;
}

function render(){
  [...nav.children].forEach(b=>b.classList.toggle('on', b.dataset.k===aba));
  const m = document.getElementById('main');
  m.innerHTML = aba==='vivo'?vivo(): aba==='trilhas'?trilhas(): aba==='conversas'?conversas(): geral();
  if(aba==='conversas'){
    const fl = ls.get('filtros',{trilha:'',sat:'',nota:'',busca:''});
    [['f-trilha','trilha'],['f-sat','sat'],['f-nota','nota']].forEach(([id,k])=>document.getElementById(id).onchange=e=>{fl[k]=e.target.value; ls.set('filtros',fl); render()});
    const b=document.getElementById('f-busca'); b.onchange=e=>{fl.busca=e.target.value; ls.set('filtros',fl); render()};
    m.querySelectorAll('details.conv').forEach(d=>d.addEventListener('toggle',()=>{let a=ls.get('abertos',[]); a=a.filter(x=>x!==d.dataset.id); if(d.open) a.push(d.dataset.id); ls.set('abertos',a.slice(-40))}));
  }
}
if(location.hash && location.hash.length>1){ aba='conversas'; }
render();
const sy = ls.get('scroll.'+aba, 0); if(sy) window.scrollTo(0, sy);
if(location.hash){const el=document.getElementById(location.hash.slice(1)); if(el) el.scrollIntoView();}
let tmo; window.addEventListener('scroll',()=>{clearTimeout(tmo); tmo=setTimeout(()=>ls.set('scroll.'+aba, window.scrollY),150)});
</script>
</body>
</html>
"""
